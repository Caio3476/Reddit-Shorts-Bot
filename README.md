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

## 🔧 Setup

### 1. Replace the Placeholders

In `main.py`, you will see several lines like this:

```python
REDDIT_CLIENT_ID = "your_client_id"
REDDIT_CLIENT_SECRET = "your_client_secret"
REDDIT_USER_AGENT = "your_user_agent"
SUBREDDIT_NAME = "your_subreddit"
```

➡️ **You must replace** each placeholder string above with your actual values:

- Create a Reddit app at https://www.reddit.com/prefs/apps
- Copy your **Client ID**, **Client Secret**, and create a simple **User Agent** like `"RedditShortsBot/1.0"`
- Set `SUBREDDIT_NAME` to the subreddit you want to pull posts from (e.g., `"AmItheAsshole"`)

---

### 2. YouTube API Credentials

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a project and enable the **YouTube Data API v3**
- Go to **APIs & Services > Credentials**
- Create an **OAuth 2.0 Client ID** (desktop app)
- Download the `client_secrets.json` file
- Place it in the root of your project folder

> The first time you run the script, it will open a browser window to authenticate your Google account and upload videos on your behalf.

---

## 🧰 Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

**`requirements.txt` should contain:**

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

You also need:

- **FFmpeg**: used by `moviepy` to process video and audio
- **ImageMagick**: required by `TextClip` to render text
  - Be sure to update this path in `main.py`:
    ```python
    change_settings({
        "IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"
    })
    ```

---

## ▶️ Running the Bot

To run it once manually:

```bash
python main.py
```

To keep it running (scheduled every 5 minutes):

- The bot uses `schedule` to run every 5 minutes
- Keep the terminal open, or run it in the background (use `screen` or a background service if deploying)

---

## 📌 Example Output

- Title: `AITA for refusing to go to my sister's wedding? (Part 1/2)`
- Description:
  ```
  Part 1 of 2

  [Story excerpt...]

  #shorts #reddit #aitah
  ```
- Uploaded to YouTube via authenticated account

---

## 🛠️ Troubleshooting

- Make sure `client_secrets.json` exists
- Ensure `ImageMagick` and `FFmpeg` are installed and added to your PATH
- Delete `youtube_token.pickle` to re-authenticate
- Check the `debug_logs/` folder if the bot says “no suitable posts found” or skips a story

---

## ⚠️ Security Note

Do **not** share your personal credentials publicly. This includes:

- Reddit client ID and secret
- Google OAuth credentials
- Your `.pickle` token file
- YouTube access tokens

---

## 📜 License

This project is for educational and personal use only. Not affiliated with Reddit or YouTube. Use responsibly and abide by platform terms of service.
