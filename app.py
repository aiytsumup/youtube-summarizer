import streamlit as st
import yt_dlp
import os
import time
from google import genai

# App Layout
st.set_page_config(page_title="AI YouTube Summarizer", page_icon="🎬")

st.title("🎬 AI YouTube Summarizer")
st.write("Paste a YouTube link below to get an instant AI summary in your preferred language.")

# Language selection dropdown
language = st.selectbox(
    "Select the summary language:",
    ["English", "Hindi", "Tamil", "Telugu", "Spanish", "French", "German"]
)

# URL Input
url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Summarize Video", type="primary"):
    if not url:
        st.warning("Please enter a valid YouTube URL.")
    else:
        status_container = st.empty()
        error_container = st.empty()
        
        audio_filename = "temp_youtube_audio"
        audio_filepath = f"{audio_filename}.mp3"
        
        try:
            # Step 1: Extract Audio Stream
            with status_container.container():
                st.info("📥 Extracting audio track from YouTube...")
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'm4a/bestaudio/best',
                'outtmpl': audio_filepath,
                'quiet': True,
                'no_warnings': True,
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            }

            # Remove cookiefile key if file doesn't exist
            if 'cookiefile' in ydl_opts and not ydl_opts['cookiefile']:
                del ydl_opts['cookiefile']

            # Download audio stream
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if not os.path.exists(audio_filepath):
                raise Exception("Audio extraction failed. Please ensure the video is public.")

            # Step 2: Upload to Gemini API
            with status_container.container():
                st.info("🚀 Uploading media payload to Gemini AI...")
            
            client = genai.Client()
            audio_file = client.files.upload(file=audio_filepath)
            
            # Step 3: Wait for Processing
            with status_container.container():
                st.info("⚙️ Processing media track...")
            
            while audio_file.state.name == "PROCESSING":
                time.sleep(2)
                audio_file = client.files.get(name=audio_file.name)
                
            if audio_file.state.name == "FAILED":
                raise Exception("Gemini API failed to process the audio track.")

            # Step 4: Generate Summary in Selected Language
            with status_container.container():
                st.info("🧠 Generating key points and summary...")
            
            prompt = f"""You are an expert YouTube video summarizer.
            Analyze the provided audio recording carefully. Provide a clear, comprehensive summary 
            along with structural bullet points detailing the key events, concepts, or takeaways.
            You MUST reply entirely and explicitly in the {language} language."""
            
            # Using stable model identifier
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, audio_file]
            )
            
            status_container.empty()
            st.success("✨ Summary Generated Successfully!")
            st.write(response.text)
            
            # Step 5: Remote Cleanup
            client.files.delete(name=audio_file.name)
            
        except Exception as e:
            status_container.empty()
            error_msg = str(e)
            
            # User-friendly error shielding
            if "503" in error_msg or "high demand" in error_msg:
                error_container.warning("⏳ The AI engine is experiencing heavy demand right now. Please wait 10 seconds and click 'Summarize' again.")
            elif "403" in error_msg or "Forbidden" in error_msg:
                error_container.error("🔒 YouTube blocked this cloud request (HTTP 403). Try re-exporting a fresh `cookies.txt` or testing locally.")
            else:
                error_container.error(f"An error occurred: {error_msg}")
                
        finally:
            # Local Storage Hygiene Cleanup
            if os.path.exists(audio_filepath):
                os.remove(audio_filepath)
