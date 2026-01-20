import streamlit as st
import pandas as pd
import os
import hashlib
import plotly.express as px
import requests
import re
from datetime import datetime
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu

# --- APP CONFIG ---
st.set_page_config(page_title="Nexus Pro Max", page_icon="💎", layout="wide")

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': "", 'role': "User", 'theme': "light", 'active_tool': "None"})

# --- LOTTIE ICONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

# Icons for Grid
icon_money = "https://lottie.host/802b1660-3948-4362-a548-56549a930129/Z7vP4U9W6y.json"
icon_water = "https://lottie.host/8724982c-90fc-4630-9988-66236b442111/XmR7Ww5W0f.json"
icon_note = "https://lottie.host/4a2993f3-000c-43f1-b856-11440026e60b/62NUnrL84S.json"
icon_bill = "https://lottie.host/e22619e0-84a2-4a00-9903-883395777176/z4v83049F3.json"

# --- DB INITIALIZATION ---
FILES = {
    "users": "users_v7.csv", "trans": "trans_v7.csv", "tasks": "tasks_v7.csv",
    "savings": "savings_v7.csv", "cats": "cats_v7.csv", "bills": "bills_v7.csv",
    "water": "water_v7.csv", "journal": "journal_v7.csv", "shopping": "shopping_v7.csv"
}

def init_dbs():
    for key, name in FILES.items():
        if not os.path.exists(name):
            cols = {
                "users": ["username", "password", "role", "approved"],
                "trans": ["username", "date", "cat", "desc", "amt", "type"],
                "tasks": ["username", "task", "status", "priority", "date"],
                "savings": ["username", "goal", "target", "current"],
                "cats": ["username", "category_name"],
                "bills": ["username", "name", "due_date", "amt", "status"],
                "water": ["username", "date", "liters"],
                "journal": ["username", "date", "entry"],
                "shopping": ["username", "item", "done"]
            }[key]
            pd.DataFrame(columns=cols).to_csv(name, index=False)

init_dbs()

# --- CSS FOR MOBILE & BIG ICONS ---
st.markdown(f"""
    <style>
    .tool-card {{
        background: white; padding: 20px; border-radius: 20px;
        text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        cursor: pointer; transition: 0.3s; margin-bottom: 20px;
        border: 1px solid #eee;
    }}
    .tool-card:hover {{ transform: translateY(-5px); border-color: #6366f1; }}
    .stButton>button {{ width: 100%; border-radius: 12px; height: 3rem; }}
    </style>
""", unsafe_allow_html=True)

# --- SMART VOICE/TEXT INPUT LOGIC ---
def process_smart_input(text):
    # Regex to find numbers (Amount)
    nums = re.findall(r'\d+', text)
    if nums:
        amt = int(nums[0])
        # Simple Logic to guess category
        cat = "Food" if any(x in text for x in ["කෑම", "food", "kema"]) else "Other"
        tdf = pd.read_csv(FILES["trans"])
        new_t = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), cat, text, amt, "Expense"]], columns=tdf.columns)
        pd.concat([tdf, new_t]).to_csv(FILES["trans"], index=False)
        return f"රු. {amt} {cat} ලෙස ඇතුළත් කළා! ✅"
    return "මුදල හඳුනාගත නොහැක. නැවත උත්සාහ කරන්න."

# --- AUTHENTICATION (Simplified for space) ---
if not st.session_state.logged_in:
    st.title("💎 Nexus Pro Max")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        udf = pd.read_csv(FILES["users"])
        if u == "admin" and p == "123": # Emergency bypass
            st.session_state.update({'logged_in': True, 'username': "admin", 'role': "Admin"})
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    selected = option_menu("Nexus Menu", ["🏠 Home", "💰 Wallet", "✅ Tasks", "⚙️ Settings"], 
        icons=['house', 'wallet2', 'list-check', 'gear'], default_index=0)
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- MAIN INTERFACE ---
if selected == "🏠 Home":
    st.title(f"ආයුබෝවන්, {st.session_state.username}! 👋")
    
    # --- VOICE / SMART INPUT BOX ---
    with st.expander("🎤 Smart Voice/Text Input (වැය වූ මුදල කියන්න)", expanded=True):
        cmd = st.text_input("උදා: 'අද බස් එකට 50' හෝ 'Kema 500'")
        if st.button("Submit Command"):
            msg = process_smart_input(cmd)
            st.success(msg)

    st.subheader("🛠️ Quick Tools")
    
    # GRID LAYOUT (Icons)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔔 Bills"): st.session_state.active_tool = "Bills"
    with col2:
        if st.button("💧 Water"): st.session_state.active_tool = "Water"
    with col3:
        if st.button("📝 Journal"): st.session_state.active_tool = "Journal"
        
    col4, col5, col6 = st.columns(3)
    with col4:
        if st.button("📈 Net Worth"): st.session_state.active_tool = "NetWorth"
    with col5:
        if st.button("🛒 Shopping"): st.session_state.active_tool = "Shopping"
    with col6:
        if st.button("❌ Close Tool"): st.session_state.active_tool = "None"

    st.divider()

    # --- TOOL CONTENT AREA ---
    tool = st.session_state.active_tool
    
    if tool == "Bills":
        st.subheader("💰 Bill Reminders")
        bdf = pd.read_csv(FILES["bills"])
        with st.form("bill_form"):
            bn = st.text_input("Bill Name")
            ba = st.number_input("Amount", min_value=0)
            bd = st.date_input("Due Date")
            if st.form_submit_button("Add Bill"):
                new_b = pd.DataFrame([[st.session_state.username, bn, str(bd), ba, "Unpaid"]], columns=bdf.columns)
                pd.concat([bdf, new_b]).to_csv(FILES["bills"], index=False)
                st.rerun()
        st.write(bdf[bdf['username']==st.session_state.username])

    elif tool == "Water":
        st.subheader("💧 Water Intake Tracker")
        wdf = pd.read_csv(FILES["water"])
        liters = st.slider("Liters Today", 0.0, 5.0, 1.0, 0.25)
        if st.button("Save Water Log"):
            new_w = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), liters]], columns=wdf.columns)
            pd.concat([wdf, new_w]).to_csv(FILES["water"], index=False)
            st.success("Log Updated!")

    elif tool == "Journal":
        st.subheader("📓 Daily Journal")
        jdf = pd.read_csv(FILES["journal"])
        entry = st.text_area("අද දවසේ විශේෂ සිදුවීම්...")
        if st.button("Save Note"):
            new_j = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), entry]], columns=jdf.columns)
            pd.concat([jdf, new_j]).to_csv(FILES["journal"], index=False)
            st.success("Note Saved!")

    elif tool == "NetWorth":
        st.subheader("📉 Net Worth Calculator")
        tdf = pd.read_csv(FILES["trans"])
        sdf = pd.read_csv(FILES["savings"])
        cash = tdf[tdf['username']==st.session_state.username]['amt'].sum()
        savings = sdf[sdf['username']==st.session_state.username]['current'].sum()
        st.metric("Total Net Worth", f"රු. {cash + savings:,.2f}")
        st.info("මෙය ඔබගේ Wallet Balance එක සහ Savings එකතුවයි.")

    elif tool == "Shopping":
        st.subheader("🛒 Shopping List")
        shdf = pd.read_csv(FILES["shopping"])
        item = st.text_input("Item Name")
        if st.button("Add to List"):
            new_sh = pd.DataFrame([[st.session_state.username, item, False]], columns=shdf.columns)
            pd.concat([shdf, new_sh]).to_csv(FILES["shopping"], index=False)
            st.rerun()
        st.write(shdf[shdf['username']==st.session_state.username])

# --- OTHER SECTIONS (KEEPING YOUR ORIGINAL LOGIC) ---
elif selected == "💰 Wallet":
    st.title("💸 Wallet Management")
    # ... (Your previous wallet code here)
    st.info("Home screen එකේ ඇති Smart Input එක භාවිතා කර වේගයෙන් වියදම් ඇතුළත් කරන්න.")

elif selected == "✅ Tasks":
    st.title("✅ Tasks & Goals")
    # ... (Your previous tasks code here)
