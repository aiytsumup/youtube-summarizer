import streamlit as st
import requests
import os
import time
from google import genai

st.title("🎬 AI YouTube Summarizer (Ultra-Stable Pipeline)")
st.write("Paste a YouTube link below. The app will bypass cloud data-center restrictions to securely analyze the video track.")

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
        audio_filepath = "downloaded_track.mp3"
        
        try:
            with status_container.container():
                st.info("📥 Establishing bypass tunnel and extracting audio stream...")
            
            # Clean up URL format to ensure API compatibility
            clean_url = url.split("?")[0].split("&")[0]
            
            # Use a specialized public media gateway to fetch the audio download link
            api_endpoint = f"https://api.cobalt.tools/api/json"
            payload = {
                "url": clean_url,
                "isAudioOnly": True,
                "audioFormat": "mp3",
                "vCodec": "h264",
                "aCodec": "mp3",
                "isNoAudio": False
            }
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            api_response = requests.post(api_endpoint, json=payload, headers=headers)
            
            if api_response.status_code != 200:
                raise Exception("The media streaming gateway is temporarily busy. Please try again in a few seconds.")
                
            download_url = api_response.json().get("url")
            if not download_url:
                raise Exception("Could not resolve a stable audio stream for this video link.")
                
            # Stream download the audio file directly into the local environment
            audio_data = requests.get(download_url, stream=True)
            with open(audio_filepath, "wb") as f:
                for chunk in audio_data.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if not os.path.exists(audio_filepath) or os.path.getsize(audio_filepath) == 0:
                raise Exception("Audio stream verification failed. Zero bytes recovered.")

            # Step 2: Upload to Gemini File API
            with status_container.container():
                st.info("🚀 Forwarding audio payload to Gemini processing infrastructure...")
            
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
            
            status_container.empty()
            st.success("✨ Summary Generated Successfully!")
            st.write(response.text)
            
            # Step 5: Clean up file from Google's servers
            client.files.delete(name=audio_file.name)
            
        except Exception as e:
            status_container.empty()
            error_msg = str(e)
            
            if "503" in error_msg or "high demand" in error_msg:
                error_container.warning("⏳ The AI engine is experiencing heavy demand right now. Please wait a few moments and click again!")
            else:
                error_container.error(f"🩹 Processing notice: {error_msg}")
                
        finally:
            if os.path.exists(audio_filepath):
                os.remove(audio_filepath)
