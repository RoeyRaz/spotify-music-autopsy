import os
import math
from collections import Counter
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import streamlit as st
import time
import pandas as pd

# Page Configuration & Layout
st.set_page_config(
    page_title="Spotify Music Autopsy",
    page_icon="⚡",
    layout="centered"
)

# Custom CSS for Stunning Glassmorphism, Gorgeous Mode Cards, and Animations
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800;900&display=swap');

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .main {
        background: linear-gradient(-45deg, #0f172a, #311042, #1e1b4b, #030712);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: #f8fafc;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1ed760 0%, #059669 100%);
        color: #030712;
        font-weight: 800;
        letter-spacing: 0.5px;
        border-radius: 40px;
        padding: 0.9rem 1.8rem;
        border: none;
        box-shadow: 0 0 30px rgba(30, 215, 96, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
        margin-bottom: 12px;
    }
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 0 40px rgba(30, 215, 96, 0.7);
    }
    .animated-section {
        animation: fadeIn 0.8s ease-out forwards;
        background: rgba(30, 41, 59, 0.75);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 28px;
        border-radius: 24px;
        margin-bottom: 24px;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
    }
    .section-title {
        font-size: 1.6rem;
        font-weight: 900;
        color: #38bdf8;
        margin-bottom: 15px;
        text-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
    }
    .roast-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-left: 6px solid #ef4444;
        padding: 22px;
        border-radius: 16px;
        margin-bottom: 15px;
        box-shadow: 0 10px 25px rgba(239, 68, 68, 0.12);
        animation: fadeIn 0.8s ease-out forwards;
    }
    .tag-badge {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 0.9rem;
        font-weight: 700;
        margin-right: 8px;
        margin-bottom: 10px;
    }
    .live-log {
        background: rgba(15, 23, 42, 0.85);
        border-left: 4px solid #38bdf8;
        padding: 14px 20px;
        border-radius: 12px;
        font-family: monospace;
        color: #38bdf8;
        font-size: 0.95rem;
        margin-bottom: 15px;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);
    }
    .typewriter-box {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(30, 41, 59, 0.85) 100%);
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 24px;
        border-radius: 20px;
        color: #e0f2fe;
        font-weight: 600;
        margin-bottom: 24px;
        text-align: center;
        font-size: 1.15rem;
        box-shadow: 0 10px 30px rgba(56, 189, 248, 0.15);
    }
    </style>
""", unsafe_allow_html=True)

load_dotenv()
SPOTIFY_SCOPE = "user-top-read"


def typewriter_effect(text, container_class="typewriter-box", speed=0.01):
    placeholder = st.empty()
    current_text = ""
    for char in text:
        current_text += char
        placeholder.markdown(f"<div class='{container_class}'>{current_text}▌</div>", unsafe_allow_html=True)
        time.sleep(speed)
    placeholder.markdown(f"<div class='{container_class}'>{text}</div>", unsafe_allow_html=True)


st.markdown(
    "<h1 style='text-align: center; color: #ffffff; font-weight: 900; font-size: 3rem; letter-spacing: -1px; text-shadow: 0 0 40px rgba(30,215,96,0.4);'>SPOTIFY MUSIC AUTOPSY</h1>",
    unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; color: #94a3b8; font-size: 1.2rem; margin-bottom: 30px;'>A brutal breakdown of the tracks you desperately try to hide.</p>",
    unsafe_allow_html=True)

if 'stage' not in st.session_state:
    st.session_state.stage = 'init'

if st.session_state.stage == 'init':
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Unlock Your Trauma"):
            st.session_state.stage = 'fetching'
            st.rerun()

if st.session_state.stage == 'fetching':
    log_container = st.empty()
    log_container.markdown("<div class='live-log'>[1/3] Establishing connection to Spotify...</div>",
                           unsafe_allow_html=True)
    time.sleep(0.3)

    try:
        # שליפת המפתחות מתוך ה-Secrets של סטרימלייט או מתוך משתני הסביבה המקומיים
        client_id = st.secrets.get("SPOTIFY_CLIENT_ID") or os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = st.secrets.get("SPOTIFY_CLIENT_SECRET") or os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = st.secrets.get("SPOTIFY_REDIRECT_URI") or os.getenv("SPOTIFY_REDIRECT_URI")

        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=SPOTIFY_SCOPE,
            open_browser=False
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)

        log_container.markdown("<div class='live-log'>[2/3] Extracting your top artists and tracks...</div>",
                               unsafe_allow_html=True)
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
            tracks_data.append(
                {'name': item['name'], 'artist': item['artists'][0]['name'], 'image': img_url, 'rank': rank,
                 'score': score})

        st.session_state.artists_data = artists_data
        st.session_state.tracks_data = tracks_data
        st.session_state.artist_names = [a['name'] for a in artists_data]

        log_container.markdown("<div class='live-log'>[3/3] Initializing presentation flow...</div>",
                               unsafe_allow_html=True)
        time.sleep(0.4)
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

# --- Interactive Question 1 ---
if st.session_state.stage == 'q1':
    top_artist = st.session_state.artist_names[0] if st.session_state.artist_names else "this artist"
    typewriter_effect(
        f"⚠️ Forensic audit active. We notice an unhealthy obsession with {top_artist}.\n\nHow do you plead before the algorithm passes sentence?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("I stand by my artistic choices"):
            st.session_state.roast_log = f"Pled guilty to defending {top_artist}. Deep denial detected."
            st.session_state.stage = 'q2'
            st.rerun()
        if st.button("It's strictly for the gym, I swear"):
            st.session_state.roast_log = f"Blamed {top_artist} on gym sessions. Zero heavy lifting found."
            st.session_state.stage = 'q2'
            st.rerun()
    with col2:
        if st.button("My younger brother hacked my account"):
            st.session_state.roast_log = f"Tried blaming a younger sibling for listening to {top_artist}."
            st.session_state.stage = 'q2'
            st.rerun()
        if st.button("Please don't judge me"):
            st.session_state.roast_log = "Pleaded for mercy. Empathy modules rejected."
            st.session_state.stage = 'q2'
            st.rerun()

# --- Question 2 ---
if st.session_state.stage == 'q2':
    typewriter_effect(
        "🧠 Secondary psychological probe:\n\nWhen was the last time you listened to a full album from start to finish without skipping to shuffle?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yesterday, I respect real albums"):
            st.session_state.roast_log += " Claimed to respect full albums. Lie detected."
            st.session_state.stage = 'dashboard'
            st.rerun()
    with col2:
        if st.button("Never, my attention span is fried"):
            st.session_state.roast_log += " Admitted to complete digital brain rot."
            st.session_state.stage = 'dashboard'
            st.rerun()

# --- Continuous Seamless Dashboard Presentation ---
if st.session_state.stage == 'dashboard':

    # 1. Top Artists Section
    st.markdown("""
        <div class='animated-section'>
            <div class='section-title'>👑 Primary Suspects (Top Artists & Rotation Rank)</div>
        </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for idx, artist in enumerate(st.session_state.artists_data[:4]):
        with cols[idx]:
            if artist['image']:
                st.image(artist['image'], use_container_width=True)
            st.markdown(
                f"<p style='text-align: center; font-weight: 700; font-size: 0.9rem; margin-bottom:0;'>{artist['name']}</p>",
                unsafe_allow_html=True)
            st.markdown(
                f"<p style='text-align: center; color: #38bdf8; font-size: 0.75rem;'>Rank: #{artist['rank']} in rotation</p>",
                unsafe_allow_html=True)

    artists_df = pd.DataFrame(st.session_state.artists_data)
    st.bar_chart(artists_df.set_index('name')['score'], color="#38bdf8")

    time.sleep(0.3)

    # 2. Top Tracks Section
    st.markdown("""
        <div class='animated-section' style='margin-top: 30px;'>
            <div class='section-title'>🎵 Primary Anthems (Top Tracks & Rotation Rank)</div>
        </div>
    """, unsafe_allow_html=True)

    cols_t = st.columns(4)
    for idx, track in enumerate(st.session_state.tracks_data[:4]):
        with cols_t[idx]:
            if track['image']:
                st.image(track['image'], use_container_width=True)
            st.markdown(
                f"<p style='text-align: center; font-weight: 700; font-size: 0.85rem; margin-bottom:0;'>{track['name']}</p>",
                unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #94a3b8; font-size: 0.75rem;'>{track['artist']}</p>",
                        unsafe_allow_html=True)
            st.markdown(
                f"<p style='text-align: center; color: #10b981; font-size: 0.75rem;'>Rank: #{track['rank']} in rotation</p>",
                unsafe_allow_html=True)

    tracks_df = pd.DataFrame(st.session_state.tracks_data)
    st.bar_chart(tracks_df.set_index('name')['score'], color="#10b981")

    time.sleep(0.3)

    # 3. Tags Section
    st.markdown("""
        <div class='animated-section' style='margin-top: 30px;'>
            <div class='section-title'>🏷️ Assigned Judgment Tags</div>
        </div>
    """, unsafe_allow_html=True)

    tags = ["manic pixie dream girl", "terminal online", "poser", "aux cable menace", "edgelord in denial",
            "unmedicated", "npc behavior", "aux cable villain"]
    tags_html = "".join([f"<span class='tag-badge'>#{t}</span>" for t in tags])
    st.markdown(f"<div>{tags_html}</div>", unsafe_allow_html=True)

    time.sleep(0.3)

    # 4. Expanded Micro-Roasts Section
    st.markdown("""
        <div class='animated-section' style='margin-top: 30px;'>
            <div class='section-title'>🔥 Unfiltered Micro-Roasts & Behavioral Findings</div>
        </div>
    """, unsafe_allow_html=True)

    micro_roasts = [
        f"Behavioral Log: {st.session_state.roast_log}",
        "Aux Cord Hazard: Letting you pick songs at a party is a violation of basic human rights.",
        "Algorithm Victim: Your taste was carefully curated by a tired corporate machine in Stockholm.",
        "Skip Button Abuse: You never finish a single song before your brain demands instant dopamine.",
        "Main Character Syndrome: You listen to this playlist while staring dramatically out of a bus window."
    ]

    for roast in micro_roasts:
        st.markdown(f"""
            <div class="roast-card">
                <p style="font-size: 1.02rem; line-height: 1.5; color: #fca5a5; margin:0; font-weight: 600;">{roast}</p>
            </div>
        """, unsafe_allow_html=True)

    # 5. Recommendations Section
    st.markdown("""
        <div class='animated-section' style='margin-top: 30px;'>
            <div class='section-title'>💊 Mandatory Treatment Plan</div>
        </div>
    """, unsafe_allow_html=True)

    treatments = [
        "Enforce absolute silence for 48 consecutive hours to allow your fried neurons to reboot.",
        "Listen to a mainstream commercial radio station and accept that global popularity doesn't personally offend you.",
        "Delete your account, throw away your auxiliary cable, and pick up an outdoor hobby like pacing angrily in a park."
    ]
    for t in treatments:
        st.markdown(
            f"<div class='animated-section' style='border-left: 5px solid #10b981; padding: 18px 24px; margin-bottom: 12px;'><p style='margin:0; font-weight: 550;'>{t}</p></div>",
            unsafe_allow_html=True)

    # --- Export Report Button ---
    st.markdown("<br>", unsafe_allow_html=True)
    report_text = f"""=== SPOTIFY MUSIC AUTOPSY REPORT ===
Behavioral Log: {st.session_state.roast_log}
Top Artists: {', '.join(st.session_state.artist_names[:5])}
Primary Diagnosis: Terminal online culture and acute lack of musical supervision.
Aux Cord Threat Level: CRITICAL HAZARD.
"""
    st.download_button(
        label="📥 Export Autopsy Report",
        data=report_text,
        file_name="spotify_autopsy_report.txt",
        mime="text/plain"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    c_reset1, c_reset2, c_reset3 = st.columns([1, 2, 1])
    with c_reset2:
        if st.button("Start Over / Roast Someone Else"):
            st.session_state.stage = 'init'
            st.rerun()
