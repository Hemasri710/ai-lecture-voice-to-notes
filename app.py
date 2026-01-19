import os
import streamlit as st
import speech_recognition as sr
import tempfile
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# ================= SECURE GEMINI CONFIG =================
# API key is read from ENV variable (NO hardcoding)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ================= SESSION STATE =================
if "history" not in st.session_state:
    st.session_state.history = []
if "selected" not in st.session_state:
    st.session_state.selected = None

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="AI Lecture Voice-to-Notes",
    page_icon="🎓",
    layout="centered"
)

# ================= HEADER =================
st.markdown(
    """
    <h1 style='text-align: center;'>🎓 AI Lecture Voice-to-Notes Generator</h1>
    <p style='text-align: center; font-size: 16px;'>
    Convert lecture audio into notes, quizzes, flashcards & PDF using AI
    </p>
    <hr>
    """,
    unsafe_allow_html=True
)

# ================= SIDEBAR =================
st.sidebar.title("📚 Project Dashboard")
st.sidebar.write(
    "AI-powered learning assistant using Speech-to-Text, NLP, and Generative AI."
)

st.sidebar.markdown("### 🕘 Lecture History")
if st.session_state.history:
    for i, _ in enumerate(st.session_state.history):
        if st.sidebar.button(f"Lecture {i+1}"):
            st.session_state.selected = i
else:
    st.sidebar.write("No history yet.")

# ================= INPUT =================
st.subheader("📥 Input Section")

language = st.selectbox(
    "🌐 Lecture Language",
    ["English", "Tamil", "Hindi"]
)
language_code = {"English": "en-IN", "Tamil": "ta-IN", "Hindi": "hi-IN"}[language]

level = st.selectbox(
    "🎯 Learning Level",
    ["Beginner", "Intermediate", "Exam-Oriented"]
)

audio_file = st.file_uploader("🎙️ Upload WAV Audio", type=["wav"])

# ================= FUNCTIONS =================
def convert_audio_to_text(audio_file, lang):
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_file.read())
        path = f.name
    with sr.AudioFile(path) as source:
        audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language=lang)

def gemini_generate(prompt):
    try:
        model = genai.GenerativeModel("models/text-bison-001")
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return None

# ---------- FALLBACK (SAFE MODE) ----------
def fallback_summary(text):
    return ". ".join(text.split(".")[:3]) + "."

def fallback_quiz():
    return (
        "1. What is the main topic discussed?\n"
        "2. Explain the key concept.\n"
        "3. Mention one application.\n"
        "4. Why is it important?\n"
        "5. How does it help students?"
    )

def fallback_flashcards(text):
    return f"Q: What is discussed?\nA: {text.split('.')[0]}"

def get_summary(text, level):
    prompt = f"Summarize this lecture for a {level} student:\n{text}"
    return gemini_generate(prompt) or fallback_summary(text)

def get_quiz(text):
    prompt = f"Generate 5 quiz questions from this lecture:\n{text}"
    return gemini_generate(prompt) or fallback_quiz()

def get_flashcards(text):
    prompt = f"Create flashcards from this lecture:\n{text}"
    return gemini_generate(prompt) or fallback_flashcards(text)

def generate_pdf(summary, quiz, flashcards):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    t = pdf.beginText(40, 800)
    t.setFont("Helvetica", 11)

    for section in ["SUMMARY", summary, "", "QUIZ", quiz, "", "FLASHCARDS", flashcards]:
        for line in section.split("\n"):
            t.textLine(line)

    pdf.drawText(t)
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

# ================= MAIN =================
if audio_file:
    st.audio(audio_file)

    if st.button("🚀 Generate Learning Material"):
        with st.spinner("Processing lecture..."):
            text = convert_audio_to_text(audio_file, language_code)
            summary = get_summary(text, level)
            quiz = get_quiz(text)
            flashcards = get_flashcards(text)

            st.session_state.history.append({
                "text": text,
                "summary": summary,
                "quiz": quiz,
                "flashcards": flashcards
            })

            st.subheader("📝 Transcribed Text")
            st.write(text)

            st.subheader("📘 Summary")
            st.success(summary)

            st.subheader("❓ Quiz (From Voice)")
            st.write(quiz)

            st.subheader("🃏 Flashcards")
            st.info(flashcards)

            pdf = generate_pdf(summary, quiz, flashcards)
            st.download_button(
                "📥 Download PDF",
                pdf,
                "Lecture_Notes.pdf",
                "application/pdf"
            )

# ================= HISTORY VIEW =================
if st.session_state.selected is not None:
    old = st.session_state.history[st.session_state.selected]
    st.markdown("---")
    st.subheader("📜 Previous Lecture")
    st.write(old["text"])
    st.success(old["summary"])
    st.write(old["quiz"])
    st.info(old["flashcards"])
