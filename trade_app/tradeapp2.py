import streamlit as st
import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
from PIL import Image
import cv2
import plotly.graph_objects as go

# -----------------------
# Constants
# -----------------------
MODEL_FILE = "rf_trade_model.pkl"

# -----------------------
# Helper Functions
# -----------------------
def parse_expiration(value):
    """Convert expiration string to seconds."""
    try:
        if isinstance(value,(int,float)):
            return float(value)
        value = str(value).strip().upper()
        if value.startswith("S"):
            return float(value.replace("S",""))
        if value.startswith("M"):
            return float(value.replace("M",""))*60
    except:
        return 60.0
    return 60.0

def preprocess_data(df):
    """Prepare features and target for training."""
    df = df.sort_values(by='Open time').reset_index(drop=True)
    df['delta'] = df['Close price'] - df['Open price']
    df['delta_abs'] = df['delta'].abs()
    df['prev_direction'] = (df['delta']>0).astype(int)
    df['Open time'] = pd.to_datetime(df['Open time'])
    df['hour'] = df['Open time'].dt.hour
    df['minute'] = df['Open time'].dt.minute
    df['seconds_to_close'] = df['Expiration'].apply(parse_expiration)
    df['target'] = (df['Close price'].shift(-1) > df['Close price']).astype(int)
    df = df[:-1]
    feature_cols = ['Open price','Close price','delta','delta_abs','prev_direction','hour','minute','seconds_to_close']
    X = df[feature_cols]
    y = df['target']
    return X,y

def predict_next_candle(model, open_price, close_price, timestamp, expiration):
    """Predict next candle direction and probability."""
    delta = close_price - open_price
    delta_abs = abs(delta)
    prev_direction = 1 if delta>0 else 0
    ts = pd.to_datetime(timestamp)
    features = np.array([[open_price, close_price, delta, delta_abs, prev_direction, ts.hour, ts.minute, expiration]])
    prob = model.predict_proba(features)[0][1]
    direction = "UP" if prob>0.5 else "DOWN"
    # approximate next candle price for visualization
    next_open = close_price
    next_close = close_price + (delta_abs*0.5 if direction=="UP" else -delta_abs*0.5)
    next_timestamp = ts + pd.to_timedelta(expiration, unit='s')
    return {"Open": next_open, "Close": next_close, "Probability": prob, "Direction": direction, "Timestamp": next_timestamp}

def overlay_predicted_candles_on_screenshot(img, detected_candles, predicted_candles):
    """Overlay predicted candles visually on uploaded screenshot."""
    overlay_img = np.array(img).copy()
    img_h, img_w, _ = overlay_img.shape

    # compute average candle width & height from detected candles
    if len(detected_candles)==0:
        st.warning("No candles detected in screenshot.")
        return img

    avg_width = int(np.mean([c['w'] for c in detected_candles]))
    avg_height = int(np.mean([c['h'] for c in detected_candles]))
    last_x = max([c['x']+c['w'] for c in detected_candles])

    for i,p in enumerate(predicted_candles):
        x1 = last_x + i*avg_width
        x2 = x1 + avg_width
        y_mid = img_h//2
        y1 = y_mid - avg_height//2
        y2 = y_mid + avg_height//2
        color_bgr = (0,255,0) if p['Direction']=="UP" else (0,0,255)
        cv2.rectangle(overlay_img,(x1,y1),(x2,y2),color_bgr,-1)
    return overlay_img

def detect_candles_from_image(img):
    """Detect basic green/red candles from screenshot using HSV color masks."""
    img_array = np.array(img)
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    mask_green = cv2.inRange(hsv,np.array([40,40,40]),np.array([90,255,255]))
    mask_red = cv2.inRange(hsv,np.array([0,70,50]),np.array([10,255,255])) + cv2.inRange(hsv,np.array([170,70,50]),np.array([180,255,255]))
    
    contours_green,_ = cv2.findContours(mask_green,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    contours_red,_ = cv2.findContours(mask_red,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    detected_candles = []
    for c in contours_green:
        x,y,w,h = cv2.boundingRect(c)
        if w<2: continue
        detected_candles.append({"x":x,"y":y,"w":w,"h":h,"color":"green"})
    for c in contours_red:
        x,y,w,h = cv2.boundingRect(c)
        if w<2: continue
        detected_candles.append({"x":x,"y":y,"w":w,"h":h,"color":"red"})
    detected_candles = sorted(detected_candles,key=lambda c:c['x'])
    return detected_candles

# -----------------------
# Streamlit UI
# -----------------------
st.title("Binary Trade Screenshot Prediction App")
st.markdown("Train model on XLS/XLSX trade log, then upload chart screenshot for visual next candle predictions.")

# --- Step 1: Upload trade log ---
st.subheader("Step 1: Train Model")
uploaded_file = st.file_uploader("Upload your trade log XLS/XLSX", type=["xls","xlsx","csv"], key="train_file")
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    st.success(f"Loaded {df.shape[0]} rows × {df.shape[1]} columns")

    # Train or load model
    if os.path.exists(MODEL_FILE):
        model = joblib.load(MODEL_FILE)
        st.success("Loaded trained model from disk.")
    else:
        X,y = preprocess_data(df)
        X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,shuffle=False)
        model = RandomForestClassifier(n_estimators=200, random_state=42)
        model.fit(X_train,y_train)
        joblib.dump(model,MODEL_FILE)
        st.success("Model trained and saved!")

# --- Step 2: Upload screenshot ---
st.subheader("Step 2: Upload Chart Screenshot for Prediction")
uploaded_img = st.file_uploader("Upload chart screenshot", type=["png","jpg","jpeg"], key="img_file")
if uploaded_img and os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
    st.success("Model ready for predictions!")

    img = Image.open(uploaded_img)
    st.image(img, caption="Uploaded Chart", use_column_width=True)

    detected_candles = detect_candles_from_image(img)
    if len(detected_candles)>0:
        st.info(f"Detected {len(detected_candles)} candles in screenshot.")
    else:
        st.warning("No candles detected, predictions may be inaccurate.")

    # Enter last candle details
    st.subheader("Enter Last Candle Details")
    last_candle = detected_candles[-1] if len(detected_candles)>0 else None
    open_price = st.number_input("Last Candle Open Price", value=float(df['Open price'].iloc[-1]))
    close_price = st.number_input("Last Candle Close Price", value=float(df['Close price'].iloc[-1]))
    timestamp = st.text_input("Last Candle Timestamp", value=str(df['Open time'].iloc[-1]))
    expiration = st.number_input("Seconds to close / Expiration", value=parse_expiration(df['Expiration'].iloc[-1]))

    if st.button("Predict Next Candle"):
        predicted_candles = []
        temp_open,temp_close,temp_ts,temp_exp = open_price,close_price,timestamp,expiration
        for i in range(1):  # predict 1 candle; can change to 3 if desired
            p = predict_next_candle(model,temp_open,temp_close,temp_ts,temp_exp)
            predicted_candles.append(p)
            temp_open,temp_close,temp_ts = p['Open'],p['Close'],p['Timestamp']

        overlay_img = overlay_predicted_candles_on_screenshot(img, detected_candles, predicted_candles)
        st.image(overlay_img, caption="Predicted Candle Overlay", use_column_width=True)
        st.subheader("Prediction Details")
        for i,p in enumerate(predicted_candles):
            st.write(f"Candle {i+1}: {p['Direction']} | Probability UP: {p['Probability']*100:.2f}% | Open={p['Open']:.5f} Close={p['Close']:.5f}")
