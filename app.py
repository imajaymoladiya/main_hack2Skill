import os
import json
import re
import logging
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Initialize logging structure
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize dotenv to read keys from .env file
load_dotenv()

# Initialize Flask app
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# Apply secure headers after each request
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Fetch Groq API details from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Check if the API key is a placeholder or empty
has_real_groq_key = (
    GROQ_API_KEY 
    and GROQ_API_KEY.strip() 
    and "your_groq" not in GROQ_API_KEY.lower()
    and "gsk_your_actual" not in GROQ_API_KEY.lower()
)

# Setup Groq Client if API key is present
if has_real_groq_key:
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info(f"Groq client successfully initialized with model: {GROQ_MODEL}")
    except ImportError:
        logger.warning("Warning: 'groq' package is not installed. Will use fallback database.")
        has_real_groq_key = False
else:
    logger.info("Running in Local Rule-Based Mode. Please set a valid GROQ_API_KEY in the .env file for dynamic generations.")


# --- SAFETY INTERCEPTOR ---
CRISIS_KEYWORDS = [
    r"\b(suicid|suicide|self-harm|self harm|end my life|kill myself|want to die|ending my life|cutting myself|harming myself|don't want to live|wish i was dead)\b"
]

def check_crisis(text):
    if not text:
        return False
    for pattern in CRISIS_KEYWORDS:
        if re.search(pattern, text.lower()):
            return True
    return False

CRISIS_RESPONSE = {
    "is_safety_trigger": True,
    "message": "It sounds like you are going through an extremely difficult time, and we want to make sure you are safe. ZenExam AI is a digital helper, not a clinical therapy service. Please reach out to someone who can help. You are not alone, and there is support available right now.",
    "helplines": [
        {"name": "Kiran Mental Health Helpline (Govt of India)", "contact": "1800-599-0019", "availability": "24/7, Toll-Free, Multilingual"},
        {"name": "Vandrevala Foundation Helpline (India)", "contact": "9999-666-555 / +91-22-61381111", "availability": "24/7, Call or WhatsApp"},
        {"name": "AASRA Suicide Prevention (India)", "contact": "+91-9820466726", "availability": "24/7, Crisis Chat & Support"},
        {"name": "Tele-MANAS Government Helpline (India)", "contact": "14416 / 1800-891-4416", "availability": "24/7"},
        {"name": "International Crisis Lifeline", "contact": "Dial 988 (US/Canada), 111 (UK), or contact your local emergency response team.", "availability": "24/7"}
    ]
}


# --- LOCAL RULE-BASED FALLBACK PARSER ---
def process_local_wellness_analysis(journal_text, mood, exam):
    text_lower = journal_text.lower()
    
    triggers = []
    patterns = []
    
    # 1. Detect triggers
    if any(x in text_lower for x in ["test", "mock", "score", "marks", "rank", "percentile", "grade"]):
        triggers.append("Mock Test Performance")
        patterns.append("Over-identifying personal worth with scores")
    if any(x in text_lower for x in ["syllabus", "backlog", "complete", "finish", "chapters", "portion", "revision", "pending"]):
        triggers.append("Syllabus Backlog")
        patterns.append("Syllabus Overwhelm & Backlog Anxiety")
    if any(x in text_lower for x in ["time", "hours", "schedule", "clock", "manage", "waste", "wasted", "delay"]):
        triggers.append("Time Management Pressure")
        patterns.append("Rigid Scheduling Stress")
    if any(x in text_lower for x in ["parent", "family", "peer", "friends", "comparison", "expect", "relatives", "dad", "mom"]):
        triggers.append("External Expectations & Peer Comparison")
        patterns.append("Fear of Disappointing Family")
    if any(x in text_lower for x in ["sleep", "tired", "sleepy", "exhausted", "insomnia", "night", "rest", "fatigue"]):
        triggers.append("Sleep Deprivation & Physical Exhaustion")
        patterns.append("Sacrificing Rest for Study Hours")
    if any(x in text_lower for x in ["fail", "clear", "crack", "happen", "what if", "lose", "cannot", "doubt"]):
        triggers.append("Fear of Failure & Imposter Syndrome")
        patterns.append("Catastrophizing exam outcomes")
        
    if not triggers:
        triggers.append("General Exam Prep Stress")
    if not patterns:
        patterns.append("Performance-Related Self-Doubt")
        
    mood_stress_map = {
        "anxious": (7, "Medium"),
        "burned_out": (9, "High"),
        "focused": (3, "Low"),
        "hopeful": (2, "Low"),
        "calm": (1, "Low")
    }
    
    base_stress, burnout = mood_stress_map.get(mood, (5, "Medium"))
    if "Sleep Deprivation & Physical Exhaustion" in triggers:
        base_stress = min(10, base_stress + 1)
        burnout = "High" if base_stress >= 7 else "Medium"
        
    # Custom Coping Strategies
    coping = []
    
    if "Mock Test Performance" in triggers:
        coping.append({
            "title": "Post-Exam Diagnostic Framing",
            "description": "Treat mock tests strictly as a diagnostic check, not a predictor. List 3 specific conceptual errors from your latest test and solve them without judging your intelligence.",
            "time_required": "10 Mins"
        })
    if "Syllabus Backlog" in triggers:
        coping.append({
            "title": "Micro-Scheduling & Rule of One",
            "description": "Forget the entire backlog list for today. Select exactly ONE sub-topic, study it with total focus for 45 minutes, and celebrate completing it. Slow progress builds confidence.",
            "time_required": "45 Mins"
        })
    if "Time Management Pressure" in triggers or mood == "burned_out":
        coping.append({
            "title": "50-10 Pomodoro Rhythm",
            "description": "Study for 50 minutes, then completely leave your study chair for 10 minutes. Walk, stretch, or drink water. Do not look at study materials or social feeds.",
            "time_required": "60 Mins"
        })
    if "Sleep Deprivation & Physical Exhaustion" in triggers:
        coping.append({
            "title": "Non-Sleep Deep Rest (NSDR)",
            "description": "Lie down flat on your back, close your eyes, and listen to a 10-minute guided NSDR script or body scan to quickly rest your prefrontal cortex.",
            "time_required": "10 Mins"
        })
    
    if len(coping) < 2:
        coping.append({
            "title": "Circle of Control",
            "description": "Write down 3 things you can control today (e.g., your study breaks, hydration, effort) and 3 things you cannot (e.g., paper difficulty, peer cutoff scores). Direct your energy inward.",
            "time_required": "5 Mins"
        })
        coping.append({
            "title": "Vagus Nerve Splash",
            "description": "Gently splash cold water on your face or practice three double-inhales followed by an extended sigh to stimulate your parasympathetic recovery system.",
            "time_required": "2 Mins"
        })
        
    # Mindfulness Exercises
    if mood == "anxious" or "Fear of Failure & Imposter Syndrome" in triggers:
        mindfulness = {
            "name": "Box Breathing for Heart Rate Stabilization",
            "instructions": "Inhale through your nose for 4 seconds, hold for 4 seconds, exhale through your mouth for 4 seconds, and hold empty for 4 seconds. Repeat 4 times.",
            "duration_minutes": 3
        }
    elif mood == "burned_out":
        mindfulness = {
            "name": "The Grounding 5-4-3-2-1 Technique",
            "instructions": "Slow down and identify: 5 things you see around you, 4 things you can physically touch, 3 things you hear, 2 things you smell, and 1 positive quality about yourself.",
            "duration_minutes": 5
        }
    else:
        mindfulness = {
            "name": "Focus Breath & Anchoring",
            "instructions": "Close your eyes. Anchor your attention entirely to the physical sensation of breath at the tip of your nostrils. When your mind drifts to syllabus topics, gently guide it back.",
            "duration_minutes": 4
        }
        
    # Empathetic Insight
    insight = f"Preparing for {exam} is a mental marathon, and feeling overwhelmed is a standard physiological stress response. Your journal highlights that you are experiencing triggers around {', '.join(triggers).lower()}, which standard trackers often miss."
    
    # Motivational Boost
    boost_map = {
        "JEE": "Physics, Chemistry, and Math are languages of logic. Today's practice is building your analytical pathways. One problem at a time, you are fully capable of this.",
        "NEET": "Your dream of healing others starts with caring for your own mind today. Biology and Chemistry are massive, but consistency, not panic, will get you there.",
        "UPSC": "The depth of the syllabus is refining your capacity to be a future public administrator. Focus on serving your schedule today, the rank will follow.",
        "GATE": "Engineering principles aren't conquered in a single push, but in quiet, steady practice. Your technical troubleshooting skills are expanding daily.",
        "CAT": "Aptitude exams test your composure and logical flexibility. Keep your cool under time pressure—accuracy naturally follows mental clarity.",
        "CUET": "Your transition to university is a step-by-step journey. Be gentle with your self-talk; learning is compounding."
    }
    boost = boost_map.get(exam, "You are much more than the sum of your competitive exam outcomes. Your worth is not defined by a scoring sheet. Treat yourself with compassion today.")
    
    # Emotional State distribution
    emotions = {"anxiety": 20, "focus": 20, "burnout": 20, "hopefulness": 20, "frustration": 20}
    if mood == "anxious":
        emotions = {"anxiety": 50, "focus": 15, "burnout": 15, "hopefulness": 10, "frustration": 10}
    elif mood == "burned_out":
        emotions = {"anxiety": 20, "focus": 10, "burnout": 50, "hopefulness": 5, "frustration": 15}
    elif mood == "focused":
        emotions = {"anxiety": 10, "focus": 60, "burnout": 10, "hopefulness": 15, "frustration": 5}
    elif mood == "hopeful":
        emotions = {"anxiety": 10, "focus": 20, "burnout": 10, "hopefulness": 55, "frustration": 5}
    elif mood == "calm":
        emotions = {"anxiety": 5, "focus": 25, "burnout": 5, "hopefulness": 45, "frustration": 20}
        
    return {
        "stress_level": base_stress,
        "burnout_risk": burnout,
        "primary_triggers": triggers,
        "detected_cognitive_patterns": patterns,
        "emotional_state_distribution": emotions,
        "actionable_coping_strategies": coping,
        "personalized_mindfulness_exercise": mindfulness,
        "empathetic_insight": insight,
        "motivational_boost": boost
    }

def process_local_chat_reply(messages, exam, stress_level, triggers):
    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "").lower()
            break
            
    reply = ""
    prompts = []
    
    if any(x in last_user_msg for x in ["panic", "anxious", "overwhelmed", "scared", "fear", "anxiety", "worry"]):
        reply = (
            f"I hear you. Take a slow, deep breath right now. When exam pressure builds, our minds easily fall into panic. "
            f"Preparing for {exam} is tough, but you don't have to carry it all at once. Let's practice a 2-minute Box Breathing break together. "
            "Click the Breathing Exercise tool below or just inhale for 4s, hold for 4s, and exhale for 4s. How are you feeling after that?"
        )
        prompts = ["Let's do Box Breathing", "I need a study break tool", "Give me exam motivation"]
    elif any(x in last_user_msg for x in ["test", "score", "marks", "mock", "rank", "percentile", "fail"]):
        reply = (
            "Mock test scores can trigger heavy self-doubt. However, mock tests are designed to find cracks in preparation "
            "so you can patch them. They are diagnostics, not final grades. What subjects or topics took the most marks today?"
        )
        prompts = ["How to analyze mock tests?", "I made silly mistakes", "Boost my focus"]
    elif any(x in last_user_msg for x in ["tired", "sleep", "exhausted", "burnout", "lazy", "fatigue", "sleepy"]):
        reply = (
            "Exhaustion is a physical signal, not a sign of laziness. When you study with high cognitive fatigue, your brain "
            "stops storing memories. Rest is active preparation. Can you try to get at least 7 hours of sleep tonight?"
        )
        prompts = ["Should I take a day off?", "NSDR meditation steps", "20-minute study break ideas"]
    elif any(x in last_user_msg for x in ["focus", "concentrate", "distract", "phone", "concentration"]):
        reply = (
            "Focus is not a constant; it comes in blocks. If your mind is wandering, put your phone in another room and "
            "pick just ONE small engineering sum, physics law, or history page. Set a timer for 20 minutes. Can we try that?"
        )
        prompts = ["Start a Pomodoro", "How to avoid phone distractions", "Quick study tip"]
    else:
        reply = (
            f"I'm here as your digital companion as you prepare for {exam}. It's a challenging journey, but "
            "every bit of steady, calm effort adds up. Tell me, what's on your mind right now?"
        )
        prompts = ["I feel overwhelmed", "Let's do a breathing break", "Give me a focus builder"]
        
    return {
        "reply": reply,
        "suggested_quick_prompts": prompts
    }


# --- FLASK ENDPOINTS ---

@app.route("/")
def index():
    """
    Serves the main application landing page.
    """
    return render_template("index.html")


@app.route("/api/status")
def status():
    """
    Returns the backend configuration status.
    """
    return jsonify({
        "has_api_key": has_real_groq_key,
        "model_configured": GROQ_MODEL
    })


@app.route("/api/analyze-journal", methods=["POST"])
def analyze_journal():
    """
    API endpoint that accepts student journal entry, mood logs, and competitive exam info.
    Runs Groq API with JSON schema enforcement, or falls back to local NLP logic.
    """
    data = request.json or {}
    journal_text = data.get("journal_text", "")
    mood = data.get("mood", "calm")
    exam = data.get("exam", "Other")
    
    # Input validation
    allowed_moods = {"calm", "anxious", "focused", "burned_out", "hopeful"}
    if mood not in allowed_moods:
         mood = "calm"
         
    allowed_exams = {"JEE", "NEET", "UPSC", "GATE", "CAT", "CUET", "Other"}
    if exam not in allowed_exams:
         exam = "Other"
         
    # Safety Check
    if check_crisis(journal_text):
        logger.warning("Safety Interceptor triggered inside /api/analyze-journal")
        return jsonify(CRISIS_RESPONSE)

    if has_real_groq_key:
        try:
            logger.info(f"Invoking Groq API model: {GROQ_MODEL} for journal analysis...")
            
            system_prompt = (
                "You are an empathetic, expert student mental wellness assistant specialized in high-stakes competitive exams (NEET, JEE, UPSC, GATE, etc.).\n"
                "Analyze the user's journal entry and mood log. You must strictly return a valid JSON object matching this structure:\n"
                "{\n"
                "  \"stress_level\": 7,\n"
                "  \"burnout_risk\": \"High\",\n"
                "  \"primary_triggers\": [\"Mock Test Marks\", \"Peer Pressure\"],\n"
                "  \"detected_cognitive_patterns\": [\"Catastrophizing\", \"Imposter Syndrome\"],\n"
                "  \"emotional_state_distribution\": {\n"
                "    \"anxiety\": 45,\n"
                "    \"focus\": 15,\n"
                "    \"burnout\": 30,\n"
                "    \"hopefulness\": 10\n"
                "  },\n"
                "  \"actionable_coping_strategies\": [\n"
                "    {\"title\": \"Coping Activity Title\", \"description\": \"Actionable student coping explanation.\", \"time_required\": \"10 Mins\"}\n"
                "  ],\n"
                "  \"personalized_mindfulness_exercise\": {\n"
                "    \"name\": \"Exercise Name\",\n"
                "    \"instructions\": \"Step-by-step description of a mental centering exercise.\",\n"
                "    \"duration_minutes\": 5\n"
                "  },\n"
                "  \"empathetic_insight\": \"Empathetic 1-2 sentence overview detailing emotional patterns normal trackers miss.\",\n"
                "  \"motivational_boost\": \"Highly encouraging quote or mantra contextual to their chosen competitive exam.\"\n"
                "}\n"
                "Do not include markdown tags outside the JSON block. Output raw JSON."
            )
            
            user_prompt = (
                f"Student profile:\n"
                f"- Exam: {exam}\n"
                f"- Mood Logged: {mood}\n"
                f"- Daily Journal Entry: \"{journal_text}\"\n"
            )
            
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=GROQ_MODEL,
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1500
            )
            
            raw_response = completion.choices[0].message.content
            parsed = json.loads(raw_response)
            
            # Sanity guards on responses
            if "stress_level" not in parsed:
                parsed["stress_level"] = 5
            if "burnout_risk" not in parsed:
                parsed["burnout_risk"] = "Medium"
                
            return jsonify(parsed)
            
        except Exception as e:
            logger.error(f"Error in Groq journal analysis: {str(e)}. Using fallback database.")
            fallback = process_local_wellness_analysis(journal_text, mood, exam)
            fallback["api_error"] = str(e)
            return jsonify(fallback)
    else:
        logger.info("Processing journal using local rule engine...")
        fallback = process_local_wellness_analysis(journal_text, mood, exam)
        return jsonify(fallback)


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    API endpoint for Conversational AI student support chat.
    Accepts full chat message history and contextual analysis parameters.
    """
    data = request.json or {}
    messages = data.get("messages", [])
    exam = data.get("exam", "Other")
    stress_level = data.get("stress_level", 5)
    triggers = data.get("triggers", [])
    
    # Extract last message to check for safety crisis keywords
    last_msg_content = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_msg_content = msg.get("content", "")
            break
            
    if check_crisis(last_msg_content):
        logger.warning("Safety Interceptor triggered inside /api/chat")
        return jsonify({
            "reply": CRISIS_RESPONSE["message"],
            "helplines": CRISIS_RESPONSE["helplines"],
            "is_safety_trigger": True,
            "suggested_quick_prompts": ["I am safe now", "Talk about study breaks", "Need a breathing check"]
        })

    if has_real_groq_key:
        try:
            logger.info(f"Invoking Groq API model: {GROQ_MODEL} for chat reply...")
            
            system_prompt = (
                f"You are 'MindBuddy', an empathetic, always-available digital wellness companion for students preparing for the {exam} competitive exam.\n"
                f"Context about the student:\n"
                f"- Target Exam: {exam}\n"
                f"- Current Stress Level: {stress_level}/10\n"
                f"- Identified Stress Triggers: {', '.join(triggers) if triggers else 'General stress'}\n\n"
                "Guidelines:\n"
                "- Speak in an warm, highly empathetic, supportive, and non-judgmental tone.\n"
                "- Keep responses concise (3-4 sentences max) to avoid overwhelming the student.\n"
                "- Suggest small, actionable mindfulness pauses, studying methods (like Pomodoro), or self-care advice.\n"
                "- Never act as a clinical therapist, diagnostic tool, or medical professional.\n"
                "- Strictly return a valid JSON object matching the following structure:\n"
                "{\n"
                "  \"reply\": \"Your empathetic chat message reply here...\",\n"
                "  \"suggested_quick_prompts\": [\"Short user prompt option 1\", \"Short user prompt option 2\", \"Short user prompt option 3\"]\n"
                "}\n"
                "Do not include markdown tags outside the JSON block. Output raw JSON."
            )
            
            # Limit conversation history to last 6 messages to stay within token limits
            conversation_history = messages[-6:]
            api_messages = [{"role": "system", "content": system_prompt}]
            for m in conversation_history:
                api_messages.append({"role": m["role"], "content": m["content"]})
                
            completion = groq_client.chat.completions.create(
                messages=api_messages,
                model=GROQ_MODEL,
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=800
            )
            
            raw_response = completion.choices[0].message.content
            parsed = json.loads(raw_response)
            return jsonify(parsed)
            
        except Exception as e:
            logger.error(f"Error in Groq chat execution: {str(e)}. Using fallback chat.")
            fallback = process_local_chat_reply(messages, exam, stress_level, triggers)
            fallback["api_error"] = str(e)
            return jsonify(fallback)
    else:
        logger.info("Processing chat reply using local rule engine...")
        fallback = process_local_chat_reply(messages, exam, stress_level, triggers)
        return jsonify(fallback)


# Run server locally on port 5000
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
