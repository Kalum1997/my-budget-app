import streamlit as st
import pandas as pd
import os
import hashlib
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import requests
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
from fpdf import FPDF

# --- APP CONFIG ---
st.set_page_config(page_title="Nexus Ultra Pro", page_icon="💎", layout="wide")

# --- LOTTIE LOADER ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

lottie_loading = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_0p6v6x1o.json")
lottie_success = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_pqnfmone.json")

# --- THEME MANAGER (Dark/Light) ---
if 'theme' not in st.session_state: st.session_state.theme = 'light'

theme_css = {
    'light': {"bg": "#f8f9fa", "card": "white", "text": "#333"},
    'dark': {"bg": "#0e1117", "card": "#1e2130", "text": "#fafafa"}
}
t = theme_css[st.session_state.theme]

st.markdown(f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    .metric-card {{ 
        background: {t['card']}; padding: 25px; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-left: 8px solid #6366f1;
        margin-bottom: 20px;
    }}
    .fab {{
        position: fixed; bottom: 30px; right: 30px; background: #6366f1;
        color: white; width: 60px; height: 60px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        cursor: pointer; z-index: 1000; transition: 0.3s;
    }}
    .fab:hover {{ transform: scale(1.1); background: #4f46e5; }}
    </style>
""", unsafe_allow_html=True)

# --- DB INITIALIZATION ---
FILES = {"users": "u_v4.csv", "trans": "t_v4.csv", "tasks": "tk_v4.csv", "cats": "c_v4.csv", "config": "cfg_v4.csv"}
def init_dbs():
    for f, cols in [("users", ["u", "p", "r", "a"]), ("trans", ["u", "d", "c", "ds", "amt", "ty"]), ("tasks", ["u", "t", "s", "p", "d"]), ("cats", ["u", "n"]), ("config", ["u", "lim"])]:
        if not os.path.exists(FILES[f]): pd.DataFrame(columns=cols).to_csv(FILES[f], index=False)
init_dbs()

# --- AUTH & SESSION ---
if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'username': "", 'role': ""})
def make_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

# --- LOGIN PAGE ---
if not st.session_state.logged_in:
    col1, col2 = st.columns([1, 1])
    with col1: st_lottie(lottie_loading, height=400)
    with col2:
        st.title("💎 Nexus Ultra Pro")
        mode = st.tabs(["🔒 Login", "📝 Register"])
        with mode[0]:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Access Hub"):
                udf = pd.read_csv(FILES["users"])
                if not udf[(udf['u']==u) & (udf['p']==make_hash(p))].empty:
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.rerun()
    st.stop()

# --- FLOATING ACTION BUTTON (Add Transaction Quick Link) ---
st.markdown('<div class="fab" title="Add Quick Entry">+</div>', unsafe_allow_html=True)

# --- NAVIGATION MENU ---
with st.sidebar:
    st_lottie(lottie_success, height=150)
    selected = option_menu(
        "Nexus Menu", ["Dashboard", "Wallet", "Analytics", "Planner", "Settings"],
        icons=['house', 'wallet2', 'bar-chart-line', 'list-check', 'gear'], menu_icon="cast", default_index=0
    )
    if st.button("🌓 Toggle Dark Mode"):
        st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
        st.rerun()

# --- 1. DASHBOARD ---
if selected == "Dashboard":
    st.title(f"🚀 Pulse Dashboard")
    tdf = pd.read_csv(FILES["trans"])
    user_tdf = tdf[tdf['u'] == st.session_state.username]
    
    # Smart Alerts
    cfg = pd.read_csv(FILES["config"])
    u_cfg = cfg[cfg['u'] == st.session_state.username]
    if not u_cfg.empty:
        limit = u_cfg.iloc[0]['lim']
        exp = user_tdf[user_tdf['ty']=="Expense"]['amt'].sum()
        if exp > limit * 0.8:
            st.warning(f"🚨 Warning: ඔබ ඔබේ මාසික සීමාවෙන් (රු. {limit}) 80% ඉක්මවා ඇත!")

    c1, c2, c3 = st.columns(3)
    inc = user_tdf[user_tdf['ty']=="Income"]['amt'].sum()
    exp = user_tdf[user_tdf['ty']=="Expense"]['amt'].sum()
    c1.markdown(f'<div class="metric-card"><h4>Balance</h4><h2>රු. {inc-exp:,.0f}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h4>Income</h4><h2>රු. {inc:,.0f}</h2></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h4>Expense</h4><h2>රු. {exp:,.0f}</h2></div>', unsafe_allow_html=True)

# --- 2. WALLET (Data Entry & Export) ---
elif selected == "Wallet":
    st.title("💰 Smart Wallet")
    
    with st.expander("➕ Add Entry"):
        c1, c2, c3 = st.columns(3)
        ty = c1.selectbox("Type", ["Expense", "Income"])
        amt = c2.number_input("Amount", min_value=0)
        cat = c3.text_input("Category")
        ds = st.text_input("Description")
        if st.button("Save"):
            df = pd.read_csv(FILES["trans"])
            new = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), cat, ds, amt, ty]], columns=df.columns)
            pd.concat([df, new]).to_csv(FILES["trans"], index=False)
            st.success("Entry Saved!")

    # Export Section
    st.divider()
    st.subheader("📥 Export Reports")
    u_data = pd.read_csv(FILES["trans"])[pd.read_csv(FILES["trans"])['u'] == st.session_state.username]
    if st.button("Generate Excel Report"):
        u_data.to_excel("report.xlsx", index=False)
        st.success("Excel report ready!")

# --- 3. ANALYTICS (Advanced Visuals) ---
elif selected == "Analytics":
    st.title("📊 Advanced Analytics")
    u_data = pd.read_csv(FILES["trans"])[pd.read_csv(FILES["trans"])['u'] == st.session_state.username]
    if not u_data.empty:
        fig = px.line(u_data, x="d", y="amt", color="ty", title="Income vs Expense Trend", template="plotly_dark" if st.session_state.theme=='dark' else "plotly")
        st.plotly_chart(fig, use_container_width=True)
        
        fig2 = px.sunburst(u_data[u_data['ty']=="Expense"], path=['ty', 'c'], values='amt', title="Expense Breakdown")
        st.plotly_chart(fig2, use_container_width=True)

# --- 4. PLANNER (Tasks & Recurring) ---
elif selected == "Planner":
    st.title("🗓️ Life Planner")
    st.info("මෙහිදී ඔබගේ Recurring Payments (මාසික බිල්පත්) සහ Tasks කළමනාකරණය කරන්න.")
    # (Task logic and recurring logic goes here)

# --- 5. SETTINGS ---
elif selected == "Settings":
    st.title("⚙️ System Settings")
    limit = st.number_input("Set Monthly Budget Limit", min_value=0)
    if st.button("Save Config"):
        cdf = pd.read_csv(FILES["config"])
        new_cfg = pd.DataFrame([[st.session_state.username, limit]], columns=cdf.columns)
        pd.concat([cdf[cdf['u'] != st.session_state.username], new_cfg]).to_csv(FILES["config"], index=False)
        st.success("Settings Updated!")
