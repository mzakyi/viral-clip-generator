import re
from collections import Counter
import math

class ViralMomentDetector:
    """
    Detects viral moments in video transcripts using linguistic analysis
    and pattern recognition to find high-energy, emotional segments.
    """
    
    def __init__(self):
        # High-energy words that indicate excitement, emphasis
        self.energy_words = {
            'insane', 'crazy', 'amazing', 'wow', 'incredible', 'unbelievable',
            'shocking', 'mind-blowing', 'epic', 'huge', 'massive', 'legendary',
            'perfect', 'brilliant', 'genius', 'absolutely', 'literally',
            'explosion', 'explode', 'destroyed', 'killed', 'crushed', 'dominated',
            'best', 'worst', 'never', 'always', 'everyone', 'nobody',
            'holy', 'omg', 'what', 'wtf', 'damn', 'hell', 'god'
        }
        
        # Hook phrases that grab attention
        self.hook_phrases = {
            'you won\'t believe', 'wait for it', 'watch this', 'check this out',
            'no way', 'are you kidding', 'i can\'t believe', 'this is crazy',
            'hold on', 'wait', 'stop', 'listen', 'look at this', 'pay attention',
            'secret', 'nobody tells you', 'they don\'t want', 'hidden', 'truth',
            'finally', 'at last', 'here it is', 'the moment', 'revealed'
        }
        
        # Question words that create curiosity
        self.question_words = {'what', 'why', 'how', 'when', 'where', 'who', 'which'}
        
        # Emotional intensity words
        self.emotion_words = {
            'love', 'hate', 'angry', 'happy', 'sad', 'scared', 'excited',
            'frustrated', 'amazing', 'terrible', 'awesome', 'horrible',
            'beautiful', 'ugly', 'perfect', 'disaster', 'nightmare', 'dream'
        }
        
        # Conflict/drama indicators
        self.conflict_words = {
            'fight', 'argue', 'debate', 'versus', 'against', 'battle',
            'war', 'conflict', 'problem', 'issue', 'challenge', 'struggle',
            'failed', 'mistake', 'wrong', 'disaster', 'catastrophe'
        }
        
        # Call-to-action phrases
        self.cta_phrases = {
            'subscribe', 'like', 'comment', 'share', 'follow', 'click',
            'check out', 'link in', 'let me know', 'tell me', 'what do you think'
        }
    
    def analyze_transcript(self, transcript_data, video_duration=None):
        """
        Analyze video transcript to find viral moments
        
        Args:
            transcript_data: List of transcript segments with 'text' and 'start' timestamps
            video_duration: Optional video duration in seconds
            
        Returns:
            List of viral moments with scores and reasons
        """
        if not transcript_data:
            return []
        
        moments = []
        
        # Analyze each segment
        for i, segment in enumerate(transcript_data):
            text = segment.get('text', '').lower()
            start_time = segment.get('start', 0)
            duration = segment.get('duration', 5)
            
            # Calculate various scores
            scores = self._calculate_segment_scores(text, transcript_data, i)
            
            # Overall viral score (weighted combination)
            viral_score = (
                scores['energy_score'] * 0.25 +
                scores['hook_score'] * 0.25 +
                scores['emotion_score'] * 0.15 +
                scores['question_score'] * 0.15 +
                scores['conflict_score'] * 0.10 +
                scores['caps_score'] * 0.05 +
                scores['punctuation_score'] * 0.05
            )
            
            # Only keep high-scoring moments
            if viral_score > 0.15:  # Threshold for "viral-worthy"
                moment = {
                    'start_time': start_time,
                    'end_time': start_time + duration,
                    'text': segment.get('text', ''),
                    'viral_score': round(viral_score, 3),
                    'scores': scores,
                    'reasons': self._generate_reasons(scores)
                }
                moments.append(moment)
        
        # Sort by viral score
        moments.sort(key=lambda x: x['viral_score'], reverse=True)
        
        # Group nearby moments to avoid overlaps
        moments = self._merge_nearby_moments(moments)
        
        return moments
    
    def _calculate_segment_scores(self, text, all_segments, current_index):
        """Calculate various engagement scores for a text segment"""
        words = text.split()
        word_count = len(words)
        
        if word_count == 0:
            return {
                'energy_score': 0,
                'hook_score': 0,
                'emotion_score': 0,
                'question_score': 0,
                'conflict_score': 0,
                'caps_score': 0,
                'punctuation_score': 0
            }
        
        # Energy score - high-energy vocabulary (check each word)
        energy_count = sum(1 for word in words if word.strip('.,!?').lower() in self.energy_words)
        energy_score = min(energy_count / max(word_count, 1) * 3, 1.0)  # Increased multiplier
        
        # Hook score - attention-grabbing phrases
        hook_score = 0
        for phrase in self.hook_phrases:
            if phrase in text.lower():
                hook_score += 0.4  # Increased from 0.3
        hook_score = min(hook_score, 1.0)
        
        # Emotion score (check each word)
        emotion_count = sum(1 for word in words if word.strip('.,!?').lower() in self.emotion_words)
        emotion_score = min(emotion_count / max(word_count, 1) * 3, 1.0)  # Increased multiplier
        
        # Question score - curiosity generation
        question_count = sum(1 for word in words if word.strip('.,!?').lower() in self.question_words)
        has_question_mark = '?' in text
        question_score = min((question_count / max(word_count, 1) * 3) + (0.4 if has_question_mark else 0), 1.0)
        
        # Conflict/drama score (check each word)
        conflict_count = sum(1 for word in words if word.strip('.,!?').lower() in self.conflict_words)
        conflict_score = min(conflict_count / max(word_count, 1) * 3, 1.0)  # Increased multiplier
        
        # Capitalization score (indicates emphasis)
        original_text = all_segments[current_index].get('text', '')
        caps_count = sum(1 for c in original_text if c.isupper())
        caps_ratio = caps_count / max(len(original_text), 1)
        caps_score = min(caps_ratio * 5, 1.0)  # Increased multiplier
        
        # Punctuation score (! indicates excitement)
        exclamation_count = text.count('!')
        punctuation_score = min(exclamation_count * 0.3, 1.0)  # Increased from 0.2
        
        return {
            'energy_score': energy_score,
            'hook_score': hook_score,
            'emotion_score': emotion_score,
            'question_score': question_score,
            'conflict_score': conflict_score,
            'caps_score': caps_score,
            'punctuation_score': punctuation_score
        }
    
    def _generate_reasons(self, scores):
        """Generate human-readable reasons for why a moment is viral-worthy"""
        reasons = []
        
        if scores['energy_score'] > 0.5:
            reasons.append("🔥 High-energy language")
        
        if scores['hook_score'] > 0.3:
            reasons.append("🎣 Attention-grabbing hook")
        
        if scores['emotion_score'] > 0.5:
            reasons.append("💯 Strong emotional content")
        
        if scores['question_score'] > 0.5:
            reasons.append("❓ Creates curiosity")
        
        if scores['conflict_score'] > 0.5:
            reasons.append("⚔️ Drama/conflict")
        
        if scores['caps_score'] > 0.3:
            reasons.append("📢 Emphasis/excitement")
        
        if scores['punctuation_score'] > 0.3:
            reasons.append("‼️ Exclamation/intensity")
        
        return reasons if reasons else ["📊 High engagement potential"]
    
    def _merge_nearby_moments(self, moments, gap_threshold=10):
        """Merge moments that are close together to avoid fragmentation"""
        if len(moments) <= 1:
            return moments
        
        merged = []
        current = moments[0].copy()
        
        for next_moment in moments[1:]:
            # If moments are within threshold seconds, merge them
            if next_moment['start_time'] - current['end_time'] <= gap_threshold:
                # Extend current moment
                current['end_time'] = next_moment['end_time']
                current['text'] += ' ' + next_moment['text']
                current['viral_score'] = max(current['viral_score'], next_moment['viral_score'])
                # Merge reasons
                current['reasons'] = list(set(current['reasons'] + next_moment['reasons']))
            else:
                # Save current and start new
                merged.append(current)
                current = next_moment.copy()
        
        # Add the last moment
        merged.append(current)
        
        return merged
    
    def get_top_moments(self, moments, n=5, min_duration=10, max_duration=60):
        """
        Get top N viral moments, filtered by duration constraints
        
        Args:
            moments: List of detected moments
            n: Number of top moments to return
            min_duration: Minimum clip duration in seconds
            max_duration: Maximum clip duration in seconds
        """
        # Filter by duration
        filtered = []
        for moment in moments:
            duration = moment['end_time'] - moment['start_time']
            if min_duration <= duration <= max_duration:
                moment['duration'] = duration
                filtered.append(moment)
        
        # Return top N
        return filtered[:n]
    
    def format_timestamp(self, seconds):
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def generate_report(self, moments):
        """Generate a human-readable report of viral moments"""
        if not moments:
            return "No high-potential viral moments detected."
        
        report = f"🎬 Found {len(moments)} Viral-Worthy Moments:\n\n"
        
        for i, moment in enumerate(moments, 1):
            report += f"#{i} - {self.format_timestamp(moment['start_time'])} to {self.format_timestamp(moment['end_time'])}\n"
            report += f"   Score: {moment['viral_score']:.2f} | Duration: {moment['end_time'] - moment['start_time']:.0f}s\n"
            report += f"   Reasons: {', '.join(moment['reasons'])}\n"
            report += f"   Text: {moment['text'][:100]}...\n\n"
        
        return report