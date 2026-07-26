import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

st.title("🎬 AI YouTube Summarizer")

url = st.text_input("Paste YouTube Video URL:")
language = st.selectbox("Select Language:", ["English", "Hindi", "Tamil", "Spanish", "French"])

def extract_video_id(youtube_url):
    if "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in youtube_url:
        return youtube_url.split("watch?v=")[1].split("&")[0]
    return None

if st.button("Summarize Video"):
    if not url:
        st.warning("Please enter a valid URL.")
    else:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL.")
        else:
            try:
                # Fetch text transcript directly (No yt-dlp media downloading required!)
                ytt_api = YouTubeTranscriptApi()
                transcript = ytt_api.fetch(video_id, languages=['en', 'hi', 'ta', 'es', 'fr'])
                transcript_text = " ".join([item.text for item in transcript])

                # Send text directly to Gemini
                client = genai.Client()
                prompt = f"Summarize this YouTube transcript in {language}:\n\n{transcript_text}"
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt]
                )

                st.success("✨ Summary Generated!")
                st.write(response.text)

            except Exception as e:
                st.error(f"Transcript Error: {str(e)}")
