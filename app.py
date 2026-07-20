import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

st.title("🎬 AI YouTube Summarizer")
st.write("Paste a YouTube link below to get an instant AI summary of the video transcript.")

# 👇 1. Added the language selection dropdown right here!
language = st.selectbox(
    "Select the summary language:",
    ["English", "Hindi", "Tamil", "Telugu", "Spanish", "French", "German"]
)

# Text input for the user's YouTube link
url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Summarize Video"):
    if url:
        with st.spinner("Fetching transcript and generating summary..."):
            try:
                # 1. Parse the video ID out of the URL string cleanly
                if "v=" in url:
                    video_id = url.split("v=")[-1].split("&")[0]
                else:
                    # For short links like youtu.be/xyz?si=abc
                    video_id = url.split("/")[-1].split("?")[0]
                
                # 2. Grab the text transcript using the updated API syntax
                api_instance = YouTubeTranscriptApi()
                transcript_list = api_instance.get_transcript(video_id)
                
                # Join the text fragments into a single paragraph
                transcript_text = " ".join([item['text'] for item in transcript_list])
                
                # 3. Initialize the Gemini client and generate content using the language choice
                client = genai.Client()
                
                # 👇 2. Dynamic prompt that forces Gemini to use the language selected above
                prompt = f"""You are a YouTube video summarizer. You will be taking the transcript text
                and summarizing the entire video and providing the important points in bullets.
                Please provide the summary exactly in the {language} language."""
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, transcript_text]
                )
                
                st.success("Summary Generated!")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
