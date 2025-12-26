from googleapiclient.discovery import build
from datetime import datetime, timedelta
import re


class YouTubeAPI:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    # -----------------------------
    # SEARCH VIRAL VIDEOS
    # -----------------------------
    def search_viral_videos(self, category="", days_ago=7, min_views=1_000_000, max_results=20):
        try:
            date_threshold = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%SZ')
            search_query = category if category else "viral trending"

            search_response = self.youtube.search().list(
                q=search_query,
                part="id,snippet",
                type="video",
                order="viewCount",
                publishedAfter=date_threshold,
                maxResults=max_results,
                relevanceLanguage="en",
            ).execute()

            video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

            if not video_ids:
                return []

            videos_response = self.youtube.videos().list(
                part="statistics,snippet",
                id=",".join(video_ids),
            ).execute()

            videos = []
            for item in videos_response.get("items", []):
                stats = item["statistics"]
                views = int(stats.get("viewCount", 0))

                if views >= min_views:
                    videos.append({
                        "video_id": item["id"],
                        "title": item["snippet"]["title"],
                        "channel": item["snippet"]["channelTitle"],
                        "views": views,
                        "likes": int(stats.get("likeCount", 0)),
                        "comments": int(stats.get("commentCount", 0)),
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                        "url": f"https://www.youtube.com/watch?v={item['id']}",
                    })

            return sorted(videos, key=lambda x: x["views"], reverse=True)

        except Exception as e:
            print(f"Error searching videos: {e}")
            return []

    # -----------------------------
    # VIDEO INFO
    # -----------------------------
    def get_video_info(self, video_url):
        try:
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return None

            response = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=video_id,
            ).execute()

            if not response.get("items"):
                return None

            item = response["items"][0]
            stats = item["statistics"]

            duration = self._parse_duration(item["contentDetails"]["duration"])

            return {
                "video_id": video_id,
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                "duration": duration,
                "description": item["snippet"]["description"],
            }

        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    # -----------------------------
    # VIDEO TRANSCRIPT (FIXED)
    # -----------------------------
    def get_video_transcript(self, video_url):
        """
        Fetch transcript using youtube-transcript-api
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            video_id = self._extract_video_id(video_url)
            if not video_id:
                return None

            # Try English first
            try:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["en", "en-US"]
                )
            except Exception:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)

            # Convert to plain text
            return " ".join([t["text"] for t in transcript])

        except ImportError:
            print("Install with: pip install youtube-transcript-api")
            return None
        except Exception as e:
            print(f"Transcript error: {e}")
            return None

    # -----------------------------
    # HELPERS
    # -----------------------------
    def _extract_video_id(self, url):
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)",
            r"youtube\.com\/embed\/([^&\n?]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _parse_duration(self, duration_str):
        try:
            duration_str = duration_str.replace("PT", "")
            hours = minutes = seconds = 0

            if "H" in duration_str:
                hours, duration_str = duration_str.split("H")
                hours = int(hours)

            if "M" in duration_str:
                minutes, duration_str = duration_str.split("M")
                minutes = int(minutes)

            if "S" in duration_str:
                seconds = int(duration_str.replace("S", ""))

            return hours * 3600 + minutes * 60 + seconds
        except Exception:
            return 0
