import json
import copy
import re

conditions_base = [
    # Burns & Injuries
    {
        "cond": "First-degree Burn", 
        "sym": ["Redness", "Pain", "Minor swelling"], 
        "fa": "Cool the burn under cool (not cold) running water for 10-15 minutes. Apply aloe vera.", 
        "sev": "Low", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing cooling a minor {body_part} burn under clean running water, flat vector style, dark slate blue background"
    },
    {
        "cond": "Second-degree Burn", 
        "sym": ["Blisters", "Deep redness", "Pain", "Swelling"], 
        "fa": "Cool the burn. Do not break blisters. Loosely cover with a sterile, non-stick bandage.", 
        "sev": "Medium", 
        "doc": "Dermatologist",
        "prompt_template": "Medical first aid illustration showing a sterile non-stick bandage loosely covered over a {body_part} burn, flat vector style, dark slate blue background"
    },
    {
        "cond": "Third-degree Burn", 
        "sym": ["Charred skin", "White/leathery skin", "Numbness"], 
        "fa": "Call emergency immediately. Do not remove stuck clothing. Cover loosely with sterile cloth.", 
        "sev": "Critical", 
        "doc": "Emergency Medicine",
        "prompt_template": "Medical first aid illustration showing emergency rescue blankets and sterile dressing for a severe {body_part} burn, flat vector style, dark slate blue background"
    },
    {
        "cond": "Sprained Ankle", 
        "sym": ["Swelling", "Pain", "Bruising", "Inability to bear weight"], 
        "fa": "Rest, Ice, Compression, Elevation (R.I.C.E.). Avoid putting weight on it.", 
        "sev": "Low", 
        "doc": "Orthopedic",
        "prompt_template": "Medical first aid illustration showing rest, ice, compression, and elevation (RICE) for a sprained ankle, flat vector style, dark slate blue background"
    },
    {
        "cond": "Broken Arm", 
        "sym": ["Severe pain", "Deformity", "Swelling", "Inability to move"], 
        "fa": "Immobilize the arm with a splint or sling. Apply ice pack wrapped in cloth. Seek medical help.", 
        "sev": "High", 
        "doc": "Orthopedic",
        "prompt_template": "Medical first aid illustration showing immobilization of an injured arm using a splint and sling, flat vector style, dark slate blue background"
    },
    {
        "cond": "Broken Leg", 
        "sym": ["Severe pain", "Deformity", "Swelling", "Inability to stand or bear weight"], 
        "fa": "Immobilize the leg using splints. Keep completely still. Call emergency for transport.", 
        "sev": "High", 
        "doc": "Orthopedic",
        "prompt_template": "Medical first aid illustration showing immobilization of an injured leg using leg splints, flat vector style, dark slate blue background"
    },
    
    # Critical Emergencies
    {
        "cond": "Heart Attack", 
        "sym": ["Chest pain", "Shortness of breath", "Cold sweat", "Nausea", "Pain in arm/jaw"], 
        "fa": "Call ambulance immediately. Have the person sit down, rest, and keep calm. Loosen tight clothing. If conscious and not allergic, give aspirin.", 
        "sev": "Critical", 
        "doc": "Cardiologist",
        "prompt_template": "Medical first aid illustration showing a person with chest pain sitting down, loosening collar, and chewing an aspirin tablet, flat vector style, dark slate blue background"
    },
    {
        "cond": "Stroke", 
        "sym": ["Face drooping", "Arm weakness", "Speech difficulty", "Sudden numbness"], 
        "fa": "F.A.S.T. (Face, Arms, Speech, Time). Call emergency immediately. Note the time symptoms started.", 
        "sev": "Critical", 
        "doc": "Neurologist",
        "prompt_template": "Medical stroke assessment infographic demonstrating Face drooping, Arm weakness, and Speech difficulty checks, flat vector style, dark slate blue background"
    },
    {
        "cond": "Asthma Attack", 
        "sym": ["Severe shortness of breath", "Chest tightness", "Wheezing", "Coughing"], 
        "fa": "Sit the person upright. Help them use their inhaler (blue reliever). Call emergency if it doesn't improve in 5 minutes.", 
        "sev": "High", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing a person sitting upright and using a blue asthma rescue inhaler puff, flat vector style, dark slate blue background"
    },
    {
        "cond": "Severe Allergic Reaction (Anaphylaxis)", 
        "sym": ["Swelling of face/throat", "Difficulty breathing", "Hives", "Dizziness"], 
        "fa": "Administer epinephrine auto-injector (EpiPen) if available. Call emergency immediately. Lay them flat.", 
        "sev": "Critical", 
        "doc": "Emergency Medicine",
        "prompt_template": "Medical first aid illustration showing administration of an epinephrine auto-injector EpiPen in the outer thigh, flat vector style, dark slate blue background"
    },
    {
        "cond": "Mild Cut/Laceration", 
        "sym": ["Bleeding", "Pain at the site"], 
        "fa": "Wash hands. Stop bleeding with gentle pressure. Clean with water. Apply antibiotic ointment and a bandage.", 
        "sev": "Low", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing washing hands and applying an adhesive bandage to a minor cut on {body_part}, flat vector style, dark slate blue background"
    },
    {
        "cond": "Deep Cut/Laceration", 
        "sym": ["Heavy bleeding", "Gaping wound", "Exposed fat/muscle"], 
        "fa": "Apply firm, direct pressure with a clean cloth. Do not remove object if impaled. Seek emergency care.", 
        "sev": "High", 
        "doc": "Emergency Medicine",
        "prompt_template": "Medical first aid illustration showing sterile gauze applying firm direct pressure to a bleeding wound on {body_part}, flat vector style, dark slate blue background"
    },
    {
        "cond": "Snake Bite", 
        "sym": ["Puncture marks", "Pain", "Swelling", "Nausea", "Breathing difficulty"], 
        "fa": "Keep the person calm and still. Keep the bite area below heart level. Remove tight clothing/jewelry. Do NOT suck venom or apply tourniquet. Call emergency.", 
        "sev": "Critical", 
        "doc": "Emergency Medicine",
        "prompt_template": "Medical first aid illustration showing a snake bite puncture wound on {body_part} kept immobilized below heart level, flat vector style, dark slate blue background"
    },
    {
        "cond": "Dog Bite", 
        "sym": ["Puncture wound", "Bleeding", "Pain"], 
        "fa": "Wash wound gently with soap and water. Apply pressure to stop bleeding. Apply sterile bandage. See a doctor for rabies/tetanus evaluation.", 
        "sev": "Medium", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing gentle washing of a dog bite wound on {body_part} with soap and water, flat vector style, dark slate blue background"
    },
    {
        "cond": "Heat Stroke", 
        "sym": ["High body temperature", "Hot/dry skin", "Confusion", "Unconsciousness"], 
        "fa": "Call emergency. Move to a cool place. Cool the person rapidly with water, ice packs, or wet towels. Do not give fluids to drink.", 
        "sev": "Critical", 
        "doc": "Emergency Medicine",
        "prompt_template": "Medical first aid illustration showing a person being cooled with wet towels and ice packs, flat vector style, dark slate blue background"
    },
    {
        "cond": "Heat Exhaustion", 
        "sym": ["Heavy sweating", "Weakness", "Dizziness", "Nausea", "Headache"], 
        "fa": "Move to a cooler place. Loosen clothing. Sip cool water. Seek medical help if symptoms worsen or last > 1 hour.", 
        "sev": "Medium", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing a person resting in a cool shadow and sipping water, flat vector style, dark slate blue background"
    },
    {
        "cond": "Hypothermia", 
        "sym": ["Shivering", "Slurred speech", "Slow breathing", "Confusion"], 
        "fa": "Move gently to a warm place. Remove wet clothing. Warm the center of the body first with blankets. Give warm beverages if conscious.", 
        "sev": "Critical", 
        "doc": "Emergency Medicine",
        "prompt_template": "Medical first aid illustration showing a person wrapped in warm blankets sipping warm tea, flat vector style, dark slate blue background"
    },
    {
        "cond": "Frostbite", 
        "sym": ["Cold skin", "Prickling feeling", "Numbness", "Discolored skin (white/gray/yellow)"], 
        "fa": "Get into a warm room. Soak in warm (not hot) water. Do not rub the affected area. Seek medical attention.", 
        "sev": "Medium", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing frozen frostbitten fingers being warmed in warm water, flat vector style, dark slate blue background"
    },
    {
        "cond": "Seizure", 
        "sym": ["Uncontrollable jerking movements", "Loss of awareness", "Confusion"], 
        "fa": "Keep them safe from injury. Cushion their head. Loosen tight clothing around neck. Turn on side. Do NOT put anything in mouth. Time the seizure.", 
        "sev": "High", 
        "doc": "Neurologist",
        "prompt_template": "Medical first aid illustration showing a person on their side with a pillow under their head during a seizure, flat vector style, dark slate blue background"
    },
    {
        "cond": "Poisoning", 
        "sym": ["Nausea/Vomiting", "Burns around mouth", "Difficulty breathing", "Drowsiness"], 
        "fa": "Call Poison Control immediately. Do NOT induce vomiting unless instructed. Gather pill bottles/containers for information.", 
        "sev": "Critical", 
        "doc": "Emergency Medicine",
        "prompt_template": "Medical first aid illustration showing a poison chemical bottle and an emergency phone call to Poison Control, flat vector style, dark slate blue background"
    },
    {
        "cond": "Choking", 
        "sym": ["Inability to talk", "Difficulty breathing", "Blue lips/skin", "Holding neck"], 
        "fa": "Perform Heimlich maneuver (abdominal thrusts). If unconscious, start CPR and call emergency.", 
        "sev": "Critical", 
        "doc": "Emergency Medicine",
        "prompt_template": "Medical first aid illustration demonstrating Heimlich maneuver abdominal thrusts on an adult, flat vector style, dark slate blue background"
    },
    {
        "cond": "Tension Headache / Possible Migraine", 
        "sym": ["Throbbing head pain", "Sensitivity to light/sound", "Neck stiffness", "Dizziness"], 
        "fa": "Rest in a quiet, dark room. Apply a cold or warm compress to forehead. Take over-the-counter pain relievers like paracetamol (500mg) or ibuprofen.", 
        "sev": "Low", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing a person resting in a dark room with a cool compress on forehead, flat vector style, dark slate blue background"
    },
    {
        "cond": "Fever — Possible Viral or Bacterial Infection", 
        "sym": ["High body temperature", "Chills", "Shivering", "Body aches", "Fatigue"], 
        "fa": "Rest in a ventilated room. Drink plenty of fluids (water, coconut water, ORS). Take paracetamol every 6 hours. Use a damp cloth to cool forehead.", 
        "sev": "Medium", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing a person resting with a damp cloth on forehead and a glass of water, flat vector style, dark slate blue background"
    },
    {
        "cond": "Common Cold / Upper Respiratory Infection", 
        "sym": ["Runny nose", "Sore throat", "Congestion", "Sneezing", "Mild headache"], 
        "fa": "Stay hydrated with warm water, ginger tea, or broth. Steam inhale 2-3 times daily. Gargle with warm salt water. Use saline nasal drops.", 
        "sev": "Low", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing a person drinking warm ginger tea and inhaling steam, flat vector style, dark slate blue background"
    },
    {
        "cond": "Cough — Upper Respiratory Concern", 
        "sym": ["Dry or wet cough", "Throat irritation", "Mild chest congestion"], 
        "fa": "Sip warm liquids with honey. Steam inhale. Take cough syrup (expectorant for wet, suppressant for dry). See doctor if cough lasts > 2 weeks.", 
        "sev": "Low", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing warm liquids with honey and steam inhalation, flat vector style, dark slate blue background"
    },
    {
        "cond": "Stomach Pain / Gastritis", 
        "sym": ["Abdominal pain", "Burning sensation in stomach", "Bloating", "Acid reflux"], 
        "fa": "Avoid solid food for a few hours. Take an antacid or omeprazole. Apply warm compress to abdomen. Eat light, bland foods (rice, toast).", 
        "sev": "Medium", 
        "doc": "Gastroenterologist",
        "prompt_template": "Medical first aid illustration showing a warm compress applied to the abdomen, flat vector style, dark slate blue background"
    },
    {
        "cond": "Nausea and Vomiting", 
        "sym": ["Nausea", "Vomiting", "Inability to keep food down", "Weakness"], 
        "fa": "Sip small amounts of water, ORS, or coconut water. Take ondansetron if prescribed. Avoid dairy, oily, or spicy foods.", 
        "sev": "Medium", 
        "doc": "Gastroenterologist",
        "prompt_template": "Medical first aid illustration showing a person sipping ORS solution and resting, flat vector style, dark slate blue background"
    },
    {
        "cond": "Diarrhea", 
        "sym": ["Loose or watery stools", "Abdominal cramps", "Dehydration risk", "Weakness"], 
        "fa": "Drink ORS solution after every loose motion to prevent dehydration. Eat bananas, rice, applesauce, toast (BRAT diet). Avoid dairy and caffeine.", 
        "sev": "Medium", 
        "doc": "General Physician",
        "prompt_template": "Medical first aid illustration showing ORS drink packets and a glass of water, flat vector style, dark slate blue background"
    },
    {
        "cond": "Skin Rash / Allergic Dermatitis", 
        "sym": ["Redness", "Itching", "Hives", "Dry/flaky skin"], 
        "fa": "Apply calamine lotion or hydrocortisone cream. Take cetirizine (10mg) for itching. Wear loose cotton clothes and avoid scratching.", 
        "sev": "Low", 
        "doc": "Dermatologist",
        "prompt_template": "Medical first aid illustration showing calamine lotion application on an itchy skin rash, flat vector style, dark slate blue background"
    },
    {
        "cond": "Eye Irritation / Pink Eye", 
        "sym": ["Red eyes", "Itching", "Watery discharge", "Burning sensation"], 
        "fa": "Do not rub eyes. Flush with clean lukewarm water. Use lubricating artificial tears. Seek ophthalmologist if vision is blurry or painful.", 
        "sev": "Low", 
        "doc": "Ophthalmologist",
        "prompt_template": "Medical first aid illustration showing flushing a red eye with clean water streams, flat vector style, dark slate blue background"
    },
    {
        "cond": "Blood Sugar Concern (Diabetes)", 
        "sym": ["Extreme thirst", "Frequent urination", "Shaking", "Sweating", "Confusion"], 
        "fa": "If low sugar (<70 mg/dL): Consume 15g fast sugar (juice, sugar water, candy). If high (>250 mg/dL): Drink water, take insulin if prescribed.", 
        "sev": "Medium", 
        "doc": "Endocrinologist",
        "prompt_template": "Medical first aid illustration showing a glass of fruit juice and candies for low blood sugar, flat vector style, dark slate blue background"
    },
    {
        "cond": "Blood Pressure Concern", 
        "sym": ["Dizziness", "Headache", "Blurred vision", "Palpitations"], 
        "fa": "Sit down immediately and rest. Take deep, slow breaths. Avoid salt and caffeine. If BP is extremely high (>180/120) with chest pain, call 112.", 
        "sev": "Medium", 
        "doc": "Cardiologist",
        "prompt_template": "Medical first aid illustration showing a person resting and breathing deeply with a blood pressure monitor, flat vector style, dark slate blue background"
    },
    {
        "cond": "Back Pain — Musculoskeletal", 
        "sym": ["Lower back pain", "Muscle stiffness", "Difficulty bending"], 
        "fa": "Apply ice pack for first 48 hours, then switch to heat. Take ibuprofen for pain/inflammation. Lie flat on a firm mattress.", 
        "sev": "Low", 
        "doc": "Orthopedic",
        "prompt_template": "Medical first aid illustration showing an ice pack applied to the lower back while lying flat, flat vector style, dark slate blue background"
    },
    {
        "cond": "Toothache", 
        "sym": ["Severe tooth pain", "Jaw swelling", "Sensitivity to hot or cold"], 
        "fa": "Rinse mouth with warm salt water. Apply clove oil on cotton to the tooth. Take ibuprofen for pain. See a dentist.", 
        "sev": "Low", 
        "doc": "Dentist",
        "prompt_template": "Medical first aid illustration showing warm salt water rinse and clove oil application, flat vector style, dark slate blue background"
    }
]

generated_conditions = []
id_counter = 1

# List of body parts and modifiers for variations
body_parts = ["Hand", "Arm", "Leg", "Foot", "Head", "Face", "Chest", "Back", "Shoulder", "Knee"]
modifiers = ["Left", "Right", "Upper", "Lower", "Inner", "Outer", "Side", "Back", "Front"]

used_names = set()

# First, add all the base conditions
for base in conditions_base:
    c = {}
    c["id"] = id_counter
    c["condition"] = base["cond"]
    c["symptoms"] = base["sym"]
    c["firstAid"] = base["fa"]
    c["severity"] = base["sev"]
    c["doctorType"] = base["doc"]
    
    # Format the prompt with a default body part
    c["imagePrompt"] = base["prompt_template"].format(body_part="body part")
    
    generated_conditions.append(c)
    used_names.add(c["condition"])
    id_counter += 1

# Generate variations until we hit 100 conditions
base_index = 0
modifier_index = 0
body_part_index = 0

while len(generated_conditions) < 100:
    base = conditions_base[base_index % len(conditions_base)]
    part = body_parts[body_part_index % len(body_parts)]
    mod = modifiers[modifier_index % len(modifiers)]
    
    # Create a unique name
    cond_name = f"{base['cond']} ({mod} {part})"
    if cond_name not in used_names:
        c2 = {}
        c2["id"] = id_counter
        c2["condition"] = cond_name
        c2["symptoms"] = [f"{s} in {mod.lower()} {part.lower()}" if "pain" in s.lower() or "ache" in s.lower() else s for s in base["sym"]]
        c2["firstAid"] = base["fa"]
        c2["severity"] = base["sev"]
        c2["doctorType"] = base["doc"]
        
        # Format the prompt with the specific body part variation
        body_spec = f"{mod.lower()} {part.lower()}"
        c2["imagePrompt"] = base["prompt_template"].format(body_part=body_spec)
        
        generated_conditions.append(c2)
        used_names.add(cond_name)
        id_counter += 1

    # Advance indexes
    body_part_index += 1
    if body_part_index % len(body_parts) == 0:
        modifier_index += 1
    base_index += 1

with open('app/data/conditions.json', 'w') as f:
    json.dump(generated_conditions, f, indent=2)

print(f"Generated {len(generated_conditions)} unique conditions in app/data/conditions.json")
