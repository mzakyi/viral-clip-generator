# video_processor.py - COMPATIBLE WITH MOVIEPY 1.x - FIXED VERSION

import os
import cv2
import glob
import time
import numpy as np
from moviepy import (
    VideoFileClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
    AudioFileClip,
    ImageClip,
    ColorClip,
    CompositeAudioClip
)

# Force MoviePy to NOT use ImageMagick for text (we'll handle it differently)
os.environ["IMAGEMAGICK_BINARY"] = ""

def get_available_font():
    """Find an available font for text overlays"""
    import platform
    
    font_paths = []
    
    if platform.system() == "Windows":
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/verdana.ttf",
        ]
    elif platform.system() == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path
    
    return None

def create_text_clip_safe(text, fontsize=50, color='yellow', font=None, 
                          stroke_color='black', stroke_width=2, size=None, method='caption'):
    """
    Create a text clip that works with both MoviePy 1.x and 2.x
    """
    try:
        # Try MoviePy 2.x syntax first (txt=)
        return TextClip(
            txt=text,
            fontsize=fontsize,
            color=color,
            font=font,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            size=size,
            method=method
        )
    except TypeError:
        # Fall back to MoviePy 1.x syntax (text=)
        return TextClip(
            text=text,
            fontsize=fontsize,
            color=color,
            font=font,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            size=size,
            method=method
        )

def split_clip(input_path, max_clip_len=4):
    """Split video into multiple clips"""
    video = VideoFileClip(input_path)
    clips = []
    start = 0
    while start < video.duration:
        end = min(start + max_clip_len, video.duration)
        clips.append(video.subclip(start, end))
        start += max_clip_len
    return clips

def add_freeze_frame(clip, duration=1):
    """Add a freeze frame at the end of a clip"""
    last_frame = clip.get_frame(clip.duration - 0.01)
    freeze_clip = ImageClip(last_frame).set_duration(duration)
    return concatenate_videoclips([clip, freeze_clip])

def add_text_overlay(video_clip, text, position='center', fontsize=50, color='yellow', 
                     start_time=0, end_time=None, bg_color=None):
    """Add text overlay to video with proper font handling"""
    
    if end_time is None:
        end_time = video_clip.duration
    
    font_path = get_available_font()
    video_width, video_height = video_clip.size
    
    position_map = {
        'top': ('center', 50),
        'center': ('center', 'center'),
        'bottom': ('center', video_height - 100)
    }
    
    pos = position_map.get(position, ('center', 'center'))
    
    try:
        txt_clip = create_text_clip_safe(
            text=text,
            fontsize=fontsize,
            color=color,
            font=font_path,
            stroke_color='black',
            stroke_width=2,
            size=(video_width - 40, None),
            method='caption'
        )
        
        if bg_color:
            bg = ColorClip(
                size=(txt_clip.w + 20, txt_clip.h + 20),
                color=bg_color
            ).set_opacity(0.7)
            txt_clip = CompositeVideoClip([bg, txt_clip.set_position('center')])
        
        txt_clip = txt_clip.set_position(pos).set_start(start_time).set_duration(end_time - start_time)
        result = CompositeVideoClip([video_clip, txt_clip])
        
        return result
        
    except Exception as e:
        print(f"Error adding text overlay: {e}")
        return video_clip

"""
Add this to video_processor.py to diagnose the issue
"""

def diagnose_clip(clip, label="Clip"):
    """Diagnose a clip's properties"""
    print(f"\n{'='*50}")
    print(f"DIAGNOSING: {label}")
    print(f"{'='*50}")
    print(f"Type: {type(clip).__name__}")
    print(f"Duration: {clip.duration:.2f}s")
    print(f"Size: {clip.size}")
    print(f"Has audio: {clip.audio is not None}")
    
    # Check if it's a composite
    if isinstance(clip, CompositeVideoClip):
        print(f"Number of clips in composite: {len(clip.clips)}")
        for idx, subclip in enumerate(clip.clips):
            print(f"  Clip {idx}: {type(subclip).__name__}")
            if hasattr(subclip, 'txt'):
                print(f"    → Text: {subclip.txt}")
            if hasattr(subclip, 'start'):
                print(f"    → Start: {subclip.start}")
            if hasattr(subclip, 'duration'):
                print(f"    → Duration: {subclip.duration}")
            if hasattr(subclip, 'pos'):
                print(f"    → Position: {subclip.pos}")
    
    print(f"{'='*50}\n")
    return clip

def add_multiple_text_overlays(clip, text_overlays):
    """Add multiple text overlays - FIXED for MoviePy 2.x"""
    print(f"📝 Adding {len(text_overlays)} text overlays...")
    
    if not text_overlays:
        print("⏭️ No text overlays to add")
        return clip
    
    font_path = get_available_font()
    all_clips = [clip]
    
    for idx, overlay in enumerate(text_overlays):
        overlay_text = overlay.get('text', '')
        overlay_fontsize = overlay.get('fontsize', 50)
        overlay_color = overlay.get('color', 'yellow')
        start_time = overlay.get('start_time', 0)
        end_time = overlay.get('end_time', clip.duration)
        
        if not overlay_text:
            print(f"  ⚠️ Skipping overlay #{idx+1}: empty text")
            continue
        
        try:
            print(f"  Creating overlay #{idx+1}: '{overlay_text}'")
            
            # MoviePy 2.x syntax
            txt_clip = TextClip(
                text=overlay_text,
                font_size=overlay_fontsize,  # ← Changed from fontsize
                color='white',
                font=font_path,
                stroke_color='black',
                stroke_width=3,
                size=(int(clip.w * 0.80), None),
                method='caption'
            )
            
            # Calculate position
            position = overlay.get('position', 'center')
            if position == 'top':
                pos = ('center', int(clip.h * 0.15))
            elif position == 'bottom':
                pos = ('center', int(clip.h * 0.75))
            else:
                pos = 'center'
            
            # Calculate duration
            duration = min(end_time - start_time, clip.duration - start_time)
            
            if duration <= 0:
                print(f"  ⚠️ Skipping overlay #{idx+1}: invalid duration")
                continue
            
            # Set properties using MoviePy 2.x methods
            txt_clip = txt_clip.with_position(pos)
            txt_clip = txt_clip.with_start(start_time)
            txt_clip = txt_clip.with_duration(duration)
            
            all_clips.append(txt_clip)
            print(f"  ✅ Added overlay #{idx+1}: '{overlay_text}' at {start_time}s-{end_time}s, pos={position}")
            
        except Exception as e:
            print(f"  ❌ Failed to add overlay #{idx+1}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if len(all_clips) == 1:
        print("⚠️ No text overlays were successfully added")
        return clip
    
    try:
        # Create composite
        print(f"Creating composite with {len(all_clips)} clips...")
        result = CompositeVideoClip(all_clips, size=clip.size)
        
        # Preserve audio
        if clip.audio:
            result = result.with_audio(clip.audio)
        
        print(f"✅ Text overlay composite created with {len(all_clips)} clips")
        return result
        
    except Exception as e:
        print(f"❌ Error creating composite: {e}")
        import traceback
        traceback.print_exc()
        return clip

def add_intro_outro_overlay(video_clip, intro_text='', outro_text='', 
                            intro_duration=3, outro_duration=3):
    """Add intro/outro overlays - FIXED for MoviePy 2.x"""
    print(f"🎬 Adding intro/outro overlays...")
    
    if not intro_text and not outro_text:
        print("⏭️ No intro/outro to add")
        return video_clip
    
    font_path = get_available_font()
    all_clips = [video_clip]
    
    if intro_text:
        try:
            print(f"  Creating intro: '{intro_text}'")
            
            intro_clip = TextClip(
                text=intro_text,
                font_size=40,  # ← Changed from fontsize
                color='cyan',
                font=font_path,
                stroke_color='black',
                stroke_width=3,
                size=(int(video_clip.w * 0.80), None),
                method='caption'
            )
            

            actual_intro_duration = min(intro_duration, video_clip.duration)
            
            intro_clip = intro_clip.with_position('center')
            intro_clip = intro_clip.with_start(0)
            intro_clip = intro_clip.with_duration(actual_intro_duration)
            
            all_clips.append(intro_clip)
            print(f"  ✅ Added intro: '{intro_text}' for {actual_intro_duration}s")
            
        except Exception as e:
            print(f"  ❌ Failed to add intro: {e}")
            import traceback
            traceback.print_exc()
    
    if outro_text:
        try:
            print(f"  Creating outro: '{outro_text}'")
            
            outro_clip = TextClip(
                text=outro_text,
                font_size=40,  # ← Changed from fontsize
                color='cyan',
                font=font_path,
                stroke_color='black',
                stroke_width=3,
                size=(int(video_clip.w * 0.80), None),
                method='caption'
            )
            
            outro_start = max(0, video_clip.duration - outro_duration)
            actual_outro_duration = video_clip.duration - outro_start
            
            outro_clip = outro_clip.with_position('center')
            outro_clip = outro_clip.with_start(outro_start)
            outro_clip = outro_clip.with_duration(actual_outro_duration)
            
            all_clips.append(outro_clip)
            print(f"  ✅ Added outro: '{outro_text}' at {outro_start}s for {actual_outro_duration}s")
            
        except Exception as e:
            print(f"  ❌ Failed to add outro: {e}")
            import traceback
            traceback.print_exc()
    
    if len(all_clips) == 1:
        print("⚠️ No intro/outro was successfully added")
        return video_clip
    
    try:
        print(f"Creating composite with {len(all_clips)} clips...")
        result = CompositeVideoClip(all_clips, size=video_clip.size)
        
        if video_clip.audio:
            result = result.with_audio(video_clip.audio)
        
        print(f"✅ Intro/outro composite created with {len(all_clips)} clips")
        return result
        
    except Exception as e:
        print(f"❌ Error creating composite: {e}")
        import traceback
        traceback.print_exc()
        return video_clip

def add_multiple_commentary_segments(video_clip, commentary_segments, original_audio_volume=0.3):
    """Add multiple commentary audio segments - FIXED for MoviePy 2.x"""
    print(f"🎙️ Adding {len(commentary_segments)} commentary segments...")
    
    if not commentary_segments:
        print("⏭️ No commentary to add")
        return video_clip
    
    try:
        audio_clips = []
        
        # Add reduced original audio
        if video_clip.audio:
            reduced_original = video_clip.audio.with_volume_scaled(original_audio_volume)
            audio_clips.append(reduced_original)
            print(f"  ✅ Reduced original audio to {original_audio_volume * 100}%")
        else:
            print("  ⚠️ Warning: Video has no audio to reduce")
        
        # Add commentary segments
        for idx, segment in enumerate(commentary_segments):
            try:
                commentary = AudioFileClip(segment['audio_path'])
                commentary = commentary.with_start(segment.get('start_time', 0))  # ← Use with_start
                
                volume = segment.get('volume', 1.0)
                if volume != 1.0:
                    commentary = commentary.with_volume_scaled(volume)
                
                audio_clips.append(commentary)
                print(f"  ✅ Added commentary #{idx+1} at {segment.get('start_time', 0)}s (volume: {volume}x)")
            except Exception as e:
                print(f"  ⚠️ Warning: Failed to add commentary #{idx+1}: {e}")
                continue
        
        # Composite audio
        if len(audio_clips) > 0:
            final_audio = CompositeAudioClip(audio_clips)
            result = video_clip.with_audio(final_audio)
            print(f"✅ Commentary audio composite created with {len(audio_clips)} audio tracks")
            return result
        else:
            print("⚠️ No audio clips to composite")
            return video_clip
            
    except Exception as e:
        print(f"❌ Error adding commentary segments: {e}")
        import traceback
        traceback.print_exc()
        return video_clip


def add_zoom_effect(clip, zoom_factor=1.2):
    """Add subtle zoom effect - FIXED to preserve audio"""
    print(f"🔍 Adding zoom effect (factor: {zoom_factor})...")
    
    try:
        def zoom(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]
            
            new_h, new_w = int(h / zoom_factor), int(w / zoom_factor)
            
            y1, x1 = (h - new_h) // 2, (w - new_w) // 2
            y2, x2 = y1 + new_h, x1 + new_w
            
            cropped = frame[y1:y2, x1:x2]
            
            return cv2.resize(cropped, (w, h))
        
        # Apply zoom effect only to video
        zoomed = clip.fl(zoom, apply_to=['mask'])
        
        # CRITICAL: Explicitly preserve audio
        if clip.audio:
            zoomed = zoomed.with_audio(clip.audio)
            print("  ✅ Preserved audio after zoom")
        
        print(f"✅ Zoom effect applied successfully")
        return zoomed
        
    except Exception as e:
        print(f"❌ Error adding zoom effect: {e}")
        import traceback
        traceback.print_exc()
        return clip



def export_video(clips, output_path="output.mp4", fps=30):
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_path, fps=fps)
    return output_path

def download_audio_temp(video_url):
    """Download audio from YouTube video to a temporary file"""
    import yt_dlp
    import tempfile
    
    try:
        temp_dir = tempfile.mkdtemp()
        base_filename = f"audio_{int(time.time())}"
        
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
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
        
        files_in_dir = os.listdir(temp_dir)
        audio_extensions = ['.mp3', '.m4a', '.webm', '.wav', '.opus']
        
        for filename in files_in_dir:
            file_path = os.path.join(temp_dir, filename)
            
            if any(filename.endswith(ext) for ext in audio_extensions):
                if os.path.getsize(file_path) > 1000:
                    return {'success': True, 'path': file_path}
            elif filename.startswith('audio_'):
                if os.path.getsize(file_path) > 1000:
                    new_path = file_path + '.mp3'
                    os.rename(file_path, new_path)
                    return {'success': True, 'path': new_path}
        
        return {
            'success': False,
            'error': f'No valid audio file found. Files: {files_in_dir}'
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def download_video(video_url, output_dir='downloads'):
    """Download video from YouTube"""
    import yt_dlp
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        ydl_opts = {
            'format': 'best[ext=mp4][height<=720]/best[height<=720]/best',
            'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            
            possible_extensions = ['.mp4', '.webm', '.mkv', '.avi']
            video_path = None
            
            for ext in possible_extensions:
                test_path = os.path.join(output_dir, f'{video_id}{ext}')
                if os.path.exists(test_path) and os.path.getsize(test_path) > 1000:
                    video_path = test_path
                    break
            
            if not video_path:
                for file in os.listdir(output_dir):
                    if video_id in file and any(file.endswith(ext) for ext in possible_extensions):
                        video_path = os.path.join(output_dir, file)
                        break
            
            if not video_path or not os.path.exists(video_path):
                return {
                    'success': False,
                    'error': f'Video file not found. Files: {os.listdir(output_dir)}'
                }
            
            return {
                'success': True,
                'path': video_path,
                'duration': info.get('duration', 0),
                'title': info.get('title', 'Unknown')
            }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_clip(video_path, start_time, end_time, output_name='clip', add_captions=False, caption_text=''):
    """Create a clip from a video file"""
    try:
        os.makedirs('clips', exist_ok=True)
        
        video = VideoFileClip(video_path)
        clip = video.subclip(start_time, end_time)
        
        if add_captions and caption_text:
            font_path = get_available_font()

            txt_clip = create_text_clip_safe(
                text=caption_text,
                fontsize=50,
                color='yellow',
                font=font_path,
                stroke_color='black',
                stroke_width=2
            )
            
            txt_clip = txt_clip.set_position(('center', 'top')).set_duration(clip.duration)
            clip = CompositeVideoClip([clip, txt_clip])
        
        timestamp = int(time.time())
        output_path = os.path.join('clips', f'{output_name}_{timestamp}.mp4')
        
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=30)
        
        clip.close()
        video.close()
        
        return {'success': True, 'path': output_path}
        
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

def generate_ai_voice(text, output_path='temp_voice.mp3'):
    """Generate AI voice from text using gTTS"""
    try:
        from gtts import gTTS
        
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)
        
        return {'success': True, 'path': output_path}
    except Exception as e:
        return {'success': False, 'error': str(e)}
 

def analyze_video_for_monetization(video_path):
    """Analyze a video to check if it meets monetization criteria"""
    try:
        video = VideoFileClip(video_path)
        
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
        
        # Duration Score
        duration = video.duration
        if 15 <= duration <= 60:
            scores['duration_score'] = 100
        elif 10 <= duration < 15 or 60 < duration <= 90:
            scores['duration_score'] = 80
        elif duration < 10:
            scores['duration_score'] = 50
        else:
            scores['duration_score'] = 60
        
        # Audio Modification Score
        if video.audio:
            try:
                audio_array = video.audio.to_soundarray(fps=22050)
                
                if not isinstance(audio_array, np.ndarray):
                    audio_array = np.array(audio_array)
                
                if len(audio_array.shape) > 1:
                    audio_energy = np.sqrt(np.mean(audio_array**2, axis=1))
                else:
                    audio_energy = np.sqrt(audio_array**2)
                
                energy_variance = np.var(audio_energy)
                
                if energy_variance > 0.01:
                    scores['audio_modification_score'] = 100
                elif energy_variance > 0.005:
                    scores['audio_modification_score'] = 70
                else:
                    scores['audio_modification_score'] = 40
            except Exception as audio_error:
                print(f"Audio analysis error: {audio_error}")
                scores['audio_modification_score'] = 50
        else:
            scores['audio_modification_score'] = 0
        
        # Visual Complexity Score
        sample_times = [video.duration * 0.25, video.duration * 0.5, video.duration * 0.75]
        complexity_scores = []
        
        try:
            for t in sample_times:
                if t < video.duration:
                    frame = video.get_frame(t)
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
            print(f"Visual analysis error: {visual_error}")
            scores['visual_complexity_score'] = 50
        
        # Overall Score
        scores['overall_score'] = int(
            (scores['duration_score'] * 0.2) +
            (scores['audio_modification_score'] * 0.5) +
            (scores['visual_complexity_score'] * 0.3)
        )
        
        # Pass/Fail
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
        return {'success': False, 'error': str(e)}

def generate_monetization_report(analysis_result):
    """Generate a human-readable report from analysis results"""
    if not analysis_result['success']:
        return f"❌ Error analyzing video: {analysis_result['error']}"
    
    scores = analysis_result['scores']
    details = analysis_result['details']
    
    if scores['pass_status']:
        status = "✅ **PASSES MONETIZATION CHECK**"
    else:
        status = "⚠️ **NEEDS IMPROVEMENT**"
    
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
    
    recommendations = []
    
    if scores['audio_modification_score'] < 60:
        recommendations.append("❌ **CRITICAL:** Add voice commentary or analysis over the clip!")
    
    if scores['visual_complexity_score'] < 60:
        recommendations.append("⚠️ Add more text overlays, captions, or visual effects")
    
    if scores['duration_score'] < 80:
        if details['duration'] < 15:
            recommendations.append("⚠️ Video is too short. Aim for 15-60 seconds")
        elif details['duration'] > 90:
            recommendations.append("⚠️ Video is too long. Consider trimming to under 60 seconds")
    
    if not details['has_audio']:
        recommendations.append("❌ **CRITICAL:** Video has no audio! Add commentary or sound effects")
    
    if not recommendations:
        recommendations.append("✅ Your video looks great! It should be safe to monetize")
        recommendations.append("✅ Make sure the original content source allows transformative use")
    
    for rec in recommendations:
        report += f"\n{rec}\n"
    
    report += "\n---\n"
    
    if scores['pass_status']:
        report += """
### 🎉 Final Verdict:
Your video has strong transformative elements and should be eligible for monetization.

**Next Steps:**
1. ✅ Upload to your platform
2. ✅ Enable monetization
3. ✅ Monitor for any copyright claims
"""
    else:
        report += """
### ⚠️ Final Verdict:
Your video needs more transformative elements before it's monetization-ready.

**Next Steps:**
1. ⚠️ Go back to Monetization Prep
2. ⚠️ Add more transformative elements
3. ⚠️ Re-verify before uploading
"""
    
    return report

def analyze_video_for_suggestions(video_path):
    """Analyze video and suggest where to add customizations"""
    try:
        video = VideoFileClip(video_path)
        suggestions = []
        
        num_segments = min(5, int(video.duration / 3))
        segment_duration = video.duration / num_segments
        
        for i in range(num_segments):
            segment_start = i * segment_duration
            segment_mid = segment_start + (segment_duration / 2)
            segment_end = segment_start + segment_duration
            
            if segment_mid < video.duration:
                frame = video.get_frame(segment_mid)
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                brightness = np.mean(gray)
                
                edges = cv2.Canny(gray, 100, 200)
                edge_density = np.sum(edges > 0) / edges.size
                
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
        return {'success': False, 'error': str(e)}


def auto_optimize_video(video_path, suggestions, user_instructions=""):
    """Automatically optimize video based on AI suggestions"""
    import tempfile
    
    try:
        clip = VideoFileClip(video_path)
        video_clips = [clip]
        commentary_segments = []
        
        font_path = get_available_font()
        used_text_examples = set()
        
        # Process suggestions
        for idx, suggestion in enumerate(suggestions):
            for rec in suggestion['recommendations']:
                
                if rec['type'] == 'text_overlay':
                    text_options = [
                        rec['example'],
                        "🔥 Amazing!",
                        "👀 Watch this",
                        "⚡ Incredible",
                    ]
                    
                    available_texts = [t for t in text_options if t not in used_text_examples]
                    if not available_texts:
                        available_texts = text_options
                    
                    selected_text = available_texts[0]
                    used_text_examples.add(selected_text)
                    
                    try:
                        txt_clip = create_text_clip_safe(
                            text=selected_text,
                            fontsize=50,
                            color=rec.get('color', 'yellow'),
                            font=font_path,
                            stroke_color='black',
                            stroke_width=2
                        )
                        
                        position = rec.get('position', 'center')
                        if position == 'top':
                            pos = ('center', int(clip.h * 0.15))
                        elif position == 'bottom':
                            pos = ('center', int(clip.h * 0.75))
                        else:
                            pos = 'center'
                        
                        start_offset = idx * 0.2
                        txt_clip = txt_clip.set_position(pos)
                        txt_clip = txt_clip.set_start(suggestion['start_time'] + start_offset)
                        txt_clip = txt_clip.set_duration(min(suggestion['end_time'], clip.duration) - (suggestion['start_time'] + start_offset))
                        
                        video_clips.append(txt_clip)
                    except Exception as e:
                        print(f"Warning: Failed to add text clip: {e}")
                        continue
                
                elif rec['type'] == 'commentary':
                    commentary_text = rec['example']
                    
                    if user_instructions:
                        if 'exciting' in user_instructions.lower():
                            commentary_text += " This is absolutely thrilling!"
                        elif 'educational' in user_instructions.lower():
                            commentary_text = commentary_text.replace("incredible", "educational")
                    
                    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    temp_audio_path = temp_audio.name
                    temp_audio.close()
                    
                    voice_result = generate_ai_voice(commentary_text, temp_audio_path)
                    
                    if voice_result['success']:
                        commentary_segments.append({
                            'audio_path': voice_result['path'],
                            'start_time': suggestion['start_time'],
                            'volume': 1.3
                        })
        
        # Composite video
        final_clip = CompositeVideoClip(video_clips)
        
        # Add commentary audio with volume control
        if commentary_segments:
            audio_clips = []
            
            if final_clip.audio:
                reduced_original = final_clip.audio.volumex(0.20)
                audio_clips.append(reduced_original)
            
            for segment in commentary_segments:
                commentary = AudioFileClip(segment['audio_path'])
                commentary = commentary.set_start(segment['start_time'])
                commentary = commentary.volumex(segment['volume'])
                audio_clips.append(commentary)
            
            if audio_clips:
                final_audio = CompositeAudioClip(audio_clips)
                final_clip = final_clip.set_audio(final_audio)
        
        # Add intro/outro
        intro_options = ["🔥 WATCH THIS", "⚡ AMAZING MOMENT", "👀 CHECK THIS OUT"]
        outro_options = ["👍 Like & Follow!", "🔔 Subscribe for More", "💬 Comment Below"]
        
        intro_text = np.random.choice(intro_options)
        
        try:
            intro_txt = create_text_clip_safe(
                text=intro_text,
                fontsize=70,
                color='yellow',
                font=font_path,
                stroke_color='black',
                stroke_width=4
            )
            intro_txt = intro_txt.set_position('center').set_duration(2).set_start(0)
        except Exception as e:
            print(f"Warning: Failed to add intro text: {e}")
            intro_txt = None
        
        outro_text = np.random.choice(outro_options)
        
        try:
            outro_txt = create_text_clip_safe(
                text=outro_text,
                fontsize=60,
                color='white',
                font=font_path,
                stroke_color='black',
                stroke_width=4
            )
            outro_start = max(0, final_clip.duration - 3)
            outro_txt = outro_txt.set_position('center').set_duration(3).set_start(outro_start)
        except Exception as e:
            print(f"Warning: Failed to add outro text: {e}")
            outro_txt = None
        
        # Compose final video with intro/outro
        final_clips = [final_clip]
        if intro_txt:
            final_clips.append(intro_txt)
        if outro_txt:
            final_clips.append(outro_txt)
        
        final_clip = CompositeVideoClip(final_clips)
        
        return {
            'success': True,
            'clip': final_clip,
            'commentary_segments': commentary_segments
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"{str(e)}\n{traceback.format_exc()}"
        }


if __name__ == "__main__":
    print("Testing font detection...")
    font = get_available_font()
    if font:
        print(f"✓ Found working font: {font}")
    else:
        print("⚠ No font found, will use MoviePy default")