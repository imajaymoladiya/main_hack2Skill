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

LOCAL_RESPONSES = {
    "English": {
        "panic": "I hear you. Take a slow, deep breath right now. When exam pressure builds, our minds easily fall into panic. Preparing for {exam} is tough, but you don't have to carry it all at once. Let's practice a 2-minute Box Breathing break together.",
        "test": "Mock test scores can trigger heavy self-doubt. However, mock tests are designed to find cracks in preparation so you can patch them. They are diagnostics, not final grades. What subjects or topics took the most marks today?",
        "tired": "Exhaustion is a physical signal, not a sign of laziness. When you study with high cognitive fatigue, your brain stops storing memories. Rest is active preparation. Can you try to get at least 7 hours of sleep tonight?",
        "focus": "Focus is not a constant; it comes in blocks. If your mind is wandering, put your phone in another room and pick just ONE small syllabus topic. Set a timer for 20 minutes. Can we try that?",
        "default": "I'm here as your digital companion as you prepare for {exam}. It's a challenging journey, but every bit of steady, calm effort adds up. Tell me, what's on your mind right now?",
        "prompts": {
            "panic": ["Let's do Box Breathing", "I need a study break tool", "Give me exam motivation"],
            "test": ["How to analyze mock tests?", "I made silly mistakes", "Boost my focus"],
            "tired": ["Should I take a day off?", "NSDR meditation steps", "20-minute study break ideas"],
            "focus": ["Start a Pomodoro", "How to avoid phone distractions", "Quick study tip"],
            "default": ["I feel overwhelmed", "Let's do a breathing break", "Give me a focus builder"]
        }
    },
    "Hindi": {
        "panic": "मैं आपकी बात समझ सकता हूँ। कृपया एक लंबी, गहरी साँस लें। जब परीक्षा का दबाव बढ़ता है, तो हमारा दिमाग घबरा जाता है। {exam} की तैयारी कठिन है, लेकिन आपको इसे अकेले नहीं उठाना है। चलिए साथ मिलकर 2 मिनट का ब्रीदिंग अभ्यास करते हैं।",
        "test": "मॉक टेस्ट के स्कोर से भारी आत्म-संदेह हो सकता है। लेकिन याद रखें, मॉक टेस्ट गलतियाँ सुधारने के लिए होते हैं। ये अंतिम परिणाम नहीं हैं। आज आपको किस विषय में सबसे अधिक परेशानी हुई?",
        "tired": "थकान एक शारीरिक संकेत है, आलस्य नहीं। जब आप मानसिक रूप से अत्यधिक थके होते हैं, तो दिमाग याद रखना बंद कर देता है। आराम भी तैयारी का हिस्सा है। क्या आप आज रात कम से कम 7 घंटे की नींद ले सकते हैं?",
        "focus": "एकाग्रता हमेशा एक जैसी नहीं रहती, यह अंतरालों में आती है। यदि आपका ध्यान भटक रहा है, तो फोन को दूर रखें और केवल एक छोटे से टॉपिक को चुनें। 20 मिनट का टाइमर सेट करें। क्या हम यह कोशिश करें?",
        "default": "मैं {exam} की तैयारी में आपका साथी हूँ। यह एक लंबी यात्रा है, लेकिन आपका हर शांत और निरंतर प्रयास मायने रखता है। मुझे बताएं, अभी आपके मन में क्या चल रहा है?",
        "prompts": {
            "panic": ["चलो ब्रीदिंग करते हैं", "मुझे स्टडी ब्रेक चाहिए", "परीक्षा प्रेरणा दें"],
            "test": ["मॉक टेस्ट कैसे सुधारें?", "मुझसे सिली मिस्टेक हुई", "मेरा फोकस बढ़ाएं"],
            "tired": ["क्या मुझे छुट्टी लेनी चाहिए?", "मेडीटेशन के चरण", "ब्रेक के तरीके"],
            "focus": ["पोमोडोरो शुरू करें", "फोन से दूरी कैसे बनाएं", "त्वरित स्टडी टिप"],
            "default": ["मुझे तनाव महसूस हो रहा है", "ब्रीदिंग ब्रेक लें", "फोकस कैसे बढ़ाएं"]
        }
    },
    "Hinglish": {
        "panic": "Main aapki baat samajh sakta hoon. Please ek lambi, gehri saans lein. Exam pressure me panic hona normal hai. {exam} ki taiyari tough hai, par aapko akele sab handle nahi karna hai. Chalo 2-minute box breathing break lete hain.",
        "test": "Mock test scores se self-doubt hona normal hai. Par mock tests humari weaknesses ko find karne ke liye hote hain taaki hum unhe sudhar sakein. Aaj kis subject me sabse zyada dikkat aayi?",
        "tired": "Thakavat ek body signal hai, laziness nahi. Jab aap thake hote hain, toh brain focus nahi kar paata. Rest bhi study ka part hai. Aaj raat kam se kam 7 ghante ki neend lene ki koshish karein.",
        "focus": "Focus continuous nahi hota, chunks me aata hai. Agar mind distract ho raha hai, toh phone door rakhein aur kisi ek small topic par focus karein. 20 mins ka timer lagayein. Kya hum ye try karein?",
        "default": "Main aapki {exam} prep me help karne ke liye yahan hoon. Har chota step count karta hai. Bataiye, aapke mind me kya chal raha hai?",
        "prompts": {
            "panic": ["Breathing exercise karein", "Study break chahiye", "Exam motivation do"],
            "test": ["Mock test kaise analyze karein?", "Silly mistakes ho gayi", "Focus kaise badhayein"],
            "tired": ["Kya break lena chahiye?", "NSDR meditation steps", "Break ke ideas"],
            "focus": ["Pomodoro start karein", "Phone distraction kaise rokein", "Quick study tip"],
            "default": ["Mujhe stress ho raha hai", "Breathing break lein", "Focus badhana hai"]
        }
    },
    "Spanish": {
        "panic": "Te entiendo. Toma un respiro lento y profundo ahora mismo. Cuando aumenta la presión del examen, es fácil entrar en pánico. Prepararse para {exam} es difícil, pero no tienes que llevarlo todo a la vez. Practiquemos juntos.",
        "test": "Las puntuaciones de los simulacros pueden generar dudas. Sin embargo, están diseñados para encontrar fallas para que puedas corregirlas. Son diagnósticos, no calificaciones finales. ¿Qué temas te costaron más hoy?",
        "tired": "El agotamiento es una señal física, no de pereza. Cuando estudias con fatiga cognitiva, tu cerebro deja de almacenar recuerdos. El descanso es preparación activa. ¿Puedes intentar dormir al menos 7 horas hoy?",
        "focus": "El enfoque no es constante; viene en bloques. Si tu mente divaga, pon el teléfono en otra habitación y elige un solo tema pequeño. Pon un temporizador de 20 minutos. ¿Podemos intentar eso?",
        "default": "Estoy aquí como tu compañero digital mientras te preparas para {exam}. Es un viaje desafiante, pero cada esfuerzo constante y tranquilo cuenta. Dime, ¿qué tienes en mente ahora?",
        "prompts": {
            "panic": ["Hagamos respiración de caja", "Necesito un descanso", "Dame motivación"],
            "test": ["¿Cómo analizar simulacros?", "Cometí errores tontos", "Mejora mi enfoque"],
            "tired": ["¿Debería tomar un día libre?", "Meditación NSDR", "Ideas para descansos"],
            "focus": ["Iniciar un Pomodoro", "Evitar distracciones", "Consejo de estudio"],
            "default": ["Me siento abrumado", "Hagamos una pausa", "Constructor de enfoque"]
        }
    },
    "Marathi": {
        "panic": "मी समजतो. कृपया आता एक दीर्घ श्वास घ्या. परीक्षेचा ताण वाढल्यावर मन घाबरणे साहजिक आहे. {exam} ची तयारी कठीण आहे, पण तुम्हाला हे एकट्याने करायचे नाही. चला २ मिनिटांचा श्वासोच्छवासाचा सराव करूया.",
        "test": "मॉक टेस्टच्या गुणांमुळे स्वतःबद्दल शंका निर्माण होऊ शकते. पण लक्षात ठेवा, मॉक टेस्ट चुका शोधण्यासाठी असतात जेणेकरून तुम्ही त्या सुधारू शकाल. आज कोणत्या विषयात जास्त अडचण आली?",
        "tired": "थकवा हा शारीरिक संकेत आहे, आळस नाही. जेव्हा तुम्ही मानसिक थकव्यात अभ्यास करता, तेव्हा मेंदू आठवणी साठवणे थांबवतो. विश्रांती ही देखील तयारीच आहे. आज रात्री किमान ७ तास झोप घेण्याचा प्रयत्न करा.",
        "focus": "एकाग्रता सतत राहत नाही, ती तुकड्यांमध्ये येते. मन भरकटत असेल तर फोन दुसऱ्या खोलीत ठेवा आणि फक्त एका लहान विषयावर लक्ष केंद्रित करा. २० मिनिटांचा टाइमर लावा.",
        "default": "तुमच्या {exam} परीक्षेच्या तयारीसाठी मी सोबती म्हणून येथे आहे. हा प्रवास आव्हानात्मक आहे, पण प्रत्येक शांत आणि निरंतर प्रयत्न महत्त्वाचा ठरतो. सांगा, सध्या मनात काय आहे?",
        "prompts": {
            "panic": ["श्वासोच्छवासाचा सराव करूया", "मला ब्रेक हवा आहे", "परीक्षेसाठी प्रेरणा द्या"],
            "test": ["मॉक टेस्टचे विश्लेषण कसे करावे?", "माझ्याकडून चुका झाल्या", "माझी एकाग्रता वाढवा"],
            "tired": ["मी सुट्टी घ्यावी का?", "NSDR ध्यान पद्धती", "ब्रेकच्या काही कल्पना"],
            "focus": ["पोमोडोरो सुरू करा", "फोनचे लक्ष कसे टाळायचे", "अभ्यासाची सोपी टीप"],
            "default": ["मला ताण आला आहे", "एक छोटा ब्रेक घेऊया", "फोकस कसा वाढवावा"]
        }
    },
    "Tamil": {
        "panic": "நான் உங்களைப் புரிந்து கொள்கிறேன். இப்போது மெதுவாக ஆழமான மூச்சை எடுங்கள். பரீட்சை அழுத்தம் அதிகரிக்கும் போது பயம் ஏற்படுவது இயல்பு. {exam} தயாரிப்பு கடினமானது தான், ஆனால் நீங்கள் தனியாக எல்லாவற்றையும் சுமக்க வேண்டாம். வாருங்கள் ஒரு மூச்சு பயிற்சி செய்வோம்.",
        "test": "மாதிரித் தேர்வு மதிப்பெண்கள் சுய சந்தேகத்தைத் தூண்டலாம். ஆனால், தவறுகளைக் கண்டறிந்து திருத்தவே மாதிரித் தேர்வுகள் உதவுகின்றன. அவை இறுதி மதிப்பெண்கள் அல்ல. இன்று எந்தப் பாடத்தில் உங்களுக்கு அதிக சிரமம் இருந்தது?",
        "tired": "சோர்வு என்பது உடலின் அறிகுறி, சோம்பேறித்தனம் அல்ல. अधिक சோர்வோடு படிக்கும்போது மூளை தகவல்களைச் சேमीக்காது. ஓய்வு என்பதும் படிப்புதான். இன்று இரவு குறைந்தபட்சம் 7 மணிநேரம் தூங்க முயற்சிக்கலாமா?",
        "focus": "கவனம் எப்போதும் ஒரே சீராக இருக்காது, அது இடைவெளிகளில் வரும். உங்கள் மனம் அலைபாய்ந்தால், தொலைபேசியை தள்ளி வைத்துவிட்டு, ஒரு சிறிய பாடத்தைத் தேர்ந்தெடுத்து 20 நிமிடங்கள் படியுங்கள்.",
        "default": "உங்கள் {exam} தயாரிப்பில் உங்களுக்கு உதவ நான் இங்கே இருக்கிறேன். இது ஒரு சவாலான பயணம், ஆனால் உங்களது ஒவ்வொரு முயற்சியும் முக்கியமானது. இப்போது உங்கள் மனதில் என்ன இருக்கிறது?",
        "prompts": {
            "panic": ["மூச்சு பயிற்சி செய்வோம்", "எனக்கு இடைவெளி தேவை", "தேர்வு ஊக்கம் கொடுங்கள்"],
            "test": ["மாதிரி தேர்வை பகுப்பாய்வது எப்படி?", "நான் சில தவறுகள் செய்தேன்", "கவனத்தை அதிகரிக்கவும்"],
            "tired": ["நான் ஒரு நாள் ஓய்வெடுக்கலாமா?", "NSDR தியானம்", "இடைவெளி யோசனைகள்"],
            "focus": ["போமோடோரோவைத் தொடங்கு", "தொலைபேசி கவனச்சிதறலைத் தவிர்க்க", "படிப்பு குறிப்பு"],
            "default": ["மன அழுத்தம் அதிகமாக உள்ளது", "ஒரு சிறிய இடைவெளி", "கவனத்தை வளர்க்க"]
        }
    },
    "Telugu": {
        "panic": "నేను అర్థం చేసుకోగలను. దయచేసి ఇప్పుడు ఒకసారి సుదీర్ఘంగా శ్వాస తీసుకోండి. परीक्षाల ఒత్తిడి పెరిగినప్పుడు ఆందోళన చెందడం సహజం. {exam} ప్రిపరేషన్ కష్టమే, కానీ మీరు ఒంటరిగా అంతా మోయాల్సిన అవసరం లేదు. కలిసి శ్వాస నియంత్రణ వ్యాయామం చేద్దాం.",
        "test": "మాక్ టెస్ట్ మార్కుల వల్ల ఆత్మవిశ్వాసం తగ్గొచ్చు. కానీ మాక్ టెస్టులు తప్పులను తెలుసుకొని సరిదిద్దుకోవడానికే. ఇవి ఫైనల్ మార్కులు కావు. ఈ రోజు మీకు ఏ సబ్జెక్టులో ఎక్కువ ఇబ్బంది అనిపించింది?",
        "tired": "అలసట అనేది శరీరం ఇచ్చే సంकेతం, సోమరితనం కాదు. మెదడు అలసిపోయినప్పుడు విషయాలను గుర్తుంచుకోలేదు. విశ్రాంతి కూడా ప్రిపరేషన్ లో భాగమే. ఈ రోజు కనీసం 7 గంటలు పడుకోవడానికి ప్రయత్నించండి.",
        "focus": "ఏకాగ్రత అనేది ఎల్లప్పుడూ ఒకేలా ఉండదు. మీ దృష్టి మళ్లుతుంటే, ఫోన్‌ను పక్కన పెట్టి ఏదైనా ఒక చిన్న అంశాన్ని ఎంచుకోండి. 20 నిమిషాల టైమర్ పెట్టుకోండి. ప్రయత్నిద్దామా?",
        "default": "మీ {exam} ప్రిపరేషన్ లో సహాయం చేయడానికి నేను ఇక్కడే ఉన్నాను. ఇది ఒక సవాలుతో కూడిన ప్రयाణం, కానీ ప్రతి నిలకడైన ప్రయత్నం ముఖ్యం. చెప్పండి, ఇప్పుడు మీ మనసులో ఏముంది?",
        "prompts": {
            "panic": ["శ్వాస వ్యాయామం చేద్దాం", "నాకు విరామం కావాలి", "నాకు ప్రేరణ ఇవ్వండి"],
            "test": ["మాక్ టెస్ట్ ఎలా విశ్లేషించాలి?", "నేను చిన్న తప్పులు చేశాను", "నా దృష్టిని పెంచండి"],
            "tired": ["నేను సెలవు తీసుకోవాలా?", "NSDR ధ్యానం", "విరామ సమయ ఆలోచనలు"],
            "focus": ["పోమోడోరో ప్రారంభించండి", "ఫోన్ డిస్ట్రాక్షన్ ఎలా ఆపాలి", "చిన్న స్టడీ టిప్"],
            "default": ["నేను ఒత్తిడిగా ఉన్నాను", "చిన్న విరామం తీసుకుందాం", "ఏకాగ్రత పెంచే మార్గం"]
        }
    },
    "French": {
        "panic": "Je t'entends. Prends une inspiration lente et profonde. Quand la pression des examens monte, notre esprit peut paniquer. La préparation pour {exam} est difficile, mais tu n'es pas seul. Pratiquons une respiration contrôlée ensemble.",
        "test": "Les notes d'examens blancs peuvent provoquer des doutes. Cependant, ils sont faits pour identifier les lacunes afin de les corriger. Ce sont des diagnostics, pas des notes finales. Quels sujets ont posé problème aujourd'hui ?",
        "tired": "La fatigue est un signal physique, pas de la paresse. Étudier fatigué empêche le cerveau d'enregistrer les informations. Le repos fait partie de la préparation. Peux-tu essayer de dormir au moins 7 heures ce soir ?",
        "focus": "La concentration n'est pas constante; elle vient par blocs. Si ton esprit s'égare, pose ton téléphone dans une autre pièce et choisis un seul sujet. Règle un minuteur sur 20 minutes. On essaie ?",
        "default": "Je suis là comme compagnon numérique pour ta préparation à {exam}. C'est un parcours exigeant, mais chaque effort compte. Dis-moi, qu'as-tu sur le cœur aujourd'hui ?",
        "prompts": {
            "panic": ["Faisons de la respiration", "Besoin d'une pause", "Donne-moi de la motivation"],
            "test": ["Comment analyser les examens blancs?", "J'ai fait des erreurs bêtes", "Aide-moi à me concentrer"],
            "tired": ["Devrais-je prendre un jour de repos?", "Méditation NSDR", "Idées de pause"],
            "focus": ["Lancer un Pomodoro", "Éviter les distractions sur téléphone", "Astuce d'étude"],
            "default": ["Je me sens submergé", "Faire une pause respiratoire", "Améliorer ma concentration"]
        }
    },
    "German": {
        "panic": "Ich verstehe dich. Nimm jetzt einen tiefen Atemzug. Bei Prüfungsstress gerät man leicht in Panik. Die Vorbereitung auf {exam} ist hart, aber du musst das nicht alleine durchstehen. Lass uns eine kurze Atempause machen.",
        "test": "Ergebnisse von Probetests können Selbstzweifel wecken. Sie sind jedoch dazu da, Lücken zu finden, damit du sie schließen kannst. Sie sind nur eine Diagnose. Welche Themen fielen dir heute schwer?",
        "tired": "Erschöpfung ist ein Signal des Körpers, keine Faulheit. Wenn du geistig müde lernst, speichert dein Gehirn keine Erinnerungen. Ruhe ist aktive Vorbereitung. Kannst du heute Nacht mindestens 7 Stunden schlafen?",
        "focus": "Fokus ist nicht konstant; er kommt in Blöcken. Wenn deine Gedanken abschweifen, lege dein Handy in einen anderen Raum und wähle ein kleines Thema. Stelle einen Timer auf 20 Minuten.",
        "default": "Ich bin dein digitaler Begleiter bei deiner Vorbereitung auf {exam}. Es ist ein anspruchsvoller Weg, aber jeder ruhige Schritt zählt. Erzähl mir, was dich gerade beschäftigt.",
        "prompts": {
            "panic": ["Lass uns Atemübungen machen", "Ich brauche eine Pause", "Gib mir Prüfungsmotivation"],
            "test": ["Probetests analysieren", "Habe dumme Fehler gemacht", "Fokus stärken"],
            "tired": ["Sollte ich einen Tag frei nehmen?", "NSDR Meditation", "Ideen für Pausen"],
            "focus": ["Pomodoro starten", "Handy-Ablenkungen vermeiden", "Schneller Lerntipp"],
            "default": ["Ich fühle mich überfordert", "Atempause machen", "Konzentration aufbauen"]
        }
    }
}

def process_local_chat_reply(messages, exam, stress_level, triggers, language="English"):
    lang = str(language).capitalize() if language else "English"
    if lang not in LOCAL_RESPONSES:
        found = False
        for k in LOCAL_RESPONSES.keys():
            if k.lower() == lang.lower():
                lang = k
                found = True
                break
        if not found:
            lang = "English"

    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "").lower()
            break
            
    reply_type = "default"
    if any(x in last_user_msg for x in ["panic", "anxious", "overwhelmed", "scared", "fear", "anxiety", "worry"]):
        reply_type = "panic"
    elif any(x in last_user_msg for x in ["test", "score", "marks", "mock", "rank", "percentile", "fail"]):
        reply_type = "test"
    elif any(x in last_user_msg for x in ["tired", "sleep", "exhausted", "burnout", "lazy", "fatigue", "sleepy"]):
        reply_type = "tired"
    elif any(x in last_user_msg for x in ["focus", "concentrate", "distract", "phone", "concentration"]):
        reply_type = "focus"
        
    responses_dict = LOCAL_RESPONSES[lang]
    reply = responses_dict[reply_type].format(exam=exam)
    prompts = responses_dict["prompts"][reply_type]
        
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
    language = data.get("language", "English")
    
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
            logger.info(f"Invoking Groq API model: {GROQ_MODEL} for chat reply in language: {language}...")
            
            system_prompt = (
                f"You are 'MindBuddy', an empathetic, always-available digital wellness companion for students preparing for the {exam} competitive exam.\n"
                f"Context about the student:\n"
                f"- Target Exam: {exam}\n"
                f"- Current Stress Level: {stress_level}/10\n"
                f"- Identified Stress Triggers: {', '.join(triggers) if triggers else 'General stress'}\n"
                f"- Preferred Language: {language}\n\n"
                "Guidelines:\n"
                "- Speak in a warm, highly empathetic, supportive, and non-judgmental tone.\n"
                "- Keep responses concise (3-4 sentences max) to avoid overwhelming the student.\n"
                "- Suggest small, actionable mindfulness pauses, studying methods (like Pomodoro), or self-care advice.\n"
                "- Never act as a clinical therapist, diagnostic tool, or medical professional.\n"
                f"- You MUST respond entirely in the language: {language}. If Hindi, write in Devanagari script. If Hinglish, write in Latin script using common Hindi/Urdu phrases. If Spanish, write in Spanish, and so on.\n"
                f"- All output keys (specifically the 'reply' content and the options inside 'suggested_quick_prompts') MUST be translated to the requested language: {language}.\n"
                "- Strictly return a valid JSON object matching the following structure:\n"
                "{\n"
                "  \"reply\": \"Your empathetic chat message reply here in the requested language...\",\n"
                "  \"suggested_quick_prompts\": [\"Short user prompt option 1 in the requested language\", \"Short user prompt option 2 in the requested language\", \"Short user prompt option 3 in the requested language\"]\n"
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
            fallback = process_local_chat_reply(messages, exam, stress_level, triggers, language)
            fallback["api_error"] = str(e)
            return jsonify(fallback)
    else:
        logger.info("Processing chat reply using local rule engine...")
        fallback = process_local_chat_reply(messages, exam, stress_level, triggers, language)
        return jsonify(fallback)


# Run server locally on port 5000
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
