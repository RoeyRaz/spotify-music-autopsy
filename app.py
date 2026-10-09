import os
import math
from collections import Counter
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import time
import pandas as pd

# Page Configuration & Layout
st.set_page_config(
    page_title="Spotify Music Autopsy",
    page_icon="⚡",
    layout="centered"
)

# --- מפתחות האפליקציה ---
CLIENT_ID = "0f4090ee34e144d5a3605a461b8635b7"
CLIENT_SECRET = "e21950fe5a1840c3bf15d96e5791a124"
REDIRECT_URI = "https://spotify-music-autopsy-79ffaef7fwnqbs94ukwawh.streamlit.app/"
SPOTIFY_SCOPE = "user-top-read"

# Custom Clean Dark Clinical CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    .main {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .stButton>button {
        background: #111827;
        color: #f3f4f6;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        border: 1px solid #374151;
        transition: all 0.2s ease;
        width: 100%;
        margin-bottom: 10px;
    }
    .stButton>button:hover {
        background: #1f2937;
        border-color: #1ed760;
        color: #1ed760;
    }
    .clinical-card {
        background: #111827;
        border: 1px solid #1f2937;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 12px;
    }
    .roast-card {
        background: #111827;
        border-left: 4px solid #ef4444;
        border-top: 1px solid #1f2937;
        border-right: 1px solid #1f2937;
        border-bottom: 1px solid #1f2937;
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .tag-badge {
        display: inline-block;
        background: rgba(239, 68, 68, 0.1);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.2);
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .live-log {
        background: #030712;
        border-left: 3px solid #38bdf8;
        padding: 12px 16px;
        border-radius: 6px;
        font-family: monospace;
        color: #38bdf8;
        font-size: 0.9rem;
        margin-bottom: 12px;
    }
    .clinical-prompt {
        background: #111827;
        border: 1px solid #374151;
        padding: 20px;
        border-radius: 10px;
        color: #e2e8f0;
        font-weight: 500;
        margin-bottom: 20px;
        font-size: 1.05rem;
    }
    </style>
""", unsafe_allow_html=True)

# ניהול קאש מבודד לפי סשן משתמש
if 'user_session_id' not in st.session_state:
    st.session_state.user_session_id = str(time.time())

def get_auth_manager():
    unique_cache_path = f".cache_{st.session_state.user_session_id}"
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SPOTIFY_SCOPE,
        cache_path=unique_cache_path,
        show_dialog=True
    )

def clinical_prompt_effect(text):
    placeholder = st.empty()
    current_text = ""
    for char in text:
        current_text += char
        placeholder.markdown(f"<div class='clinical-prompt'>{current_text}▌</div>", unsafe_allow_html=True)
        time.sleep(0.005)
    placeholder.markdown(f"<div class='clinical-prompt'>{text}</div>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #f8fafc; font-weight: 700; font-size: 2.2rem;'>SPOTIFY MUSIC AUTOPSY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1rem; margin-bottom: 30px;'>Clinical diagnostic suite for severe auditory trauma.</p>", unsafe_allow_html=True)

if 'stage' not in st.session_state:
    st.session_state.stage = 'init'

auth_manager = get_auth_manager()

query_params = st.query_params
if "code" in query_params:
    code = query_params["code"]
    try:
        token_info = auth_manager.get_access_token(code, as_dict=True)
        if token_info:
            st.session_state.token_info = token_info
            st.query_params.clear()
            st.session_state.stage = 'fetching'
            st.rerun()
    except Exception as e:
        st.error(f"Authentication error: {e}")

if st.session_state.stage == 'init':
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        auth_url = auth_manager.get_authorize_url()
        st.markdown(f"""
            <a href="{auth_url}" target="_blank" style="text-decoration: none;">
                <div style="background: #1f2937; color: #1ed760; font-weight: 600; text-align: center; border-radius: 8px; padding: 0.8rem 1.5rem; border: 1px solid #374151; font-size: 1rem;">
                    Connect Spotify Account
                </div>
            </a>
        """, unsafe_allow_html=True)

if st.session_state.stage == 'fetching':
    log_container = st.empty()
    log_container.markdown("<div class='live-log'>[LOG 01] Initializing isolated session for incoming user...</div>", unsafe_allow_html=True)
    time.sleep(0.2)

    try:
        token_info = auth_manager.get_cached_token()
        if not token_info:
            st.session_state.stage = 'init'
            st.rerun()

        sp = spotipy.Spotify(auth_manager=auth_manager)

        log_container.markdown("<div class='live-log'>[LOG 02] Extracting unique user behavioral patterns...</div>", unsafe_allow_html=True)
        top_artists = sp.current_user_top_artists(limit=8, time_range='short_term')
        top_tracks = sp.current_user_top_tracks(limit=8, time_range='short_term')

        artists_data = []
        for idx, item in enumerate(top_artists['items']):
            img_url = item['images'][0]['url'] if item.get('images') else ""
            rank = idx + 1
            score = max(20, 100 - (idx * 10))
            artists_data.append({'name': item['name'], 'image': img_url, 'rank': rank, 'score': score})

        tracks_data = []
        for idx, item in enumerate(top_tracks['items']):
            img_url = item['album']['images'][0]['url'] if item.get('album') and item['album'].get('images') else ""
            rank = idx + 1
            score = max(20, 100 - (idx * 10))
            tracks_data.append({'name': item['name'], 'artist': item['artists'][0]['name'], 'image': img_url, 'rank': rank, 'score': score})

        st.session_state.artists_data = artists_data
        st.session_state.tracks_data = tracks_data
        st.session_state.artist_names = [a['name'] for a in artists_data]
        st.session_state.track_names = [t['name'] for t in tracks_data]

        log_container.markdown("<div class='live-log'>[LOG 03] Compiling personalized diagnostic framework...</div>", unsafe_allow_html=True)
        time.sleep(0.3)
        log_container.empty()

        st.session_state.stage = 'q1'
        st.rerun()

    except Exception as e:
        log_container.empty()
        st.error(f"Execution failed: {e}")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Return to Start"):
            st.session_state.stage = 'init'
            st.rerun()

# --- Question 1 ---
if st.session_state.stage == 'q1':
    top_artist = st.session_state.artist_names[0] if st.session_state.artist_names else "this artist"
    clinical_prompt_effect(f"Diagnostic Probe 01:\n\nSubject exhibits an extreme statistical anomaly regarding the presence of '{top_artist}' in rotation.\n\nHow does the subject justify this dependency?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("I stand by my artistic choices"):
            st.session_state.roast_log = f"Pled guilty to defending {top_artist}. Severe denial."
            st.session_state.stage = 'q2'
            st.rerun()
        if st.button("It's strictly for physical training"):
            st.session_state.roast_log = f"Blamed {top_artist} on gym sessions. Zero cardiovascular exertion detected."
            st.session_state.stage = 'q2'
            st.rerun()
    with col2:
        if st.button("A sibling accessed my credentials"):
            st.session_state.roast_log = f"Disowned responsibility, blaming family members for {top_artist}."
            st.session_state.stage = 'q2'
            st.rerun()
        if st.button("No comment, please spare me"):
            st.session_state.roast_log = "Refused cooperation under questioning. Guilt assumed."
            st.session_state.stage = 'q2'
            st.rerun()

# --- Question 2 ---
if st.session_state.stage == 'q2':
    clinical_prompt_effect("Diagnostic Probe 02:\n\nWhen was the last instance the subject completed an entire studio album without triggering shuffle mode or skipping tracks?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Recently, I respect album sequencing"):
            st.session_state.roast_log += " | Claimed linear album appreciation. Fabricated testimony."
            st.session_state.stage = 'q3'
            st.rerun()
    with col2:
        if st.button("Never, my attention span is entirely fried"):
            st.session_state.roast_log += " | Admitted to acute digital cognitive decline."
            st.session_state.stage = 'q3'
            st.rerun()

# --- Question 3 ---
if st.session_state.stage == 'q3':
    clinical_prompt_effect("Diagnostic Probe 03:\n\nIf you were handed the AUX cord at a social gathering right now, what is the immediate outcome?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Absolute silence and universal panic"):
            st.session_state.roast_log += " | Acknowledged public safety hazard status of music taste."
            st.session_state.stage = 'q4'
            st.rerun()
        if st.button("Instant elevation of the room's vibe"):
            st.session_state.roast_log += " | Suffers from severe main character delusions."
            st.session_state.stage = 'q4'
            st.rerun()
    with col2:
        if st.button("People would politely ask me to leave"):
            st.session_state.roast_log += " | Fully aware of social rejection triggers."
            st.session_state.stage = 'q4'
            st.rerun()
        if st.button("I don't go to social gatherings"):
            st.session_state.roast_log += " | Confirmed terminal online isolation."
            st.session_state.stage = 'q4'
            st.rerun()

# --- Question 4 ---
if st.session_state.stage == 'q4':
    top_track = st.session_state.track_names[0] if st.session_state.track_names else "this track"
    clinical_prompt_effect(f"Diagnostic Probe 04:\n\nTelemetry reveals continuous, uninterrupted looping of '{top_track}' during vulnerable hours (02:00 - 05:00 AM).\n\nWhat is the clinical rationale for this pattern?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Deep existential processing and healing"):
            st.session_state.roast_log += f" | Masked late-night emotional breakdown over '{top_track}' as 'healing'."
            st.session_state.stage = 'dashboard'
            st.rerun()
        if st.button("Background noise to suppress inner monologue"):
            st.session_state.roast_log += " | Utilized audio loops as a tactical defense mechanism against thoughts."
            st.session_state.stage = 'dashboard'
            st.rerun()
    with col2:
        if st.button("Fell asleep and left it playing on repeat"):
            st.session_state.roast_log += " | Blamed severe physical exhaustion on algorithmic loop repetition."
            st.session_state.stage = 'dashboard'
            st.rerun()
        if st.button("Pure, unadulterated masochism"):
            st.session_state.roast_log += " | Exhibited absolute self-awareness of emotional self-sabotage."
            st.session_state.stage = 'dashboard'
            st.rerun()

# --- Clinical Dashboard ---
if st.session_state.stage == 'dashboard':

    st.markdown("""
        <div class='clinical-card'>
            <div class='section-title'>Primary Entities (Top Artists & Metrics)</div>
        </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for idx, artist in enumerate(st.session_state.artists_data[:4]):
        with cols[idx]:
            if artist['image']:
                st.image(artist['image'], use_container_width=True)
            st.markdown(f"<p style='text-align: center; font-weight: 600; font-size: 0.85rem; margin-bottom:0;'>{artist['name']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #38bdf8; font-size: 0.75rem;'>Index: #{artist['rank']}</p>", unsafe_allow_html=True)

    artists_df = pd.DataFrame(st.session_state.artists_data)
    st.bar_chart(artists_df.set_index('name')['score'], color="#38bdf8")

    time.sleep(0.2)

    st.markdown("""
        <div class='clinical-card' style='margin-top: 20px;'>
            <div class='section-title'>High-Frequency Vectors (Top Tracks)</div>
        </div>
    """, unsafe_allow_html=True)

    cols_t = st.columns(4)
    for idx, track in enumerate(st.session_state.tracks_data[:4]):
        with cols_t[idx]:
            if track['image']:
                st.image(track['image'], use_container_width=True)
            st.markdown(f"<p style='text-align: center; font-weight: 600; font-size: 0.8rem; margin-bottom:0;'>{track['name']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #94a3b8; font-size: 0.75rem;'>{track['artist']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #10b981; font-size: 0.75rem;'>Index: #{track['rank']}</p>", unsafe_allow_html=True)

    tracks_df = pd.DataFrame(st.session_state.tracks_data)
    st.bar_chart(tracks_df.set_index('name')['score'], color="#10b981")

    time.sleep(0.2)

    st.markdown("""
        <div class='clinical-card' style='margin-top: 20px;'>
            <div class='section-title'>Assigned Behavioral Classifications</div>
        </div>
    """, unsafe_allow_html=True)

    tags = [
        "recession indicator", "bad vibes only", "needs professional help", 
        "auxiliary cable security risk", "chronically online", "parasocial relationship enjoyer", 
        "dopamine deficiency marker", "unsupervised listener", "crying in the club"
    ]
    tags_html = "".join([f"<span class='tag-badge'>#{t}</span>" for t in tags])
    st.markdown(f"<div>{tags_html}</div>", unsafe_allow_html=True)

    time.sleep(0.2)

    st.markdown("""
        <div class='clinical-card' style='margin-top: 20px;'>
            <div class='section-title'>Pathological Findings & Behavioral Notes</div>
        </div>
    """, unsafe_allow_html=True)

    findings = [
        f"Subject Log: {st.session_state.roast_log}",
        "Auxiliary Risk Assessment: Permitting subject direct control over shared environment output constitutes a structural hazard.",
        "Dopamine Management: Complete reliance on high-rotation loops indicates severe resistance to cognitive friction.",
        "Aesthetic Profile: Taste parameters suggest heavy exposure to unmonitored digital isolation."
    ]

    for finding in findings:
        st.markdown(f"""
            <div class="roast-card">
                <p style="font-size: 0.95rem; line-height: 1.4; color: #fca5a5; margin:0; font-weight: 500;">{finding}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div class='clinical-card' style='margin-top: 20px;'>
            <div class='section-title'>Mandatory Remediation Protocol</div>
        </div>
    """, unsafe_allow_html=True)

    remediations = [
        "Enforce absolute acoustic deprivation for 72 hours to allow baseline neurological reset.",
        "Expose subject to unfiltered terrestrial radio broadcast formats to re-establish tolerance for mainstream consensus.",
        "Revoke auxiliary connection privileges indefinitely."
    ]
    for r in remediations:
        st.markdown(f"<div class='clinical-card' style='border-left: 3px solid #10b981; padding: 14px 18px; margin-bottom: 8px;'><p style='margin:0; font-size: 0.9rem;'>{r}</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    report_text = f"""=== CLINICAL MUSIC AUTOPSY REPORT ===
Behavioral Log: {st.session_state.roast_log}
Top Artists: {', '.join(st.session_state.artist_names[:5])}
Diagnostic Conclusion: Acute exposure to terminal online echo chambers and cognitive looping.
"""
    st.download_button(
        label="📥 Export Diagnostic Summary",
        data=report_text,
        file_name="spotify_clinical_autopsy.txt",
        mime="text/plain"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    c_reset1, c_reset2, c_reset3 = st.columns([1, 2, 1])
    with c_reset2:
        if st.button("New Patient Diagnostic Scan"):
            st.session_state.stage = 'init'
            st.rerun()
