import os
import sys
import asyncio
import json
import base64
import random
from pathlib import Path
import streamlit as st

# Setup python path so app modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

# Import backend services
from backend.app.services.gemini_service import analyze_symptoms
from backend.app.services.image_generation_service import generate_step_prompt, get_flux_image_for_step
from backend.app.services.sdxl_service import generate_sdxl_image
from backend.app.services.map_service import geocode_query, find_nearby_hospitals
from backend.app.services.fda_service import search_drug
from backend.app.services.disease_service import get_global_stats
from backend.app.services.country_service import get_country_info, get_emergency_numbers
from backend.app.services.data_service import load_emergency_contacts, DATA_DIR

# Folium integration for hospital maps
import folium
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(
    page_title="MediAssist AI — Multimodal Health Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme aesthetic
st.markdown("""
<style>
    /* Dark glassmorphism container styling */
    .stApp {
        background-color: #020617;
        color: #f8fafc;
    }
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .badge-critical {
        background-color: rgba(244, 63, 94, 0.15);
        color: #f43f5e;
        border: 1px solid rgba(244, 63, 94, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-high {
        background-color: rgba(249, 115, 22, 0.15);
        color: #f97316;
        border: 1px solid rgba(249, 115, 22, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-medium {
        background-color: rgba(234, 179, 8, 0.15);
        color: #eab308;
        border: 1px solid rgba(234, 179, 8, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-low {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 13px;
    }
    .step-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Helper for async execution in Streamlit
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# Health Quotes
HEALTH_QUOTES = [
    {"content": "The greatest wealth is health.", "author": "Virgil"},
    {"content": "Health is not valued till sickness comes.", "author": "Thomas Fuller"},
    {"content": "To keep the body in good health is a duty... otherwise we shall not be able to keep our mind strong and clear.", "author": "Buddha"},
    {"content": "It is health that is real wealth and not pieces of gold and silver.", "author": "Mahatma Gandhi"},
    {"content": "Early to bed and early to rise makes a man healthy, wealthy, and wise.", "author": "Benjamin Franklin"}
]

# Initialize Session State
if "page" not in st.session_state:
    st.session_state["page"] = "🏠 Home"
if "analyzer_query" not in st.session_state:
    st.session_state["analyzer_query"] = ""
if "analyzer_image_b64" not in st.session_state:
    st.session_state["analyzer_image_b64"] = None
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

pages = ["🏠 Home", "🩺 AI Symptom Analyzer", "🏥 Hospital Finder", "💊 Drug Lookup", "📖 First Aid Guide", "📞 Emergency Contacts"]
current_page = st.session_state.get("page", "🏠 Home")
if current_page not in pages:
    current_page = "🏠 Home"

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/color/96/medical-heart.png", width=60)
st.sidebar.title("MediAssist AI")
st.sidebar.caption("Intelligent Multimodal Health Assistant")

selected_page = st.sidebar.radio(
    "Navigation",
    pages,
    index=pages.index(current_page)
)

st.session_state["page"] = selected_page


# -----------------------------------------------------------------------------
# 🏠 HOME PAGE
# -----------------------------------------------------------------------------
if selected_page == "🏠 Home":
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <span style="background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); padding: 4px 16px; border-radius: 9999px; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">
            AI Healthcare Companion
        </span>
        <h1 style="font-size: 2.8rem; font-weight: 800; margin-top: 16px; margin-bottom: 8px;">
            Your Intelligent Shield in <br/>
            <span style="background: linear-gradient(to right, #3b82f6, #10b981, #14b8a6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Medical Situations
            </span>
        </h1>
        <p style="color: #94a3b8; max-width: 600px; margin: 0 auto; font-size: 1rem;">
            MediAssist AI combines generative intelligence with location-aware search to give you fast, reliable first aid information and connect you with local medical care.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Symptom Input Box
    st.markdown("### 🔍 Quick Symptom Check")
    with st.form("home_symptom_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            home_query = st.text_input(
                "Describe your symptoms",
                placeholder="e.g. severe burn on hand, chest tightness, fever and cold...",
                label_visibility="collapsed"
            )
        with col2:
            home_uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

        submit_home = st.form_submit_button("⚡ Analyze Symptoms Now", use_container_width=True, type="primary")
        
        if submit_home:
            if home_query or home_uploaded_file:
                st.session_state.analyzer_query = home_query
                if home_uploaded_file:
                    bytes_data = home_uploaded_file.getvalue()
                    mime = home_uploaded_file.type
                    b64 = base64.b64encode(bytes_data).decode("utf-8")
                    st.session_state.analyzer_image_b64 = f"data:{mime};base64,{b64}"
                else:
                    st.session_state.analyzer_image_b64 = None
                
                st.session_state.page = "🩺 AI Symptom Analyzer"
                st.rerun()
            else:
                st.warning("Please enter a text description or upload a photo.")

    # Global Health Tracker Widget
    st.markdown("---")
    st.markdown("#### 🌐 Global Health Tracker")
    stats = run_async(get_global_stats())
    if stats and "cases" in stats:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Cases", f"{stats.get('cases', 0):,}")
        c2.metric("Active Cases", f"{stats.get('active', 0):,}")
        c3.metric("Recovered", f"{stats.get('recovered', 0):,}")
        c4.metric("Today's Cases", f"{stats.get('todayCases', 0):,}")
    else:
        st.info("Live global health metrics temporarily updating.")

    # Quote Widget
    q = random.choice(HEALTH_QUOTES)
    st.info(f"💬 *\"{q['content']}\"* — **{q['author']}**")

    # Critical Disclaimer
    st.error("🚨 **Critical Medical Notice**: MediAssist AI provides general first-aid guidance and hospital directories. It is **not** a substitute for professional medical advice, diagnosis, or emergency rescue. In serious medical emergencies, please call **112** or **108** immediately.")


# -----------------------------------------------------------------------------
# 🩺 AI SYMPTOM ANALYZER PAGE
# -----------------------------------------------------------------------------
elif selected_page == "🩺 AI Symptom Analyzer":
    st.title("🩺 AI Symptom Analyzer & Multimodal Diagnostic Assistant")
    st.caption("Powered by Google Gemini 2.0 / 3.1 & OpenRouter Multi-Model Fallback Chain")

    with st.form("analyzer_form"):
        query = st.text_area(
            "Describe your symptoms in detail:",
            value=st.session_state.analyzer_query,
            placeholder="e.g., I accidentally spilled hot boiling water on my forearm. The skin is red and blistering...",
            height=100
        )
        uploaded_image = st.file_uploader("Upload an image of the affected area (optional):", type=["jpg", "jpeg", "png"])
        
        analyze_btn = st.form_submit_button("🚀 Run AI Symptom Analysis", type="primary", use_container_width=True)

    if analyze_btn or (st.session_state.analyzer_query and st.session_state.analysis_result is None):
        if not query and not uploaded_image and not st.session_state.analyzer_image_b64:
            st.warning("Please enter your symptoms or upload an image to analyze.")
        else:
            image_b64 = None
            if uploaded_image:
                bytes_data = uploaded_image.getvalue()
                mime = uploaded_image.type
                b64 = base64.b64encode(bytes_data).decode("utf-8")
                image_b64 = f"data:{mime};base64,{b64}"
            elif st.session_state.analyzer_image_b64:
                image_b64 = st.session_state.analyzer_image_b64

            with st.spinner("Analyzing symptoms with AI models & evaluating first aid steps..."):
                result = run_async(analyze_symptoms(query or st.session_state.analyzer_query, image_b64))
                st.session_state.analysis_result = result
                st.session_state.analyzer_query = ""
                st.session_state.analyzer_image_b64 = None

    # Render Analysis Result
    if st.session_state.analysis_result:
        res = st.session_state.analysis_result
        st.markdown("---")
        st.subheader("📋 Diagnostic & First Aid Report")

        sev = res.get("severity", "Low")
        sev_class = f"badge-{sev.lower()}" if sev.lower() in ["low", "medium", "high", "critical"] else "badge-low"

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f"**Possible Condition:**\n### {res.get('condition', 'Unknown')}")
        with col_b:
            st.markdown(f"**Severity Rating:**\n\n<span class='{sev_class}'>{sev.upper()}</span>", unsafe_allow_html=True)
        with col_c:
            st.markdown(f"**Recommended Specialist:**\n### 🩺 {res.get('doctor_type', 'General Physician')}")

        if res.get("symptoms"):
            st.markdown("**Key Identified Symptoms:** " + ", ".join([f"`{s}`" for s in res.get("symptoms", [])]))

        st.markdown("---")
        st.subheader("⚡ Step-by-Step First Aid Instructions")
        
        first_aid_text = res.get("first_aid", "")
        st.markdown(first_aid_text)

        # Generate Visual First Aid Cards
        st.markdown("---")
        st.subheader("🖼️ Visual First Aid Guide")
        
        steps = [line.strip() for line in first_aid_text.split('\n') if line.strip() and not line.startswith(('⚠️', '⚡', '🚨'))]
        if steps:
            for idx, step in enumerate(steps[:5]):
                with st.expander(f"Step {idx + 1}: {step[:60]}...", expanded=(idx==0)):
                    st.write(f"**Action Plan:** {step}")
                    if st.button(f"🎨 Generate Visual Guide for Step {idx + 1}", key=f"img_btn_{idx}"):
                        with st.spinner("Generating medical illustration..."):
                            prompt = generate_step_prompt(res.get("condition", "General"), step)
                            try:
                                data_uri = run_async(generate_sdxl_image(prompt))
                                st.image(data_uri, caption=f"Visual Guide for Step {idx + 1}", use_container_width=True)
                            except Exception as e:
                                st.error(f"Image generation failed: {e}")


# -----------------------------------------------------------------------------
# 🏥 HOSPITAL FINDER PAGE
# -----------------------------------------------------------------------------
elif selected_page == "🏥 Hospital Finder":
    st.title("🏥 Locality-Aware Emergency Hospital Finder")
    st.caption("Real-time OpenStreetMap & Overpass API GIS Spatial Queries")

    col1, col2 = st.columns([3, 1])
    with col1:
        location_query = st.text_input("Enter Pincode or City/Location name:", value="500081", placeholder="e.g. 500081, Gachibowli Hyderabad, Mumbai")
    with col2:
        radius_km = st.slider("Search Radius (km):", min_value=1.0, max_value=50.0, value=10.0, step=1.0)

    if st.button("🔍 Find Nearby Hospitals & Clinics", type="primary", use_container_width=True):
        with st.spinner("Geocoding location and querying OpenStreetMap GIS database..."):
            lat, lon = run_async(geocode_query(location_query))
            if lat is not None and lon is not None:
                hospitals = run_async(find_nearby_hospitals(lat, lon, radius_km))
                
                st.success(f"Found {len(hospitals)} medical facilities within {radius_km} km of {location_query}.")
                
                # Render Folium Map
                m = folium.Map(location=[lat, lon], zoom_start=13)
                folium.Marker(
                    [lat, lon],
                    popup=f"Search Center: {location_query}",
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(m)

                for h in hospitals:
                    folium.Marker(
                        [h["latitude"], h["longitude"]],
                        popup=f"<b>{h['name']}</b><br/>{h['address']}<br/>Distance: {h['distance_km']} km",
                        tooltip=h["name"],
                        icon=folium.Icon(color="red", icon="plus")
                    ).add_to(m)

                st_folium(m, width=1100, height=450)

                # Render Hospitals List
                st.markdown("### 📋 Facility Directory")
                for h in hospitals:
                    with st.container():
                        st.markdown(f"#### 🏥 {h['name']}")
                        st.write(f"📍 **Address:** {h['address']}")
                        st.write(f"📏 **Distance:** {h['distance_km']} km away")
                        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={h['latitude']},{h['longitude']}"
                        st.markdown(f"[🗺️ Navigate via Google Maps]({maps_url})")
                        st.markdown("---")
            else:
                st.error("Could not resolve location coordinates. Please verify pincode or location name.")


# -----------------------------------------------------------------------------
# 💊 DRUG LOOKUP PAGE
# -----------------------------------------------------------------------------
elif selected_page == "💊 Drug Lookup":
    st.title("💊 OpenFDA Drug Reference Directory")
    st.caption("Vetted drug labeling, usage, dosage, and side-effect lookup")

    drug_name = st.text_input("Enter Drug Name (Brand or Generic):", value="", placeholder="e.g. Paracetamol, Aspirin, Ibuprofen, Amoxicillin...")
    
    st.markdown("**Quick Searches:**")
    quick_cols = st.columns(6)
    quick_drugs = ["Aspirin", "Paracetamol", "Ibuprofen", "Amoxicillin", "Metformin", "Atorvastatin"]
    selected_quick = None
    for i, qd in enumerate(quick_drugs):
        if quick_cols[i].button(qd, key=f"qd_{i}"):
            selected_quick = qd

    search_target = selected_quick or drug_name

    if search_target:
        with st.spinner(f"Querying OpenFDA database for {search_target}..."):
            results = run_async(search_drug(search_target, limit=5))
            if results:
                st.success(f"Found {len(results)} FDA drug record(s) for '{search_target}'")
                for drug in results:
                    with st.expander(f"💊 {drug.get('brand_name', search_target)} ({drug.get('generic_name', 'Generic')})", expanded=True):
                        st.write(f"**Manufacturer:** {drug.get('manufacturer', 'N/A')}")
                        st.write(f"**Administration Route:** {drug.get('route', 'N/A')}")
                        st.markdown("##### 📌 Indications & Usage")
                        st.write(drug.get("indications", "N/A"))
                        st.markdown("##### ⚠️ Warnings & Precautions")
                        st.write(drug.get("warnings", "N/A"))
                        st.markdown("##### 💊 Dosage & Administration")
                        st.write(drug.get("dosage", "N/A"))
                        st.markdown("##### 🧪 Side Effects")
                        st.write(drug.get("side_effects", "N/A"))
            else:
                st.warning(f"No FDA records found for '{search_target}'. Check spelling or try generic name.")


# -----------------------------------------------------------------------------
# 📖 FIRST AID GUIDE PAGE
# -----------------------------------------------------------------------------
elif selected_page == "📖 First Aid Guide":
    st.title("📖 Vetted First Aid Knowledge Base")
    st.caption("Searchable directory of verified first-aid protocols")

    conditions_file = DATA_DIR / "conditions.json"
    conditions_data = []
    if conditions_file.exists():
        with open(conditions_file, "r") as f:
            conditions_data = json.load(f)

    search_term = st.text_input("Search Medical Conditions:", placeholder="e.g., Burn, Fracture, Snake Bite, Asthma...")

    filtered = conditions_data
    if search_term:
        filtered = [c for c in conditions_data if search_term.lower() in (c.get("condition") or c.get("Condition") or "").lower()]

    st.write(f"Showing {len(filtered)} condition(s)")
    for cond in filtered:
        c_name = cond.get("condition") or cond.get("Condition")
        c_sev = cond.get("severity") or cond.get("Severity")
        c_first_aid = cond.get("firstAid") or cond.get("FirstAid")
        c_doc = cond.get("doctorType") or cond.get("DoctorType")
        c_syms = cond.get("symptoms") or cond.get("Symptoms") or []

        with st.expander(f"🩺 {c_name} (Severity: {c_sev})"):
            st.write(f"**Recommended Specialist:** {c_doc}")
            st.write(f"**Key Symptoms:** {', '.join(c_syms)}")
            st.markdown("##### ⚡ First Aid Instructions:")
            st.write(c_first_aid)


# -----------------------------------------------------------------------------
# 📞 EMERGENCY CONTACTS PAGE
# -----------------------------------------------------------------------------
elif selected_page == "📞 Emergency Contacts":
    st.title("📞 Emergency Contacts & National Hotlines")
    st.caption("Instant phone directory for emergency dispatch services")

    contacts = load_emergency_contacts()

    cols = st.columns(2)
    for idx, contact in enumerate(contacts):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"### 🚨 {contact['name']}")
                st.markdown(f"# 📞 [{contact['number']}](tel:{contact['number']})")
                st.write(contact.get("description", ""))
                st.markdown("---")

st.markdown("<br/><hr/><center style='color: #64748b;'>MediAssist AI © 2026 | Built for Rapid First Aid Response</center>", unsafe_allow_html=True)
