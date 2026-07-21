import streamlit as st
import yt_dlp
import os
import time
from google import genai

st.title("🎬 AI YouTube Summarizer")
st.write("Paste a YouTube link below to get an instant AI summary of the video audio.")

# Language selection dropdown
language = st.selectbox(
    "Select the summary language:",
    ["English", "Hindi", "Tamil", "Telugu", "Spanish", "French", "German"]
)

# Text input for the user's YouTube link
url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Summarize Video"):
    if url:
        status_container = st.empty()
        error_container = st.empty()
        
        audio_filename = "youtube_audio_track"
        audio_filepath = f"{audio_filename}.mp3"
        
        try:
            # Step 1: Download audio stream using yt-dlp
            with status_container.container():
                st.info("📥 Downloading audio track from YouTube...")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_filename,
                'cookiefile': 'cookies.txt',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if not os.path.exists(audio_filepath):
                raise Exception("Audio file creation failed.")

            # Step 2: Upload audio file to Gemini File API
            with status_container.container():
                st.info("🚀 Uploading audio payload to Gemini...")
            
            client = genai.Client()
            audio_file = client.files.upload(file=audio_filepath)
            
            # Step 3: Wait for processing on Gemini cloud
            with status_container.container():
                st.info("⚙️ Processing audio track with Gemini...")
            
            while audio_file.state.name == "PROCESSING":
                time.sleep(2)
                audio_file = client.files.get(name=audio_file.name)
                
            if audio_file.state.name == "FAILED":
                raise Exception("Google media API failed to process the track.")

            # Step 4: Generate summary
            with status_container.container():
                st.info("🧠 Generating your summary...")
            
            prompt = f"""You are an advanced media intelligence assistant. 
            Analyze the provided audio recording carefully. Break down the core discussion topics,
            contextual narrative, and deliver structural bullet points detailing the key events or data.
            You must reply entirely and explicitly in the {language} language."""
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, audio_file]
            )
            
            status_container.empty()
            st.success("✨ Summary Generated Successfully!")
            st.write(response.text)
            
            # Step 5: Clean up file on Google servers
            client.files.delete(name=audio_file.name)
            
        except Exception as e:
            status_container.empty()
            error_msg = str(e)
            
            if "503" in error_msg or "high demand" in error_msg:
                error_container.warning("⏳ The AI engine is experiencing heavy demand right now. Please try again in a few moments!")
            else:
                error_container.error(f"An error occurred: {error_msg}")
                
        finally:
            # Clean up local audio file
            if os.path.exists(audio_filepath):
                os.remove(audio_filepath)
