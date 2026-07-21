import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

st.title("🎬 AI YouTube Summarizer")
st.write("Paste a YouTube link below to get an instant AI summary of the transcript.")

# Language selection
language = st.selectbox(
    "Select the summary language:",
    ["English", "Hindi", "Tamil", "Telugu", "Spanish", "French", "German"]
)

url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

def extract_video_id(youtube_url):
    """Extracts video ID from standard or short YouTube URLs."""
    if "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in youtube_url:
        return youtube_url.split("watch?v=")[1].split("&")[0]
    return None

if st.button("Summarize Video"):
    if url:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL. Please check the link format.")
        else:
            with st.spinner("Fetching transcript and generating summary..."):
                try:
                    # 1. Fetch transcript text
                    ytt_api = YouTubeTranscriptApi()
                    transcript_list = ytt_api.fetch(video_id, languages=['en', 'hi', 'ta', 'te', 'es', 'fr', 'de'])
                    transcript_text = " ".join([chunk.text for chunk in transcript_list])

                    if not transcript_text.strip():
                        raise Exception("The transcript is empty or unavailable for this video.")

                    # 2. Call Gemini API
                    # On Streamlit Cloud, it automatically pulls GEMINI_API_KEY from Secrets
                    client = genai.Client()
                    
                    prompt = f"""You are an advanced YouTube video summarizer.
                    Take the following transcript text, summarize the main topic, and list key bullet points.
                    Provide the entire response explicitly in the {language} language."""

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[prompt, transcript_text]
                    )

                    st.success("✨ Summary Generated Successfully!")
                    st.write(response.text)

                except Exception as e:
                    st.error(f"Error: {str(e)}")
