import streamlit as st
import yt_dlp
import os
import time
from google import genai

st.title("🎬 AI YouTube Summarizer (Stable Audio Engine)")
st.write("Paste a YouTube link below. The app will securely process the video's audio track via Gemini for a 100% reliable summary.")

# Language selection dropdown
language = st.selectbox(
    "Select the summary language:",
    ["English", "Hindi", "Tamil", "Telugu", "Spanish", "French", "German"]
)

# Text input for the user's YouTube link
url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Summarize Video"):
    if url:
        # Create visual containers to keep UI clean
        status_container = st.empty()
        error_container = st.empty()
        
        # Audio file naming configuration
        audio_filename = "youtube_audio_track"
        audio_filepath = f"{audio_filename}.mp3"
        
        try:
            # Step 1: Download the audio track using yt-dlp
            with status_container.container():
                st.info("📥 Streaming audio track from YouTube video...")
            
            ydl_opts = {
                # Fallback to standard progressive formats to bypass data-center IP binding
                'format': 'worst/best',
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
                raise Exception("Audio extraction failed. The media file was not created successfully.")

            # Step 2: Upload the audio file to Google's Gemini File API
            with status_container.container():
                st.info("🚀 Uploading audio payload to Gemini processing infrastructure...")
            
            client = genai.Client()
            audio_file = client.files.upload(file=audio_filepath)
            
            # Step 3: Wait for processing to finalize on Google's cloud servers
            with status_container.container():
                st.info("⚙️ Waiting for Google's multi-modal processing engine to ready the track...")
            
            while audio_file.state.name == "PROCESSING":
                time.sleep(2)
                audio_file = client.files.get(name=audio_file.name)
                
            if audio_file.state.name == "FAILED":
                raise Exception("Google media API failed to securely compile the video track.")

            # Step 4: Generate the text content using the production flash model
            with status_container.container():
                st.info("🧠 Gemini is listening to the track and generating your summary...")
            
            prompt = f"""You are an advanced media intelligence assistant. 
            Analyze the provided audio recording carefully. Break down the core discussion topics,
            contextual narrative, and deliver structural bullet points detailing the key events or data.
            You must reply entirely and explicitly in the {language} language."""
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, audio_file]
            )
            
            # Clean up the UI status indicators and print the markdown text
            status_container.empty()
            st.success("✨ Summary Generated Successfully!")
            st.write(response.text)
            
            # Step 5: Clean up the file from Google's servers immediately
            client.files.delete(name=audio_file.name)
            
        except Exception as e:
            status_container.empty()
            error_msg = str(e)
            
            # Translate cryptic system bugs into elegant tips for your visitors
            if "503" in error_msg or "high demand" in error_msg:
                error_container.warning("⏳ The AI engine is experiencing heavy demand right now. Please wait a few moments and click again!")
            elif "404" in error_msg:
                error_container.error("🔍 We couldn't locate that specific link. Please double-check your formatting.")
            else:
                error_container.error(f"🩹 Something disrupted processing: {error_msg}")
                
        finally:
            # Crucial cleanup step to maintain server environment storage hygiene
            if os.path.exists(audio_filepath):
                os.remove(audio_filepath)
