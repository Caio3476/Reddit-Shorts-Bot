# 📹 Reddit Shorts Bot

This Python bot generates YouTube Shorts from top Reddit posts. It fetches stories from a specified subreddit, uses text-to-speech to narrate them, overlays subtitles on a vertical video, and uploads the final result to YouTube automatically.

---

## 🚀 Features

- 🔥 Fetches top Reddit posts (filtered for quality & safety)
- 🎙️ Converts story text to voice using `pyttsx3`
- 🎞️ Creates vertical videos with subtitles and rotating backgrounds
- ⏱️ Automatically splits long stories into 60-second parts
- 📤 Uploads videos to YouTube Shorts using the YouTube API
- 🧠 Tracks processed posts to avoid duplicates
- 📅 Runs every 5 minutes by default

---

## 🗂️ Folder Structure

```
project/
├── assets/               # Background video files
├── output/               # Temporary voice/video files
├── debug_logs/           # Logs for each processed post
├── processed_posts.txt   # Tracks used Reddit post IDs
├── video_index.txt       # Background video rotation index
├── client_secrets.json   # OAuth client credentials for YouTube API
├── youtube_token.pickle  # Saved access token
├── main.py               # Main script
└── README.md
```

---

## 🧰 Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Your `requirements.txt` should contain:

```
praw
pyttsx3
gTTS
moviepy
pydub
google-api-python-client
google-auth
google-auth-oauthlib
schedule
mutagen
numpy
```

Additional Requirements:

- **FFmpeg** (used by `moviepy`)
- **ImageMagick** (required for `TextClip`)
  - Update the path in `main.py`:

```python
from moviepy.config import change_settings

change_settings({
    "IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"
})
```

---

## 🔧 Setup

### 1. Reddit API

- Go to: https://www.reddit.com/prefs/apps
- Create a new script-type application
- Fill in the following in `main.py`:

```python
REDDIT_CLIENT_ID = "your_client_id"
REDDIT_CLIENT_SECRET = "your_client_secret"
REDDIT_USER_AGENT = "your_user_agent"
SUBREDDIT_NAME = "your_target_subreddit"
```

### 2. YouTube API

- Go to: https://console.cloud.google.com/
- Create a new project
- Enable **YouTube Data API v3**
- Create OAuth 2.0 Client ID credentials
- Download `client_secrets.json` and place it in your project folder

---

## ▶️ Running the Bot

Run manually:

```bash
python main.py
```

The script is already set up to automatically run every 5 minutes using `schedule`.

---

## 📝 Notes

- Only fetches non-stickied, non-NSFW posts with text longer than 300 characters
- Splits stories into multiple parts if necessary (max 5 parts)
- Each video stays under 60 seconds for Shorts compatibility
- Titles and hashtags are auto-formatted for YouTube Shorts

---

## 📌 Example Output

- **Title**: `AITA for refusing to go to my sister's wedding? (Part 1/2)`
- **Description**:
  ```
  Part 1 of 2
  
  [Story content here...]
  
  #shorts #reddit #aitah
  ```
- **YouTube Link**: Uploaded automatically and printed to console

---

## 🛠️ Troubleshooting

- 🧪 Check `debug_logs/` to review processed stories
- 🧼 Delete `youtube_token.pickle` if you need to re-authenticate YouTube
- 🔁 Make sure background videos exist in `assets/` and match file names in the `BACKGROUND_FILES` list in `main.py`
- ⚙️ Confirm `FFmpeg` and `ImageMagick` are installed and accessible

---

## 📜 License

This project is for educational and personal use only. Not affiliated with Reddit or YouTube. Use responsibly and abide by platform terms of service.
