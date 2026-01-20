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

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Nexus Pro Elite", page_icon="💎", layout="wide")

# --- 2. SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': "", 'role': "User", 'theme': "light", 'active_tool': "None"})

# --- 3. THEME & CSS (FULL INTERFACE FIX) ---
t = {"bg": "#f8f9fa", "card": "white", "text": "#333"} if st.session_state.theme == "light" else {"bg": "#0e1117", "card": "#1e2130", "text": "#fafafa"}

st.markdown(f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    .metric-card {{ 
        background: {t['card']}; padding: 25px; border-radius: 20px; 
        box-shadow: 0 10px 15px rgba(0,0,0,0.1); border-bottom: 5px solid #6366f1;
        color: {t['text']}; margin-bottom: 20px; text-align: center;
    }}
    /* Big Button Grid Styling */
    div.stButton > button {{
        border-radius: 20px; font-weight: 700; height: 100px; font-size: 1.2rem;
        background-color: {t['card']}; color: {t['text']}; border: 2px solid #6366f1;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: 0.3s;
    }}
    div.stButton > button:hover {{ background-color: #6366f1; color: white; transform: scale(1.02); }}
    </style>
""", unsafe_allow_html=True)

# --- 4. DB INITIALIZATION (ALL FILES) ---
FILES = {
    "users": "db_users.csv", "trans": "db_trans.csv", "tasks": "db_tasks.csv", 
    "savings": "db_savings.csv", "cats": "db_cats.csv", "bills": "db_bills.csv", 
    "water": "db_water.csv", "journal": "db_journal.csv", "shopping": "db_shopping.csv"
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
                    "cats": ["username", "category_name"],
                    "bills": ["username", "name", "amt", "due", "status"],
                    "water": ["username", "date", "liters"],
                    "journal": ["username", "date", "note"],
                    "shopping": ["username", "item", "status"]
                }[key]
                pd.DataFrame(columns=cols).to_csv(name, index=False)

init_dbs()

# --- 5. AUTHENTICATION ---
if not st.session_state.logged_in:
    st.title("💎 Nexus Pro Elite")
    tab_l, tab_r = st.tabs(["🔑 Login", "📝 Register"])
    with tab_l:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            udf = pd.read_csv(FILES["users"])
            res = udf[(udf['username']==u) & (udf['password']==make_hash(p))]
            if not res.empty and res.iloc[0]['approved']:
                st.session_state.update({'logged_in': True, 'username': u, 'role': res.iloc[0]['role']})
                st.rerun()
            else: st.error("Login Failed or Not Approved.")
    with tab_r:
        nu = st.text_input("New User")
        np = st.text_input("New Pass", type="password")
        if st.button("Register"):
            udf = pd.read_csv(FILES["users"])
            new_u = pd.DataFrame([[nu, make_hash(np), "User", False]], columns=udf.columns)
            pd.concat([udf, new_u]).to_csv(FILES["users"], index=False)
            st.success("Wait for Admin Approval.")
    st.stop()

# --- 6. DATA LOADING (FIXING ALL ERRORS) ---
tdf = pd.read_csv(FILES["trans"])
user_tdf = tdf[tdf['username'] == st.session_state.username]
tkdf = pd.read_csv(FILES["tasks"])
user_tk = tkdf[tkdf['username'] == st.session_state.username]
sdf = pd.read_csv(FILES["savings"])
user_sd = sdf[sdf['username'] == st.session_state.username]

# --- 7. SMART INPUT LOGIC ---
def smart_save(text):
    nums = re.findall(r'\d+', text)
    if nums:
        amt = float(nums[0])
        cat = "Food" if any(x in text.lower() for x in ["කෑම", "food", "kema"]) else "Other"
        new_row = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), cat, text, amt, "Expense"]], columns=tdf.columns)
        pd.concat([tdf, new_row]).to_csv(FILES["trans"], index=False)
        return True
    return False

# --- 8. SIDEBAR ---
with st.sidebar:
    selected = option_menu("Nexus Pro", ["🏠 Dashboard", "💰 Wallet", "✅ Tasks & Goals", "👨‍💼 Admin Panel" if st.session_state.role=="Admin" else "⚙️ Settings"], 
        icons=['house', 'wallet2', 'list-check', 'person-badge'], default_index=0)
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- 9. DASHBOARD (FIXED INTERFACE) ---
if selected == "🏠 Dashboard":
    st.title(f"Welcome, {st.session_state.username}! 🚀")
    
    # 🎤 Smart Input
    with st.container():
        cmd = st.text_input("🎤 Smart Input (උදා: කෑම 500)", placeholder="Type & Press Enter...")
        if cmd:
            if smart_save(cmd): st.success("Added to Wallet!"); st.rerun()

    # Metrics
    inc = user_tdf[user_tdf['type']=="Income"]['amt'].sum()
    exp = user_tdf[user_tdf['type']=="Expense"]['amt'].sum()
    prog = (len(user_tk[user_tk['status']=="Done"])/len(user_tk)*100) if not user_tk.empty else 0
    
    m1, m2, m3 = st.columns(3)
    m1.markdown(f"<div class='metric-card'><h4>💵 Wallet</h4><h2>රු. {inc-exp:,.0f}</h2></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-card'><h4>📈 Efficiency</h4><h2>{prog:.0f}%</h2></div>", unsafe_allow_html=True)
    m3.markdown(f"<div class='metric-card'><h4>🐷 Savings</h4><h2>රු. {user_sd['current'].sum():,.0f}</h2></div>", unsafe_allow_html=True)

    st.subheader("🛠️ Life Management Tools")
    c1, c2, c3 = st.columns(3)
    if c1.button("💰\nBill Reminders"): st.session_state.active_tool = "Bills"
    if c2.button("💧\nWater Tracker"): st.session_state.active_tool = "Water"
    if c3.button("📓\nJournal Notes"): st.session_state.active_tool = "Journal"
    
    c4, c5, c6 = st.columns(3)
    if c4.button("📉\nNet Worth"): st.session_state.active_tool = "NetWorth"
    if c5.button("🛒\nShopping List"): st.session_state.active_tool = "Shopping"
    if c6.button("❌\nClose Tool"): st.session_state.active_tool = "None"

    # --- TOOLS LOGIC ---
    tool = st.session_state.active_tool
    if tool == "Bills":
        st.subheader("🔔 Bill Reminders")
        bdf = pd.read_csv(FILES["bills"])
        with st.expander("Add New Bill", expanded=True):
            bn = st.text_input("Bill Name")
            ba = st.number_input("Amount", min_value=0)
            if st.button("Save Bill"):
                new_b = pd.DataFrame([[st.session_state.username, bn, ba, str(datetime.now().date()), "Unpaid"]], columns=bdf.columns)
                pd.concat([bdf, new_b]).to_csv(FILES["bills"], index=False); st.rerun()
        st.dataframe(bdf[bdf['username']==st.session_state.username], use_container_width=True)

    elif tool == "Water":
        st.subheader("💧 Water Tracker")
        wdf = pd.read_csv(FILES["water"])
        vol = st.slider("Liters Today", 0.0, 5.0, 2.0)
        if st.button("Update Water"):
            new_w = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), vol]], columns=wdf.columns)
            pd.concat([wdf, new_w]).to_csv(FILES["water"], index=False); st.success("Updated!")

    elif tool == "Journal":
        st.subheader("📓 Daily Journal")
        jdf = pd.read_csv(FILES["journal"])
        note = st.text_area("How was your day?")
        if st.button("Save Note"):
            new_j = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), note]], columns=jdf.columns)
            pd.concat([jdf, new_j]).to_csv(FILES["journal"], index=False); st.success("Saved!")

    elif tool == "NetWorth":
        st.subheader("📉 Your Total Net Worth")
        st.info(f"Wallet Balance: රු. {inc-exp:,.2f}")
        st.info(f"Total Savings: රු. {user_sd['current'].sum():,.2f}")
        st.metric("NET WORTH", f"රු. {(inc-exp) + user_sd['current'].sum():,.2f}")

    elif tool == "Shopping":
        st.subheader("🛒 Shopping List")
        shdf = pd.read_csv(FILES["shopping"])
        item = st.text_input("Item Name")
        if st.button("Add to List"):
            new_s = pd.DataFrame([[st.session_state.username, item, "Pending"]], columns=shdf.columns)
            pd.concat([shdf, new_s]).to_csv(FILES["shopping"], index=False); st.rerun()
        st.table(shdf[shdf['username']==st.session_state.username])

# --- 10. WALLET (ORIGINAL FIX) ---
elif selected == "💰 Wallet":
    st.title("💸 Wallet Management")
    with st.expander("➕ නව ගනුදෙනුවක්", expanded=True):
        col1, col2, col3 = st.columns(3)
        ty = col1.selectbox("Type", ["Expense", "Income"])
        cat = col2.selectbox("Category", ["Food", "Rent", "Salary", "Fuel", "Bills", "Health", "Other"])
        amt = col3.number_input("Amount", min_value=0)
        ds = st.text_input("Description")
        if st.button("Save Transaction"):
            new_t = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), cat, ds, amt, ty]], columns=tdf.columns)
            pd.concat([tdf, new_t]).to_csv(FILES["trans"], index=False); st.rerun()
    
    if not user_tdf.empty:
        fig = px.pie(user_tdf[user_tdf['type']=="Expense"], values='amt', names='cat', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(user_tdf.tail(10), use_container_width=True)

# --- 11. TASKS & GOALS (ORIGINAL FIX) ---
elif selected == "✅ Tasks & Goals":
    st.title("🎯 Tasks & Savings")
    t1, t2 = st.tabs(["📝 Tasks", "🐷 Savings"])
    with t1:
        with st.form("task_f"):
            tn = st.text_input("Task Name")
            tp = st.select_slider("Priority", ["Low", "Medium", "High"])
            if st.form_submit_button("Add Task"):
                new_tk = pd.DataFrame([[st.session_state.username, tn, "Pending", tp, str(datetime.now().date())]], columns=tkdf.columns)
                pd.concat([tkdf, new_tk]).to_csv(FILES["tasks"], index=False); st.rerun()
        for i, r in tkdf[tkdf['username']==st.session_state.username].iterrows():
            c1, c2 = st.columns([0.8, 0.2])
            if r['status']=="Pending":
                c1.warning(r['task'])
                if c2.button("Done", key=f"t_{i}"):
                    tkdf.at[i, 'status'] = "Done"; tkdf.to_csv(FILES["tasks"], index=False); st.rerun()
            else: c1.success(f"~~{r['task']}~~")

    with t2:
        with st.expander("Set New Goal"):
            gn = st.text_input("Goal Name")
            gt = st.number_input("Target", min_value=1)
            if st.button("Set"):
                new_g = pd.DataFrame([[st.session_state.username, gn, gt, 0]], columns=sdf.columns)
                pd.concat([sdf, new_g]).to_csv(FILES["savings"], index=False); st.rerun()
        for i, r in sdf[sdf['username']==st.session_state.username].iterrows():
            st.write(f"**{r['goal']}**")
            st.progress(min(r['current']/r['target'], 1.0))
            amt_in = st.number_input("Add", min_value=0, key=f"s_{i}")
            if st.button("Update", key=f"b_{i}"):
                sdf.at[i, 'current'] += amt_in; sdf.to_csv(FILES["savings"], index=False); st.rerun()

# --- 12. ADMIN PANEL ---
elif selected == "👨‍💼 Admin Panel":
    st.title("👨‍💼 Admin Control")
    udf = pd.read_csv(FILES["users"])
    for i, r in udf.iterrows():
        if r['username'] != 'admin':
            c1, c2, c3 = st.columns([2,1,1])
            c1.write(f"**{r['username']}** | {r['approved']}")
            if not r['approved'] and c2.button("Approve", key=f"a_{i}"):
                udf.at[i, 'approved'] = True; udf.to_csv(FILES["users"], index=False); st.rerun()
            if c3.button("Delete", key=f"d_{i}"):
                udf.drop(i).to_csv(FILES["users"], index=False); st.rerun()
