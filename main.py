# REDDIT SHORTS BOT

import os
import mutagen
import logging
import pyttsx3
import time
import datetime
import schedule
import praw
from gtts import gTTS
import moviepy.editor as mp
from moviepy.audio.AudioClip import AudioClip, CompositeAudioClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
import random
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import re
import numpy as np
from moviepy.config import change_settings
from pydub import AudioSegment

# Get the absolute path to the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure ImageMagick path
change_settings({
    "IMAGEMAGICK_BINARY": "C:\\Path\\To\\ImageMagick\\magick.exe"
})

# =============== CONFIGURATION ===============
REDDIT_CLIENT_ID = "your_client_id"
REDDIT_CLIENT_SECRET = "your_client_secret"
REDDIT_USER_AGENT = "your_user_agent"
SUBREDDIT_NAME = "your_subreddit_name"

DEBUG_LOG_DIR = os.path.join(SCRIPT_DIR, "debug_logs")
PROCESSED_FILE = os.path.join(SCRIPT_DIR, "processed_posts.txt")
BACKGROUND_FILES = [
    "background1.mp4",
    "background2.mp4",
    "background3.mp4",
    "background4.mp4",
    "background5.mp4",
]
INDEX_FILE = os.path.join(SCRIPT_DIR, "video_index.txt")
VOICE_FILE = os.path.join(SCRIPT_DIR, "output", "voice.mp3")
OUTPUT_VIDEO = os.path.join(SCRIPT_DIR, "output", "output.mp4")
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "youtube_token.pickle")

MAX_STORY_LENGTH = 5000
MAX_TITLE_LENGTH = 70
MAX_VIDEO_DURATION = 58
MAX_TTS_SPEED = 1.5
TTS_CHARS_PER_SECOND = 15
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920
# =============================================

# Create necessary directories
os.makedirs(DEBUG_LOG_DIR, exist_ok=True)
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)


def load_processed_ids():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, 'r') as f:
        return set(line.strip() for line in f)

def save_processed_id(post_id):
    with open(PROCESSED_FILE, 'a') as f:
        f.write(post_id + '\n')

def get_top_post():
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    
    processed_ids = load_processed_ids()
    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    
    for post in subreddit.hot(limit=20):
        if (not post.stickied and 
            post.selftext and 
            post.id not in processed_ids and
            not post.over_18 and
            len(post.selftext) > 300):
            return post.id, post.title, post.selftext
    
    print("No suitable posts found in hot submissions")
    return None, None, None

def clean_text(text):
    """Remove markdown but preserve essential punctuation"""
    # Remove markdown links
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Replace problem characters with spaces
    text = re.sub(r'[\(\)]', ' ', text)
    # Keep essential punctuation
    text = re.sub(r'[^\w\s.,!?\'\"\-—:;]', '', text)
    # Replace multiple spaces with single space
    return re.sub(r'\s+', ' ', text).strip()

def split_text_for_tts(text):
    """Split text into parts that will generate TTS under MAX_VIDEO_DURATION"""
    if not text:
        return []
    
    max_chars_per_part = int(MAX_VIDEO_DURATION * TTS_CHARS_PER_SECOND)
    parts = []
    
    # Improved sentence splitting that handles parentheses
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+(?![^()]*\))', text)
    current_chunk = ""
    
    for sentence in sentences:
        if not sentence:
            continue
            
        # Check if adding this sentence would exceed limit
        if len(current_chunk) + len(sentence) + 1 <= max_chars_per_part:
            current_chunk = current_chunk + (" " if current_chunk else "") + sentence
        else:
            # Finalize current chunk if it has content
            if current_chunk:
                parts.append(current_chunk)
                current_chunk = ""
            
            # Handle extra long sentences
            if len(sentence) > max_chars_per_part:
                # Split long sentence into words
                words = sentence.split()
                for word in words:
                    if len(word) > max_chars_per_part:
                        # Break long word into chunks
                        start_idx = 0
                        while start_idx < len(word):
                            chunk = word[start_idx:start_idx + max_chars_per_part]
                            
                            # Check if we can add to current chunk
                            if len(current_chunk) + len(chunk) + 1 <= max_chars_per_part:
                                current_chunk = current_chunk + (" " if current_chunk else "") + chunk
                            else:
                                if current_chunk:
                                    parts.append(current_chunk)
                                current_chunk = chunk
                            start_idx += len(chunk)
                    else:
                        # Add normal-sized words
                        if len(current_chunk) + len(word) + 1 <= max_chars_per_part:
                            current_chunk = current_chunk + (" " if current_chunk else "") + word
                        else:
                            if current_chunk:
                                parts.append(current_chunk)
                            current_chunk = word
            else:
                # Sentence fits in a new chunk
                current_chunk = sentence
    
    # Add the last chunk if it exists
    if current_chunk:
        parts.append(current_chunk)
    
    return parts

def generate_tts(text_part, part_num):
    """Generate TTS with speed adjustment"""
    output_file = os.path.join(OUTPUT_DIR, f"voice_part_{part_num}.wav")
    print(f"Generating TTS audio for part {part_num} to {output_file}...")
    
    # Clean text
    clean_text = re.sub(r'[\(\)]', '', text_part)
    clean_text = re.sub(r'\b(\w+)\s+\1\b', r'\1', clean_text)
    
    try:
        # Initialize TTS engine
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
        engine.setProperty('rate', 200)
        
        # Save to file
        engine.save_to_file(clean_text, output_file)
        engine.runAndWait()
        
        # Verify file
        if not os.path.exists(output_file) or os.path.getsize(output_file) < 1024:
            raise Exception("TTS file not created properly")
        
        # Load audio to get duration
        sound = AudioSegment.from_wav(output_file)
        duration = len(sound) / 1000.0
        
        # Speed up if too long
        if duration > MAX_VIDEO_DURATION:
            print(f"Audio too long ({duration:.1f}s), speeding up...")
            speed_factor = min(MAX_TTS_SPEED, duration / MAX_VIDEO_DURATION)
            sped_sound = sound.speedup(playback_speed=speed_factor)
            sped_sound.export(output_file, format="wav")
            duration = len(sped_sound) / 1000.0
        
        return output_file, duration
        
    except Exception as e:
        print(f"TTS generation failed: {str(e)}")
        return None, min(len(text_part) / TTS_CHARS_PER_SECOND, MAX_VIDEO_DURATION)

    
def wrap_text(text, max_chars=60):
    """Wrap text into multiple lines while preserving parentheses"""
    lines = []
    current_line = ""
    
    # Split while keeping parentheses together
    tokens = re.split(r'(\s|\(|\))', text)
    tokens = [t for t in tokens if t]  # Remove empty tokens
    
    for token in tokens:
        if len(current_line) + len(token) <= max_chars:
            current_line += token
        else:
            lines.append(current_line.strip())
            current_line = token
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines

def create_padded_audio(audio_clip, total_duration):
    """Create audio padded with silence to match total duration"""
    silence = AudioClip(
        lambda t: np.zeros(audio_clip.nchannels),
        duration=total_duration,
        fps=audio_clip.fps
    )
    return CompositeAudioClip([
        silence.set_start(0),
        audio_clip.set_start(0)
    ]).set_duration(total_duration)

def get_next_bg_path():
    """Get the next background video path in rotation"""
    try:
        if not os.path.exists(INDEX_FILE):
            current_index = 0
        else:
            with open(INDEX_FILE, 'r') as f:
                current_index = int(f.read().strip())
        
        bg_file = BACKGROUND_FILES[current_index % len(BACKGROUND_FILES)]
        next_index = (current_index + 1) % len(BACKGROUND_FILES)
        
        with open(INDEX_FILE, 'w') as f:
            f.write(str(next_index))
        
        return bg_file
    except Exception as e:
        print(f"Background rotation error: {e}")
        return random.choice(BACKGROUND_FILES)

def create_video_part(title, story_part, bg_file, part_num, total_parts):
    """Create video with proper timing and title display"""
    output_file = os.path.join(OUTPUT_DIR, f"output_part_{part_num}.mp4")
    
    # Only add title to the FIRST part
    if part_num == 1:
        full_story = f"{title}. {story_part}"
    else:
        full_story = story_part
    
    # Add part information
    if total_parts > 1:
        full_story = f"Part {part_num} of {total_parts}. {full_story}"
    
    # Generate TTS audio
    audio_file, tts_duration = generate_tts(full_story, part_num)
    print(f"Audio duration: {tts_duration}s")
    
    # Calculate actual characters per second
    actual_chars_per_second = len(full_story) / tts_duration if tts_duration > 0 else TTS_CHARS_PER_SECOND
    
    # Load background
    bg_path = os.path.join(ASSETS_DIR, bg_file)
    if not os.path.exists(bg_path):
        print(f"ERROR: Background file not found: {bg_path}")
        return None, 0
    
    bg = VideoFileClip(bg_path).resize(height=SHORTS_HEIGHT)
    
    # Crop width
    bg_w = bg.w
    target_w = int(SHORTS_HEIGHT * 9/16)
    if bg_w > target_w:
        bg = bg.crop(x_center=bg_w/2, width=target_w)
    
    # Loop background if needed
    if bg.duration < tts_duration:
        bg = bg.loop(duration=tts_duration)
    else:
        bg = bg.subclip(0, tts_duration)
    
    # Prepare story text
    lines = wrap_text(full_story, max_chars=50)
    line_height = 40
    y_start = (SHORTS_HEIGHT - (len(lines) * line_height)) // 2
    
    # Create story text clips with ACTUAL timing
    story_clips = []
    cumulative_chars = 0
    
    for i, line in enumerate(lines):
        start_time = cumulative_chars / actual_chars_per_second
        duration_time = len(line) / actual_chars_per_second
        cumulative_chars += len(line)
        
        txt_clip = TextClip(
            line,
            fontsize=34,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=1.5,
            method='caption',
            size=(SHORTS_WIDTH * 0.9, None),
            align='center'
        ).set_position(('center', y_start + i * line_height))
        story_clips.append(txt_clip.set_start(start_time).set_duration(duration_time))
    
    # Load audio
    audio_clip = None
    if audio_file and os.path.exists(audio_file):
        try:
            audio_clip = AudioFileClip(audio_file)
        except Exception as e:
            print(f"Audio load failed: {str(e)}")
    
    if audio_clip is None:
        print("Using silent audio")
        audio_clip = AudioClip(lambda t: [0, 0], duration=tts_duration)
    
    # Create final video
    final = CompositeVideoClip(
        [bg] + story_clips, 
        size=(SHORTS_WIDTH, SHORTS_HEIGHT)
    ).set_audio(audio_clip).set_duration(tts_duration)
    
    # Write output
    final.write_videofile(
        output_file,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        threads=4,
        logger=None
    )
    
    # Clean up
    if audio_file and os.path.exists(audio_file):
        try:
            os.remove(audio_file)
        except:
            pass
    
    return output_file, tts_duration

def format_title(title, part_num, total_parts):
    """Robust title formatting for YouTube"""
    # Clean and truncate title
    clean_title = re.sub(r'[^\w\s]', '', title)[:MAX_TITLE_LENGTH].strip()
    
    # Add part info
    title_with_part = f"{clean_title} (Part {part_num}/{total_parts})"
    
    # Add hashtags if space allows
    hashtags = " #RedditStories #AITAH #Shorts"
    if len(title_with_part) + len(hashtags) <= 100:
        return title_with_part + hashtags
    
    return title_with_part


def authenticate_youtube():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                scopes=['https://www.googleapis.com/auth/youtube.upload']
            )
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('youtube', 'v3', credentials=creds)

def upload_video(youtube, video_file, title, description):
    """Robust video upload with title validation"""
    # Validate title
    if not title or len(title) < 5:
        title = "Reddit Story #Shorts"
    
    request_body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['reddit', 'shorts', 'AITAH'],
            'categoryId': '24'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    
    try:
        media = MediaFileUpload(video_file, mimetype='video/mp4', resumable=True)
        request = youtube.videos().insert(part='snippet,status', body=request_body, media_body=media)
        response = request.execute()
        print(f"Uploaded: https://youtu.be/{response['id']}")
        return response['id']
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        return None

def run_bot():
    print(f"\n[{datetime.datetime.now()}] Starting bot cycle...")
    
    try:
        # Step 1: Get Reddit post
        post_id, title, story = get_top_post()
        if not post_id:
            print("No suitable post found. Skipping cycle.")
            return
        
        print(f"Processing post: {title[:50]}...")
        
        # Save original story for debugging
        debug_file = os.path.join(DEBUG_LOG_DIR, f"{post_id}_{int(time.time())}.txt")
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n\n")
            f.write(f"Original Story:\n{story}\n\n")
        
        # MARK AS PROCESSED IMMEDIATELY
        save_processed_id(post_id)
        
        # Step 2: Split story into parts
        clean_story = clean_text(story)
        if len(clean_story) > MAX_STORY_LENGTH:
            print(f"Story too long ({len(clean_story)} characters). Skipping.")
            return
        with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"Cleaned Length: {len(clean_story)} chars\n")
        story_parts = split_text_for_tts(clean_story)
        total_parts = len(story_parts)
        
        with open(debug_file, 'a', encoding='utf-8') as f:
            f.write(f"Split into {total_parts} parts:\n")
            for i, part in enumerate(story_parts):
                f.write(f"\n=== Part {i+1} ===\n{part}\n")
        
        if total_parts == 0:
            print("No valid story parts found. Skipping.")
            return
        
        if total_parts > 5:
            print("Story too long (would require >5 parts). Skipping.")
            return
        
        print(f"Story split into {total_parts} parts")
        print(f"Debug log saved to: {debug_file}")
        
        
        # Step 3: Process each part
        bg_file = get_next_bg_path()
        youtube = authenticate_youtube()
        
        for part_num, story_part in enumerate(story_parts, 1):
            try:
                print(f"\nProcessing part {part_num} of {total_parts}...")
                
                # Add title and part info
                full_content = f"{title}. Part {part_num} of {total_parts}. {story_part}"
                
                # Generate TTS
                audio_file, tts_duration = generate_tts(full_content, part_num)
                
                if tts_duration > MAX_VIDEO_DURATION:
                    print(f"Part {part_num} too long ({tts_duration:.1f}s). Skipping.")
                    continue
                
                # Create video
                video_file, duration = create_video_part(
                    title, story_part, bg_file, part_num, total_parts
                )
                
                if video_file is None:
                    continue
                
                # Upload to YouTube
                youtube_title = format_title(title, part_num, total_parts)
                description = f"Part {part_num} of {total_parts}\n\n{story_part[:500]}\n\n#shorts #reddit #aitah"
                upload_video(youtube, video_file, youtube_title, description)
                
                print(f"Uploaded part {part_num} (duration: {duration:.1f}s)")
            
            except Exception as e:
                print(f"ERROR in part {part_num}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue  # Continue with next part
        for f in os.listdir(OUTPUT_DIR):
            if f.startswith("voice_part_") or f.startswith("output_part_"):
                os.remove(os.path.join(OUTPUT_DIR, f))
        print("Processing completed!")
        
    except Exception as e:
        print(f"Critical error in bot cycle: {str(e)}")
        import traceback
        traceback.print_exc()

# =============== MAIN SCHEDULER ===============
if __name__ == "__main__":
    print("Reddit Shorts Bot started")
    print(f"Running in directory: {SCRIPT_DIR}")
    print(f"Next run at: {datetime.datetime.now() + datetime.timedelta(minutes=30)}")
    
    # Initial test run
    run_bot()
    
    # Schedule every 30 minutes
    schedule.every(5).minutes.do(run_bot)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
