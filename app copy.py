import streamlit as st
from dotenv import load_dotenv
import os
import time
import importlib
import youtube_api
importlib.reload(youtube_api)
from youtube_api import YouTubeAPI
from video_processor import (
    split_clip, 
    add_freeze_frame, 
    add_text_overlay, 
    export_video, 
    download_audio_temp, 
    download_video, 
    create_clip, 
    get_all_clips, 
    cleanup_downloads,
    add_commentary_audio,
    add_multiple_text_overlays,
    add_intro_outro_overlay,
    add_zoom_effect,
    generate_ai_voice,
    analyze_video_for_monetization,
    generate_monetization_report,
    add_multiple_commentary_segments,
    analyze_video_for_suggestions
)
import random
from viral_moment_detector import ViralMomentDetector
from audio_energy_detector import detect_energy_peaks, generate_report as energy_generate_report, format_timestamp

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Viral Clip Generator",
    page_icon="🎬",
    layout="wide"
)

# ===== HELPER FUNCTIONS =====
def generate_simple_clickbait(video_title):
    """Generate smart template-based clickbait caption"""
    
    # Power words and templates
    templates = [
        "🔥 You WON'T believe this...",
        "😱 This changes EVERYTHING",
        "💯 The SECRET nobody tells you",
        "⚡ INSANE {topic} method",
        "🚀 This ONE {topic} trick...",
        "🤯 Mind-blowing {topic}",
        "💪 You've been doing {topic} WRONG",
        "🎯 GENIUS {topic} hack",
        "⚠️ Don't skip this {topic}",
        "👀 Wait for the {topic} part...",
        "💎 Hidden {topic} GOLD",
        "⭐ {topic} GAME CHANGER",
        "🤑 They hide this {topic} trick",
        "😳 The {topic} reveal is CRAZY",
        "🔥 {topic} hack that WORKS",
        "💰 {topic} method that made $$",
        "🚨 STOP doing {topic} like this",
        "✨ {topic} SECRET exposed",
        "🎬 Best {topic} ever?",
        "💥 {topic} you NEED to see"
    ]
    
    # Extract topic from video title
    title_lower = video_title.lower()
    topic = None
    
    # Common topics to detect
    topics = {
        'money': ['money', 'cash', 'income', 'earn', 'profit', 'rich'],
        'fitness': ['workout', 'fitness', 'gym', 'exercise', 'muscle'],
        'food': ['cook', 'recipe', 'food', 'meal', 'eat'],
        'tech': ['tech', 'ai', 'computer', 'phone', 'software'],
        'business': ['business', 'startup', 'entrepreneur', 'company'],
        'gaming': ['game', 'gaming', 'play', 'gamer'],
        'life': ['life', 'lifestyle', 'daily', 'routine'],
        'beauty': ['makeup', 'beauty', 'skincare', 'hair'],
    }
    
    # Detect topic
    for key, keywords in topics.items():
        if any(keyword in title_lower for keyword in keywords):
            topic = key
            break
    
    # Select template
    caption = random.choice(templates)
    
    # Replace {topic} with detected topic or remove it
    if '{topic}' in caption:
        if topic:
            caption = caption.replace('{topic}', topic)
        else:
            caption = caption.replace('{topic} ', '')
    
    # Ensure it's under 60 characters
    if len(caption) > 60:
        caption = caption[:57] + "..."
    
    return caption

def format_timestamp(seconds):
    """Convert seconds to MM:SS format"""
    # Convert to int if it's a string
    if isinstance(seconds, str):
        try:
            seconds = int(seconds)
        except:
            seconds = 0
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

# Initialize services
@st.cache_resource
def get_youtube_api():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        st.error("⚠️ YouTube API key not found! Add it to your .env file")
        st.stop()
    return YouTubeAPI(api_key)

youtube_api = get_youtube_api()


# Title
st.title("🎬 Viral Video Discovery & Clip Generator")
st.markdown("---")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Choose a feature:",
    ["🔥 Discover Viral Videos", "🤖 AI Viral Moments", "✂️ Clip Generator", "💰 Monetization Prep", "🔍 Monetization Checker", "👥 Creator Inspiration", "💰 Monetization Dashboard"]
)

# ====== DISCOVER VIRAL VIDEOS PAGE ======
if page == "🔥 Discover Viral Videos":
    st.header("🔥 Discover High-View YouTube Videos")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category = st.selectbox(
            "Category",
            ["All", "podcast", "gaming", "education", "comedy", "finance", "sports", "music", "tech"]
        )
    
    with col2:
        days = st.selectbox(
            "Time Range",
            [7, 30, 90, 365],
            format_func=lambda x: f"Last {x} days"
        )
    
    with col3:
        min_views = st.selectbox(
            "Minimum Views",
            [1000000, 5000000, 10000000],
            format_func=lambda x: f"{x:,}"
        )
    
    # Search button
    if st.button("🔍 Search Viral Videos", type="primary"):
        with st.spinner("Searching for viral videos..."):
            search_category = "" if category == "All" else category
            videos = youtube_api.search_viral_videos(
                category=search_category,
                days_ago=days,
                min_views=min_views,
                max_results=20
            )
            
            if videos:
                st.success(f"Found {len(videos)} viral videos!")
                
                # Display videos in a grid
                for video in videos:
                    with st.container():
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            st.image(video['thumbnail'], use_column_width=True)
                        
                        with col2:
                            st.subheader(video['title'])
                            st.write(f"**Channel:** {video['channel']}")
                            st.write(f"**Views:** {video['views']:,} | **Likes:** {video['likes']:,} | **Comments:** {video['comments']:,}")
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.link_button("Watch on YouTube", video['url'], use_column_width=True)
                            with col_b:
                                if st.button("🤖 Analyze Moments", key=f"analyze_{video['video_id']}", use_column_width=True):
                                    st.session_state.analyze_url = video['url']
                                    st.info("✅ Video selected! Go to 'AI Viral Moments' to analyze.")
                        
                        st.markdown("---")
            else:
                st.warning("No videos found matching your criteria. Try adjusting the filters.")

# ====== CLIP GENERATOR PAGE ======
elif page == "✂️ Clip Generator":
    st.header("✂️ Create Short-Form Clips")
    
    # Show existing clips
    st.subheader("📁 Your Clips")
    clips = get_all_clips()
    
    if clips:
        st.success(f"You have {len(clips)} clips in your clips folder!")
        st.info(f"📂 Clips folder location: {os.path.abspath('clips')}")
        
        for clip in clips:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.text(clip['filename'])
            with col2:
                st.text(f"{clip['size_mb']} MB")
            with col3:
                with open(clip['path'], 'rb') as file:
                    st.download_button(
                        "⬇️ Download",
                        data=file,
                        file_name=clip['filename'],
                        mime="video/mp4",
                        key=clip['filename']
                    )
        st.markdown("---")
    else:
        st.info("No clips yet. Create your first clip below!")
        st.code(f"Clips will be saved to: {os.path.abspath('clips')}")
        st.markdown("---")
    
    # Check if coming from AI Viral Moments
    if 'clip_start' in st.session_state and 'video_url_for_clip' in st.session_state:
        st.success("🎯 Clip times pre-filled from AI analysis!")
        video_url = st.session_state.video_url_for_clip
    else:
        video_url = st.text_input("📎 Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")
    
    if video_url:
        # Get video info
        video_info = youtube_api.get_video_info(video_url)
        
        if video_info:
            # Display video preview
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(video_info['thumbnail'])
            
            with col2:
                st.subheader(video_info['title'])
                st.write(f"**Channel:** {video_info['channel']}")
                st.write(f"**Views:** {video_info['views']:,}")
            
            st.markdown("---")
            
            # Download video first
            st.subheader("Step 1: Download Video")
            
            if 'downloaded_video' not in st.session_state:
                st.session_state.downloaded_video = None
            
            if st.button("⬇️ Download Video", type="primary"):
                with st.spinner("Downloading video... This may take a minute..."):
                    result = download_video(video_url)
                    
                    if result['success']:
                        st.session_state.downloaded_video = result
                        st.success(f"✅ Video downloaded! Duration: {result['duration']} seconds")
                    else:
                        st.error(f"❌ Error downloading video: {result['error']}")
            
            # Clip creation section
            if st.session_state.downloaded_video:
                st.markdown("---")
                st.subheader("Step 2: Create Clips")
                
                video_duration = st.session_state.downloaded_video['duration']
                
                # Use pre-filled times if available
                default_start = st.session_state.get('clip_start', 0)
                default_end = st.session_state.get('clip_end', min(30, int(video_duration)))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    start_time = st.number_input(
                        "Start Time (seconds)",
                        min_value=0,
                        max_value=int(video_duration),
                        value=int(default_start)
                    )
                
                with col2:
                    end_time = st.number_input(
                        "End Time (seconds)",
                        min_value=0,
                        max_value=int(video_duration),
                        value=int(default_end)
                    )
                
                add_captions = st.checkbox("Add Caption Overlay")
                
                caption_text = ""
                if add_captions:
                    video_title = st.session_state.downloaded_video.get('title', '')
                    if video_title:
                        st.info(f"📹 Video: {video_title}")
                    
                    caption_mode = st.radio(
                        "Caption Style",
                        ["⚡ Smart Template", "✏️ Custom Text"],
                        horizontal=True
                    )
                    
                    if caption_mode == "⚡ Smart Template":
                        col_a, col_b = st.columns([2, 1])
                        
                        with col_a:
                            if st.button("🎲 Generate Clickbait Caption", type="primary"):
                                template_caption = generate_simple_clickbait(video_title)
                                st.session_state.template_caption = template_caption
                                st.success(f"✅ {template_caption}")
                        
                        with col_b:
                            if st.button("🔄 New One"):
                                if 'template_caption' in st.session_state:
                                    del st.session_state.template_caption
                                st.rerun()
                        
                        if 'template_caption' in st.session_state:
                            caption_text = st.text_input(
                                "✏️ Edit caption if needed:",
                                value=st.session_state.template_caption,
                                max_chars=60
                            )
                    else:
                        caption_text = st.text_input(
                            "Enter your custom caption:",
                            max_chars=60,
                            placeholder="Type your caption here..."
                        )
                
                if end_time <= start_time:
                    st.error("End time must be greater than start time!")
                elif end_time - start_time > 60:
                    st.warning("Clip is longer than 60 seconds. Consider shortening for social media.")
                else:
                    if st.button("✂️ Create Clip", type="primary", use_column_width=True):
                        with st.spinner("Creating clip... This may take a minute..."):
                            result = create_clip(
                                video_path=st.session_state.downloaded_video['path'],
                                start_time=start_time,
                                end_time=end_time,
                                output_name="clip",
                                add_captions=add_captions,
                                caption_text=caption_text
                            )
                            
                            if result['success']:
                                st.success("✅ Clip created successfully!")
                                st.info(f"📁 Saved to: {result['path']}")
                                
                                # Download button
                                with open(result['path'], 'rb') as file:
                                    st.download_button(
                                        label="⬇️ Download Clip",
                                        data=file,
                                        file_name=os.path.basename(result['path']),
                                        mime="video/mp4"
                                    )
                                
                                # Clear pre-filled times
                                if 'clip_start' in st.session_state:
                                    del st.session_state.clip_start
                                if 'clip_end' in st.session_state:
                                    del st.session_state.clip_end
                                
                                st.rerun()
                            else:
                                st.error(f"❌ Error creating clip: {result['error']}")
                
                # Cleanup button
                st.markdown("---")
                if st.button("🗑️ Delete Downloaded Video (Save Space)", type="secondary"):
                    cleanup_downloads()
                    st.session_state.downloaded_video = None
                    st.success("✅ Downloads cleaned up!")
                    st.rerun()
        else:
            st.error("❌ Invalid YouTube URL or video not found!")
            
# ====== MONETIZATION PREP PAGE ======
elif page == "💰 Monetization Prep":
    st.header("💰 Prepare Clip for Monetization")
    st.info("✨ Add transformative elements to your clip to meet platform monetization requirements!")
    
    st.markdown("""
    ### What Makes Content Monetizable?
    To avoid copyright claims and qualify for monetization, add:
    - 🎙️ **Voice commentary** - Your analysis or reaction
    - 📝 **Text overlays** - Context, facts, or commentary
    - 🎬 **Intro/Outro** - Your branding and call-to-action
    - 🎨 **Visual effects** - Zoom, highlights, or emphasis
    """)
    
    st.markdown("---")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "📤 Upload Your Clip (MP4)",
        type=['mp4'],
        help="Upload the clip you want to prepare for monetization"
    )
    
    if uploaded_file:
        # Save uploaded file temporarily
        import tempfile
        
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_input.write(uploaded_file.read())
        temp_input_path = temp_input.name
        temp_input.close()
        
        # Load video for preview
        from moviepy.editor import VideoFileClip
        video = VideoFileClip(temp_input_path)
        
        st.success(f"✅ Clip uploaded! Duration: {video.duration:.1f} seconds")
        
        # Preview video
        st.video(temp_input_path)
        
        # ADD/UPDATE THIS SECTION 👇
        # Initialize session state for customizations (with all fields)
        if 'customizations' not in st.session_state:
            st.session_state.customizations = {
                'commentary_audio': None,
                'commentary_segments': [],
                'text_overlays': [],
                'intro_text': '',
                'outro_text': '',
                'intro_duration': 3,
                'outro_duration': 3,
                'add_zoom': False,
                'original_audio_volume': 0.3
            }
        
        # Ensure all keys exist (for backwards compatibility)
        if 'commentary_segments' not in st.session_state.customizations:
            st.session_state.customizations['commentary_segments'] = []
        if 'text_overlays' not in st.session_state.customizations:
            st.session_state.customizations['text_overlays'] = []
        if 'original_audio_volume' not in st.session_state.customizations:
            st.session_state.customizations['original_audio_volume'] = 0.3
        
        # ... continue with AI suggestions and tabs ...
        
            # ADD THIS NEW SECTION HERE
        st.markdown("---")
        st.subheader("🤖 AI-Powered Customization Suggestions")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info("Let AI analyze your video and suggest where to add text, commentary, and effects")
        with col2:
            if st.button("🧠 Get AI Suggestions", type="primary", use_column_width=True):
                with st.spinner("Analyzing video..."):
                    analysis = analyze_video_for_suggestions(temp_input_path)
                    
                    if analysis['success']:
                        st.session_state.ai_suggestions = analysis['suggestions']
                        st.success("✅ Suggestions ready!")
                        st.rerun()
        
        # Display suggestions if available
        if 'ai_suggestions' in st.session_state:
            with st.expander("💡 View AI Suggestions", expanded=True):
                for suggestion in st.session_state.ai_suggestions:
                    st.markdown(f"### Segment {suggestion['segment']} ({format_timestamp(suggestion['start_time'])} - {format_timestamp(suggestion['end_time'])})")
                    
                    for rec in suggestion['recommendations']:
                        if rec['type'] == 'text_overlay':
                            st.info(f"📝 **Text Overlay**: {rec['reason']}")
                            st.caption(f"Example: \"{rec['example']}\" at {rec['position']} in {rec['color']}")
                        
                        elif rec['type'] == 'commentary':
                            st.success(f"🎙️ **Commentary**: {rec['reason']}")
                            st.caption(f"Example: \"{rec['example']}\"")
                        
                        elif rec['type'] == 'effect':
                            st.warning(f"🎨 **Effect**: {rec['reason']}")
                            st.caption(f"Suggested: {rec['effect_name']}")
                    
                    st.markdown("---")
        
        # THEN continue with existing tabs section...
        st.markdown("---")
        st.subheader("🎨 Add Transformative Elements")


        # Tabs for different customization options
        tab1, tab2, tab3, tab4 = st.tabs(["🎙️ Commentary", "📝 Text Overlays", "🎬 Intro/Outro", "🎨 Effects"])
        
        # Initialize session state for customizations
        if 'customizations' not in st.session_state:
            st.session_state.customizations = {
                'commentary_audio': None,
                'text_overlays': [],
                'intro_text': '',
                'outro_text': '',
                'add_zoom': False
            }
        
        # TAB 1: Commentary Audio
        # TAB 1: Commentary Audio
        with tab1:
            st.markdown("### 🎙️ Add Voice Commentary")
            st.info("💡 Add commentary at different points in your video for maximum engagement")
            
            commentary_method = st.radio(
                "Commentary Method:",
                ["🤖 AI Voice (Text-to-Speech)", "🎤 Upload Recording"],
                horizontal=True
            )
            
            # Initialize commentary segments in session state
            if 'commentary_segments' not in st.session_state.customizations:
                st.session_state.customizations['commentary_segments'] = []
            
            st.markdown("---")
                # ADD THIS NEW SECTION HERE 👇
            st.subheader("🔊 Audio Mixing Settings")
            
            original_volume = st.slider(
                "Original Video Audio Volume",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.05,
                help="Lower this to make your commentary clearer (0.3 = 30% volume recommended)"
            )
            st.session_state.customizations['original_audio_volume'] = original_volume
            
            if original_volume <= 0.2:
                st.warning("⚠️ Very low volume - original audio will be barely audible")
            elif original_volume <= 0.4:
                st.success("✅ Good balance - commentary will be clear")
            else:
                st.info("💡 Consider lowering for better commentary clarity")
            
            st.markdown("---")
            # END OF NEW SECTION
            
            st.subheader("Commentary Segments")
            
            # Add new segment
            with st.expander("➕ Add Commentary Segment", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    segment_start = st.number_input(
                        "Start Time (seconds)",
                        min_value=0.0,
                        max_value=float(video.duration),
                        value=0.0,
                        step=0.5,
                        key='new_segment_start'
                    )
                
                with col2:
                    segment_volume = st.slider(
                        "Volume",
                        min_value=0.5,
                        max_value=2.0,
                        value=1.0,
                        step=0.1,
                        key='new_segment_volume'
                    )
                
                if commentary_method == "🤖 AI Voice (Text-to-Speech)":
                    commentary_text = st.text_area(
                        "Commentary Script for this segment:",
                        placeholder="What do you want to say at this point in the video?",
                        height=100,
                        key='segment_commentary_text'
                    )
                    
                    if commentary_text:
                        if st.button("🎵 Generate & Add This Segment", type="primary"):
                            with st.spinner("Generating AI voice..."):
                                import tempfile
                                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                                temp_audio_path = temp_audio.name
                                temp_audio.close()
                                
                                result = generate_ai_voice(commentary_text, temp_audio_path)
                                
                                if result['success']:
                                    # Add to segments
                                    st.session_state.customizations['commentary_segments'].append({
                                        'audio_path': result['path'],
                                        'start_time': segment_start,
                                        'volume': segment_volume,
                                        'text': commentary_text[:50] + '...' if len(commentary_text) > 50 else commentary_text
                                    })
                                    st.success("✅ Commentary segment added!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {result['error']}")
                
                else:  # Upload Recording
                    segment_file = st.file_uploader(
                        "Upload Audio for this segment (MP3/WAV)",
                        type=['mp3', 'wav'],
                        key='segment_upload'
                    )
                    
                    if segment_file and st.button("➕ Add This Segment", type="primary"):
                        import tempfile
                        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                        temp_audio.write(segment_file.read())
                        temp_audio_path = temp_audio.name
                        temp_audio.close()
                        
                        st.session_state.customizations['commentary_segments'].append({
                            'audio_path': temp_audio_path,
                            'start_time': segment_start,
                            'volume': segment_volume,
                            'text': f"Uploaded audio at {segment_start}s"
                        })
                        st.success("✅ Commentary segment added!")
                        st.rerun()
            
            st.markdown("---")
            
            # Display existing segments
            if st.session_state.customizations['commentary_segments']:
                st.subheader(f"📋 Added Segments ({len(st.session_state.customizations['commentary_segments'])})")
                
                for idx, segment in enumerate(st.session_state.customizations['commentary_segments']):
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.text(f"🎙️ {segment['text']}")
                    with col2:
                        st.text(f"⏱️ {segment['start_time']:.1f}s")
                    with col3:
                        st.text(f"🔊 {segment['volume']}x")
                    with col4:
                        if st.button("🗑️", key=f"delete_segment_{idx}"):
                            st.session_state.customizations['commentary_segments'].pop(idx)
                            st.rerun()
                
                st.success(f"✅ {len(st.session_state.customizations['commentary_segments'])} commentary segment(s) ready!")
                
                    # ADD THIS NEW SECTION 👇
                st.markdown("---")
                if st.button("🗑️ Clear All Commentary Segments", type="secondary"):
                    st.session_state.customizations['commentary_segments'] = []
                    st.success("✅ All commentary cleared!")
                    st.rerun()
            else:
                st.info("No commentary segments added yet. Add your first one above!")
        
        # TAB 2: Text Overlays
        # TAB 2: Text Overlays
        with tab2:
            st.markdown("### 📝 Add Text Overlays")
            st.info("Add context, facts, or commentary as text on screen")
            
            # Initialize text overlays in session state if not exists
            if 'text_overlays' not in st.session_state.customizations:
                st.session_state.customizations['text_overlays'] = []
            
            st.markdown("---")
            
            # Add new overlay section
            with st.expander("➕ Add New Text Overlay", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_text = st.text_input("Text content", key="new_overlay_text")
                    new_start = st.number_input(
                        "Start time (seconds)", 
                        min_value=0.0, 
                        max_value=float(video.duration), 
                        value=0.0,
                        step=0.5,
                        key="new_overlay_start"
                    )
                
                with col2:
                    new_position = st.selectbox("Position", ['top', 'center', 'bottom'], key="new_overlay_position")
                    new_end = st.number_input(
                        "End time (seconds)", 
                        min_value=0.0, 
                        max_value=float(video.duration), 
                        value=min(3.0, video.duration),
                        step=0.5,
                        key="new_overlay_end"
                    )
                
                col_color, col_size = st.columns(2)
                with col_color:
                    new_color = st.selectbox("Text Color", ['yellow', 'white', 'red', 'green', 'blue'], key="new_overlay_color")
                with col_size:
                    new_fontsize = st.slider("Font Size", 30, 80, 50, key="new_overlay_fontsize")
                
                if new_text:
                    if st.button("➕ Add This Overlay", type="primary"):
                        # Add to session state
                        st.session_state.customizations['text_overlays'].append({
                            'text': new_text,
                            'start_time': new_start,
                            'end_time': new_end,
                            'position': new_position,
                            'fontsize': new_fontsize,
                            'color': new_color
                        })
                        st.success("✅ Text overlay added!")
                        st.rerun()
            
            st.markdown("---")
            
            # Display existing overlays
            if st.session_state.customizations['text_overlays']:
                st.subheader(f"📋 Added Overlays ({len(st.session_state.customizations['text_overlays'])})")
                
                for idx, overlay in enumerate(st.session_state.customizations['text_overlays']):
                    with st.expander(f"Overlay #{idx+1}: \"{overlay['text'][:30]}...\"", expanded=False):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**Text:** {overlay['text']}")
                            st.write(f"**Position:** {overlay['position']}")
                        
                        with col2:
                            st.write(f"**Time:** {overlay['start_time']:.1f}s - {overlay['end_time']:.1f}s")
                            st.write(f"**Color:** {overlay['color']} | **Size:** {overlay['fontsize']}")
                        
                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_overlay_{idx}"):
                                st.session_state.customizations['text_overlays'].pop(idx)
                                st.success("✅ Overlay deleted!")
                                st.rerun()
                
                st.success(f"✅ {len(st.session_state.customizations['text_overlays'])} text overlay(s) ready!")
            else:
                st.info("No text overlays added yet. Add your first one above!")
            
            
            # ADD THIS NEW SECTION 👇
            if st.session_state.customizations['text_overlays']:
                st.markdown("---")
                if st.button("🗑️ Clear All Text Overlays", type="secondary"):
                    st.session_state.customizations['text_overlays'] = []
                    st.success("✅ All text overlays cleared!")
                    st.rerun()
            
       
        # TAB 3: Intro/Outro
        with tab3:
            st.markdown("### 🎬 Add Intro & Outro Text Overlays")
            st.info("✨ Text will appear ON TOP of your video (not black screens)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Intro Text")
                intro_text = st.text_area(
                    "Intro message (shown at start)",
                    placeholder="Example: '🔥 WATCH THIS MOMENT'",
                    max_chars=80,
                    height=100
                )
                intro_duration = st.slider("Intro duration (seconds)", 1, 5, 3, key="intro_dur")
                st.session_state.customizations['intro_text'] = intro_text
                st.session_state.customizations['intro_duration'] = intro_duration
            
            with col2:
                st.markdown("#### Outro Text")
                outro_text = st.text_area(
                    "Outro message (shown at end)",
                    placeholder="Example: '👍 Like & Subscribe for more!'",
                    max_chars=80,
                    height=100
                )
                outro_duration = st.slider("Outro duration (seconds)", 1, 5, 3, key="outro_dur")
                st.session_state.customizations['outro_text'] = outro_text
                st.session_state.customizations['outro_duration'] = outro_duration
            
            if intro_text or outro_text:
                st.success("✅ Intro/Outro text configured!")
            
                # ADD THIS NEW SECTION 👇
            st.markdown("---")
            if st.button("🗑️ Clear Intro & Outro", type="secondary"):
                st.session_state.customizations['intro_text'] = ''
                st.session_state.customizations['outro_text'] = ''
                st.success("✅ Intro/Outro cleared!")
                st.rerun()
        
        # TAB 4: Effects
        with tab4:
            st.markdown("### 🎨 Add Visual Effects")
            st.info("Subtle effects to make your clip more engaging")
            
            add_zoom = st.checkbox("Add subtle zoom effect", value=False)
            st.session_state.customizations['add_zoom'] = add_zoom
            
            if add_zoom:
                st.success("✅ Zoom effect will be applied!")
        
        # PROCESS BUTTON
        st.markdown("---")
        st.subheader("🚀 Generate Monetization-Ready Clip")
        

        # ADD THIS NEW SECTION 👇
        col_reset, col_process = st.columns([1, 2])

        with col_reset:
            if st.button("🔄 Reset All Customizations", type="secondary", use_column_width=True):
                st.session_state.customizations = {
                    'commentary_audio': None,
                    'commentary_segments': [],
                    'text_overlays': [],
                    'intro_text': '',
                    'outro_text': '',
                    'intro_duration': 3,
                    'outro_duration': 3,
                    'add_zoom': False,
                    'original_audio_volume': 0.3
                }
                st.success("✅ All customizations cleared!")
                st.rerun()

        with col_process:
            if st.button("🎬 Process & Download", type="primary", use_column_width=True):
                with st.spinner("Processing your clip... This may take 2-3 minutes..."):
                    try:
                        from moviepy.editor import VideoFileClip
                        
                        # Load video
                        clip = VideoFileClip(temp_input_path)
                        
                        # Apply customizations in order
                        
                        # 1. Add text overlays
                        if st.session_state.customizations['text_overlays']:
                            clip = add_multiple_text_overlays(clip, st.session_state.customizations['text_overlays'])
                        
                        # 2. Add zoom effect
                        if st.session_state.customizations['add_zoom']:
                            clip = add_zoom_effect(clip, zoom_factor=1.15)
                        
                        # 3. Add intro/outro overlays
                        if st.session_state.customizations['intro_text'] or st.session_state.customizations['outro_text']:
                            clip = add_intro_outro_overlay(
                                clip,
                                intro_text=st.session_state.customizations['intro_text'],
                                outro_text=st.session_state.customizations['outro_text'],
                                intro_duration=st.session_state.customizations.get('intro_duration', 3),
                                outro_duration=st.session_state.customizations.get('outro_duration', 3)
                            )
                        
                        # 4. Add commentary audio (multiple segments) with volume control
                        if st.session_state.customizations.get('commentary_segments'):
                            original_volume = st.session_state.customizations.get('original_audio_volume', 0.3)
                            clip = add_multiple_commentary_segments(
                                clip, 
                                st.session_state.customizations['commentary_segments'],
                                original_audio_volume=original_volume
                            )
                        
                        # Export final video
                        output_dir = 'monetization_ready'
                        os.makedirs(output_dir, exist_ok=True)
                        
                        timestamp = int(time.time())
                        output_path = os.path.join(output_dir, f'monetization_ready_{timestamp}.mp4')
                        
                        clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=30)
                        
                        # Close clips
                        clip.close()
                        video.close()
                        
                        st.success("🎉 Your monetization-ready clip is complete!")
                        
                        # Download button
                        with open(output_path, 'rb') as file:
                            st.download_button(
                                label="⬇️ Download Monetization-Ready Clip",
                                data=file,
                                file_name=f'monetization_ready_{timestamp}.mp4',
                                mime="video/mp4",
                                use_column_width=True
                            )
                        
                        st.balloons()
                        
                        
                        # Cleanup temp files
                        try:
                            os.remove(temp_input_path)
                            if st.session_state.customizations['commentary_audio']:
                                os.remove(st.session_state.customizations['commentary_audio'])
                        except:
                            pass
                        
                    except Exception as e:
                        st.error(f"❌ Error processing clip: {str(e)}")
                        st.error("Please try again or contact support if the issue persists.")
                    
# ====== MONETIZATION VERIFICATION PAGE ======
elif page == "🔍 Monetization Checker":
    st.header("🔍 Monetization Verification Scanner")
    st.markdown("""
    Upload your final edited video and get an instant analysis to see if it meets monetization criteria.
    
    **What we check:**
    - ✅ Transformative audio (commentary/analysis)
    - ✅ Visual modifications (text, effects, overlays)
    - ✅ Optimal duration for engagement
    - ✅ Overall copyright safety score
    """)
    
    st.markdown("---")
    
    # File uploader for verification
    verification_file = st.file_uploader(
        "📤 Upload Your Final Video for Verification",
        type=['mp4'],
        help="Upload the video you want to check before posting"
    )
    
    if verification_file:
        import tempfile
        
        # Save uploaded file temporarily
        temp_verify = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_verify.write(verification_file.read())
        temp_verify_path = temp_verify.name
        temp_verify.close()
        
        st.success("✅ Video uploaded! Ready for analysis")
        
        # Preview video
        st.video(temp_verify_path)
        
        st.markdown("---")
        
        # Analysis button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🔍 Analyze for Monetization", type="primary", use_column_width=True):
                with st.spinner("🧠 Analyzing your video... This may take 30-60 seconds..."):
                    # Run analysis
                    analysis = analyze_video_for_monetization(temp_verify_path)
                    
                    if analysis['success']:
                        # Display results
                        st.markdown("---")
                        
                        # Show score with color
                        score = analysis['scores']['overall_score']
                        
                        if score >= 80:
                            st.success(f"## 🎉 Score: {score}/100")
                        elif score >= 60:
                            st.warning(f"## ⚠️ Score: {score}/100")
                        else:
                            st.error(f"## ❌ Score: {score}/100")
                        
                        # Generate and display report
                        report = generate_monetization_report(analysis)
                        st.markdown(report)
                        
                        # Download report option
                        st.markdown("---")
                        st.download_button(
                            label="📄 Download Full Report",
                            data=report,
                            file_name=f"monetization_report_{int(time.time())}.md",
                            mime="text/markdown"
                        )
                        
                        # Action buttons based on result
                        st.markdown("---")
                        
                        if analysis['scores']['pass_status']:
                            st.success("### ✅ Your video is ready to monetize!")
                            st.balloons()
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.info("💡 **Tip:** Always monitor for copyright claims after upload")
                            with col_b:
                                if st.button("🔄 Check Another Video"):
                                    st.rerun()
                        else:
                            st.warning("### ⚠️ Improve your video before uploading")
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("🔙 Go to Monetization Prep"):
                                    st.switch_page("pages/monetization_prep.py")  # Adjust if needed
                            with col_b:
                                if st.button("🔄 Check Another Video"):
                                    st.rerun()
                    else:
                        st.error(f"❌ Error analyzing video: {analysis['error']}")
                
                # Cleanup temp file
                try:
                    os.remove(temp_verify_path)
                except:
                    pass
    
    else:
        # Show example scores
        st.info("### 📊 Understanding the Scores")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Duration Score**
            - Checks optimal length
            - 15-60s is ideal
            - Too short/long = lower score
            """)
        
        with col2:
            st.markdown("""
            **Audio Modification**
            - Most important factor!
            - Checks for commentary
            - Multiple audio layers = higher
            """)
        
        with col3:
            st.markdown("""
            **Visual Complexity**
            - Checks for text overlays
            - Detects visual effects
            - More edits = higher score
            """)
        
        st.markdown("---")
        st.info("💡 **Pro Tip:** Videos scoring 70+ with good audio modification are typically safe to monetize!")
        

elif page == "🤖 AI Viral Moments":
    st.header("🤖 AI Viral Moment Detector")
    st.markdown("Automatically finds the most exciting moments — works even without captions!")

    if 'analyze_url' in st.session_state:
        video_url = st.text_input("📎 YouTube Video URL:", value=st.session_state.analyze_url)
    else:
        video_url = st.text_input("📎 YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

    if video_url:
        video_info = youtube_api.get_video_info(video_url)
        if video_info:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(video_info['thumbnail'])
            with col2:
                st.subheader(video_info['title'])
                st.write(f"**Channel:** {video_info['channel']}")
            st.markdown("---")

        if st.button("🔍 Analyze for Viral Moments", type="primary"):
            with st.spinner("Trying transcript first..."):
                transcript = youtube_api.get_video_transcript(video_url)

            if transcript:
                st.success("✅ Transcript found! Analyzing language patterns...")
                detector = ViralMomentDetector()
                moments = detector.analyze_transcript(transcript)
                top_moments = detector.get_top_moments(moments, n=5)

                st.subheader("🗣️ Linguistic Analysis Results")
                st.markdown(detector.generate_report(moments))

            else:
                st.warning("No transcript available — switching to audio energy detection!")
                with st.spinner("Downloading audio and analyzing energy peaks... (this may take 1-2 minutes)"):
                    audio_result = download_audio_temp(video_url)
                    
                    if audio_result['success']:
                        audio_path = audio_result['path']
                        energy_moments = detect_energy_peaks(audio_path)
                        
                        # Cleanup
                        try:
                            os.remove(audio_path)
                        except:
                            pass
                        
                        if energy_moments:
                            st.success("✅ Audio analysis complete!")
                            st.markdown(energy_generate_report(energy_moments))
                            top_moments = energy_moments[:5]
                        else:
                            st.info("No high-energy moments detected in audio.")
                            top_moments = []
                    else:
                        st.error(f"Audio download failed: {audio_result.get('error')}")
                        top_moments = []

            # Show top moments for clipping (works for both methods)
            if 'top_moments' in locals() and top_moments:
                st.subheader("🏆 Top Moments (Click to Create Clip)")
                for i, moment in enumerate(top_moments):
                    score = moment.get('viral_score', moment.get('energy_score', 0))
                    reason = ', '.join(moment.get('reasons', [moment.get('reason', '')]))

                    with st.expander(f"#{i+1} • {format_timestamp(moment['start_time'])} - {format_timestamp(moment['end_time'])} • Score: {score}"):
                        st.write(f"**Duration:** {moment['duration']}s")
                        st.write(f"**Why viral:** {reason}")
                        if 'text' in moment:
                            st.write(f"**Text:** {moment['text']}")

                        if st.button("✂️ Use This Moment for Clip", key=f"energy_clip_{i}"):
                            st.session_state.clip_start = moment['start_time']
                            st.session_state.clip_end = moment['end_time']
                            st.session_state.video_url_for_clip = video_url
                            st.success("✅ Times set! Go to 'Clip Generator' → create your short!")
                            st.balloons()

    if 'analyze_url' in st.session_state and st.button("🗑️ Clear Video"):
        del st.session_state.analyze_url
        st.rerun()

# ====== CREATOR INSPIRATION PAGE ======
elif page == "👥 Creator Inspiration":
    st.header("👥 Trending Creators")
    st.info("Coming soon! This will show top performing creators and viral content patterns.")

# ====== MONETIZATION DASHBOARD ======
elif page == "💰 Monetization Dashboard":
    st.header("💰 Track Your Earnings")
    st.info("Coming soon! This will track your clip performance and estimated earnings across platforms.")