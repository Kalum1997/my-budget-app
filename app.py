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
st.set_page_config(page_title="Nexus Pro - Wealth & Productivity", page_icon="💎", layout="wide")

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
    .icon-box {{
        background: {t['card']}; border-radius: 20px; padding: 20px;
        text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        border: 1px solid #6366f1; cursor: pointer; height: 150px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }}
    div.stButton > button {{ border-radius: 12px; font-weight: 600; height: 3.5rem; width: 100%; }}
    </style>
""", unsafe_allow_html=True)

# --- DB INITIALIZATION ---
FILES = {
    "users": "users_v8.csv", "trans": "trans_v8.csv", 
    "tasks": "tasks_v8.csv", "savings": "savings_v8.csv", 
    "config": "config_v8.csv", "cats": "cats_v8.csv",
    "bills": "bills_v8.csv", "water": "water_v8.csv",
    "journal": "journal_v8.csv", "shopping": "shopping_v8.csv"
}

def make_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def init_dbs():
    if not os.path.exists(FILES["users"]):
        admin_pw = make_hash("123") 
        pd.DataFrame([["admin", admin_pw, "Admin", True]], columns=["username", "password", "role", "approved"]).to_csv(FILES["users"], index=False)
    
    defaults = {
        "trans": ["username", "date", "cat", "desc", "amt", "type"],
        "tasks": ["username", "task", "status", "priority", "date"],
        "savings": ["username", "goal", "target", "current"],
        "config": ["username", "monthly_limit"],
        "cats": ["username", "category_name"],
        "bills": ["username", "name", "amt", "due", "status"],
        "water": ["username", "date", "liters"],
        "journal": ["username", "date", "note"],
        "shopping": ["username", "item", "status"]
    }
    for key, cols in defaults.items():
        if not os.path.exists(FILES[key]): pd.DataFrame(columns=cols).to_csv(FILES[key], index=False)

init_dbs()

# --- SMART VOICE INPUT PROCESSOR ---
def smart_input_logic(text):
    nums = re.findall(r'\d+', text)
    if nums:
        amt = float(nums[0])
        category = "Food" if any(x in text for x in ["කෑම", "food", "kema"]) else "Other"
        tdf = pd.read_csv(FILES["trans"])
        new_row = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), category, text, amt, "Expense"]], columns=tdf.columns)
        pd.concat([tdf, new_row]).to_csv(FILES["trans"], index=False)
        return f"✅ රු. {amt} {category} ලෙස සුරැකුණා!"
    return "❌ මුදල හඳුනාගත නොහැක."

# --- AUTHENTICATION ---
if not st.session_state.logged_in:
    col1, col2 = st.columns([1, 1])
    with col1:
        if lottie_main: st_lottie(lottie_main, height=400)
        else: st.title("💎 Nexus Pro")
    with col2:
        st.subheader("Nexus Pro Management System")
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        with tab1:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Log In"):
                udf = pd.read_csv(FILES["users"])
                res = udf[(udf['username']==u) & (udf['password']==make_hash(p))]
                if not res.empty:
                    if res.iloc[0]['approved']:
                        st.session_state.update({'logged_in': True, 'username': u, 'role': res.iloc[0]['role']})
                        st.rerun()
                    else: st.error("Admin අනුමැතිය අවශ්‍යයි.")
                else: st.error("වැරදි Username හෝ Password.")
        with tab2:
            nu = st.text_input("New Username")
            np = st.text_input("New Password", type="password")
            if st.button("Register"):
                udf = pd.read_csv(FILES["users"])
                if nu in udf['username'].values: st.warning("නම පවතී.")
                else:
                    new_u = pd.DataFrame([[nu, make_hash(np), "User", False]], columns=udf.columns)
                    pd.concat([udf, new_u]).to_csv(FILES["users"], index=False)
                    st.success("සාර්ථකයි! Admin අනුමත කරන තෙක් රැඳී සිටින්න.")
    st.stop()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown(f"### 👋 Welcome, {st.session_state.username}")
    menu_items = ["🏠 Dashboard", "💰 Wallet", "✅ Tasks & Goals", "⚙️ Settings"]
    if st.session_state.role == "Admin": menu_items.append("👨‍💼 Admin Panel")
    selected = option_menu("Nexus Menu", menu_items, icons=['house', 'wallet2', 'list-check', 'gear', 'person-badge'], menu_icon="cast", default_index=0)
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- 1. DASHBOARD & NEW FEATURES ---
if selected == "🏠 Dashboard":
    st.title("🚀 Pulse Dashboard")
    
    # Smart Input Box
    with st.container():
        st.markdown("### 🎤 Smart Input")
        cmd = st.text_input("උදා: 'අද කෑමට 500' හෝ 'Bus 50'", placeholder="මෙහි සටහන් කරන්න...")
        if st.button("Add Automatically"):
            st.toast(smart_input_logic(cmd))

    # Existing Metrics
    tdf = pd.read_csv(FILES["trans"])
    user_tdf = tdf[tdf['username'] == st.session_state.username]
    inc = user_tdf[user_tdf['type']=="Income"]['amt'].sum()
    exp = user_tdf[user_tdf['type']=="Expense"]['amt'].sum()
    tkdf = pd.read_csv(FILES["tasks"])
    user_tk = tkdf[tkdf['username'] == st.session_state.username]
    prog = (len(user_tk[user_tk['status']=="Done"])/len(user_tk)*100) if not user_tk.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><h4>💵 අතේ ඇති මුදල</h4><h2>රු. {inc-exp:,.0f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h4>📊 මූල්‍ය මට්ටම</h4><h2>{'Excellent' if inc>exp*2 else 'Stable'}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h4>✅ Productivity</h4><h2>{prog:.0f}%</h2></div>", unsafe_allow_html=True)

    st.divider()
    
    # --- ALUTH FEATURES GRID (ICON BASED) ---
    st.subheader("🛠️ Life Trackers (Select One)")
    grid_col1, grid_col2, grid_col3 = st.columns(3)
    
    with grid_col1:
        if st.button("💰 Bill Reminders"): st.session_state.active_tool = "Bills"
    with grid_col2:
        if st.button("💧 Water Tracker"): st.session_state.active_tool = "Water"
    with grid_col3:
        if st.button("📓 Journal"): st.session_state.active_tool = "Journal"
        
    grid_col4, grid_col5, grid_col6 = st.columns(3)
    with grid_col4:
        if st.button("📈 Net Worth"): st.session_state.active_tool = "NetWorth"
    with grid_col5:
        if st.button("🛒 Shopping List"): st.session_state.active_tool = "Shopping"
    with grid_col6:
        if st.button("🏠 Clear Screen"): st.session_state.active_tool = "None"

    # Tool Execution Area
    tool = st.session_state.active_tool
    if tool == "Bills":
        with st.expander("🔔 Bill Reminders", expanded=True):
            bdf = pd.read_csv(FILES["bills"])
            bc1, bc2 = st.columns(2)
            bn = bc1.text_input("බිල්පතේ නම")
            ba = bc2.number_input("මුදල", min_value=0)
            if st.button("Save Bill"):
                new_b = pd.DataFrame([[st.session_state.username, bn, ba, str(datetime.now().date()), "Pending"]], columns=bdf.columns)
                pd.concat([bdf, new_b]).to_csv(FILES["bills"], index=False)
                st.rerun()
            st.table(bdf[bdf['username']==st.session_state.username])

    elif tool == "Water":
        with st.expander("💧 Water Tracker", expanded=True):
            wdf = pd.read_csv(FILES["water"])
            liters = st.number_input("බීපු වතුර ප්‍රමාණය (Liters)", step=0.5)
            if st.button("Add Log"):
                new_w = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), liters]], columns=wdf.columns)
                pd.concat([wdf, new_w]).to_csv(FILES["water"], index=False)
                st.success("Saved!")

    elif tool == "Journal":
        with st.expander("📓 Daily Journal", expanded=True):
            jdf = pd.read_csv(FILES["journal"])
            note = st.text_area("අද දවසේ විශේෂ සිදුවීම් සටහන් කරන්න...")
            if st.button("Save Journal"):
                new_j = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), note]], columns=jdf.columns)
                pd.concat([jdf, new_j]).to_csv(FILES["journal"], index=False)
                st.success("Note Saved!")

    elif tool == "NetWorth":
        with st.expander("📈 Total Net Worth", expanded=True):
            tdf = pd.read_csv(FILES["trans"])
            sdf = pd.read_csv(FILES["savings"])
            cash = tdf[tdf['username']==st.session_state.username]['amt'].sum()
            saved = sdf[sdf['username']==st.session_state.username]['current'].sum()
            st.metric("ඔබේ මුළු වටිනාකම", f"රු. {cash + saved:,.2f}")

    elif tool == "Shopping":
        with st.expander("🛒 Shopping List", expanded=True):
            shdf = pd.read_csv(FILES["shopping"])
            item = st.text_input("ගැනීමට ඇති දේ (Item Name)")
            if st.button("Add Item"):
                new_i = pd.DataFrame([[st.session_state.username, item, "Pending"]], columns=shdf.columns)
                pd.concat([shdf, new_i]).to_csv(FILES["shopping"], index=False)
                st.rerun()
            st.dataframe(shdf[shdf['username']==st.session_state.username])

# --- 2. WALLET (Original) ---
elif selected == "💰 Wallet":
    st.title("💸 Wallet Management")
    # ... (මුල් Wallet code එක එලෙසම පවතී)
    with st.expander("➕ නව ගනුදෙනුවක්"):
        c1, c2, c3 = st.columns(3)
        ty = c1.selectbox("Type", ["Expense", "Income"])
        cat = c2.selectbox("Category", ["Food", "Rent", "Salary", "Fuel", "Bills", "Health", "Other"])
        amt = c3.number_input("Amount", min_value=0)
        ds = st.text_input("Description")
        if st.button("Save"):
            new_t = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), cat, ds, amt, ty]], columns=user_tdf.columns)
            pd.concat([tdf, new_t]).to_csv(FILES["trans"], index=False)
            st.success("Saved!")
            st.rerun()
    if not user_tdf.empty:
        fig = px.pie(user_tdf[user_tdf['type']=="Expense"], values='amt', names='cat', hole=0.4, title="වියදම් බෙදී ඇති ආකාරය")
        st.plotly_chart(fig, use_container_width=True)

# --- 3. TASKS & GOALS (Original) ---
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
            amt = st.number_input("Add Amount", min_value=0, key=f"s_{i}")
            if st.button("Update", key=f"b_{i}"):
                sdf.at[i, 'current'] += amt
                sdf.to_csv(FILES["savings"], index=False)
                st.rerun()

# --- 4. SETTINGS & 5. ADMIN PANEL ---
elif selected == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.write(f"Username: {st.session_state.username}")
    new_p = st.text_input("Change Password", type="password")
    if st.button("Update Password"):
        udf = pd.read_csv(FILES["users"])
        udf.loc[udf['username'] == st.session_state.username, 'password'] = make_hash(new_p)
        udf.to_csv(FILES["users"], index=False)
        st.success("Updated!")

elif selected == "👨‍💼 Admin Panel":
    st.title("👨‍💼 Admin Control")
    udf = pd.read_csv(FILES["users"])
    for i, r in udf.iterrows():
        if r['username'] != 'admin':
            c1, c2, c3 = st.columns([2,1,1])
            c1.write(f"**{r['username']}** | {'Approved' if r['approved'] else 'Pending'}")
            if not r['approved'] and c2.button("Approve", key=f"a_{i}"):
                udf.at[i, 'approved'] = True
                udf.to_csv(FILES["users"], index=False)
                st.rerun()
            if c3.button("Delete", key=f"d_{i}"):
                udf.drop(i).to_csv(FILES["users"], index=False)
                st.rerun()
