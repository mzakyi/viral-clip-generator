import os
import yt_dlp
import shutil
import librosa
import numpy as np

# === Ensure ffmpeg & ffprobe are in PATH for yt_dlp subprocesses ===
os.environ['PATH'] = "/usr/local/bin:" + os.environ.get('PATH', '')

print("ffmpeg path:", shutil.which("ffmpeg"))
print("ffprobe path:", shutil.which("ffprobe"))

# Replace with your YouTube video or channel URL
url = "https://www.youtube.com/@ViralSankatos"

# Download options with postprocessing to extract WAV audio
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": "downloaded_audio/%(title)s.%(ext)s",
    "ffmpeg_location": "/usr/local/bin",  # <--- Add this line exactly here
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "wav",
        "preferredquality": "192",
    }],
    "ignoreerrors": True,
    "quiet": False,
    "no_warnings": True,
    "noplaylist": False,
}


def detect_energy_peaks(audio_path, threshold=0.7, min_duration=3):
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        if len(y) == 0:
            return []
        rms = librosa.feature.rms(y=y)[0]
        rms_normalized = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-10)
        peaks = []
        frame_length = len(rms)
        hop_length = 512
        i = 0
        while i < frame_length:
            if rms_normalized[i] > threshold:
                start_frame = i
                while i < frame_length and rms_normalized[i] > threshold * 0.8:
                    i += 1
                end_frame = i
                start_time = librosa.frames_to_time(start_frame, sr=sr, hop_length=hop_length)
                end_time = librosa.frames_to_time(end_frame, sr=sr, hop_length=hop_length)
                duration = end_time - start_time
                if duration >= min_duration:
                    energy_score = int(np.mean(rms_normalized[start_frame:end_frame]) * 100)
                    peaks.append({
                        'start_time': float(start_time),
                        'end_time': float(end_time),
                        'duration': float(duration),
                        'energy_score': energy_score,
                        'reason': 'High audio energy detected'
                    })
            i += 1
        peaks.sort(key=lambda x: x['energy_score'], reverse=True)
        return peaks[:10]
    except Exception as e:
        print(f"Error analyzing audio: {str(e)}")
        return []

def format_timestamp(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def generate_report(moments):
    if not moments:
        return "No high-energy moments detected in the audio."
    report = "## 🔊 Audio Energy Analysis\n\n"
    report += f"Found **{len(moments)}** high-energy moments:\n\n"
    for i, moment in enumerate(moments[:5], 1):
        report += f"### {i}. {format_timestamp(moment['start_time'])} - {format_timestamp(moment['end_time'])}\n"
        report += f"- **Duration:** {moment['duration']:.1f}s\n"
        report += f"- **Energy Score:** {moment['energy_score']}/100\n"
        report += f"- **Why:** {moment['reason']}\n\n"
    return report

# === Run download ===
os.makedirs("downloaded_audio", exist_ok=True)

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])

# === Process downloaded WAV files ===
import glob
wav_files = glob.glob("downloaded_audio/*.wav")

for wav_path in wav_files:
    print(f"Processing {wav_path}")
    peaks = detect_energy_peaks(wav_path)
    report = generate_report(peaks)
    print(report)
