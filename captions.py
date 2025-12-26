from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

import whisper

# Load Whisper model (small, fast)
model = whisper.load_model("base")

def add_captions(video_path, output_path):
    """
    Adds auto captions using Whisper to the given video file.
    """
    video = VideoFileClip(video_path)
    result = model.transcribe(video_path)

    clips = [video]
    for seg in result["segments"]:
        txt = TextClip(
            seg["text"],
            fontsize=48,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(video.w * 0.9, None)
        ).set_start(seg["start"]).set_duration(seg["end"] - seg["start"])\
         .set_position(("center", "bottom"))

        clips.append(txt)

    final = CompositeVideoClip(clips)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    video.close()
