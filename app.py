import streamlit as st
import pandas as pd
import os
import hashlib
import plotly.express as px
from datetime import datetime
import time
import requests
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu

# --- APP CONFIG ---
st.set_page_config(page_title="Nexus Ultra Pro", page_icon="💎", layout="wide")

# --- LOTTIE ANIMATION LOADER ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json()
    except:
        return None

# ලෝටී ඇනිමේෂන් ලින්ක්ස් (අලුත් ලින්ක්ස්)
lottie_main = load_lottieurl("https://lottie.host/802b1660-3948-4362-a548-56549a930129/Z7vP4U9W6y.json")
lottie_wallet = load_lottieurl("https://lottie.host/68291b5c-420b-4682-9654-e6995641777d/1Wf29Jj9Y1.json")

# --- THEME MANAGEMENT ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

t_color = "#333" if st.session_state.theme == 'light' else "#fafafa"
b_color = "#f8f9fa" if st.session_state.theme == 'light' else "#0e1117"
c_color = "white" if st.session_state.theme == 'light' else "#1e2130"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {b_color}; color: {t_color}; }}
    .metric-card {{ 
        background: {c_color}; padding: 25px; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-left: 8px solid #6366f1;
        margin-bottom: 20px; color: {t_color};
    }}
    .fab {{
        position: fixed; bottom: 30px; right: 30px; background: #6366f1;
        color: white; width: 60px; height: 60px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 1000;
    }}
    </style>
""", unsafe_allow_html=True)

# --- DB INITIALIZATION ---
FILES = {"users": "u_v5.csv", "trans": "t_v5.csv", "tasks": "tk_v5.csv", "cats": "c_v5.csv", "config": "cfg_v5.csv"}

def make_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def init_dbs():
    # Admin ගිණුම සාදන කොටම Username: admin සහ Password: 123 ලෙස ඇතුළත් කිරීම
    if not os.path.exists(FILES["users"]):
        admin_pw = make_hash("123") # මුරපදය 123 ලෙස සෙට් කිරීම
        pd.DataFrame([["admin", admin_pw, "Admin", True]], columns=["u", "p", "r", "a"]).to_csv(FILES["users"], index=False)
    
    defaults = {
        "trans": ["u", "d", "c", "ds", "amt", "ty"],
        "tasks": ["u", "t", "s", "p", "d"],
        "cats": ["u", "n"],
        "config": ["u", "lim"]
    }
    for key, cols in defaults.items():
        if not os.path.exists(FILES[key]): pd.DataFrame(columns=cols).to_csv(FILES[key], index=False)

init_dbs()

# --- AUTH SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'username': ""})

# --- LOGIN / REGISTER PAGE ---
if not st.session_state.logged_in:
    col1, col2 = st.columns([1, 1])
    with col1:
        if lottie_main: st_lottie(lottie_main, height=400, key="login_anim")
        else: st.title("💎 Nexus Ultra Pro")
    with col2:
        st.subheader("Welcome Back")
        mode = st.tabs(["🔑 Login", "📝 Register"])
        with mode[0]:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("Log In"):
                udf = pd.read_csv(FILES["users"])
                # මෙතනදී hashed password එක සමඟ පරීක්ෂා කෙරේ
                if not udf[(udf['u']==u) & (udf['p']==make_hash(p))].empty:
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.rerun()
                else: st.error("වැරදි පරිශීලක නමක් හෝ මුරපදයක්! (Try admin/123)")
        with mode[1]:
            nu = st.text_input("New Username", key="reg_u")
            np = st.text_input("New Password", type="password", key="reg_p")
            if st.button("Create Account"):
                udf = pd.read_csv(FILES["users"])
                if nu not in udf['u'].values:
                    new_u = pd.DataFrame([[nu, make_hash(np), "User", True]], columns=udf.columns)
                    pd.concat([udf, new_u]).to_csv(FILES["users"], index=False)
                    st.success("ගිණුම සාර්ථකව සෑදුවා! දැන් Login වෙන්න.")
    st.stop()

# --- MAIN NAVIGATION ---
with st.sidebar:
    st.markdown(f"### 👋 Hi, {st.session_state.username}")
    selected = option_menu(
        "Main Menu", ["Dashboard", "Wallet", "Analytics", "Settings"],
        icons=['house', 'wallet2', 'bar-chart-line', 'gear'], menu_icon="cast", default_index=0
    )
    if st.button("🌓 Theme Switch"):
        st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
        st.rerun()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- DASHBOARD LOGIC ---
tdf = pd.read_csv(FILES["trans"])
user_tdf = tdf[tdf['u'] == st.session_state.username]

if selected == "Dashboard":
    st.title("🚀 Financial Dashboard")
    
    # Metrics
    c1, c2, c3 = st.columns(3)
    inc = user_tdf[user_tdf['ty']=="Income"]['amt'].sum()
    exp = user_tdf[user_tdf['ty']=="Expense"]['amt'].sum()
    
    c1.markdown(f'<div class="metric-card"><h4>ශේෂය (Balance)</h4><h2>රු. {inc-exp:,.2f}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h4>ආදායම (Income)</h4><h2>රු. {inc:,.2f}</h2></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h4>වියදම (Expense)</h4><h2>රු. {exp:,.2f}</h2></div>', unsafe_allow_html=True)

    st.subheader("මෑතකාලීන ගනුදෙනු")
    st.dataframe(user_tdf.tail(10), use_container_width=True)

elif selected == "Wallet":
    st.title("💰 Wallet Management")
    with st.form("wallet_form"):
        col_t, col_a, col_c = st.columns(3)
        t_type = col_t.selectbox("Type", ["Expense", "Income"])
        t_amt = col_a.number_input("Amount (Rs.)", min_value=0)
        t_cat = col_c.text_input("Category (e.g. Food, Fuel)")
        t_desc = st.text_input("Description")
        if st.form_submit_button("Save Transaction"):
            new_t = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), t_cat, t_desc, t_amt, t_type]], columns=tdf.columns)
            pd.concat([tdf, new_t]).to_csv(FILES["trans"], index=False)
            st.success("ගනුදෙනුව සාර්ථකව සුරැකුණා!")
            st.rerun()

elif selected == "Analytics":
    st.title("📊 Data Analytics")
    if not user_tdf.empty:
        fig = px.pie(user_tdf[user_tdf['ty']=="Expense"], values='amt', names='c', title="වියදම් බෙදී ඇති ආකාරය")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("පෙන්වීමට දත්ත කිසිවක් නැත.")

elif selected == "Settings":
    st.title("⚙️ Settings")
    st.write(f"දැනට Log වී ඇත්තේ: **{st.session_state.username}**")
    # තව සෙටින්ග්ස් මෙතනට එක් කළ හැක
