import streamlit as st
import whisper
import google.generativeai as genai
import tempfile
import os
import time
import json
import difflib

# Try to load dotenv for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

st.set_page_config(page_title="SpeedRun Exam Simulator", page_icon="⏱️", layout="centered")

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

@st.cache_resource
def load_whisper_model():
    # 'base' model is faster and good enough for basic transcription. 
    # Use 'small' or 'medium' for better accuracy if system resources allow.
    return whisper.load_model("base")

def transcribe_audio(audio_file_path):
    model = load_whisper_model()
    result = model.transcribe(audio_file_path)
    return result["text"]

def generate_flashcards(text):
    if not api_key:
        st.error("GEMINI_API_KEY is not set. Please set it as an environment variable or in a .env file.")
        return []
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    You are an expert tutor creating a SpeedRun Exam. 
    Based on the following transcription of a class, generate exactly 10 difficult flashcard questions and their short, concise answers.
    Output the result as a valid JSON array of objects, where each object has a 'question' and an 'answer' key.
    CRITICAL: Output ONLY the JSON array. Do not output markdown blocks or conversational text.
    
    Transcription:
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        # Use regex to extract only the JSON array part
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            json_str = match.group(0)
            flashcards = json.loads(json_str)
            return flashcards
        else:
            st.error("Gemini no devolvió un formato JSON válido.")
            return []
    except Exception as e:
        st.error(f"Failed to parse Gemini response: {e}")
        return []

def initialize_session_state():
    if "flashcards" not in st.session_state:
        st.session_state.flashcards = []
    if "queue" not in st.session_state:
        st.session_state.queue = []
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "current_q_index" not in st.session_state:
        st.session_state.current_q_index = None
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "game_over" not in st.session_state:
        st.session_state.game_over = False

def is_answer_correct(user_ans, correct_ans):
    user_ans = str(user_ans).lower().strip()
    correct_ans = str(correct_ans).lower().strip()
    if not user_ans:
        return False
    
    # Check string similarity
    seq = difflib.SequenceMatcher(None, user_ans, correct_ans)
    if seq.ratio() > 0.4:  # Fairly forgiving for speed runs
        return True
    
    # Check if a significant word is present
    correct_words = [w for w in correct_ans.split() if len(w) > 3]
    user_words = user_ans.split()
    
    for cw in correct_words:
        if cw in user_ans:
            return True
            
    if user_ans in correct_ans or correct_ans in user_ans:
        return True
        
    return False

initialize_session_state()

st.title("⏱️ SpeedRun Exam Simulator")

if not api_key:
    st.warning("⚠️ Please set your GEMINI_API_KEY in a .env file or environment variables to generate questions.")

# Sidebar for uploading audio
with st.sidebar:
    st.header("1. Upload Class Audio")
    audio_file = st.file_uploader("Upload MP3/WAV", type=["mp3", "wav"])
    if st.button("Generate SpeedRun"):
        if audio_file is not None:
            with st.spinner("Transcribing audio with Whisper (this might take a moment)..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_file.write(audio_file.read())
                    tmp_file_path = tmp_file.name
                
                try:
                    transcription = transcribe_audio(tmp_file_path)
                finally:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
            
            st.success("Transcription complete!")
            
            with st.spinner("Generating hard questions with Gemini..."):
                flashcards = generate_flashcards(transcription)
                if flashcards:
                    st.session_state.flashcards = flashcards
                    # Initialize queue with indices of all flashcards
                    st.session_state.queue = list(range(len(flashcards)))
                    st.session_state.score = 0
                    st.session_state.current_q_index = st.session_state.queue.pop(0)
                    st.session_state.start_time = time.time()
                    st.session_state.game_over = False
                    st.success("SpeedRun Ready!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.error("Please upload an audio file first.")

# Game Logic
if st.session_state.flashcards and not st.session_state.game_over:
    st.header("2. SpeedRun Mode!")
    st.progress(st.session_state.score / len(st.session_state.flashcards))
    st.write(f"**Score:** {st.session_state.score} / {len(st.session_state.flashcards)}")
    
    if st.session_state.current_q_index is not None:
        current_q = st.session_state.flashcards[st.session_state.current_q_index]
        st.subheader("Question:")
        st.info(current_q["question"])
        
        # TIME LIMIT logic
        time_limit = 15  # seconds
        
        # Visual countdown using HTML/JS
        components_html = f"""
        <div id="timer_container" style="padding: 10px; border-radius: 5px; background-color: #ffebee; border: 2px solid #ef5350; text-align: center; font-family: sans-serif;">
            <span style="font-size: 20px; font-weight: bold; color: #c62828;">Time Remaining: </span>
            <span id="timer" style="font-size: 24px; font-weight: bold; color: #b71c1c;">{time_limit}</span>
            <span style="font-size: 20px; font-weight: bold; color: #c62828;"> s</span>
        </div>
        <script>
            var timeLeft = {time_limit};
            var elem = document.getElementById('timer');
            var container = document.getElementById('timer_container');
            
            var timerId = setInterval(countdown, 1000);
            
            function countdown() {{
                if (timeLeft <= 0) {{
                    clearTimeout(timerId);
                    elem.innerHTML = "0";
                    container.innerHTML = "<span style='font-size: 24px; font-weight: bold; color: #b71c1c;'>TIME IS UP! SUBMIT NOW!</span>";
                }} else {{
                    timeLeft--;
                    elem.innerHTML = timeLeft;
                }}
            }}
        </script>
        """
        st.components.v1.html(components_html, height=80)
        
        with st.form("answer_form", clear_on_submit=True):
            user_answer = st.text_input("Your Answer:", key="answer_input")
            submitted = st.form_submit_button("Submit Fast!")
            
            if submitted:
                elapsed_time = time.time() - st.session_state.start_time
                
                correct_answer = current_q["answer"]
                is_correct = is_answer_correct(user_answer, correct_answer)
                
                if elapsed_time > time_limit:
                    st.error(f"🐌 Too slow! Took {elapsed_time:.1f}s (Limit is {time_limit}s).")
                    st.warning(f"The correct answer was: **{correct_answer}**")
                    # Put back in queue
                    st.session_state.queue.append(st.session_state.current_q_index)
                elif not is_correct:
                    st.error("❌ Wrong answer!")
                    st.warning(f"The correct answer was: **{correct_answer}**")
                    # Put back in queue
                    st.session_state.queue.append(st.session_state.current_q_index)
                else:
                    st.success(f"✅ Correct! Time taken: {elapsed_time:.1f}s")
                    st.session_state.score += 1
                
                # Next question logic
                if len(st.session_state.queue) > 0:
                    st.session_state.current_q_index = st.session_state.queue.pop(0)
                    st.session_state.start_time = time.time()
                else:
                    st.session_state.current_q_index = None
                    st.session_state.game_over = True
                
                time.sleep(2.5) # Give user a moment to see the feedback
                st.rerun()

elif st.session_state.game_over:
    st.balloons()
    st.success(f"🎉 YOU BEAT THE SPEEDRUN! {len(st.session_state.flashcards)}/{len(st.session_state.flashcards)} 🎉")
    if st.button("Play Again"):
        st.session_state.queue = list(range(len(st.session_state.flashcards)))
        st.session_state.score = 0
        st.session_state.current_q_index = st.session_state.queue.pop(0)
        st.session_state.start_time = time.time()
        st.session_state.game_over = False
        st.rerun()
