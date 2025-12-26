# video_processor.py
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
import cv2
import os
import glob
import time

def split_clip(input_path, max_clip_len=4):
    video = VideoFileClip(input_path)
    clips = []
    start = 0
    while start < video.duration:
        end = min(start + max_clip_len, video.duration)
        clips.append(video.subclip(start, end))
        start += max_clip_len
    return clips

def add_freeze_frame(clip, duration=1):
    """
    Add a freeze frame at the end of a clip
    
    Args:
        clip: VideoFileClip object
        duration: Duration of freeze frame in seconds
    """
    from moviepy.editor import ImageClip
    
    # Get the last frame and create a freeze frame
    last_frame = clip.get_frame(clip.duration - 0.01)
    freeze_clip = ImageClip(last_frame).set_duration(duration)
    
    # Concatenate original clip with freeze frame
    return concatenate_videoclips([clip, freeze_clip])

def add_text_overlay(clip, text="Hook", fontsize=50, color='white', pos='center', duration=None):
    if duration is None:
        duration = clip.duration
    txt_clip = TextClip(text, fontsize=fontsize, color=color)
    txt_clip = txt_clip.set_position(pos).set_duration(duration)
    return CompositeVideoClip([clip, txt_clip])

def export_video(clips, output_path="output.mp4", fps=30):
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_path, fps=fps)
    return output_path

def download_audio_temp(video_url):
    """Download audio from YouTube video to a temporary file"""
    import yt_dlp
    import tempfile
    
    try:
        # Create a temporary file for the audio
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_audio_path = temp_audio.name
        temp_audio.close()
        
        # yt-dlp options for audio extraction
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': temp_audio_path.replace('.mp3', ''),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        return {
            'success': True,
            'path': temp_audio_path
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
        
        # yt-dlp options
        ydl_opts = {
            'format': 'best[height<=720]',  # 720p or lower for faster download
            'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_path = ydl.prepare_filename(info)
            
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
        clip = video.subclip(start_time, end_time)
        
        # Add captions if requested
        if add_captions and caption_text:
            txt_clip = TextClip(
                caption_text,
                fontsize=50,
                color='white',
                stroke_color='black',
                stroke_width=2,
                font='Arial-Bold',
                method='caption',
                size=(clip.w * 0.9, None)
            )
            txt_clip = txt_clip.set_position(('center', 'top')).set_duration(clip.duration)
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
        return {
            'success': False,
            'error': str(e)
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
    
    Args:
        video_clip: VideoFileClip object
        audio_path: Path to audio file (mp3, wav, etc.)
    """
    from moviepy.editor import AudioFileClip, CompositeAudioClip
    
    # Load the commentary audio
    commentary = AudioFileClip(audio_path)
    
    # Mix original video audio with commentary
    if video_clip.audio:
        mixed_audio = CompositeAudioClip([video_clip.audio, commentary])
    else:
        mixed_audio = commentary
    
    # Set the mixed audio to the video
    final_clip = video_clip.set_audio(mixed_audio)
    
    return final_clip

def add_multiple_text_overlays(clip, text_overlays):
    """
    Add multiple text overlays at different times with proper positioning
    
    Args:
        clip: VideoFileClip object
        text_overlays: List of dicts with keys: text, start_time, end_time, position, fontsize, color
    """
    from moviepy.editor import TextClip, CompositeVideoClip
    
    video_clips = [clip]
    
    for overlay in text_overlays:
        # Create text with better styling
        txt_clip = TextClip(
            overlay.get('text', ''),
            fontsize=overlay.get('fontsize', 50),
            color=overlay.get('color', 'yellow'),
            stroke_color='black',
            stroke_width=3,
            font='Arial-Bold',
            method='caption',
            size=(int(clip.w * 0.85), None)  # 85% of video width
        )
        
        # Position mapping with proper margins
        position = overlay.get('position', 'center')
        if position == 'top':
            pos = ('center', int(clip.h * 0.15))  # 15% from top
        elif position == 'bottom':
            pos = ('center', int(clip.h * 0.75))  # 75% from top (leaves 25% margin)
        else:  # center
            pos = 'center'
        
        txt_clip = txt_clip.set_position(pos)
        txt_clip = txt_clip.set_start(overlay.get('start_time', 0))
        txt_clip = txt_clip.set_end(overlay.get('end_time', clip.duration))
        
        video_clips.append(txt_clip)
    
    return CompositeVideoClip(video_clips)

def add_intro_outro_overlay(clip, intro_text="", outro_text="", intro_duration=3, outro_duration=3):
    """
    Add intro and outro text overlays ON TOP of the video (not black screens)
    
    Args:
        clip: VideoFileClip object
        intro_text: Text for intro overlay
        outro_text: Text for outro overlay
        intro_duration: How long intro text shows (seconds)
        outro_duration: How long outro text shows (seconds)
    """
    from moviepy.editor import TextClip, CompositeVideoClip
    
    video_clips = [clip]
    
    # Add intro text overlay at the start
    if intro_text:
        intro_txt = TextClip(
            intro_text,
            fontsize=70,
            color='white',
            stroke_color='black',
            stroke_width=4,
            font='Arial-Bold',
            method='caption',
            size=(int(clip.w * 0.8), None)
        )
        intro_txt = intro_txt.set_position('center')
        intro_txt = intro_txt.set_start(0)
        intro_txt = intro_txt.set_end(intro_duration)
        intro_txt = intro_txt.crossfadein(0.5).crossfadeout(0.5)  # Fade effect
        
        video_clips.append(intro_txt)
    
    # Add outro text overlay at the end
    if outro_text:
        outro_start = max(0, clip.duration - outro_duration)
        
        outro_txt = TextClip(
            outro_text,
            fontsize=60,
            color='yellow',
            stroke_color='black',
            stroke_width=4,
            font='Arial-Bold',
            method='caption',
            size=(int(clip.w * 0.8), None)
        )
        outro_txt = outro_txt.set_position('center')
        outro_txt = outro_txt.set_start(outro_start)
        outro_txt = outro_txt.set_end(clip.duration)
        outro_txt = outro_txt.crossfadein(0.5)  # Fade in effect
        
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
    
    Args:
        video_clip: VideoFileClip object
        commentary_segments: List of dicts with keys: audio_path, start_time, volume
        original_audio_volume: Volume level for original video audio (0.0 to 1.0)
    
    Returns:
        Video clip with all commentary segments mixed in
    """
    from moviepy.editor import AudioFileClip, CompositeAudioClip
    
    try:
        audio_clips = []
        
        # Keep original video audio if it exists, but reduce volume
        if video_clip.audio:
            # Reduce the original audio volume so commentary is clearer
            reduced_original = video_clip.audio.volumex(original_audio_volume)
            audio_clips.append(reduced_original)
        
        # Add each commentary segment
        for segment in commentary_segments:
            commentary = AudioFileClip(segment['audio_path'])
            
            # Set start time
            commentary = commentary.set_start(segment.get('start_time', 0))
            
            # Adjust volume if specified
            volume = segment.get('volume', 1.0)
            if volume != 1.0:
                commentary = commentary.volumex(volume)
            
            audio_clips.append(commentary)
        
        # Composite all audio
        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            return video_clip.set_audio(final_audio)
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