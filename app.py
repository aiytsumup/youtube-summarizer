import streamlit as st
import yt_dlp
from google import genai

st.title("🎬 AI YouTube Summarizer")
st.write("Paste a YouTube link below to get an instant AI summary of the video transcript.")

# Language selection dropdown
language = st.selectbox(
    "Select the summary language:",
    ["English", "Hindi", "Tamil", "Telugu", "Spanish", "French", "German"]
)

# Text input for the user's YouTube link
url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Summarize Video"):
    if url:
        with st.spinner("Extracting transcript data and generating summary..."):
            try:
                # 1. Configure yt-dlp options to safely extract subtitles/transcripts
                ydl_opts = {
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True,
                }
                
                # 2. Extract information using the yt-dlp context manager
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    
                    # Try to look for manually written subtitles first, then automatic captions
                    subtitles = info_dict.get('subtitles') or info_dict.get('automatic_captions')
                
                # Default fallback language keys to check
                lang_keys = ['en', 'en-US', 'en-GB']
                chosen_subtitles = None
                
                if subtitles:
                    # Look for an available English transcript track first
                    for key in lang_keys:
                        if key in subtitles:
                            chosen_subtitles = subtitles[key]
                            break
                    # If specific keys aren't found, grab the first track available
                    if not chosen_subtitles:
                        chosen_subtitles = next(iter(subtitles.values()))
                
                if not chosen_subtitles:
                    raise Exception("No transcript or auto-generated captions could be found for this video.")
                
                # 3. Locate the JSON or plain text formats and pull out text entries
                # Look for modern JSON/srv3 formats that don't need heavy web parsing
                json_formats = [s for s in chosen_subtitles if s.get('ext') in ['json3', 'srv3']]
                
                if json_formats:
                    import requests
                    sub_url = json_formats[0]['url']
                    sub_data = requests.get(sub_url).json()
                    # Loop through track layers to extract clean sentence fragments
                    transcript_fragments = []
                    if 'events' in sub_data:
                        for event in sub_data['events']:
                            if 'segs' in event:
                                for seg in event['segs']:
                                    if seg['utf8'].strip():
                                        transcript_fragments.append(seg['utf8'].strip())
                    transcript_text = " ".join(transcript_fragments)
                else:
                    raise Exception("Could not find a readable transcript format.")
                
                if not transcript_text.strip():
                    raise Exception("The extracted transcript is empty.")

                # 4. Initialize the Gemini client and generate content
                client = genai.Client()
                
                prompt = f"""You are a YouTube video summarizer. You will be taking the transcript text
                and summarizing the entire video and providing the important points in bullets.
                Please provide the summary exactly in the {language} language."""
               response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=[prompt, transcript_text]
                )
                
                st.success("Summary Generated!")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
