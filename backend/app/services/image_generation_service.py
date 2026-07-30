import httpx
import urllib.parse
import hashlib
import logging
import re
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

import os as _os
if _os.environ.get("VERCEL"):
    CACHE_DIR = Path("/tmp/image_cache")
else:
    CACHE_DIR = Path("app/data/image_cache")
try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    CACHE_DIR = Path("/tmp/image_cache")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def generate_step_prompt(condition: str, step_text: str) -> str:
    """
    Generate a highly detailed medical illustration prompt based on the specific first aid action.
    """
    clean_step = step_text.strip()
    clean_step = re.sub(r'^\d+[\.\)]\s*', '', clean_step)
    clean_step = re.sub(r'^[\-\*]\s*', '', clean_step)
    
    cond_lower = condition.lower()
    step_lower = clean_step.lower()
    
    # Default visual action description
    action_desc = f"a person correctly performing the action: {clean_step}"
    
    # 1. Burns
    if "burn" in cond_lower:
        if any(w in step_lower for w in ["cool", "running water", "water", "tap", "rinse"]):
            action_desc = "a person placing a burned hand under cool running water"
        elif any(w in step_lower for w in ["ring", "jewelry", "watch", "remove", "tight"]):
            action_desc = "a person gently removing a ring from a swollen burned finger"
        elif any(w in step_lower for w in ["cover", "sterile dressing", "bandage", "dressing", "gauze"]):
            action_desc = "correct sterile dressing application over a burn wound on the arm"
            
    # 2. Snake Bite
    elif "snake" in cond_lower:
        if any(w in step_lower for w in ["calm", "still", "reassure", "rest"]):
            action_desc = "a snake bite victim lying calmly while another person reassures them"
        elif any(w in step_lower for w in ["call", "emergency", "ambulance", "112", "108", "services"]):
            action_desc = "a person calling emergency services after a snake bite incident"
        elif any(w in step_lower for w in ["below", "heart", "level", "limb"]):
            action_desc = "a victim keeping the bitten leg below heart level after a snake bite"
            
    # 3. Choking
    elif "chok" in cond_lower:
        if any(w in step_lower for w in ["heimlich", "thrust", "abdominal"]):
            action_desc = "the Heimlich maneuver abdominal thrusts on a standing adult from behind"
        elif any(w in step_lower for w in ["back", "blow"]):
            action_desc = "a person giving 5 firm back blows between the shoulder blades of a choking victim"
            
    # 4. Fracture / Broken bone
    elif any(w in cond_lower for w in ["fracture", "broken", "sprain"]):
        if any(w in step_lower for w in ["splint", "sling", "immobilize"]):
            action_desc = "correct immobilization of a fractured arm using a splint and secure bandages"
        elif any(w in step_lower for w in ["ice", "cold", "compress"]):
            action_desc = "a cold compress wrapped in a towel applied gently to an injured arm"
        elif any(w in step_lower for w in ["elevate", "raise", "pillow"]):
            action_desc = "a fractured arm elevated comfortably on soft pillows"
            
    # 5. Heart Attack / Chest Pain
    elif any(w in cond_lower for w in ["heart", "cardiac", "chest pain"]):
        if any(w in step_lower for w in ["call", "emergency", "ambulance"]):
            action_desc = "a person dialing emergency services on a phone in a medical situation"
        elif any(w in step_lower for w in ["aspirin", "chew", "tablet"]):
            action_desc = "a person chewing a 325mg aspirin tablet"
        elif any(w in step_lower for w in ["sit", "rest", "loosen"]):
            action_desc = "a person sitting upright comfortably, loosening a shirt collar to assist breathing"
        elif any(w in step_lower for w in ["cpr", "compressions"]):
            action_desc = "hands performing CPR chest compressions on the chest torso of a mannequin"
            
    # 6. Bleeding / Wound
    elif any(w in cond_lower for w in ["bleed", "cut", "wound", "laceration"]):
        if any(w in step_lower for w in ["pressure", "apply", "firm"]):
            action_desc = "a hand applying a clean sterile gauze pad with firm pressure to a bleeding wound"
        elif any(w in step_lower for w in ["clean", "wash", "rinse", "water"]):
            action_desc = "a minor cut wound on a hand being washed gently under clean running water"
        elif any(w in step_lower for w in ["bandage", "cover", "dress"]):
            action_desc = "an adhesive bandage being applied carefully over a clean cut wound"
            
    # 7. Seizure
    elif "seizure" in cond_lower or "convulsion" in cond_lower:
        if any(w in step_lower for w in ["head", "cushion", "pillow", "soft"]):
            action_desc = "a person lying down with a soft folded jacket cushioning their head during a seizure"
        elif any(w in step_lower for w in ["side", "turn", "recovery"]):
            action_desc = "a person turned onto their side in the recovery position to keep airway clear"
            
    # 8. Poisoning
    elif "poison" in cond_lower:
        if "vomit" in step_lower:
            action_desc = "a poison warning label on a chemical container next to a phone calling poison control"
        elif any(w in step_lower for w in ["flush", "rinse", "water"]):
            action_desc = "a person rinsing a chemical spill from their skin under running water"
            
    # 9. Fever / Cold / Cough
    elif any(w in cond_lower for w in ["fever", "cold", "cough", "infection"]):
        if any(w in step_lower for w in ["compress", "damp", "forehead"]):
            action_desc = "a person resting with a cool damp cloth applied on their forehead"
        elif any(w in step_lower for w in ["hydrate", "drink", "water", "fluid", "tea"]):
            action_desc = "a person drinking warm tea or water from a cup to stay hydrated"
            
    # 10. Gastrointestinal (Stomach pain, nausea, diarrhea)
    elif any(w in cond_lower for w in ["stomach", "gastritis", "nausea", "diarrhea"]):
        if any(w in step_lower for w in ["ors", "fluid", "rehydrate"]):
            action_desc = "ORS oral rehydration salt packets next to a glass of clean water"
        elif any(w in step_lower for w in ["warm", "compress", "abdomen", "heat"]):
            action_desc = "a warm heating pad applied to the abdomen of a person resting"
            
    # 11. Eye irritation
    elif "eye" in cond_lower:
        if any(w in step_lower for w in ["flush", "rinse", "wash"]):
            action_desc = "clean water streams from an eyewash bottle gently rinsing an eye"

    prompt = (
        "3D animated educational medical illustration.\n"
        f"Show a person correctly performing this first aid action: {action_desc}.\n"
        "Pixar style.\n"
        "Healthcare training animation.\n"
        "Friendly characters.\n"
        "Clear visual explanation.\n"
        "Medical education poster.\n"
        "Highly detailed.\n"
        "Colorful.\n"
        "Professional healthcare infographic.\n"
        "No text overlay.\n"
        "High resolution."
    )
    return prompt

async def get_flux_image_for_step(condition: str, step_text: str, step_num: int) -> str:
    """Generate prompt, query FLUX Schnell via Pollinations, and cache image locally on disk."""
    prompt = generate_step_prompt(condition, step_text)
    prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
    cache_path = CACHE_DIR / f"{prompt_hash}.jpg"
    
    # Base URL for the backend API
    API_URL = "http://localhost:8000"
    
    # Return path to cache if file already exists
    if cache_path.exists():
        return f"{API_URL}/api/analyze/image-file/{prompt_hash}"
        
    try:
        # Generate with deterministic seed for stable results
        seed = step_num * 100 + 42
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true&model=flux&seed={seed}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(3):  # Try up to 3 times
                try:
                    # Stagger requests to avoid triggering 429 Rate Limits
                    if attempt == 0:
                        await asyncio.sleep((step_num - 1) * 3.0)
                    else:
                        # Backoff sleep on retry
                        await asyncio.sleep(4.0 * attempt)
                        
                    # On 3rd attempt, fallback to 'turbo' (SDXL) model to guarantee success
                    current_model = "flux" if attempt < 2 else "turbo"
                    encoded_prompt = urllib.parse.quote(prompt)
                    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true&model={current_model}&seed={seed}"
                    
                    response = await client.get(url)
                    if response.status_code == 200:
                        cache_path.write_bytes(response.content)
                        logger.info(f"Generated and cached {current_model} image for '{condition}' Step {step_num}")
                        return f"{API_URL}/api/analyze/image-file/{prompt_hash}"
                    elif response.status_code == 429:
                        logger.warning(f"Pollinations.ai returned 429 Too Many Requests. Model: {current_model}, Attempt {attempt+1}")
                    else:
                        logger.warning(f"Pollinations.ai attempt {attempt+1} returned status {response.status_code}")
                except Exception as e:
                    logger.warning(f"Pollinations.ai attempt {attempt+1} failed: {e}")
    except Exception as e:
        logger.error(f"Failed to generate FLUX image: {e}")
        
    # Standard placeholder image path if generation fails
    return f"{API_URL}/api/analyze/step-image-fallback?condition={urllib.parse.quote(condition)}&step_num={step_num}"
