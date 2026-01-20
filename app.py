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

# --- LOTTIE ANIMATION LOADER (With Error Handling) ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json()
    except:
        return None

# Working Lottie URLs
lottie_main = load_lottieurl("https://lottie.host/802b1660-3948-4362-a548-56549a930129/Z7vP4U9W6y.json")
lottie_wallet = load_lottieurl("https://lottie.host/68291b5c-420b-4682-9654-e6995641777d/1Wf29Jj9Y1.json")

# --- THEME MANAGEMENT ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# CSS for Card Designs and Floating Action Button
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
FILES = {"users": "u_v4.csv", "trans": "t_v4.csv", "tasks": "tk_v4.csv", "cats": "c_v4.csv", "config": "cfg_v4.csv"}
def init_dbs():
    for f, cols in [("users", ["u", "p", "r", "a"]), ("trans", ["u", "d", "c", "ds", "amt", "ty"]), 
                    ("tasks", ["u", "t", "s", "p", "d"]), ("cats", ["u", "n"]), ("config", ["u", "lim"])]:
        if not os.path.exists(FILES[f]): pd.DataFrame(columns=cols).to_csv(FILES[f], index=False)
init_dbs()

# --- AUTH SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'username': ""})
def make_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

# --- LOGIN / REGISTER PAGE ---
if not st.session_state.logged_in:
    col1, col2 = st.columns([1, 1])
    with col1:
        if lottie_main: st_lottie(lottie_main, height=400)
        else: st.title("💎 Nexus Ultra Pro")
    with col2:
        st.subheader("Welcome to the Next Level")
        mode = st.tabs(["🔑 Login", "📝 Register"])
        with mode[0]:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("Log In"):
                udf = pd.read_csv(FILES["users"])
                if not udf[(udf['u']==u) & (udf['p']==make_hash(p))].empty:
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.rerun()
                else: st.error("Invalid Credentials")
        with mode[1]:
            nu = st.text_input("New Username", key="reg_u")
            np = st.text_input("New Password", type="password", key="reg_p")
            if st.button("Create Account"):
                udf = pd.read_csv(FILES["users"])
                if nu not in udf['u'].values:
                    new_u = pd.DataFrame([[nu, make_hash(np), "User", True]], columns=udf.columns)
                    pd.concat([udf, new_u]).to_csv(FILES["users"], index=False)
                    st.success("Registration Successful!")
                else: st.warning("Username Taken")
    st.stop()

# --- MAIN NAVIGATION (Streamlit Option Menu) ---
with st.sidebar:
    st.markdown(f"### 👋 Hi, {st.session_state.username}")
    selected = option_menu(
        "Nexus Menu", ["Dashboard", "Wallet", "Analytics", "Settings"],
        icons=['house', 'wallet2', 'bar-chart-line', 'gear'], menu_icon="cast", default_index=0
    )
    if st.button("🌓 Toggle Dark/Light"):
        st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
        st.rerun()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- FLOATING ACTION BUTTON ---
st.markdown('<div class="fab">+</div>', unsafe_allow_html=True)

# --- DATA LOAD ---
tdf = pd.read_csv(FILES["trans"])
user_tdf = tdf[tdf['u'] == st.session_state.username]

# --- 1. DASHBOARD ---
if selected == "Dashboard":
    st.title("🚀 Financial Pulse")
    
    # Budget Alert Logic
    cfg = pd.read_csv(FILES["config"])
    u_cfg = cfg[cfg['u'] == st.session_state.username]
    if not u_cfg.empty:
        limit = u_cfg.iloc[0]['lim']
        total_exp = user_tdf[user_tdf['ty']=="Expense"]['amt'].sum()
        if total_exp > limit * 0.8:
            st.error(f"⚠️ Budget Alert: ඔබ ඔබේ මාසික සීමාවෙන් (රු. {limit}) 80% ඉක්මවා ඇත!")

    c1, c2, c3 = st.columns(3)
    inc = user_tdf[user_tdf['ty']=="Income"]['amt'].sum()
    exp = user_tdf[user_tdf['ty']=="Expense"]['amt'].sum()
    
    c1.markdown(f'<div class="metric-card"><h4>සම්පූර්ණ ශේෂය</h4><h2>රු. {inc-exp:,.0f}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h4>මුළු ආදායම</h4><h2>රු. {inc:,.0f}</h2></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h4>මුළු වියදම</h4><h2>රු. {exp:,.0f}</h2></div>', unsafe_allow_html=True)

    st.subheader("🗓️ මෑතකාලීන ගනුදෙනු")
    st.dataframe(user_tdf.tail(10), use_container_width=True)

# --- 2. WALLET ---
elif selected == "Wallet":
    st.title("💰 Wallet Manager")
    
    col_a, col_b = st.columns([1, 1])
    with col_a:
        with st.form("entry_form", clear_on_submit=True):
            ty = st.selectbox("වර්ගය", ["Expense", "Income"])
            amt = st.number_input("මුදල (Rs.)", min_value=0)
            
            # Category Selection
            cat_df = pd.read_csv(FILES["cats"])
            u_cats = cat_df[cat_df['u'] == st.session_state.username]['n'].tolist()
            final_cats = sorted(list(set(["Food", "Rent", "Salary", "Fuel", "Bills"] + u_cats)))
            cat = st.selectbox("Category", final_cats)
            
            ds = st.text_input("විස්තරය")
            if st.form_submit_button("ගනුදෙනුව සුරකින්න"):
                new_entry = pd.DataFrame([[st.session_state.username, str(datetime.now().date()), cat, ds, amt, ty]], columns=tdf.columns)
                pd.concat([tdf, new_entry]).to_csv(FILES["trans"], index=False)
                st.success("Saved Successfully!")
                st.rerun()

    with col_b:
        if lottie_wallet: st_lottie(lottie_wallet, height=250)
        st.subheader("📥 වාර්තා ලබාගන්න")
        if st.button("Excel වාර්තාව බාගත කරන්න"):
            user_tdf.to_excel("My_Finances.xlsx", index=False)
            st.success("Excel File එක සූදානම්!")

# --- 3. ANALYTICS ---
elif selected == "Analytics":
    st.title("📊 වියදම් විශ්ලේෂණය")
    if not user_tdf.empty:
        fig1 = px.pie(user_tdf[user_tdf['ty']=="Expense"], values='amt', names='c', hole=0.4, title="වියදම් බෙදී ඇති ආකාරය (By Category)")
        st.plotly_chart(fig1, use_container_width=True)
        
        fig2 = px.line(user_tdf.sort_values('d'), x='d', y='amt', color='ty', title="කාලයත් සමඟ ආදායම්/වියදම් වෙනස් වීම")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("විශ්ලේෂණය කිරීමට දත්ත කිසිවක් නැත.")

# --- 4. SETTINGS ---
elif selected == "Settings":
    st.title("⚙️ සැකසුම් (Settings)")
    
    t1, t2 = st.tabs(["📊 Budget Limit", "📂 Custom Categories"])
    
    with t1:
        st.subheader("මාසික වියදම් සීමාව සකසන්න")
        cfg_df = pd.read_csv(FILES["config"])
        u_cfg = cfg_df[cfg_df['u'] == st.session_state.username]
        curr_lim = u_cfg.iloc[0]['lim'] if not u_cfg.empty else 0
        
        new_lim = st.number_input("උපරිම සීමාව (රු.)", value=int(curr_lim))
        if st.button("සීමාව Update කරන්න"):
            new_cfg = pd.DataFrame([[st.session_state.username, new_lim]], columns=cfg_df.columns)
            pd.concat([cfg_df[cfg_df['u'] != st.session_state.username], new_cfg]).to_csv(FILES["config"], index=False)
            st.success("Budget Limit එක Update වුණා!")

    with t2:
        st.subheader("ඔබේම Categories සාදන්න")
        cat_df = pd.read_csv(FILES["cats"])
        new_cat = st.text_input("Category නම")
        if st.button("Add Category"):
            new_c_row = pd.DataFrame([[st.session_state.username, new_cat]], columns=cat_df.columns)
            pd.concat([cat_df, new_c_row]).to_csv(FILES["cats"], index=False)
            st.success("Category Added!")
            st.rerun()
