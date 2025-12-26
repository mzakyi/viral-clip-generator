# video_processor.py

import os
import cv2
import glob
import time
import numpy as np
from numpy import random

# Force MoviePy to NOT use ImageMagick
os.environ["IMAGEMAGICK_BINARY"] = ""

from moviepy import (
    VideoFileClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
    AudioFileClip
)


def split_clip(input_path, max_clip_len=4):
    """Split video into multiple clips"""
    video = VideoFileClip(input_path)
    clips = []
    start = 0
    while start < video.duration:
        end = min(start + max_clip_len, video.duration)
        clips.append(video.subclipped(start, end))  # FIXED: subclip → subclipped
        start += max_clip_len
    return clips


def add_freeze_frame(clip, duration=1):
    """
    Add a freeze frame at the end of a clip
    
    Args:
        clip: VideoFileClip object
        duration: Duration of freeze frame in seconds
    """
    from moviepy import ImageClip, concatenate_videoclips
    
    # Get the last frame and create a freeze frame
    last_frame = clip.get_frame(clip.duration - 0.01)
    freeze_clip = ImageClip(last_frame, duration=duration)  # FIXED: set_duration → duration
    
    # Concatenate original clip with freeze frame
    return concatenate_videoclips([clip, freeze_clip])


def add_text_overlay(clip, text="Hook", font_size=50, color='white', pos='center', duration=None):
    """Add text overlay to clip"""
    from moviepy import TextClip, CompositeVideoClip
    
    if duration is None:
        duration = clip.duration
    
    txt_clip = TextClip(text=text, font_size=font_size, color=color)
    txt_clip = txt_clip.with_position(pos).with_duration(duration)  # FIXED: set_position/set_duration → with_position/with_duration
    
    return CompositeVideoClip([clip, txt_clip])

def export_video(clips, output_path="output.mp4", fps=30):
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_path, fps=fps)
    return output_path

def download_audio_temp(video_url):
    """Download audio from YouTube video to a temporary file"""
    import yt_dlp
    import tempfile
    import os
    import time
    
    try:
        # Create a unique temporary directory
        temp_dir = tempfile.mkdtemp()
        base_filename = f"audio_{int(time.time())}"
        
        # yt-dlp options for audio extraction
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(temp_dir, base_filename + '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
        
        # Look for the actual file created
        files_in_dir = os.listdir(temp_dir)
        
        # Find any audio file (mp3, m4a, webm, etc.)
        audio_extensions = ['.mp3', '.m4a', '.webm', '.wav', '.opus']
        
        for filename in files_in_dir:
            file_path = os.path.join(temp_dir, filename)
            
            # Check if it's a file with audio extension or just the base name
            if any(filename.endswith(ext) for ext in audio_extensions):
                if os.path.getsize(file_path) > 1000:  # At least 1KB
                    return {
                        'success': True,
                        'path': file_path
                    }
            # Check if it's the base file without extension (yt-dlp sometimes does this)
            elif filename.startswith('audio_'):
                if os.path.getsize(file_path) > 1000:
                    # Rename it to .mp3
                    new_path = file_path + '.mp3'
                    os.rename(file_path, new_path)
                    return {
                        'success': True,
                        'path': new_path
                    }
        
        return {
            'success': False,
            'error': f'No valid audio file found. Files: {files_in_dir}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def download_video(video_url, output_dir='downloads'):
    """Download video from YouTube"""
    import yt_dlp
    
    try:
        # Create downloads directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # yt-dlp options - FIXED VERSION
        ydl_opts = {
            'format': 'best[ext=mp4][height<=720]/best[height<=720]/best',  # Force mp4 when possible
            'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
            'quiet': False,  # Changed to see what's happening
            'no_warnings': False,  # See warnings
            'merge_output_format': 'mp4',  # Merge to mp4 if separate streams
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # Convert to mp4 if needed
            }],
        }
        
        print(f"Downloading from: {video_url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
            # Get the actual downloaded filename
            video_id = info.get('id')
            
            # Check for the downloaded file with various extensions
            possible_extensions = ['.mp4', '.webm', '.mkv', '.avi']
            video_path = None
            
            for ext in possible_extensions:
                test_path = os.path.join(output_dir, f'{video_id}{ext}')
                if os.path.exists(test_path) and os.path.getsize(test_path) > 1000:
                    video_path = test_path
                    break
            
            # If still not found, search the directory
            if not video_path:
                for file in os.listdir(output_dir):
                    if video_id in file and any(file.endswith(ext) for ext in possible_extensions):
                        video_path = os.path.join(output_dir, file)
                        break
            
            if not video_path or not os.path.exists(video_path):
                return {
                    'success': False,
                    'error': f'Video file not found after download. Files in directory: {os.listdir(output_dir)}'
                }
            
            print(f"Downloaded to: {video_path}")
            
            return {
                'success': True,
                'path': video_path,
                'duration': info.get('duration', 0),
                'title': info.get('title', 'Unknown')
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def create_clip(video_path, start_time, end_time, output_name='clip', add_captions=False, caption_text=''):
    """Create a clip from a video file"""
    try:
        # Create clips directory if it doesn't exist
        os.makedirs('clips', exist_ok=True)
        
        # Load video and create clip
        video = VideoFileClip(video_path)
        clip = video.subclipped(start_time, end_time)  # FIXED: subclip → subclipped
        
        # Add captions if requested
        if add_captions and caption_text:
            from moviepy import TextClip, CompositeVideoClip
            
            txt_clip = TextClip(
                text=caption_text,
                font_size=50,
                color='white',
                stroke_color='black',
                stroke_width=2,
                font='Arial-Bold',
                method='caption',
                size=(clip.w * 0.9, None)
            )
            txt_clip = txt_clip.with_position(('center', 'top')).with_duration(clip.duration)
            clip = CompositeVideoClip([clip, txt_clip])
        
        # Generate output filename
        import time
        timestamp = int(time.time())
        output_path = os.path.join('clips', f'{output_name}_{timestamp}.mp4')
        
        # Export clip
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=30)
        
        # Close clips
        clip.close()
        video.close()
        
        return {
            'success': True,
            'path': output_path
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"{str(e)}\n{traceback.format_exc()}"
        }


def get_all_clips(clips_dir='clips'):
    """Get list of all clips in the clips directory"""
    try:
        os.makedirs(clips_dir, exist_ok=True)
        clip_files = glob.glob(os.path.join(clips_dir, '*.mp4'))
        
        clips = []
        for clip_path in clip_files:
            file_size = os.path.getsize(clip_path)
            clips.append({
                'filename': os.path.basename(clip_path),
                'path': clip_path,
                'size_mb': round(file_size / (1024 * 1024), 2)
            })
        
        return clips
    except Exception as e:
        return []

def cleanup_downloads(downloads_dir='downloads'):
    """Clean up downloaded video files"""
    try:
        if os.path.exists(downloads_dir):
            for file in glob.glob(os.path.join(downloads_dir, '*')):
                os.remove(file)
        return True
    except Exception as e:
        return False

def add_commentary_audio(video_clip, audio_path):
    """
    Add voice commentary audio to a video clip
    """
    from moviepy import AudioFileClip, CompositeAudioClip
    
    # Load the commentary audio
    commentary = AudioFileClip(audio_path)
    
    # Mix original video audio with commentary
    if video_clip.audio:
        mixed_audio = CompositeAudioClip([video_clip.audio, commentary])
    else:
        mixed_audio = commentary
    
    # FIXED: set_audio → with_audio
    final_clip = video_clip.with_audio(mixed_audio)
    
    return final_clip


def add_multiple_text_overlays(clip, text_overlays):
    """
    Add multiple text overlays at different times with proper positioning
    
    Args:
        clip: VideoFileClip object
        text_overlays: List of dicts with keys: text, start_time, end_time, position, font_size, color
    """
    from moviepy import TextClip, CompositeVideoClip
    
    video_clips = [clip]
    
    for overlay in text_overlays:
        # Create text with better styling
        txt_clip = TextClip(
            text=overlay.get('text', ''),
            font_size=overlay.get('fontsize', 50),
            color=overlay.get('color', 'yellow'),
            stroke_color='black',
            stroke_width=3,
            font='Arial-Bold',
            method='caption',
            size=(int(clip.w * 0.85), None)
        )
        
        # Position mapping with proper margins
        position = overlay.get('position', 'center')
        if position == 'top':
            pos = ('center', int(clip.h * 0.15))
        elif position == 'bottom':
            pos = ('center', int(clip.h * 0.75))
        else:
            pos = 'center'
        
        # FIXED: Use with_position, with_start, with_end instead of set_
        txt_clip = txt_clip.with_position(pos)
        txt_clip = txt_clip.with_start(overlay.get('start_time', 0))
        txt_clip = txt_clip.with_end(overlay.get('end_time', clip.duration))
        
        video_clips.append(txt_clip)
    
    return CompositeVideoClip(video_clips)


def add_intro_outro_overlay(clip, intro_text="", outro_text="", intro_duration=3, outro_duration=3):
    """
    Add intro and outro text overlays ON TOP of the video (not black screens)
    """
    from moviepy import TextClip, CompositeVideoClip
    
    video_clips = [clip]
    
    # Add intro text overlay at the start
    if intro_text:
        intro_txt = TextClip(
            text=intro_text,
            font_size=70,
            color='white',
            stroke_color='black',
            stroke_width=4,
            font='Arial-Bold',
            method='caption',
            size=(int(clip.w * 0.8), None)
        )
        intro_txt = intro_txt.with_position('center')
        intro_txt = intro_txt.with_start(0)
        intro_txt = intro_txt.with_end(intro_duration)
        intro_txt = intro_txt.crossfadein(0.5).crossfadeout(0.5)
        
        video_clips.append(intro_txt)
    
    # Add outro text overlay at the end
    if outro_text:
        outro_start = max(0, clip.duration - outro_duration)
        
        outro_txt = TextClip(
            text=outro_text,
            font_size=60,
            color='yellow',
            stroke_color='black',
            stroke_width=4,
            font='Arial-Bold',
            method='caption',
            size=(int(clip.w * 0.8), None)
        )
        outro_txt = outro_txt.with_position('center')
        outro_txt = outro_txt.with_start(outro_start)
        outro_txt = outro_txt.with_end(clip.duration)
        outro_txt = outro_txt.crossfadein(0.5)
        
        video_clips.append(outro_txt)
    
    return CompositeVideoClip(video_clips)


def add_zoom_effect(clip, zoom_factor=1.2):
    """
    Add a subtle zoom effect to emphasize moments
    
    Args:
        clip: VideoFileClip object
        zoom_factor: How much to zoom (1.0 = no zoom, 1.5 = 50% zoom)
    """
    def zoom(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        
        # Calculate zoom
        new_h, new_w = int(h / zoom_factor), int(w / zoom_factor)
        
        # Crop center
        y1, x1 = (h - new_h) // 2, (w - new_w) // 2
        y2, x2 = y1 + new_h, x1 + new_w
        
        cropped = frame[y1:y2, x1:x2]
        
        # Resize back to original size
        import cv2
        return cv2.resize(cropped, (w, h))
    
    return clip.fl(zoom)

def generate_ai_voice(text, output_path='temp_voice.mp3'):
    """
    Generate AI voice from text using gTTS (Google Text-to-Speech)
    
    Args:
        text: The text to convert to speech
        output_path: Where to save the audio file
    
    Returns:
        Path to the generated audio file
    """
    try:
        from gtts import gTTS
        import os
        
        # Generate speech
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)
        
        return {
            'success': True,
            'path': output_path
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
        
        
def analyze_video_for_monetization(video_path):
    """
    Analyze a video to check if it meets monetization criteria
    
    Returns a detailed report with scores and recommendations
    """
    from moviepy.editor import VideoFileClip
    import numpy as np
    
    try:
        video = VideoFileClip(video_path)
        
        # Initialize scores
        scores = {
            'duration_score': 0,
            'audio_modification_score': 0,
            'visual_complexity_score': 0,
            'overall_score': 0,
            'pass_status': False
        }
        
        details = {
            'duration': video.duration,
            'has_audio': video.audio is not None,
            'resolution': f"{video.w}x{video.h}",
            'fps': video.fps
        }
        
        # 1. DURATION SCORE (15-60 seconds is ideal for shorts)
        duration = video.duration
        if 15 <= duration <= 60:
            scores['duration_score'] = 100
        elif 10 <= duration < 15 or 60 < duration <= 90:
            scores['duration_score'] = 80
        elif duration < 10:
            scores['duration_score'] = 50
        else:
            scores['duration_score'] = 60
        
        # 2. AUDIO MODIFICATION SCORE
        if video.audio:
            try:
                # Check if audio has multiple layers (commentary + original)
                audio_array = video.audio.to_soundarray(fps=22050)
                
                # Ensure audio_array is a numpy array
                if not isinstance(audio_array, np.ndarray):
                    audio_array = np.array(audio_array)
                
                # Calculate audio energy variance (more variance = more edited)
                if len(audio_array.shape) > 1:
                    # Stereo audio - calculate energy for each channel then average
                    audio_energy = np.sqrt(np.mean(audio_array**2, axis=1))
                else:
                    # Mono audio
                    audio_energy = np.sqrt(audio_array**2)
                
                # Calculate variance
                energy_variance = np.var(audio_energy)
                
                # Higher variance suggests commentary/editing
                if energy_variance > 0.01:
                    scores['audio_modification_score'] = 100
                elif energy_variance > 0.005:
                    scores['audio_modification_score'] = 70
                else:
                    scores['audio_modification_score'] = 40
            except Exception as audio_error:
                # If audio analysis fails, give a moderate score if audio exists
                print(f"Audio analysis error: {audio_error}")
                scores['audio_modification_score'] = 50
        else:
            scores['audio_modification_score'] = 0
        
        # 3. VISUAL COMPLEXITY SCORE (checks for overlays, effects)
        # Sample frames and check for complexity
        sample_times = [video.duration * 0.25, video.duration * 0.5, video.duration * 0.75]
        complexity_scores = []
        
        try:
            import cv2
            
            for t in sample_times:
                if t < video.duration:
                    frame = video.get_frame(t)
                    
                    # Calculate edge density (more edges = more overlays/text)
                    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                    edges = cv2.Canny(gray, 100, 200)
                    edge_density = np.sum(edges > 0) / edges.size
                    
                    complexity_scores.append(edge_density)
            
            avg_complexity = np.mean(complexity_scores) if complexity_scores else 0
            
            if avg_complexity > 0.15:
                scores['visual_complexity_score'] = 100
            elif avg_complexity > 0.10:
                scores['visual_complexity_score'] = 80
            elif avg_complexity > 0.05:
                scores['visual_complexity_score'] = 60
            else:
                scores['visual_complexity_score'] = 40
                
        except Exception as visual_error:
            # If visual analysis fails, give a moderate score
            print(f"Visual analysis error: {visual_error}")
            scores['visual_complexity_score'] = 50
        
        # 4. CALCULATE OVERALL SCORE
        scores['overall_score'] = int(
            (scores['duration_score'] * 0.2) +
            (scores['audio_modification_score'] * 0.5) +  # Most important
            (scores['visual_complexity_score'] * 0.3)
        )
        
        # 5. PASS/FAIL STATUS
        scores['pass_status'] = (
            scores['overall_score'] >= 70 and
            scores['audio_modification_score'] >= 60
        )
        
        video.close()
        
        return {
            'success': True,
            'scores': scores,
            'details': details
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
        
def generate_monetization_report(analysis_result):
    """
    Generate a human-readable report from analysis results
    """
    if not analysis_result['success']:
        return f"❌ Error analyzing video: {analysis_result['error']}"
    
    scores = analysis_result['scores']
    details = analysis_result['details']
    
    # Status badge
    if scores['pass_status']:
        status = "✅ **PASSES MONETIZATION CHECK**"
        status_color = "green"
    else:
        status = "⚠️ **NEEDS IMPROVEMENT**"
        status_color = "orange"
    
    # Generate report
    report = f"""
## {status}

### 📊 Overall Score: {scores['overall_score']}/100

---

### Detailed Analysis:

**🎬 Video Details:**
- Duration: {details['duration']:.1f} seconds
- Resolution: {details['resolution']}
- FPS: {details['fps']}
- Has Audio: {'Yes ✅' if details['has_audio'] else 'No ❌'}

---

**📈 Score Breakdown:**

| Criteria | Score | Status |
|----------|-------|--------|
| ⏱️ Duration Optimization | {scores['duration_score']}/100 | {'✅' if scores['duration_score'] >= 80 else '⚠️'} |
| 🎙️ Audio Modification | {scores['audio_modification_score']}/100 | {'✅' if scores['audio_modification_score'] >= 60 else '❌'} |
| 🎨 Visual Complexity | {scores['visual_complexity_score']}/100 | {'✅' if scores['visual_complexity_score'] >= 60 else '⚠️'} |

---

### 💡 Recommendations:
"""
    
    # Add specific recommendations
    recommendations = []
    
    if scores['audio_modification_score'] < 60:
        recommendations.append("❌ **CRITICAL:** Add voice commentary or analysis over the clip. This is the most important factor!")
    
    if scores['visual_complexity_score'] < 60:
        recommendations.append("⚠️ Add more text overlays, captions, or visual effects to increase transformative value")
    
    if scores['duration_score'] < 80:
        if details['duration'] < 15:
            recommendations.append("⚠️ Video is too short. Aim for 15-60 seconds for optimal engagement")
        elif details['duration'] > 90:
            recommendations.append("⚠️ Video is too long for shorts format. Consider trimming to under 60 seconds")
    
    if not details['has_audio']:
        recommendations.append("❌ **CRITICAL:** Video has no audio! Add commentary, music, or sound effects")
    
    if not recommendations:
        recommendations.append("✅ Your video looks great! It should be safe to monetize")
        recommendations.append("✅ Make sure the original content source allows transformative use")
        recommendations.append("✅ Consider adding your own intro/outro for branding")
    
    for rec in recommendations:
        report += f"\n{rec}\n"
    
    report += "\n---\n"
    
    # Final verdict
    if scores['pass_status']:
        report += """
### 🎉 Final Verdict:
Your video has strong transformative elements and should be eligible for monetization. 
However, always ensure you're following platform guidelines and the original content allows transformative use.

**Next Steps:**
1. ✅ Upload to your platform
2. ✅ Enable monetization
3. ✅ Monitor for any copyright claims
4. ✅ Respond to claims with Fair Use if needed
"""
    else:
        report += """
### ⚠️ Final Verdict:
Your video needs more transformative elements before it's monetization-ready.
Focus on the recommendations above, especially adding voice commentary.

**Next Steps:**
1. ⚠️ Go back to Monetization Prep
2. ⚠️ Add more transformative elements
3. ⚠️ Re-verify before uploading
"""
    
    return report


def add_multiple_commentary_segments(video_clip, commentary_segments, original_audio_volume=0.3):
    """
    Add multiple commentary audio segments at different timestamps
    """
    from moviepy import AudioFileClip, CompositeAudioClip
    
    try:
        audio_clips = []
        
        # Keep original video audio if it exists, but reduce volume
        if video_clip.audio:
            # FIXED: volumex → with_volume_scaled
            reduced_original = video_clip.audio.with_volume_scaled(original_audio_volume)
            audio_clips.append(reduced_original)
        
        # Add each commentary segment
        for segment in commentary_segments:
            commentary = AudioFileClip(segment['audio_path'])
            
            # FIXED: set_start → with_start
            commentary = commentary.with_start(segment.get('start_time', 0))
            
            # Adjust volume if specified
            volume = segment.get('volume', 1.0)
            if volume != 1.0:
                commentary = commentary.with_volume_scaled(volume)
            
            audio_clips.append(commentary)
        
        # Composite all audio
        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            return video_clip.with_audio(final_audio)
        else:
            return video_clip
            
    except Exception as e:
        print(f"Error adding commentary segments: {e}")
        return video_clip
    

def analyze_video_for_suggestions(video_path):
    """
    Analyze video and suggest where to add customizations
    
    Returns suggestions for text overlays, commentary timing, and effects
    """
    from moviepy.editor import VideoFileClip
    import numpy as np
    import cv2
    
    try:
        video = VideoFileClip(video_path)
        suggestions = []
        
        # Analyze the video in segments
        num_segments = min(5, int(video.duration / 3))  # Max 5 segments, 3 seconds each
        segment_duration = video.duration / num_segments
        
        for i in range(num_segments):
            segment_start = i * segment_duration
            segment_mid = segment_start + (segment_duration / 2)
            segment_end = segment_start + segment_duration
            
            # Get frame from middle of segment
            if segment_mid < video.duration:
                frame = video.get_frame(segment_mid)
                
                # Analyze frame brightness (darker = might need text)
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                brightness = np.mean(gray)
                
                # Analyze frame complexity
                edges = cv2.Canny(gray, 100, 200)
                edge_density = np.sum(edges > 0) / edges.size
                
                # Generate suggestions based on analysis
                suggestion = {
                    'segment': i + 1,
                    'start_time': round(segment_start, 1),
                    'end_time': round(segment_end, 1),
                    'mid_time': round(segment_mid, 1),
                    'recommendations': []
                }
                
                # Text overlay suggestions
                if brightness < 100:
                    suggestion['recommendations'].append({
                        'type': 'text_overlay',
                        'reason': 'Dark scene - white/yellow text would stand out',
                        'position': 'center',
                        'example': '🔥 Key Moment!',
                        'color': 'yellow'
                    })
                elif brightness > 180:
                    suggestion['recommendations'].append({
                        'type': 'text_overlay',
                        'reason': 'Bright scene - dark text with outline would work well',
                        'position': 'bottom',
                        'example': '👀 Watch this...',
                        'color': 'white'
                    })
                else:
                    suggestion['recommendations'].append({
                        'type': 'text_overlay',
                        'reason': 'Balanced lighting - perfect for text overlay',
                        'position': 'top',
                        'example': '⚡ Amazing!',
                        'color': 'yellow'
                    })
                
                # Commentary suggestions
                if i == 0:
                    suggestion['recommendations'].append({
                        'type': 'commentary',
                        'reason': 'Video start - introduce what viewers will see',
                        'example': 'Watch what happens in this incredible moment...'
                    })
                elif i == num_segments - 1:
                    suggestion['recommendations'].append({
                        'type': 'commentary',
                        'reason': 'Video end - call to action or conclusion',
                        'example': 'That was amazing! Follow for more content like this.'
                    })
                else:
                    suggestion['recommendations'].append({
                        'type': 'commentary',
                        'reason': 'Mid-video - explain or react to what\'s happening',
                        'example': 'Notice the technique being used here...'
                    })
                
                # Effect suggestions
                if edge_density < 0.05:
                    suggestion['recommendations'].append({
                        'type': 'effect',
                        'reason': 'Low visual complexity - zoom effect would add emphasis',
                        'effect_name': 'zoom'
                    })
                
                suggestions.append(suggestion)
        
        video.close()
        
        return {
            'success': True,
            'suggestions': suggestions,
            'duration': video.duration
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
        
def auto_optimize_video(video_path, suggestions, user_instructions=""):
    """
    Automatically optimize video based on AI suggestions and content analysis

    Args:
        video_path: Path to the video file
        suggestions: Suggestions from analyze_video_for_suggestions
        user_instructions: Additional user instructions for optimization

    Returns:
        Optimized video clip
    """
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    import tempfile

    try:
        # Load video
        clip = VideoFileClip(video_path)
        video_clips = [clip]
        commentary_segments = []
        
        # Get contextual commentary suggestions
        commentary_analysis = analyze_video_content_for_commentary(video_path)
        
        if not commentary_analysis['success']:
            print(f"Commentary analysis failed: {commentary_analysis.get('error')}")
            # Fall back to basic suggestions
            commentary_data = suggestions
        else:
            commentary_data = commentary_analysis['commentary_suggestions']
        
        # Track used text overlays to avoid repetition
        used_text_examples = set()
        
        # Process each suggestion
        for idx, suggestion in enumerate(suggestions):
            for rec in suggestion['recommendations']:
                
                # Add text overlays based on suggestions (with variety)
                if rec['type'] == 'text_overlay':
                    # Use the suggested text or create varied alternatives
                    text_options = [
                        rec['example'],
                        "🔥 Amazing!",
                        "👀 Watch this",
                        "⚡ Incredible",
                        "💯 Perfect timing",
                        "🎯 Key moment",
                        "✨ Notice this"
                    ]
                    
                    # Pick text that hasn't been used yet
                    available_texts = [t for t in text_options if t not in used_text_examples]
                    if not available_texts:
                        available_texts = text_options  # Reset if all used
                    
                    selected_text = available_texts[0]
                    used_text_examples.add(selected_text)
                    
                    # Create text overlay
                    txt_clip = TextClip(
                        selected_text,
                        fontsize=55,
                        color=rec['color'],
                        stroke_color='black',
                        stroke_width=3,
                        font='Arial-Bold',
                        method='caption',
                        size=(int(clip.w * 0.85), None)
                    )
                    
                    # Position mapping
                    position = rec['position']
                    if position == 'top':
                        pos = ('center', int(clip.h * 0.15))
                    elif position == 'bottom':
                        pos = ('center', int(clip.h * 0.75))
                    else:
                        pos = 'center'
                    
                    # Set timing with variation
                    start_offset = idx * 0.2  # Stagger text appearances
                    txt_clip = txt_clip.set_position(pos)
                    txt_clip = txt_clip.set_start(suggestion['start_time'] + start_offset)
                    txt_clip = txt_clip.set_end(min(suggestion['end_time'], clip.duration))
                    txt_clip = txt_clip.crossfadein(0.3).crossfadeout(0.3)
                    
                    video_clips.append(txt_clip)
        
        # Add contextual commentary at each segment
        if commentary_analysis['success']:
            for comm_data in commentary_data:
                commentary_text = comm_data['commentary']
                
                # Apply user instructions if provided
                if user_instructions:
                    if 'exciting' in user_instructions.lower():
                        commentary_text += " This is absolutely thrilling"
                    elif 'educational' in user_instructions.lower():
                        commentary_text = commentary_text.replace("incredible", "educational").replace("amazing", "informative")
                    elif 'professional' in user_instructions.lower():
                        commentary_text = commentary_text.replace("!", ".").replace("absolutely", "notably")
                
                # Generate AI voice for this segment
                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_audio_path = temp_audio.name
                temp_audio.close()
                
                voice_result = generate_ai_voice(commentary_text, temp_audio_path)
                
                if voice_result['success']:
                    commentary_segments.append({
                        'audio_path': voice_result['path'],
                        'start_time': comm_data['start_time'],
                        'volume': 1.3  # Slightly louder for clarity
                    })
        
        # Composite all visual elements
        final_clip = CompositeVideoClip(video_clips)
        
        # Add all commentary segments with reduced original audio
        if commentary_segments:
            from moviepy.editor import AudioFileClip, CompositeAudioClip
            
            audio_clips = []
            
            # Reduce original audio to 20% for clear commentary
            if final_clip.audio:
                reduced_original = final_clip.audio.volumex(0.20)
                audio_clips.append(reduced_original)
            
            # Add all commentary
            for segment in commentary_segments:
                commentary = AudioFileClip(segment['audio_path'])
                commentary = commentary.set_start(segment['start_time'])
                commentary = commentary.volumex(segment['volume'])
                audio_clips.append(commentary)
            
            # Composite audio
            if audio_clips:
                final_audio = CompositeAudioClip(audio_clips)
                final_clip = final_clip.set_audio(final_audio)
        
        # Add varied intro/outro overlays
        intro_options = ["🔥 WATCH THIS", "⚡ AMAZING MOMENT", "👀 CHECK THIS OUT", "💯 INCREDIBLE"]
        outro_options = ["👍 Like & Follow!", "🔔 Subscribe for More", "💬 Comment Below", "🎯 More Content Daily"]
        
        intro_txt = TextClip(
            np.random.choice(intro_options),
            fontsize=70,
            color='yellow',
            stroke_color='black',
            stroke_width=4,
            font='Arial-Bold'
        )
        intro_txt = intro_txt.set_position('center').set_duration(2).set_start(0)
        intro_txt = intro_txt.crossfadein(0.5).crossfadeout(0.5)
        
        outro_txt = TextClip(
            np.random.choice(outro_options),
            fontsize=60,
            color='white',
            stroke_color='black',
            stroke_width=4,
            font='Arial-Bold'
        )
        outro_start = max(0, final_clip.duration - 3)
        outro_txt = outro_txt.set_position('center').set_duration(3).set_start(outro_start)
        outro_txt = outro_txt.crossfadein(0.5)
        
        # Add intro/outro to composite
        final_clip = CompositeVideoClip([final_clip, intro_txt, outro_txt])
        
        return {
            'success': True,
            'clip': final_clip,
            'commentary_segments': commentary_segments
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
        
def analyze_video_content_for_commentary(video_path):
    """
    Analyze video content to generate contextual, varied commentary
    
    Returns suggestions for diverse, relevant commentary based on visual analysis
    """
    from moviepy.editor import VideoFileClip
    import numpy as np
    import cv2
    
    try:
        video = VideoFileClip(video_path)
        commentary_suggestions = []
        
        # Analyze the video in segments
        num_segments = min(5, int(video.duration / 3))
        segment_duration = video.duration / num_segments
        
        # Commentary templates based on video characteristics
        intro_templates = [
            "Let me break down what's happening here",
            "This is really interesting, watch closely",
            "Pay attention to what happens next",
            "Here's something you need to see",
            "Check out this incredible moment"
        ]
        
        action_templates = [
            "Look at the movement and timing here",
            "Notice how everything comes together",
            "This is where things get exciting",
            "The energy in this moment is incredible",
            "Watch how this unfolds perfectly"
        ]
        
        analysis_templates = [
            "What makes this special is the precision",
            "The key detail most people miss here",
            "This demonstrates real skill and timing",
            "There's so much happening in this frame",
            "The composition here is really well done"
        ]
        
        reaction_templates = [
            "That's absolutely impressive",
            "This never gets old to watch",
            "You can feel the intensity here",
            "That's exactly what makes this viral",
            "The execution here is flawless"
        ]
        
        outro_templates = [
            "Drop a like if this amazed you too",
            "Follow for more breakdowns like this",
            "Let me know what you think in the comments",
            "Thanks for watching, more coming soon",
            "Hit that follow button for daily content"
        ]
        
        for i in range(num_segments):
            segment_start = i * segment_duration
            segment_mid = segment_start + (segment_duration / 2)
            segment_end = segment_start + segment_duration
            
            if segment_mid < video.duration:
                # Get frame from middle of segment
                frame = video.get_frame(segment_mid)
                
                # Analyze frame characteristics
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                
                # Motion detection (compare with next frame if possible)
                motion_level = 0
                if segment_mid + 0.5 < video.duration:
                    next_frame = video.get_frame(segment_mid + 0.5)
                    next_gray = cv2.cvtColor(next_frame, cv2.COLOR_RGB2GRAY)
                    frame_diff = cv2.absdiff(gray, next_gray)
                    motion_level = np.mean(frame_diff)
                
                # Edge detection for complexity
                edges = cv2.Canny(gray, 100, 200)
                edge_density = np.sum(edges > 0) / edges.size
                
                # Brightness analysis
                brightness = np.mean(gray)
                
                # Color analysis
                color_variance = np.var(frame, axis=(0, 1))
                avg_color_var = np.mean(color_variance)
                
                # Generate contextual commentary based on analysis
                commentary = ""
                
                if i == 0:
                    # Intro segment - set context
                    commentary = np.random.choice(intro_templates)
                    
                elif i == num_segments - 1:
                    # Outro segment - call to action
                    commentary = np.random.choice(outro_templates)
                    
                else:
                    # Middle segments - vary based on content
                    if motion_level > 30:
                        # High motion - action commentary
                        commentary = np.random.choice(action_templates)
                    elif edge_density > 0.12:
                        # Complex visual - analysis commentary
                        commentary = np.random.choice(analysis_templates)
                    elif brightness < 100 or brightness > 180:
                        # Dramatic lighting - reaction commentary
                        commentary = np.random.choice(reaction_templates)
                    else:
                        # Balanced scene - rotate through types
                        all_mid_templates = action_templates + analysis_templates + reaction_templates
                        commentary = np.random.choice(all_mid_templates)
                
                commentary_suggestions.append({
                    'segment': i + 1,
                    'start_time': round(segment_start, 1),
                    'end_time': round(segment_end, 1),
                    'commentary': commentary,
                    'characteristics': {
                        'motion_level': round(motion_level, 2),
                        'complexity': round(edge_density, 2),
                        'brightness': round(brightness, 2)
                    }
                })
        
        video.close()
        
        return {
            'success': True,
            'commentary_suggestions': commentary_suggestions
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }