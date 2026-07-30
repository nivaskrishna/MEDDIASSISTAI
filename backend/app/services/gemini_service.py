from google import genai
from google.genai import types
from app.core.config import settings
import json
import logging
import base64
import re
import asyncio
import time

# OpenRouter fallback (imported lazily to avoid import errors if package missing)
try:
    from app.services.openrouter_service import analyze_with_openrouter as _openrouter_analyze
except ImportError:
    _openrouter_analyze = None

logger = logging.getLogger(__name__)

# Initialize client using new google-genai SDK
client = None
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize GenAI Client: {e}")

SYSTEM_PROMPT = """
You are MediAssist AI, an expert medical assistant. Analyze the user's symptoms (text description and/or image of the condition).
Return ONLY a valid JSON object.
Do not include markdown blocks, just raw JSON.
The JSON must have the following keys exactly:
- "condition": A short string representing the possible condition.
- "first_aid": A clear, detailed string for first aid instructions outlining step-by-step what the user can do right now.
- "severity": A string, one of: "Low", "Medium", "High", "Critical".
- "doctor_type": A short string representing the recommended doctor specialty.
- "image_prompt": A highly specific, concrete medical illustration prompt describing first aid for the identified condition (e.g. "Medical first aid illustration showing a hand under running water to cool a burn").
- "symptoms": A list of strings representing the key symptoms identified.

If an image is provided, inspect the image (e.g., of a burn, cut, rash, wound) and cross-reference it with the description to formulate the assessment.
"""

# ── Comprehensive local fallback matching engine ──────────────────────────
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Direct mappings of keywords to specific conditions for high precision matching
DIRECT_MAPPINGS = {
    "heart attack": "Heart Attack",
    "chest pain": "Heart Attack",
    "stroke": "Stroke",
    "snake": "Snake Bite",
    "dog": "Dog Bite",
    "poison": "Poisoning",
    "chok": "Choking",
    "asthma": "Asthma Attack",
    "seizure": "Seizure",
    "heat stroke": "Heat Stroke",
    "heat exhaustion": "Heat Exhaustion",
    "frostbite": "Frostbite",
    "hypothermia": "Hypothermia",
    "burn": "First-degree Burn",
    "broken": "Broken Arm",
    "fracture": "Broken Arm",
    "sprain": "Sprained Ankle",
    "headache": "Tension Headache / Possible Migraine",
    "fever": "Fever — Possible Viral or Bacterial Infection",
    "cough": "Cough — Upper Respiratory Concern",
    "cold": "Common Cold / Upper Respiratory Infection",
    "rash": "Skin Rash / Allergic Dermatitis",
    "diarrhea": "Diarrhea",
    "vomit": "Nausea and Vomiting",
    "nausea": "Nausea and Vomiting",
    "stomach": "Stomach Pain / Gastritis",
}

CRITICAL_RED_FLAGS = {
    "chest pain": {
        "condition": "Chest Pain — Requires Urgent Evaluation",
        "first_aid": "1. STOP all physical activity and sit down immediately.\n2. If you have prescribed nitroglycerin, take it.\n3. Chew one aspirin (325 mg) unless allergic.\n4. Call emergency services (112 or 108) immediately.\n5. Keep calm and take deep breaths. Do not lie down.",
        "severity": "Critical",
        "doctor_type": "Cardiologist / Emergency Medicine"
    },
    "heart attack": {
        "condition": "Heart Attack — Emergency",
        "first_aid": "1. Call 108 or 112 for an ambulance immediately.\n2. Help the person sit down and stay calm.\n3. Loosen tight clothing.\n4. Chew one aspirin (325 mg) unless allergic.\n5. If they become unconscious and stop breathing, start CPR.",
        "severity": "Critical",
        "doctor_type": "Cardiologist / Emergency Medicine"
    },
    "breathing difficulty": {
        "condition": "Breathing Difficulty — Critical Status",
        "first_aid": "1. Sit upright. Do not lie down.\n2. Loosen tight clothing around neck/chest.\n3. Use prescribed rescue inhaler (salbutamol) if available.\n4. Stay calm and breathe slowly.\n5. Call 112 or 108 immediately if it persists or fingers/lips turn blue.",
        "severity": "Critical",
        "doctor_type": "Pulmonologist / Emergency Medicine"
    },
    "shortness of breath": {
        "condition": "Breathing Difficulty — Critical Status",
        "first_aid": "1. Sit upright. Do not lie down.\n2. Loosen tight clothing around neck/chest.\n3. Use prescribed rescue inhaler (salbutamol) if available.\n4. Stay calm and breathe slowly.\n5. Call 112 or 108 immediately if it persists or fingers/lips turn blue.",
        "severity": "Critical",
        "doctor_type": "Pulmonologist / Emergency Medicine"
    },
    "snake bite": {
        "condition": "Snake Bite — Emergency",
        "first_aid": "1. Call 108 or 112 immediately for anti-venom.\n2. Keep the person calm and completely still.\n3. Immobilize the limb and keep it below heart level.\n4. Do NOT cut the wound or suck the venom.\n5. Do NOT apply ice or tight tourniquets.",
        "severity": "Critical",
        "doctor_type": "Emergency Medicine"
    },
    "stroke": {
        "condition": "Stroke — Emergency",
        "first_aid": "1. Remember F.A.S.T.: Face drooping, Arm weakness, Speech difficulty, Time to call emergency.\n2. Call 112 or 108 immediately.\n3. Note the exact time symptoms started.\n4. Keep the person warm and on their side if they are breathing but unconscious.",
        "severity": "Critical",
        "doctor_type": "Neurologist / Emergency Medicine"
    },
    "choking": {
        "condition": "Choking — Airway Blockage",
        "first_aid": "1. If conscious, perform abdominal thrusts (Heimlich maneuver).\n2. Give 5 back blows followed by 5 abdominal thrusts.\n3. Call 112 or 108 immediately.\n4. If unconscious, start CPR.",
        "severity": "Critical",
        "doctor_type": "Emergency Medicine"
    },
    "poison": {
        "condition": "Poisoning / Chemical Ingestion",
        "first_aid": "1. Call Poison Control or go to ER immediately.\n2. Do NOT induce vomiting unless instructed by professionals.\n3. If skin/eye contact, flush with water for 15 minutes.\n4. Keep the chemical container to show doctors.",
        "severity": "Critical",
        "doctor_type": "Emergency Medicine"
    },
    "heavy bleeding": {
        "condition": "Severe Hemorrhage / Heavy Bleeding",
        "first_aid": "1. Apply firm, direct pressure on the wound with a clean cloth.\n2. Elevate the bleeding limb above the heart.\n3. Do NOT remove the cloth if soaked; add another on top.\n4. Tie a clean cloth/bandage tightly above the wound if bleeding is catastrophic.\n5. Call 108/112.",
        "severity": "High",
        "doctor_type": "General Surgeon / Emergency Medicine"
    },
    "unconscious": {
        "condition": "Unconsciousness / Fainting",
        "first_aid": "1. Check breathing. If breathing, lay them on their back and elevate feet.\n2. If not breathing, start CPR and call 112/108 immediately.\n3. Turn them on their side (recovery position) if vomiting to prevent choking.\n4. Do not give them anything to eat or drink.",
        "severity": "High",
        "doctor_type": "Emergency Medicine"
    }
}

SYNONYMS = {
    "fracture": ["broken", "break", "cracked", "snap"],
    "cut": ["bleed", "bleeding", "wound", "scratch", "slash", "laceration", "rip", "tear"],
    "dog bite": ["bitten by dog", "dog attacked", "rabies"],
    "snake bite": ["bitten by snake", "cobra", "viper"],
    "burn": ["scald", "blister", "charred", "fire", "hot oil", "stove"],
    "stomach pain": ["abdominal pain", "gastritis", "tummy ache", "indigestion", "acid reflux", "belly ache"],
    "fever": ["high temperature", "chills", "hot forehead", "shivering"],
    "seizure": ["fit", "convulsion", "shaking", "foaming", "epilepsy"],
    "choking": ["suffocating", "throat blocked", "blocked airway", "lodged in throat"],
    "allergy": ["hives", "itchy rash", "allergic reaction", "anaphylaxis", "swollen lips"]
}

def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text

def _preprocess_query(query: str) -> set:
    words = _clean_text(query).split()
    stop_words = {"my", "got", "have", "having", "with", "is", "are", "and", "the", "an", "on", "in", "to", "for", "of", "from", "at", "feel", "feeling", "pain", "hurt", "some", "any", "me", "he", "she", "they", "we", "you", "body", "part"}
    processed = {w for w in words if w not in stop_words and len(w) > 1}
    
    expanded = set(processed)
    for key, syns in SYNONYMS.items():
        if any(s in words for s in syns) or (key in _clean_text(query)):
            expanded.add(key)
            for s in key.split():
                expanded.add(s)
    return expanded

def _get_local_fallback(query: str) -> dict:
    """Intelligent fallback symptom analyzer that matches user queries to the local conditions database."""
    if not query:
        return {
            "condition": "Unknown Concern",
            "first_aid": "Please specify symptoms to receive guidance.",
            "severity": "Low",
            "doctor_type": "General Physician"
        }
        
    query_clean = _clean_text(query)
    
    # 1. Check direct critical red flags first
    for flag, response in CRITICAL_RED_FLAGS.items():
        if flag in query_clean:
            return response
            
    # Load conditions database
    conditions_file = DATA_DIR / "conditions.json"
    conditions = []
    if conditions_file.exists():
        try:
            with open(conditions_file, "r") as f:
                conditions = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load conditions.json for fallback: {e}")
            
    if not conditions:
        # Emergency backup if JSON fails to load
        return {
            "condition": "Health Concern — General Assessment",
            "first_aid": "1. Rest and monitor your symptoms closely.\n2. Stay well hydrated.\n3. Take paracetamol for pain or fever.\n4. Call emergency 112 or 108 if symptoms are severe.",
            "severity": "Low",
            "doctor_type": "General Physician"
        }
        
    # 2. Token overlap and scoring
    query_tokens = _preprocess_query(query)
    
    # Apply direct mapping score boosters
    boosted_conditions = {}
    for kw, cond_name in DIRECT_MAPPINGS.items():
        if kw in query_clean:
            boosted_conditions[cond_name] = boosted_conditions.get(cond_name, 0.0) + 5.0
            
    best_match = None
    best_score = -1.0
    
    for c in conditions:
        score = 0.0
        c_name = c.get("condition") or c.get("Condition")
        if not c_name:
            continue
        
        # Add score booster if matched via DIRECT_MAPPINGS
        base_name_clean = re.sub(r"\s*\(.*\)\s*", "", c_name)
        if base_name_clean in boosted_conditions:
            score += boosted_conditions[base_name_clean]
            
        # A. Condition Name Match
        cond_name_lower = c_name.lower()
        base_name_lower = base_name_clean.lower()
        
        if base_name_lower in query_clean:
            score += 3.0
        else:
            name_tokens = set(base_name_lower.split())
            overlap = query_tokens.intersection(name_tokens)
            if overlap:
                score += (len(overlap) / len(name_tokens)) * 1.5
                
        # B. Symptoms Match
        syms_matched = 0
        c_symptoms = c.get("symptoms") or c.get("Symptoms") or []
        total_syms = len(c_symptoms)
        
        for sym in c_symptoms:
            sym_clean = _clean_text(sym)
            sym_tokens = set(sym_clean.split())
            
            overlap = query_tokens.intersection(sym_tokens)
            if len(sym_tokens) > 0:
                overlap_ratio = len(overlap) / len(sym_tokens)
                if overlap_ratio >= 0.5:
                    syms_matched += overlap_ratio
                    
        if total_syms > 0:
            score += (syms_matched / total_syms) * 2.0
            
        # C. De-prioritize variations unless we have an exact mention
        if "(" in c_name:
            body_part_match = False
            match_part = re.search(r"\((.*?)\)", c_name)
            if match_part:
                part_words = set(_clean_text(match_part.group(1)).split())
                if part_words.issubset(query_tokens):
                    score += 0.5
                    body_part_match = True
            if not body_part_match:
                score *= 0.7
                
        if score > best_score:
            best_score = score
            best_match = c
            
    if best_match and best_score > 0.15:
        # Determine severity and check for escalation
        sev = best_match.get("severity") or best_match.get("Severity")
        if sev not in ["Critical", "High"]:
            critical_indicators = ["chest", "breath", "bleed", "broken", "fracture", "bite", "unconscious"]
            if any(ind in query_clean for ind in critical_indicators):
                if "broken" in query_clean or "fracture" in query_clean or "bleed" in query_clean:
                    sev = "High"
                elif "chest" in query_clean or "breath" in query_clean or "bite" in query_clean:
                    sev = "Critical"
                    
        return {
            "condition": best_match.get("condition") or best_match.get("Condition"),
            "first_aid": best_match.get("firstAid") or best_match.get("FirstAid"),
            "severity": sev,
            "doctor_type": best_match.get("doctorType") or best_match.get("DoctorType"),
            "image_prompt": best_match.get("imagePrompt") or best_match.get("image_prompt"),
            "symptoms": best_match.get("symptoms") or best_match.get("Symptoms") or []
        }
        
    # Default fallback with safety assessment if no close match
    default_sev = "Low"
    default_first_aid = (
        "1. Rest and monitor your symptoms closely.\n"
        "2. Stay well hydrated with water, ORS, or clear fluids.\n"
        "3. Take paracetamol (500 mg) if experiencing pain or fever.\n"
        "4. Avoid self-medicating with antibiotics.\n"
        "5. Keep a log of symptoms and consult a General Physician if they persist.\n"
        "6. If you experience difficulty breathing, chest pain, or high fever, seek emergency medical care immediately."
    )
    
    urgent_words = ["pain", "bleed", "head", "vomit", "fever"]
    critical_words = ["chest", "breath", "heart", "stroke", "paralysis", "unconscious", "choke", "poison", "snake"]
    
    if any(w in query_clean for w in critical_words):
        default_sev = "Critical"
        default_first_aid = (
            "⚠️ CRITICAL EMERGENCY HEALTH CONCERN DETECTED.\n\n"
            "1. Sit down, rest, and keep calm.\n"
            "2. CALL EMERGENCY SERVICES (112 or 108) IMMEDIATELY.\n"
            "3. If chest pain/heart concern: Chew one aspirin (325 mg) unless allergic.\n"
            "4. If breathing difficulty: Sit upright, loosen clothing, use rescue inhaler.\n"
            "5. If unconscious: Turn on recovery side, check breathing, start CPR if needed.\n"
            "6. Do NOT try to walk or drive yourself to the hospital."
        )
    elif any(w in query_clean for w in urgent_words):
        default_sev = "High"
        default_first_aid = (
            "⚠️ URGENT HEALTH CONCERN DETECTED.\n\n"
            "1. Rest and try to isolate or stabilize the affected area.\n"
            "2. Clean any wounds with water and apply direct pressure to stop bleeding.\n"
            "3. Monitor temperature and take paracetamol if fever/pain is high.\n"
            "4. Contact a doctor or visit the nearest clinic/hospital as soon as possible.\n"
            "5. If symptoms escalate (difficulty breathing, chest tightness, extreme pain), call emergency 112/108 immediately."
        )
        
    return {
        "condition": "Unidentified Symptoms — Safety Assessment",
        "first_aid": default_first_aid,
        "severity": default_sev,
        "doctor_type": "General Physician",
        "image_prompt": None,
        "symptoms": []
    }



def parse_base64_image(base64_str: str):
    # Match data URI schema: data:image/png;base64,...
    match = re.match(r"^data:(image/\w+);base64,(.*)$", base64_str)
    if match:
        mime_type = match.group(1)
        image_bytes = base64.b64decode(match.group(2))
        return image_bytes, mime_type
    return None, None


# Track API rate limiting to avoid repeated failed calls
_rate_limit_until = 0  # Unix timestamp until which we should skip API calls


async def analyze_symptoms(query: str, image_b64: str = None) -> dict:
    global _rate_limit_until
    
    if client is None:
        logger.info("No Gemini client configured — using local fallback")
        return _get_local_fallback(query)

    # If we know we're rate-limited, skip API calls and use fallback directly
    now = time.time()
    if now < _rate_limit_until:
        remaining = int(_rate_limit_until - now)
        logger.info(f"API rate-limited for {remaining}s more — using local knowledge base")
        result = _get_local_fallback(query)
        result["first_aid"] = result["first_aid"] + "\n\n⚡ Note: This is from our built-in medical knowledge base. AI-powered analysis will resume shortly."
        return result

    try:
        prompt = f"{SYSTEM_PROMPT}\n\nUser Input: {query}"
        contents = []
        
        if image_b64:
            image_bytes, mime_type = parse_base64_image(image_b64)
            if image_bytes and mime_type:
                contents.append(
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type
                    )
                )
        
        contents.append(prompt)
        
        # Models ordered by free-tier quota availability and operational status
        models_to_try = [
            'gemini-3.1-flash-lite',  # Operational with good quota
            'gemini-2.5-flash-lite',  # Operational with good quota
            'gemini-2.0-flash',       # Free-tier backup
            'gemini-2.0-flash-lite',  # Free-tier backup
            'gemini-2.5-flash',       # Free-tier backup
        ]
        
        last_error = None
        for model_name in models_to_try:
            try:
                logger.info(f"Attempting symptom analysis with model: {model_name}")
                
                # Wrap sync API call in asyncio.to_thread with a strict 8s timeout
                # This prevents the Gemini SDK's internal retry delays from blocking
                def _call_model(mn=model_name, ct=contents):
                    return client.models.generate_content(
                        model=mn,
                        contents=ct,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(_call_model),
                    timeout=8.0  # Max 8 seconds per model attempt
                )
                text = response.text.strip()
                parsed = json.loads(text)
                logger.info(f"✅ Successfully analyzed with model: {model_name}")
                # Clear rate limit on success
                _rate_limit_until = 0
                # Normalize keys on return
                return {
                    "condition": parsed.get("condition") or parsed.get("Condition") or "Unknown",
                    "first_aid": parsed.get("first_aid") or parsed.get("FirstAid") or "Not available",
                    "severity": parsed.get("severity") or parsed.get("Severity") or "Unknown",
                    "doctor_type": parsed.get("doctor_type") or parsed.get("DoctorType") or "General Physician",
                    "image_prompt": parsed.get("image_prompt") or parsed.get("imagePrompt") or parsed.get("ImagePrompt"),
                    "symptoms": parsed.get("symptoms") or parsed.get("Symptoms") or []
                }
            except asyncio.TimeoutError:
                logger.warning(f"Model {model_name} timed out (8s) — trying next")
                continue
            except Exception as model_err:
                error_str = str(model_err)
                logger.warning(f"Model {model_name} failed: {error_str[:200]}")
                last_error = model_err
                
                # If rate limited, try next model immediately without delay
                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    continue
                # For other errors, also try next model
                continue
        
        # All Gemini models failed — try OpenRouter before falling back to local engine
        logger.warning("All Gemini models exhausted — trying OpenRouter fallback…")
        _rate_limit_until = time.time() + 60  # Cool down Gemini for 60s

        if _openrouter_analyze and settings.OPENROUTER_API_KEY:
            try:
                or_result = await _openrouter_analyze(query, image)
                if or_result and or_result.get("condition"):
                    logger.info("[OpenRouter] Fallback succeeded: condition=%s", or_result.get("condition"))
                    or_result["first_aid"] = (
                        or_result.get("first_aid", "") +
                        "\n\n⚡ Note: Analysis provided by OpenRouter free AI model."
                    )
                    return or_result
            except Exception as or_err:
                logger.error("[OpenRouter] Fallback also failed: %s", or_err)

        # Final fallback: local keyword engine
        logger.warning("All AI providers failed — using local fallback engine")
        result = _get_local_fallback(query)
        result["first_aid"] = result["first_aid"] + "\n\n⚡ Note: This guidance is from our built-in medical knowledge base. AI-powered analysis will resume shortly."
        return result

    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        # Try OpenRouter before local fallback
        if _openrouter_analyze and settings.OPENROUTER_API_KEY:
            try:
                or_result = await _openrouter_analyze(query, image)
                if or_result and or_result.get("condition"):
                    return or_result
            except Exception:
                pass
        return _get_local_fallback(query)
