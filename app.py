import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

st.title("🎬 AI YouTube Summarizer")
st.write("Paste a YouTube link below to get an instant AI summary of the video transcript.")

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
                transcript_list = api_instance.list(video_id)
                
                # Automatically pick the first available transcript (English, Hindi, etc.)
                srt_object = next(iter(transcript_list))
                srt = srt_object.fetch()
                
                # Bulletproof text parsing that handles both new and old library formats
                transcript_parts = []
                for item in srt:
                    if hasattr(item, 'text'):
                        transcript_parts.append(item.text)
                    elif isinstance(item, dict) and 'text' in item:
                        transcript_parts.append(item['text'])
                    else:
                        transcript_parts.append(str(item))
                        
                transcript = " ".join(transcript_parts)
                
                # 3. Initialize the Gemini client
                client = genai.Client()
                
             # 4. Prompt Gemini to clean up and condense the text
                response = client.models.generate_content(
                    model='gemini-3.1-flash-lite',  # <-- Swap to the stable lite server track!
                    contents=f"Please provide a clean, highly structured, bulleted summary of the following video transcript:\n\n{transcript}"
                )
                
                st.success("Done!")
                st.subheader("🤖 AI Summary")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.info("Tip: If it complains about API keys, make sure your GEMINI_API_KEY environment variable is set in the terminal.")
    else:
        st.warning("Please paste a valid YouTube URL first!")