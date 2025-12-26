import librosa
import numpy as np

def detect_energy_peaks(audio_path, threshold=0.7, min_duration=3):
    """
    Detect high-energy moments in audio using librosa
    """
    try:
        # Load audio with error handling
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        
        # Check if audio is valid
        if len(y) == 0:
            return []
        
        # Calculate RMS energy
        rms = librosa.feature.rms(y=y)[0]
        
        # Normalize
        rms_normalized = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-10)
        
        # Find peaks
        peaks = []
        frame_length = len(rms)
        hop_length = 512
        
        i = 0
        while i < frame_length:
            if rms_normalized[i] > threshold:
                start_frame = i
                
                # Find end of peak
                while i < frame_length and rms_normalized[i] > threshold * 0.8:
                    i += 1
                
                end_frame = i
                
                # Convert frames to time
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
        
        # Sort by energy score
        peaks.sort(key=lambda x: x['energy_score'], reverse=True)
        
        return peaks[:10]  # Return top 10
        
    except EOFError:
        print("Error: Audio file is corrupted or incomplete")
        return []
    except Exception as e:
        print(f"Error analyzing audio: {str(e)}")
        return []

def generate_report(moments):
    """Generate a markdown report of detected moments"""
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

def format_timestamp(seconds):
    """Convert seconds to MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"