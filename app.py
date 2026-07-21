import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

st.title("🎬 AI YouTube Summarizer")
st.write("Paste a YouTube link below to summarize its content automatically.")

# Language selection
language = st.selectbox(
    "Select the summary language:",
    ["English", "Hindi", "Tamil", "Telugu", "Spanish", "French", "German"]
)

url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

# Store transcript text in session state across UI clicks
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = ""

def extract_video_id(youtube_url):
    """Extracts video ID from standard or short YouTube URLs."""
    if "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in youtube_url:
        return youtube_url.split("watch?v=")[1].split("&")[0]
    return None

if st.button("Fetch & Summarize Video"):
    if not url:
        st.error("Please paste a valid YouTube link first.")
    else:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL. Please double-check the link.")
        else:
            with st.spinner("Attempting to retrieve transcript..."):
                try:
                    # 1. Try automated fetching
                    ytt_api = YouTubeTranscriptApi()
                    transcript_list = ytt_api.fetch(video_id, languages=['en', 'hi', 'ta', 'te', 'es', 'fr', 'de'])
                    st.session_state.transcript_text = " ".join([chunk.text for chunk in transcript_list])
                    st.success("Transcript retrieved automatically!")
                except Exception:
                    st.session_state.transcript_text = ""
                    st.warning("⚠️ YouTube blocked automated transcript retrieval from Streamlit's cloud server IP.")

# Fallback UI element if automated fetch is blocked or fails
if st.session_state.get("transcript_text") == "":
    st.info("💡 **Fallback Mode:** Open the video on YouTube, click `...` -> `Show transcript`, copy it, and paste it below:")
    manual_transcript = st.text_area("Paste Transcript / Video Notes Here:", height=200)
    if manual_transcript.strip():
        st.session_state.transcript_text = manual_transcript

# Trigger Gemini Summary once text is available
if st.session_state.transcript_text:
    if st.button("Generate AI Summary"):
        with st.spinner("Gemini is analyzing the text..."):
            try:
                client = genai.Client()
                
                prompt = f"""You are an advanced YouTube video summarizer.
                Take the following transcript or text content, summarize the main discussion, and list key bullet points.
                Provide the entire response explicitly in the {language} language."""

                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=[prompt, st.session_state.transcript_text]
                )

                st.success("✨ Summary Generated Successfully!")
                st.write(response.text)

            except Exception as e:
                st.error(f"Error calling Gemini API: {str(e)}")
