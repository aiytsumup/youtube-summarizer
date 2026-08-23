import streamlit as st
import time
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from google.genai.errors import APIError

# Set page layout
st.set_page_config(page_title="AI YouTube Summarizer", page_icon="🎬")

st.title("🎬 AI YouTube Summarizer (VS Code Local Version)")
st.write("Run this locally in VS Code for fast, block-free transcript summaries.")

# 1. Language selection dropdown
language = st.selectbox(
    "Select the summary language:",
    ["English", "Hindi", "Tamil", "Telugu", "Spanish", "French", "German"]
)

# 2. URL Input box
url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

def extract_video_id(youtube_url):
    """Extracts video ID from standard or short YouTube URLs."""
    if "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in youtube_url:
        return youtube_url.split("watch?v=")[1].split("&")[0]
    return None

def generate_summary_with_retry(prompt, text):
    """Generates content using the Gemini client."""
    # 🔑 PASTE YOUR ACTUAL GEMINI API KEY INSIDE THE QUOTES BELOW
    client = genai.Client(api_key="AQ.Ab8RN6Iv_a3GWRlzoU7n8R3E9ft5xW60j7q9cRvUWBjxI9dJMA")
    
    models_to_try = ["gemini-3.5-flash", "gemini-2.0-flash"]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt, text]
            )
            return response.text
        except APIError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                time.sleep(3)
                continue
            else:
                raise e
                
    raise Exception("API quota exceeded. Please wait 1 minute before trying again.")

# 3. Summarize Button
if st.button("Summarize Video", type="primary"):
    if not url.strip():
        st.error("Please paste a valid YouTube link first.")
    else:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL format.")
        else:
            with st.spinner("Fetching transcript and generating summary..."):
                try:
                    # Fetch YouTube transcript
                    ytt_api = YouTubeTranscriptApi()
                    transcript_list = ytt_api.fetch(video_id, languages=['en', 'hi', 'ta', 'te', 'es', 'fr', 'de'])
                    transcript_text = " ".join([chunk.text for chunk in transcript_list])
                    
                    prompt = f"""You are an advanced YouTube video summarizer.
                    Summarize the main discussion points and key takeaways from this transcript.
                    Provide the entire response explicitly in {language}."""

                    summary = generate_summary_with_retry(prompt, transcript_text)

                    st.success("✨ Summary Generated Successfully!")
                    st.write(summary)

                except Exception as e:
                    st.error(f"Error: {str(e)}")
