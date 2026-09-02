# SpeedRun Exam Simulator ⏱️

A Streamlit Web App focused on adrenaline-based studying. Upload your class audio, generate tough flashcards via AI, and try to answer them before the timer runs out! If you fail or run out of time, the question goes back into the queue. You must get 10/10!

## Prerequisites

1. **Python 3.8+**
2. **FFmpeg** installed on your system (Required by `openai-whisper` for audio processing).
   - **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or install via winget `winget install ffmpeg`.
   - **Mac**: `brew install ffmpeg`
   - **Linux**: `sudo apt update && sudo apt install ffmpeg`

## Setup

1. Open your terminal and navigate to the project directory:
   ```bash
   cd "SPEEDRUN_EXAM_SIMULATOR"
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On macOS/Linux
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set your Google Gemini API Key:
   - Create a `.env` file in the project directory.
   - Add your key like this:
     ```env
     GEMINI_API_KEY="your_api_key_here"
     ```
   - Alternatively, set it as an environment variable in your terminal before running.

## Running the App

```bash
streamlit run app.py
```

## How to Play

1. **Upload**: Drop an MP3 or WAV file of your class/lecture into the sidebar.
2. **Wait**: Whisper transcribes the audio, and Gemini generates 10 hard flashcards based on the transcription.
3. **SpeedRun!**: A question appears with a visual 15-second countdown timer.
4. **Answer Fast**: If you're wrong or take too long, the question is thrown back to the end of the queue.
5. **Win**: You must answer all 10 questions correctly to finish the SpeedRun!
