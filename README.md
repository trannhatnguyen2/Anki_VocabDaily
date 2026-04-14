# Word Audio + Image Downloader

A small Streamlit app to create vocabulary study assets for Anki or other learning tools.

The app can:

- generate word audio as MP3
- generate sentence audio as MP3
- search related images using the Pexels API
- save the selected image as JPG

## Features

- simple Streamlit UI
- configurable audio download folder
- configurable image download folder
- word audio generated with `gTTS`
- sentence audio generated with `gTTS`
- image search powered by Pexels
- safe local secret file for API key storage

## File Naming

The app saves files using these naming rules:

- word audio: `{tag}_{lesson}_{word}.mp3`
- sentence audio: `{tag}_{lesson}_{word}_sentence.mp3`
- image: `{tag}_{lesson}_{word}.jpg`

Example:

```text
EH_1_assurance.mp3
EH_1_assurance_sentence.mp3
EH_1_assurance.jpg
```

## Requirements

- Python 3.10+ recommended
- internet connection
- Pexels API key for image search

Python packages used:

- `streamlit`
- `requests`
- `gtts`
- `Pillow`

## Install

Install dependencies:

```bash
pip install streamlit requests gtts Pillow
```

## Pexels API Key Setup

This repo does not store the real API key in source code.

Create a local file named:

```text
local_secrets.json
```

Example content:

```json
{
  "PEXELS_API_KEY": "your-real-pexels-api-key"
}
```

You can copy from:

```text
local_secrets.example.json
```

Important:

- `local_secrets.json` is ignored by Git
- do not commit your real API key to GitHub

## Run The App

From the repo folder, run:

```bash
streamlit run app.py
```

If `streamlit` is not recognized, use:

```bash
python -m streamlit run app.py
```

After running, open the local Streamlit URL in your browser, usually:

```text
http://localhost:8501
```

## How To Use

### 1. Fill In The Main Inputs

Enter:

- `Tag`
- `Lesson`
- `Word`
- `Sentence`

Example:

- Tag: `EH`
- Lesson: `1`
- Word: `assurance`
- Sentence: `The sales associate gave his assurance that the missing keyboard would be replaced the next day.`

### 2. Choose Output Folders

Set:

- `Audio download folder`
- `Image download folder`

Examples:

- `audio/`
- `image/`

The app will create these folders automatically if they do not exist.

### 3. Generate Word Audio

Click:

```text
Download Word Pronunciation
```

This creates:

```text
{tag}_{lesson}_{word}.mp3
```

### 4. Generate Sentence Audio

Click:

```text
Download Sentence Audio
```

This creates:

```text
{tag}_{lesson}_{word}_sentence.mp3
```

### 5. Search Images

Choose how many image results to show, then click:

```text
Search Images
```

The app will search Pexels and show image results below the form.

### 6. Save An Image

Click one of the save buttons under the image results.

This creates:

```text
{tag}_{lesson}_{word}.jpg
```

inside your selected image folder.

### 7. Reset The Form

Click:

```text
Reset
```

This clears the current inputs and image search results.

## Current Repo Structure

Main files:

- `app.py` - active app
- `README.md` - project introduction and usage
- `local_secrets.example.json` - example local secret file
- `.gitignore` - ignored local/generated files

Generated folders:

- `audio/`
- `image/`

## Notes

- Word audio uses `gTTS`, not a dictionary pronunciation API
- Image search depends on a valid Pexels API key
- Pexels results may be weaker for abstract or rare vocabulary words
- This app uses text input for output folders, not a native folder picker

## Troubleshooting

### `streamlit` command not found

Use:

```bash
python -m streamlit run app.py
```

### Image search says API key is required

Make sure `local_secrets.json` exists and contains:

```json
{
  "PEXELS_API_KEY": "your-real-pexels-api-key"
}
```

### No images found

Try:

- a more common word
- a shorter keyword
- checking whether your Pexels API key is valid

### Audio or image folder does not exist

The app should create it automatically. If it does not, check whether the folder path is valid and writable.

## Future Ideas

- split app into tabs for audio and images
- add fallback image upload if Pexels has weak results
- add overwrite warning before saving files
- add saved-file history in the UI
