import streamlit as st
import pandas as pd
import os
import hashlib
import plotly.express as px
import requests
from datetime import datetime
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu

# --- APP CONFIG ---
st.set_page_config(page_title="Nexus Pro - Wealth & Productivity", page_icon="💎", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': "", 'role': "User", 'theme': "light"})

# --- LOTTIE LOADER ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

lottie_main = load_lottieurl("https://lottie.host/802b1660-3948-4362-a548-56549a930129/Z7vP4U9W6y.json")

# --- THEME & CSS (Responsive & Mobile Friendly) ---
t = {"bg": "#f8f9fa", "card": "white", "text": "#333"} if st.session_state.theme == "light" else {"bg": "#0e1117", "card": "#1e2130", "text": "#fafafa"}

st.markdown(f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    .metric-card {{ 
        background: {t['card']}; padding: 20px; border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-bottom: 5px solid #6366f1;
        color: {t['text']}; margin-bottom: 15px; text-align: center;
    }}
    /* Mobile responsive adjustments */
    @media (max-width: 640px) {{
        .metric-card h2 {{ font-size: 1.5rem; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 10px; }}
    }}
    div.stButton > button {{ border-radius: 12px; font-weight: 600; width: 100%; }}
    </style>
""", unsafe_allow_html=True)

# --- DB INITIALIZATION ---
FILES = {
    "users": "users_v6.csv", "trans": "trans_v6.csv", 
    "tasks": "tasks_v6.csv", "savings": "savings_v6.csv", 
    "config": "config_v6.csv", "cats": "cats_v6.csv"
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
        "cats": ["username", "category_name"]
    }
    for key, cols in defaults.items():
        if not os.path.exists(FILES[key]): pd.DataFrame(columns=cols).to_csv(FILES[key], index=False)

init_dbs()

# --- AUTHENTICATION ---
if not st.session_state.logged_in:
    col1, col2 = st.columns([1, 1])
    with col1:
        if lottie_main: st_lottie(lottie_main, height=300)
        else: st.title("💎 Nexus Pro")
    with col2:
        st.subheader("Nexus Pro Login")
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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👋 Welcome, {st.session_state.username}")
    menu_items = ["🏠 Dashboard", "💰 Wallet", "✅ Tasks & Goals", "⚙️ Settings"]
    if st.session_state.role == "Admin": menu_items.append("👨‍💼 Admin Panel")
    
    selected = option_menu("Nexus Menu", menu_items, icons=['house', 'wallet2', 'list-check', 'gear', 'person-badge'], menu_icon="cast", default_index=0)
    
    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- 1. DASHBOARD ---
if selected == "🏠 Dashboard":
    st.title("🚀 Pulse Dashboard")
    tdf = pd.read_csv(FILES["trans"])
    user_tdf = tdf[tdf['username'] == st.session_state.username]
    
    inc = user_tdf[user_tdf['type']=="Income"]['amt'].sum()
    exp = user_tdf[user_tdf['type']=="Expense"]['amt'].sum()
    
    tkdf = pd.read_csv(FILES["tasks"])
    user_tk = tkdf[tkdf['username'] == st.session_state.username]
    prog = (len(user_tk[user_tk['status']=="Done"])/len(user_tk)*100) if not user_tk.empty else 0

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: st.markdown(f"<div class='metric-card'><h4>💵 අතේ ඇති මුදල</h4><h2>රු. {inc-exp:,.0f}</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h4>📊 මූල්‍ය මට්ටම</h4><h2>{'Stable' if inc>exp else 'Warning'}</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h4>✅ Productivity</h4><h2>{prog:.0f}%</h2></div>", unsafe_allow_html=True)

    st.subheader("🗓️ මෑතකාලීන ගනුදෙනු")
    st.dataframe(user_tdf.tail(5), use_container_width=True)

# --- 2. WALLET (With Category Management) ---
elif selected == "💰 Wallet":
    st.title("💸 Wallet Management")
    
    # Load Transactions and Categories
    tdf = pd.read_csv(FILES["trans"])
    cat_df = pd.read_csv(FILES["cats"])
    
    # Get user specific categories + defaults
    default_cats = ["Food", "Salary", "Rent", "Bills", "Health", "Fuel"]
    user_cats = cat_df[cat_df['username'] == st.session_state.username]['category_name'].tolist()
    all_cats = list(set(default_cats + user_cats))

    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        with st.expander("➕ නව ගනුදෙනුවක්", expanded=True):
            ty = st.selectbox("Type", ["Expense", "Income"])
            cat = st.selectbox("Category", all_cats)
            amt = st.number_input("Amount", min_value=0)
            ds = st.text_input("Description")
            if st.button("Save Transaction"):
                new_t = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), cat, ds, amt, ty]], columns=tdf.columns)
                pd.concat([tdf, new_t]).to_csv(FILES["trans"], index=False)
                st.success("ගනුදෙනුව සුරැකුණා!")
                st.rerun()

    with col_b:
        with st.expander("📁 නව Category එකක් එක් කරන්න"):
            new_cat_name = st.text_input("Category Name (e.g., Gym, Gifts)")
            if st.button("Add Category"):
                if new_cat_name and new_cat_name not in all_cats:
                    new_c = pd.DataFrame([[st.session_state.username, new_cat_name]], columns=cat_df.columns)
                    pd.concat([cat_df, new_c]).to_csv(FILES["cats"], index=False)
                    st.success(f"{new_cat_name} එක් කළා!")
                    st.rerun()
                else:
                    st.warning("නම ඇතුළත් කරන්න හෝ දැනටමත් පවතී.")

    st.divider()
    user_tdf = tdf[tdf['username'] == st.session_state.username]
    if not user_tdf.empty:
        fig = px.pie(user_tdf[user_tdf['type']=="Expense"], values='amt', names='cat', hole=0.4, title="වියදම් විශ්ලේෂණය")
        st.plotly_chart(fig, use_container_width=True)

# --- 3. TASKS & GOALS ---
elif selected == "✅ Tasks & Goals":
    st.title("🎯 Tasks & Savings")
    t1, t2 = st.tabs(["📝 Tasks", "🐷 Savings"])
    
    with t1:
        tkdf = pd.read_csv(FILES["tasks"])
        with st.form("tk_form", clear_on_submit=True):
            name = st.text_input("Task Name")
            prio = st.select_slider("Priority", ["Low", "Medium", "High"])
            if st.form_submit_button("Add Task"):
                new_tk = pd.DataFrame([[st.session_state.username, name, "Pending", prio, str(datetime.now().date())]], columns=tkdf.columns)
                pd.concat([tkdf, new_tk]).to_csv(FILES["tasks"], index=False)
                st.rerun()
        
        for i, r in tkdf[tkdf['username'] == st.session_state.username].iterrows():
            c1, c2 = st.columns([0.8, 0.2])
            if r['status'] == "Pending":
                c1.info(f"📌 {r['task']} ({r['priority']})")
                if c2.button("Done", key=f"tk_{i}"):
                    tkdf.at[i, 'status'] = "Done"
                    tkdf.to_csv(FILES["tasks"], index=False)
                    st.rerun()
            else: c1.success(f"✅ ~~{r['task']}~~")

    with t2:
        sdf = pd.read_csv(FILES["savings"])
        with st.expander("🎯 New Savings Goal"):
            gn = st.text_input("Goal Name")
            gt = st.number_input("Target Amount", min_value=1)
            if st.button("Set Goal"):
                new_g = pd.DataFrame([[st.session_state.username, gn, gt, 0]], columns=sdf.columns)
                pd.concat([sdf, new_g]).to_csv(FILES["savings"], index=False)
                st.rerun()
        
        for i, r in sdf[sdf['username'] == st.session_state.username].iterrows():
            st.write(f"**{r['goal']}**")
            st.progress(min(r['current']/r['target'], 1.0))
            colx, coly = st.columns([0.7, 0.3])
            amt = colx.number_input(f"Add to {r['goal']}", min_value=0, key=f"s_{i}")
            if coly.button("Add", key=f"b_{i}"):
                sdf.at[i, 'current'] += amt
                sdf.to_csv(FILES["savings"], index=False)
                st.rerun()

# --- 4. SETTINGS ---
elif selected == "⚙️ Settings":
    st.title("⚙️ Profile Settings")
    st.info(f"User: {st.session_state.username} | Role: {st.session_state.role}")
    new_p = st.text_input("New Password", type="password")
    if st.button("Update Password"):
        udf = pd.read_csv(FILES["users"])
        udf.loc[udf['username'] == st.session_state.username, 'password'] = make_hash(new_p)
        udf.to_csv(FILES["users"], index=False)
        st.success("මුරපදය වෙනස් කළා!")

# --- 5. ADMIN PANEL ---
elif selected == "👨‍💼 Admin Panel":
    st.title("👨‍💼 Admin Management")
    udf = pd.read_csv(FILES["users"])
    for i, r in udf.iterrows():
        if r['username'] != 'admin':
            c1, c2, c3 = st.columns([2,1,1])
            status = "✅" if r['approved'] else "⏳"
            c1.write(f"{status} **{r['username']}** ({r['role']})")
            if not r['approved'] and c2.button("Approve", key=f"app_{i}"):
                udf.at[i, 'approved'] = True
                udf.to_csv(FILES["users"], index=False)
                st.rerun()
            if c3.button("Delete", key=f"del_{i}"):
                udf.drop(i).to_csv(FILES["users"], index=False)
                st.rerun()
