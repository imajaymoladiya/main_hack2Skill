# ZenExam AI 🧘

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/imajaymoladiya/main_hack2Skill)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/imajaymoladiya/main_hack2Skill)

ZenExam AI is a premium, generative AI-powered student mental wellness companion designed to support students preparing for high-stakes board exams and competitive entrance tests (e.g., NEET, JEE, CUET, CAT, GATE, UPSC). 

Students preparing for these career-defining milestones face immense pressure, anxiety, mock exam stress, syllabus backlog paralysis, and burnout. ZenExam AI provides a secure, glassmorphic single-page wellness panel featuring dynamic stress triggers analysis, cognitive distortion tracking, a real-time empathetic conversation companion, guided box-breathing, and a focus Pomodoro study tracker.

---

## ✨ Features

- **GenAI Journal & Mood Analysis:** Analyze open-ended daily journaling to extract stress triggers (e.g., Mock test scores, family expectation) and cognitive distortions (e.g., Catastrophizing, Imposter Syndrome) that basic emoji trackers miss.
- **Empathetic Chat Companion (MindBuddy):** A dedicated, non-judgmental conversational buddy tailored to the student's exam context (e.g., UPSC study strategies or JEE fatigue relief) offering advice within 3-4 sentences to prevent information overwhelm.
- **Immediate Safety Interceptor:** Scans user inputs using safety expressions. If self-harm indicators or acute crises are found, standard AI generation is intercepted, and it displays emergency helpline cards (Kiran Govt Helpline, AASRA, Vandrevala Foundation) instantly.
- **Active Privacy Shield:** All journal entries and chat transcripts are saved strictly within the user's browser `localStorage`. No data is persisted in a database, ensuring maximum confidentiality.
- **Mindfulness & Productivity Toolkit:**
  - **Interactive Box Breathing Circle:** Visual expansion/contraction animation following the 4s-4s-4s-4s rule to lower cortisol levels.
  - **Pomodoro Focus Timer:** Promotes cognitive accuracy via structured study intervals, using the HTML5 Web Audio API to synthesize relaxing end-of-session chimes.
- **Resilient Local Fallback Engine:** If the Groq API Key is unconfigured or a rate-limit error occurs, a local rule-based NLP parser processes the logs to supply high-quality recommendations seamlessly.

---

## 📂 Project Structure

```
d:\Ajay\main_hack2skill\
├── .env                  # Environment secrets (Groq API Key & Model parameters)
├── .gitignore            # Git exclusion guidelines
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation and developer instructions
├── app.py                # Flask Backend Web Server & Groq SDK wrapper
├── templates/
│   └── index.html        # Soothing glassmorphic dark-theme frontend
└── static/
    ├── css/
    │   └── index.css     # CSS variable stylesheet and keyframe animations
    └── js/
        └── app.js        # Browser timer loops, local storage logger, and AJAX handlers
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher.
- A Groq Cloud API key (Optional: App activates rule-based Local Mode if missing).

### Installation & Run Setup

1. **Activate the Virtual Environment:**
   If you have a virtual environment in your directory, activate it:
   ```powershell
   .\myenv\Scripts\activate
   ```

2. **Install Dependencies:**
   Install required Python packages from the directory root:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create or edit the `.env` file in the root directory and ensure the variables are set:
   ```env
   GROQ_API_KEY=gsk_your_actual_groq_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   PORT=5000
   ```
   *Note: Both the Groq key and the model identifier are read dynamically from `.env`.*

4. **Start the Flask Web Server:**
   ```powershell
   python app.py
   ```

5. **Open the Application:**
   Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

---

## 🛡️ Code Accuracy & Security

- **Secure HTTP Headers:** The Flask server uses `@app.after_request` intercepts to enforce:
  - `X-Frame-Options: DENY` (prevents clickjacking).
  - `X-Content-Type-Options: nosniff` (mitigates MIME-sniffing).
  - `X-XSS-Protection: 1; mode=block` (guards against cross-site scripting).
  - `Referrer-Policy: strict-origin-when-cross-origin`.
- **Sanitized Server inputs:** Sanitizes data fields and enforces strict whitelist checking on mood selections and exam parameters.
- **Silent Fallbacks:** Handles API network loss or authentication failure gracefully, rendering local diagnostic answers without crashing.
