import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os
import plotly.graph_objects as go
import time

# -------------------
# Constants
# -------------------
MODEL_FILE = "rf_model.pkl"
BUY_THRESHOLD = 0.55
SELL_THRESHOLD = 0.45
FEATURE_COLS = [
    'open_price', 'close_price', 'delta', 'delta_abs',
    'prev_direction', 'hour', 'minute', 'seconds_to_close'
]

# -------------------
# Helper Functions
# -------------------
def parse_expiration(value):
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip().upper()
    if value.startswith("S"):
        return float(value.replace("S", ""))
    if value.startswith("M"):
        return float(value.replace("M", "")) * 60
    return 60.0

def preprocess_data(df):
    df = df.copy()
    df['Open time'] = pd.to_datetime(df['Open time'])
    df['seconds_to_close'] = df['Expiration'].apply(parse_expiration)

    df['delta'] = df['Close price'] - df['Open price']
    df['delta_abs'] = df['delta'].abs()
    df['prev_direction'] = (df['delta'] > 0).astype(int)
    df['hour'] = df['Open time'].dt.hour
    df['minute'] = df['Open time'].dt.minute

    df['target'] = (df['Close price'].shift(-1) > df['Close price']).astype(int)
    df.dropna(inplace=True)

    X = df.rename(columns={
        'Open price': 'open_price',
        'Close price': 'close_price'
    })[FEATURE_COLS]
    y = df['target']
    return X, y

def predict_next_candle(model, recent_candles, expiration):
    """
    recent_candles: list of 3 dicts with keys ['Open', 'Close', 'Timestamp']
    """
    last_candle = recent_candles[-1]
    delta = last_candle['Close'] - last_candle['Open']
    ts = pd.to_datetime(last_candle['Timestamp'])
    features = np.array([[last_candle['Open'], last_candle['Close'], delta, abs(delta),
                          1 if delta > 0 else 0, ts.hour, ts.minute, expiration]])
    prob = model.predict_proba(features)[0][1]
    move = max(abs(delta)*0.5, 0.00005)
    next_close = last_candle['Close'] + move if prob > 0.5 else last_candle['Close'] - move
    return {"Open": last_candle['Close'], "Close": next_close, "Probability": prob, "Timestamp": ts + pd.to_timedelta(expiration, unit='s')}

def plot_interactive_chart(df, predicted_candles, n=10):
    recent = df.tail(n).copy()
    recent.reset_index(drop=True, inplace=True)
    fig = go.Figure()
    for _, row in recent.iterrows():
        color = 'green' if row['Close price'] > row['Open price'] else 'red'
        fig.add_trace(go.Bar(
            x=[row['Open time']], y=[row['Close price'] - row['Open price']], base=row['Open price'],
            marker_color=color,
            hovertemplate=f"Time: {row['Open time']}<br>Open: {row['Open price']:.5f}<br>Close: {row['Close price']:.5f}"
        ))
    for i, p in enumerate(predicted_candles):
        prob = p['Probability']
        color = 'blue' if prob > 0.5 else 'orange'
        fig.add_trace(go.Bar(
            x=[p['Timestamp']], y=[p['Close'] - p['Open']], base=p['Open'],
            marker_color=color,
            hovertemplate=f"Predicted Candle {i+1}<br>Open: {p['Open']:.5f}<br>Close: {p['Close']:.5f}<br>Prob Above: {prob*100:.2f}%"
        ))
    fig.update_layout(title=f"Last {n} Candles + Predicted Candles",
                      xaxis_title="Time", yaxis_title="Price", barmode='overlay', showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# -------------------
# Streamlit UI
# -------------------
st.title("Binary Candle Predictor (3-Candle Input, 3-Candle Prediction)")

uploaded_file = st.file_uploader("Upload CSV / XLS / XLSX", type=["csv", "xls", "xlsx"])
uploaded_model = st.file_uploader("Optional: Upload existing model (.pkl)", type=["pkl"])

# Load model
model = None
if uploaded_model:
    model = joblib.load(uploaded_model)
    st.success("✅ Loaded model from upload")
elif os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
    st.success("✅ Loaded model from disk")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    st.info(f"Dataset: {df.shape[0]} rows × {df.shape[1]} columns")
    st.dataframe(df.head())

    # Train if no model
    if model is None:
        X, y = preprocess_data(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False)
        model = RandomForestClassifier(n_estimators=300, random_state=42)
        model.fit(X_train, y_train)
        joblib.dump(model, MODEL_FILE)
        st.success("✅ Model trained and saved to rf_model.pkl")

    st.subheader("Enter Last 3 Closed Candles")
    candles_input = []
    for i in range(3):
        st.markdown(f"**Candle {i+1}**")
        open_price = st.number_input(f"Candle {i+1} Open Price", value=float(df['Open price'].iloc[-3+i]), format="%.5f", step=0.00001, key=f"open{i}")
        close_price = st.number_input(f"Candle {i+1} Close Price", value=float(df['Close price'].iloc[-3+i]), format="%.5f", step=0.00001, key=f"close{i}")
        timestamp = st.text_input(f"Candle {i+1} Timestamp (YYYY-MM-DD HH:MM:SS)", value=str(df['Open time'].iloc[-3+i]), key=f"time{i}")
        candles_input.append({"Open": open_price, "Close": close_price, "Timestamp": timestamp})

    expiration = st.number_input("Candle Duration in seconds", value=parse_expiration(df['Expiration'].iloc[-1]), min_value=10.0, step=1.0)
    pause_checkbox = st.checkbox("Pause Live Updates")
    placeholder = st.empty()

    if st.button("Start Live Predictions"):
        recent_candles = candles_input.copy()
        while True:
            if not pause_checkbox:
                predicted_candles = []
                for _ in range(3):
                    p = predict_next_candle(model, recent_candles[-3:], expiration)
                    predicted_candles.append(p)
                    recent_candles.append(p)

                # Display predictions with confidence
                with placeholder.container():
                    st.write("Live Predictions (3 candles ahead):")
                    for i, p in enumerate(predicted_candles):
                        prob = p['Probability']
                        if prob > BUY_THRESHOLD:
                            action = "BUY / Above"
                            confidence = prob
                        elif prob < SELL_THRESHOLD:
                            action = "SELL / Below"
                            confidence = 1 - prob
                        else:
                            action = "HOLD / Uncertain"
                            confidence = None

                        if confidence is not None:
                            st.write(f"Candle {i+1}: {action} | Confidence: {confidence*100:.2f}% | Open={p['Open']:.5f} → Close={p['Close']:.5f}")
                        else:
                            st.write(f"Candle {i+1}: {action} | Open={p['Open']:.5f} → Close={p['Close']:.5f}")

                    plot_interactive_chart(df, predicted_candles, n=10)

            time.sleep(expiration)
