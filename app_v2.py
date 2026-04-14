from io import BytesIO
from pathlib import Path
import json
import re

from PIL import Image
import requests
from gtts import gTTS
import streamlit as st


PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
DEFAULT_IMAGE_LIMIT = 5
LOCAL_SECRETS_PATH = Path("local_secrets.json")
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def safe_filename(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r'[<>:"/\\|?*]+', "_", text)
    text = re.sub(r"\s+", "_", text)
    return text


def validate_lesson(lesson_text: str) -> int:
    lesson_text = str(lesson_text).strip()
    if not lesson_text:
        raise ValueError("Lesson must not be empty.")
    try:
        lesson = int(lesson_text)
    except ValueError as exc:
        raise ValueError("Lesson must be an integer.") from exc
    return lesson


def build_base_filename(tag: str, lesson: int, word: str) -> str:
    safe_tag = safe_filename(tag)
    safe_word = safe_filename(word)

    if not safe_tag:
        raise ValueError("Tag must be a non-empty string.")
    if not safe_word:
        raise ValueError("Word must be a non-empty string.")

    return f"{safe_tag}_{lesson}_{safe_word}"


def ensure_required_fields(tag: str, lesson_text: str, word: str) -> tuple[int, str]:
    if not str(tag).strip():
        raise ValueError("Please enter a tag.")
    if not str(word).strip():
        raise ValueError("Please enter a word.")
    lesson = validate_lesson(lesson_text)
    return lesson, str(word).strip()


def load_local_pexels_api_key() -> str:
    if not LOCAL_SECRETS_PATH.exists():
        return ""

    try:
        payload = json.loads(LOCAL_SECRETS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""

    return str(payload.get("PEXELS_API_KEY", "")).strip()


def build_tts_bytes(text: str, lang: str = "en") -> bytes:
    if not text or not str(text).strip():
        raise ValueError("Text must be a non-empty string.")

    audio_buffer = BytesIO()
    tts = gTTS(text=str(text).strip(), lang=lang)
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.getvalue()


def search_pexels_images(word: str, api_key: str, limit: int = DEFAULT_IMAGE_LIMIT) -> list[dict]:
    if not word or not str(word).strip():
        raise ValueError("Word must be a non-empty string.")
    if not api_key or not str(api_key).strip():
        raise ValueError("Pexels API key is required.")

    search_limit = max(1, min(limit, 15))
    response = requests.get(
        PEXELS_SEARCH_URL,
        params={
            "query": str(word).strip(),
            "per_page": search_limit,
            "page": 1,
        },
        headers={
            **DEFAULT_HEADERS,
            "Authorization": str(api_key).strip(),
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    images = []
    for item in payload.get("photos", []):
        src = item.get("src", {})
        original = src.get("large2x") or src.get("large") or src.get("original")
        thumbnail = src.get("medium") or src.get("small") or original
        if not original or not thumbnail:
            continue

        photographer = item.get("photographer", "Pexels")
        photo_page = item.get("url", "https://www.pexels.com")
        images.append(
            {
                "title": item.get("alt", "") or f"{word} photo",
                "source": f"{photographer} | {photo_page}",
                "original": original,
                "thumbnail": thumbnail,
            }
        )

        if len(images) >= search_limit:
            break

    if not images:
        raise ValueError(f"No image results found on Pexels for '{word}'.")

    return images


def build_jpg_bytes_from_url(image_url: str) -> bytes:
    response = requests.get(
        image_url,
        headers=DEFAULT_HEADERS,
        timeout=30,
        stream=True,
    )
    response.raise_for_status()

    image = Image.open(BytesIO(response.content))
    rgb_image = image.convert("RGB")

    output_buffer = BytesIO()
    rgb_image.save(output_buffer, format="JPEG", quality=92)
    output_buffer.seek(0)
    return output_buffer.getvalue()


def reset_fields():
    st.session_state.tag = ""
    st.session_state.lesson = ""
    st.session_state.word = ""
    st.session_state.sentence = ""
    st.session_state.image_search_limit = DEFAULT_IMAGE_LIMIT
    st.session_state.pexels_api_key = load_local_pexels_api_key()
    st.session_state.image_results = []
    st.session_state.last_image_query = ""
    st.session_state.word_audio_bytes = None
    st.session_state.word_audio_name = ""
    st.session_state.sentence_audio_bytes = None
    st.session_state.sentence_audio_name = ""


st.set_page_config(page_title="Audio + Image Downloader", page_icon="🔊", layout="wide")

session_defaults = {
    "tag": "",
    "lesson": "",
    "word": "",
    "sentence": "",
    "image_search_limit": DEFAULT_IMAGE_LIMIT,
    "pexels_api_key": load_local_pexels_api_key(),
    "image_results": [],
    "last_image_query": "",
    "word_audio_bytes": None,
    "word_audio_name": "",
    "sentence_audio_bytes": None,
    "sentence_audio_name": "",
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


st.title("🔊 Word Audio + Image Downloader")
st.caption(
    "This deployed version sends files to your browser. "
    "Downloads will go to your browser's normal download folder on Windows."
)

with st.container():
    form_col1, form_col2 = st.columns(2)

    with form_col1:
        st.text_input(
            "Tag",
            key="tag",
            placeholder="Enter tag, example: EH",
        )
        st.text_input(
            "Lesson",
            key="lesson",
            placeholder="Enter lesson number, example: 1",
        )
        st.text_input(
            "Word",
            key="word",
            placeholder="Enter a word, example: assurance",
        )

    with form_col2:
        st.slider(
            "Image results to show",
            min_value=1,
            max_value=15,
            key="image_search_limit",
        )
        st.info(
            "For Streamlit Cloud, files cannot be saved directly to D:\\ on your PC. "
            "Use the download buttons below.",
            icon="ℹ️",
        )

st.text_area(
    "Sentence",
    key="sentence",
    placeholder="Enter a sentence",
    height=150,
)

audio_col1, audio_col2, action_col = st.columns(3)

with audio_col1:
    if st.button("Generate Word Pronunciation", use_container_width=True):
        try:
            tag = st.session_state.tag.strip()
            lesson, word = ensure_required_fields(tag, st.session_state.lesson, st.session_state.word)

            file_name = f"{build_base_filename(tag, lesson, word)}.mp3"
            audio_bytes = build_tts_bytes(word, lang="en")

            st.session_state.word_audio_bytes = audio_bytes
            st.session_state.word_audio_name = file_name
            st.success(f"Generated: {file_name}")
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.word_audio_bytes:
        st.audio(st.session_state.word_audio_bytes, format="audio/mp3")
        st.download_button(
            label="Download word mp3",
            data=st.session_state.word_audio_bytes,
            file_name=st.session_state.word_audio_name,
            mime="audio/mpeg",
            use_container_width=True,
            key="download_word_audio",
        )

with audio_col2:
    if st.button("Generate Sentence Audio", use_container_width=True):
        try:
            tag = st.session_state.tag.strip()
            lesson, word = ensure_required_fields(tag, st.session_state.lesson, st.session_state.word)
            sentence = st.session_state.sentence.strip()
            if not sentence:
                raise ValueError("Please enter a sentence.")

            file_name = f"{build_base_filename(tag, lesson, word)}_sentence.mp3"
            audio_bytes = build_tts_bytes(sentence, lang="en")

            st.session_state.sentence_audio_bytes = audio_bytes
            st.session_state.sentence_audio_name = file_name
            st.success(f"Generated: {file_name}")
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.sentence_audio_bytes:
        st.audio(st.session_state.sentence_audio_bytes, format="audio/mp3")
        st.download_button(
            label="Download sentence mp3",
            data=st.session_state.sentence_audio_bytes,
            file_name=st.session_state.sentence_audio_name,
            mime="audio/mpeg",
            use_container_width=True,
            key="download_sentence_audio",
        )

with action_col:
    st.button(
        "Reset",
        use_container_width=True,
        on_click=reset_fields,
    )

search_col, info_col = st.columns([1, 2])

with search_col:
    search_images = st.button("Search Images", use_container_width=True, type="primary")

with info_col:
    st.info(
        "Image file name: {tag}_{lesson}_{word}.jpg | "
        "Photos provided by Pexels.",
        icon="🖼️",
    )

if search_images:
    try:
        tag = st.session_state.tag.strip()
        lesson, word = ensure_required_fields(tag, st.session_state.lesson, st.session_state.word)
        _ = lesson

        api_key = st.secrets.get("PEXELS_API_KEY", "") or st.session_state.pexels_api_key
        results = search_pexels_images(
            word=word,
            api_key=api_key,
            limit=st.session_state.image_search_limit,
        )

        st.session_state.image_results = results
        st.session_state.last_image_query = word
        st.success(f"Found {len(results)} image results for '{word}'.")
    except Exception as exc:
        st.session_state.image_results = []
        st.error(str(exc))

if st.session_state.image_results:
    st.subheader(f"Image Results for '{st.session_state.last_image_query}'")
    gallery_columns = st.columns(3)

    for index, image_item in enumerate(st.session_state.image_results):
        with gallery_columns[index % 3]:
            st.image(image_item["thumbnail"], use_container_width=True)
            if image_item["title"]:
                st.caption(image_item["title"])
            if image_item["source"]:
                st.caption(f"Source: {image_item['source']}")

            try:
                tag = st.session_state.tag.strip()
                lesson, word = ensure_required_fields(tag, st.session_state.lesson, st.session_state.word)
                base_name = build_base_filename(tag, lesson, word)
                image_bytes = build_jpg_bytes_from_url(image_item["original"])

                st.download_button(
                    label=f"Download image {index + 1}",
                    data=image_bytes,
                    file_name=f"{base_name}.jpg",
                    mime="image/jpeg",
                    use_container_width=True,
                    key=f"download_image_{index}",
                )
            except Exception as exc:
                st.error(str(exc))

st.caption(
    "Word file: {tag}_{lesson}_{word}.mp3 | "
    "Sentence file: {tag}_{lesson}_{word}_sentence.mp3 | "
    "Image file: {tag}_{lesson}_{word}.jpg"
)