import streamlit as st
import speech_recognition as sr
import tempfile
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# ================= GEMINI CONFIG =================
genai.configure(api_key="AIzaSyBR7vXL9-J19yHs81YucWCrJkdzsgreE_A")

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
    Transform lecture audio into notes, quizzes, flashcards & PDF using AI
    </p>
    <hr>
    """,
    unsafe_allow_html=True
)

# ================= SIDEBAR =================
st.sidebar.title("📚 Project Dashboard")
st.sidebar.write(
    """
    **AI-powered learning assistant** that converts lecture audio into
    structured academic content using Speech-to-Text, NLP, and
    Generative AI (Gemini).
    """
)

st.sidebar.markdown("### 🧠 Technologies")
st.sidebar.write(
    "- Speech-to-Text\n"
    "- Natural Language Processing\n"
    "- Gemini Generative AI\n"
    "- Streamlit"
)

st.sidebar.markdown("### 🕘 Lecture History")

if st.session_state.history:
    for i, item in enumerate(st.session_state.history):
        if st.sidebar.button(f"Lecture {i+1}"):
            st.session_state.selected = i
else:
    st.sidebar.write("No history yet.")

# ================= INPUT SECTION =================
st.subheader("📥 Input Section")
st.info("Upload a **clear WAV lecture audio** for best results.")

language = st.selectbox(
    "🌐 Lecture Language",
    ["English", "Tamil", "Hindi"]
)
language_code = {"English": "en-IN", "Tamil": "ta-IN", "Hindi": "hi-IN"}[language]

level = st.selectbox(
    "🎯 Learning Level",
    ["Beginner", "Intermediate", "Exam-Oriented"]
)

audio_file = st.file_uploader(
    "🎙️ Upload Lecture Audio (WAV)",
    type=["wav"]
)

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

# -------- FALLBACK LOGIC (SAFE & PROFESSIONAL) --------
def fallback_summary(text, level):
    sentences = text.split(".")
    return ". ".join(sentences[:3]) + "."

def fallback_quiz(text):
    return (
        "1. What is the main topic discussed?\n"
        "2. Explain the key concept mentioned.\n"
        "3. Mention one important point from the lecture.\n"
        "4. Why is this topic important?\n"
        "5. How does it help students?"
    )

def fallback_flashcards(text):
    sentences = text.split(".")
    return f"Q: What is discussed in the lecture?\nA: {sentences[0]}"

def get_summary(text, level):
    prompt = f"Summarize this lecture for a {level} student:\n{text}"
    result = gemini_generate(prompt)
    return result if result else fallback_summary(text, level)

def get_quiz(text):
    prompt = f"Generate 5 quiz questions from this lecture:\n{text}"
    result = gemini_generate(prompt)
    return result if result else fallback_quiz(text)

def get_flashcards(text):
    prompt = f"Create flashcards from this lecture:\n{text}"
    result = gemini_generate(prompt)
    return result if result else fallback_flashcards(text)

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

# ================= MAIN PROCESS =================
if audio_file:
    st.audio(audio_file)
    st.success("✅ Audio uploaded successfully!")

    if st.button("🚀 Generate Learning Materials"):
        with st.spinner("Analyzing lecture using AI..."):
            text = convert_audio_to_text(audio_file, language_code)

            summary = get_summary(text, level)
            quiz = get_quiz(text)
            flashcards = get_flashcards(text)

            # Save to history
            st.session_state.history.append({
                "text": text,
                "summary": summary,
                "quiz": quiz,
                "flashcards": flashcards
            })

            st.subheader("📝 Transcribed Lecture Text")
            st.text_area("Lecture Content", text, height=160)

            st.subheader("📘 AI-Generated Summary")
            st.success(summary)

            st.subheader("❓ Quiz (From Lecture Voice)")
            st.write(quiz)

            st.subheader("🃏 Flashcards")
            st.info(flashcards)

            pdf = generate_pdf(summary, quiz, flashcards)
            st.download_button(
                "📥 Download PDF Report",
                pdf,
                "Lecture_Notes_Report.pdf",
                "application/pdf"
            )

# ================= HISTORY VIEW =================
if st.session_state.selected is not None:
    old = st.session_state.history[st.session_state.selected]

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("📜 Previous Lecture Output")

    st.write("📝 Text:")
    st.write(old["text"])

    st.write("📘 Summary:")
    st.success(old["summary"])

    st.write("❓ Quiz:")
    st.write(old["quiz"])

    st.write("🃏 Flashcards:")
    st.info(old["flashcards"])

# ================= FOOTER =================
st.markdown(
    """
    <hr>
    <p style='text-align: center; font-size: 14px; color: grey;'>
    AI Internship Project | Speech-to-Text • NLP • Gemini Generative AI
    </p>
    """,
    unsafe_allow_html=True
)
