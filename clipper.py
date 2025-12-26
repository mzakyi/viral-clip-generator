# clipper.py

import os
import tempfile
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

import yt_dlp


def download_youtube_video(url):
    """
    Download YouTube video using yt-dlp and return the file path.
    """
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(tempfile.gettempdir(), 'video.%(ext)s'),
        'quiet': True,
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
    return filename


def add_captions(clip, caption_text, fontsize=30, color='white', position=('center', 'bottom')):
    """
    Overlay text captions onto a video clip.
    """
    txt_clip = TextClip(caption_text, fontsize=fontsize, color=color, method='caption')
    txt_clip = txt_clip.set_position(position).set_duration(clip.duration)
    return CompositeVideoClip([clip, txt_clip])




def auto_generate_clips(url, clip_times=[(0,5)], captions=None):
    video_path = download_youtube_video(url)
    clips_paths = []

    if captions is None:
        captions = [""] * len(clip_times)

    for i, (start, end) in enumerate(clip_times):
        output_path = f"clip_{i+1}.mp4"
        ffmpeg_extract_subclip(video_path, start, end, targetname=output_path)

        if captions[i]:
            # Add captions if needed using VideoFileClip + CompositeVideoClip
            from moviepy.video.io.VideoFileClip import VideoFileClip
            from moviepy.video.VideoClip import TextClip
            from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

            clip = VideoFileClip(output_path)
            txt = TextClip(captions[i], fontsize=24, color='white').set_duration(clip.duration).set_position('bottom')
            clip_with_caption = CompositeVideoClip([clip, txt])
            clip_with_caption.write_videofile(output_path, codec="libx264", audio_codec="aac")
            clip.close()

        clips_paths.append(output_path)

    return clips_paths

