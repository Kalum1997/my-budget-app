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

# --- INITIALIZE SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': "", 'role': "User", 'theme': "light", 'active_tool': "None"})

# --- LOTTIE LOADER ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

lottie_main = load_lottieurl("https://lottie.host/802b1660-3948-4362-a548-56549a930129/Z7vP4U9W6y.json")

# --- THEME & CSS ---
t = {"bg": "#f8f9fa", "card": "white", "text": "#333"} if st.session_state.theme == "light" else {"bg": "#0e1117", "card": "#1e2130", "text": "#fafafa"}

st.markdown(f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    .metric-card {{ 
        background: {t['card']}; padding: 25px; border-radius: 20px; 
        box-shadow: 0 10px 15px rgba(0,0,0,0.1); border-bottom: 5px solid #6366f1;
        color: {t['text']}; margin-bottom: 20px; text-align: center;
    }}
    div.stButton > button {{ border-radius: 15px; font-weight: 700; height: 4rem; font-size: 1.1rem; width: 100%; }}
    </style>
""", unsafe_allow_html=True)

# --- DB INITIALIZATION ---
FILES = {
    "users": "users_v9.csv", "trans": "trans_v9.csv", 
    "tasks": "tasks_v9.csv", "savings": "savings_v9.csv", 
    "config": "config_v9.csv", "cats": "cats_v9.csv",
    "bills": "bills_v9.csv", "water": "water_v9.csv",
    "journal": "journal_v9.csv", "shopping": "shopping_v9.csv"
}

def make_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def init_dbs():
    for key, name in FILES.items():
        if not os.path.exists(name):
            if key == "users":
                pd.DataFrame([["admin", make_hash("123"), "Admin", True]], columns=["username", "password", "role", "approved"]).to_csv(name, index=False)
            else:
                cols = {
                    "trans": ["username", "date", "cat", "desc", "amt", "type"],
                    "tasks": ["username", "task", "status", "priority", "date"],
                    "savings": ["username", "goal", "target", "current"],
                    "config": ["username", "monthly_limit"],
                    "cats": ["username", "category_name"],
                    "bills": ["username", "name", "amt", "due", "status"],
                    "water": ["username", "date", "liters"],
                    "journal": ["username", "date", "note"],
                    "shopping": ["username", "item", "status"]
                }[key]
                pd.DataFrame(columns=cols).to_csv(name, index=False)

init_dbs()

# --- SMART INPUT PROCESSOR ---
def smart_input_logic(text):
    nums = re.findall(r'\d+', text)
    if nums:
        amt = float(nums[0])
        cat = "Food" if any(x in text.lower() for x in ["කෑම", "food", "kema", "rice"]) else "Other"
        tdf = pd.read_csv(FILES["trans"])
        new_row = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), cat, text, amt, "Expense"]], columns=tdf.columns)
        pd.concat([tdf, new_row]).to_csv(FILES["trans"], index=False)
        return f"✅ රු. {amt} '{cat}' ලෙස Wallet එකට ඇතුළත් කළා!"
    return "❌ මුදල හඳුනාගත නොහැක. (උදා: කෑම 500)"

# --- AUTHENTICATION ---
if not st.session_state.logged_in:
    col1, col2 = st.columns([1, 1])
    with col1:
        if lottie_main: st_lottie(lottie_main, height=400)
        else: st.title("💎 Nexus Pro")
    with col2:
        st.subheader("Nexus Pro Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            udf = pd.read_csv(FILES["users"])
            res = udf[(udf['username']==u) & (udf['password']==make_hash(p))]
            if not res.empty:
                if res.iloc[0]['approved']:
                    st.session_state.update({'logged_in': True, 'username': u, 'role': res.iloc[0]['role']})
                    st.rerun()
                else: st.error("Admin Approval Required")
            else: st.error("Invalid Login")
    st.stop()

# --- PRE-LOAD DATA (To Fix NameError) ---
tdf = pd.read_csv(FILES["trans"])
user_tdf = tdf[tdf['username'] == st.session_state.username]

# --- SIDEBAR ---
with st.sidebar:
    selected = option_menu("Nexus Menu", ["🏠 Dashboard", "💰 Wallet", "✅ Tasks & Goals", "⚙️ Settings"], 
        icons=['house', 'wallet2', 'list-check', 'gear'], default_index=0)
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- 1. DASHBOARD ---
if selected == "🏠 Dashboard":
    st.title("🚀 Smart Dashboard")
    
    # Smart Input Section
    with st.container():
        st.markdown("### 🎤 Voice/Text Smart Input")
        cmd = st.text_input("වියදම සටහන් කරන්න (Ex: Bus 50)", placeholder="Type here...")
        if st.button("Add Now"):
            st.success(smart_input_logic(cmd))
            st.rerun()

    # Metrics
    inc = user_tdf[user_tdf['type']=="Income"]['amt'].sum()
    exp = user_tdf[user_tdf['type']=="Expense"]['amt'].sum()
    tkdf = pd.read_csv(FILES["tasks"])
    user_tk = tkdf[tkdf['username'] == st.session_state.username]
    prog = (len(user_tk[user_tk['status']=="Done"])/len(user_tk)*100) if not user_tk.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><h4>💵 Wallet</h4><h2>රු. {inc-exp:,.0f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h4>📊 Status</h4><h2>{'Stable' if inc>exp else 'Low'}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h4>✅ Tasks</h4><h2>{prog:.0f}%</h2></div>", unsafe_allow_html=True)

    st.divider()

    # --- BIG ICON TOOLS ---
    st.subheader("🛠️ Quick Life Tools")
    g1, g2, g3 = st.columns(3)
    if g1.button("💰 Bills"): st.session_state.active_tool = "Bills"
    if g2.button("💧 Water"): st.session_state.active_tool = "Water"
    if g3.button("📓 Journal"): st.session_state.active_tool = "Journal"
    
    g4, g5, g6 = st.columns(3)
    if g4.button("📈 Net Worth"): st.session_state.active_tool = "NetWorth"
    if g5.button("🛒 Shopping"): st.session_state.active_tool = "Shopping"
    if g6.button("🏠 Close"): st.session_state.active_tool = "None"

    # Tool Content
    tool = st.session_state.active_tool
    if tool == "Bills":
        with st.expander("🔔 Bill Reminders", expanded=True):
            bdf = pd.read_csv(FILES["bills"])
            bn = st.text_input("බිල්පතේ නම")
            ba = st.number_input("මුදල", min_value=0)
            if st.button("Save"):
                new_b = pd.DataFrame([[st.session_state.username, bn, ba, str(datetime.now().date()), "Unpaid"]], columns=bdf.columns)
                pd.concat([bdf, new_b]).to_csv(FILES["bills"], index=False)
                st.rerun()
            st.dataframe(bdf[bdf['username']==st.session_state.username], use_container_width=True)

    elif tool == "Water":
        with st.expander("💧 Water Intake", expanded=True):
            wdf = pd.read_csv(FILES["water"])
            liters = st.slider("Liters Today", 0.0, 5.0, 1.5)
            if st.button("Log Water"):
                new_w = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), liters]], columns=wdf.columns)
                pd.concat([wdf, new_w]).to_csv(FILES["water"], index=False)
                st.success("Log Saved!")

    elif tool == "Journal":
        with st.expander("📓 Daily Journal", expanded=True):
            jdf = pd.read_csv(FILES["journal"])
            note = st.text_area("අද දවසේ සටහන්...")
            if st.button("Save Note"):
                new_j = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), note]], columns=jdf.columns)
                pd.concat([jdf, new_j]).to_csv(FILES["journal"], index=False)
                st.success("Saved!")

    elif tool == "NetWorth":
        with st.expander("📈 Total Net Worth", expanded=True):
            sdf = pd.read_csv(FILES["savings"])
            saved = sdf[sdf['username']==st.session_state.username]['current'].sum()
            st.metric("Total Worth", f"රු. { (inc-exp) + saved:,.2f}")

    elif tool == "Shopping":
        with st.expander("🛒 Shopping List", expanded=True):
            shdf = pd.read_csv(FILES["shopping"])
            item = st.text_input("Item")
            if st.button("Add Item"):
                new_s = pd.DataFrame([[st.session_state.username, item, "Pending"]], columns=shdf.columns)
                pd.concat([shdf, new_s]).to_csv(FILES["shopping"], index=False)
                st.rerun()
            st.write(shdf[shdf['username']==st.session_state.username])

# --- 2. WALLET (FIXED) ---
elif selected == "💰 Wallet":
    st.title("💸 Wallet Management")
    with st.expander("➕ නව ගනුදෙනුවක්"):
        c1, c2, c3 = st.columns(3)
        ty = c1.selectbox("Type", ["Expense", "Income"])
        cat = c2.selectbox("Category", ["Food", "Rent", "Salary", "Fuel", "Bills", "Health", "Other"])
        amt = c3.number_input("Amount", min_value=0)
        ds = st.text_input("Description")
        if st.button("Save"):
            new_t = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), cat, ds, amt, ty]], columns=tdf.columns)
            pd.concat([tdf, new_t]).to_csv(FILES["trans"], index=False)
            st.success("Saved!")
            st.rerun()
    
    if not user_tdf.empty:
        fig = px.pie(user_tdf[user_tdf['type']=="Expense"], values='amt', names='cat', hole=0.4, title="වියදම් බෙදී ඇති ආකාරය")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(user_tdf.tail(10), use_container_width=True)

# --- 3. TASKS & GOALS ---
elif selected == "✅ Tasks & Goals":
    st.title("🎯 Tasks & Savings")
    t1, t2 = st.tabs(["📝 Tasks", "🐷 Savings"])
    
    with t1:
        tkdf = pd.read_csv(FILES["tasks"])
        with st.form("tk_form"):
            name = st.text_input("Task Name")
            prio = st.select_slider("Priority", ["Low", "Medium", "High"])
            if st.form_submit_button("Add"):
                new_tk = pd.DataFrame([[st.session_state.username, name, "Pending", prio, str(datetime.now().date())]], columns=tkdf.columns)
                pd.concat([tkdf, new_tk]).to_csv(FILES["tasks"], index=False)
                st.rerun()
        
        for i, r in tkdf[tkdf['username'] == st.session_state.username].iterrows():
            col1, col2 = st.columns([0.8, 0.2])
            if r['status'] == "Pending":
                col1.warning(f"**{r['task']}**")
                if col2.button("Done", key=f"k_{i}"):
                    tkdf.at[i, 'status'] = "Done"
                    tkdf.to_csv(FILES["tasks"], index=False)
                    st.rerun()
            else: col1.success(f"~~{r['task']}~~ ✅")

    with t2:
        sdf = pd.read_csv(FILES["savings"])
        with st.expander("🎯 New Goal"):
            gn = st.text_input("Goal Name")
            gt = st.number_input("Target", min_value=1)
            if st.button("Set"):
                new_g = pd.DataFrame([[st.session_state.username, gn, gt, 0]], columns=sdf.columns)
                pd.concat([sdf, new_g]).to_csv(FILES["savings"], index=False)
                st.rerun()
        
        for i, r in sdf[sdf['username'] == st.session_state.username].iterrows():
            st.write(f"**{r['goal']}** ({r['current']}/{r['target']})")
            st.progress(min(r['current']/r['target'], 1.0))
            amt_s = st.number_input("Add Amount", min_value=0, key=f"s_{i}")
            if st.button("Update", key=f"b_{i}"):
                sdf.at[i, 'current'] += amt_s
                sdf.to_csv(FILES["savings"], index=False)
                st.rerun()
