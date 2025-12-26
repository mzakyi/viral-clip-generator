import librosa
import numpy as np

def detect_energy_peaks(audio_path, threshold=0.5, min_duration=8, gap_threshold=6):
    """
    Detect high-energy moments in audio using RMS energy peaks.
    Adjusted for more moments: lower threshold, shorter min duration.
    """
    y, sr = librosa.load(audio_path, sr=None)
    
    rmse = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rmse, sr=sr)
    
    if np.max(rmse) == 0:
        return []
    rmse_norm = rmse / np.max(rmse)
    
    peak_frames = np.where(rmse_norm > threshold)[0]
    
    if len(peak_frames) == 0:
        return []
    
    moments = []
    start_time = times[peak_frames[0]]
    segment_frame_indices = [peak_frames[0]]
    
    for i in range(1, len(peak_frames)):
        current_frame = peak_frames[i]
        prev_frame = peak_frames[i - 1]
        
        if times[current_frame] - times[prev_frame] > gap_threshold:
            end_time = times[prev_frame]
            duration = end_time - start_time
            
            if duration >= min_duration:
                segment_energy = np.mean(rmse_norm[segment_frame_indices])
                moments.append({
                    'start_time': round(start_time, 2),
                    'end_time': round(end_time, 2),
                    'duration': round(duration, 2),
                    'energy_score': round(segment_energy, 3),
                    'reason': '🔥 High audio energy (excitement, shouting, music peak)'
                })
            
            start_time = times[current_frame]
            segment_frame_indices = [current_frame]
        else:
            segment_frame_indices.append(current_frame)
    
    # Last segment
    end_time = times[peak_frames[-1]]
    duration = end_time - start_time
    if duration >= min_duration:
        segment_energy = np.mean(rmse_norm[segment_frame_indices])
        moments.append({
            'start_time': round(start_time, 2),
            'end_time': round(end_time, 2),
            'duration': round(duration, 2),
            'energy_score': round(segment_energy, 3),
            'reason': '🔥 High audio energy (excitement, shouting, music peak)'
        })
    
    # Sort descending by score
    moments.sort(key=lambda x: x['energy_score'], reverse=True)
    
    return moments

def format_timestamp(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def generate_report(moments):
    if not moments:
        return "No high-energy audio moments detected (try a louder/more dynamic video)."
    
    report = f"🎵 Found {len(moments)} High-Energy Audio Moments:\n\n"
    for i, m in enumerate(moments, 1):
        report += f"#{i} - {format_timestamp(m['start_time'])} to {format_timestamp(m['end_time'])}\n"
        report += f"   Score: {m['energy_score']:.3f} | Duration: {m['duration']}s\n"
        report += f"   {m['reason']}\n\n"
    return report