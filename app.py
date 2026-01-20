import streamlit as st
import pandas as pd
import os
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# --- APP CONFIG ---
st.set_page_config(page_title="Nexus Pro - Personal Edition", page_icon="💎", layout="wide")

# --- 1. LOADING PAGE ---
if 'initialized' not in st.session_state:
    with st.empty():
        st.markdown("""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh;">
                <h1 style="font-size: 70px;">💎</h1>
                <h2 style="color: #6366f1; font-family: 'Inter', sans-serif;">Nexus Pro පද්ධතිය සූදානම් වෙමින් පවතී...</h2>
                <p style="color: gray;">ඔබේ සිහින සහ මූල්‍ය කළමනාකරණය සඳහා සියල්ල සකසමින්</p>
            </div>
        """, unsafe_allow_html=True)
        bar = st.progress(0)
        for p in range(100):
            time.sleep(0.01)
            bar.progress(p + 1)
        st.session_state['initialized'] = True
    st.rerun()

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: #f8f9fa; }
    .metric-card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-bottom: 5px solid #6366f1; }
    div.stButton > button { background: #6366f1; color: white; border-radius: 12px; width: 100%; font-weight: 600; border: none; height: 3rem; }
    .cat-tag { background: #e0e7ff; color: #4338ca; padding: 5px 15px; border-radius: 15px; margin-right: 5px; display: inline-block; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- DB INITIALIZATION ---
FILES = {
    "users": "users_pro_v3.csv",
    "trans": "trans_pro_v3.csv",
    "tasks": "tasks_pro_v3.csv",
    "savings": "savings_pro_v3.csv",
    "cats": "custom_cats_v3.csv" # අලුත් ෆයිල් එක
}

def init_dbs():
    if not os.path.exists(FILES["users"]):
        admin_pw = hashlib.sha256("password123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Admin", True]], columns=["username", "password", "role", "approved"]).to_csv(FILES["users"], index=False)
    
    defaults = {
        "trans": ["username", "date", "cat", "desc", "amt", "type"],
        "tasks": ["username", "task", "status", "priority", "date"],
        "savings": ["username", "goal", "target", "current"],
        "cats": ["username", "category_name"] # Default categories සඳහා
    }
    for key, cols in defaults.items():
        if not os.path.exists(FILES[key]): pd.DataFrame(columns=cols).to_csv(FILES[key], index=False)

init_dbs()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': "", 'role': ""})

def make_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

if not st.session_state['logged_in']:
    st.title("💎 Nexus Pro Login")
    t1, t2 = st.tabs(["🔑 Login", "📝 Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            udf = pd.read_csv(FILES["users"])
            res = udf[(udf['username']==u) & (udf['password']==make_hash(p))]
            if not res.empty:
                if res.iloc[0]['approved']:
                    st.session_state.update({'logged_in': True, 'username': u, 'role': res.iloc[0]['role']})
                    st.rerun()
                else: st.error("Admin approval pending...")
            else: st.error("Wrong info!")
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            udf = pd.read_csv(FILES["users"])
            if nu not in udf['username'].values:
                new_u = pd.DataFrame([[nu, make_hash(np), "User", False]], columns=udf.columns)
                pd.concat([udf, new_u]).to_csv(FILES["users"], index=False)
                st.success("Registered! Wait for Admin.")
            else: st.warning("Username exists.")
    st.stop()

# --- NAVIGATION ---
nav = st.sidebar.radio("Navigation", ["🏠 Dashboard", "💰 Wallet", "📂 My Categories", "🎯 Goals", "👨‍💼 Admin"])

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- GET USER CATEGORIES ---
def get_user_cats(user):
    cdf = pd.read_csv(FILES["cats"])
    user_cats = cdf[cdf['username'] == user]['category_name'].tolist()
    # Default ඒවා කිහිපයක් එකතු කරමු
    default_cats = ["Food", "Transport", "Rent", "Bills", "Salary", "Gift"]
    return sorted(list(set(default_cats + user_cats)))

# --- MY CATEGORIES (NEW FEATURE) ---
if nav == "📂 My Categories":
    st.title("📂 මගේ වියදම් වර්ග (Custom Categories)")
    st.info("ඔබට අවශ්‍ය ඕනෑම වියදම් හෝ ආදායම් වර්ගයක් මෙතැනින් එකතු කරන්න.")
    
    cdf = pd.read_csv(FILES["cats"])
    
    with st.form("add_cat"):
        new_cat = st.text_input("අලුත් Category එකේ නම (උදා: සුරතල් සතුන්)")
        if st.form_submit_button("එකතු කරන්න"):
            if new_cat and new_cat not in get_user_cats(st.session_state['username']):
                new_row = pd.DataFrame([[st.session_state['username'], new_cat]], columns=cdf.columns)
                pd.concat([cdf, new_row]).to_csv(FILES["cats"], index=False)
                st.success("Category එක සාර්ථකව එකතු වුණා!")
                st.rerun()
            else: st.warning("මෙය දැනටමත් පවතී හෝ හිස්ව ඇත.")

    st.subheader("දැනට පවතින වර්ග:")
    user_c = cdf[cdf['username'] == st.session_state['username']]
    for i, r in user_c.iterrows():
        col1, col2 = st.columns([0.8, 0.2])
        col1.markdown(f"<span class='cat-tag'>{r['category_name']}</span>", unsafe_allow_html=True)
        if col2.button("Delete", key=f"del_cat_{i}"):
            cdf.drop(i).to_csv(FILES["cats"], index=False)
            st.rerun()

# --- WALLET (MODIFIED) ---
elif nav == "💰 Wallet":
    st.title("💸 Wallet")
    tdf = pd.read_csv(FILES["trans"])
    
    with st.expander("➕ නව ගනුදෙනුව"):
        c1, c2, c3 = st.columns(3)
        t_type = c1.selectbox("Type", ["Expense", "Income"])
        # මෙතනින් තමයි අලුත් Categories ටික පෙන්වන්නේ
        t_cat = c2.selectbox("Category", get_user_cats(st.session_state['username']))
        t_amt = c3.number_input("Amount (Rs.)", min_value=0)
        t_desc = st.text_input("Description")
        if st.button("Add"):
            new_t = pd.DataFrame([[st.session_state['username'], str(datetime.now().date()), t_cat, t_desc, t_amt, t_type]], columns=tdf.columns)
            pd.concat([tdf, new_t]).to_csv(FILES["trans"], index=False)
            st.success("Done!")
            st.rerun()
    
    user_tdf = tdf[tdf['username'] == st.session_state['username']]
    if not user_tdf.empty:
        fig = px.pie(user_tdf[user_tdf['type']=="Expense"], values='amt', names='cat', hole=0.5, title="වියදම් බෙදී ඇති ආකාරය")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(user_tdf, use_container_width=True)

# --- DASHBOARD, GOALS, ADMIN (කලින් තිබූ ලෙසම පවතී) ---
elif nav == "🏠 Dashboard":
    st.title(f"🚀 {st.session_state['username']}'s Pulse")
    # (කලින් Dashboard කෝඩ් එක මෙතැනට)
    st.write("ඔබේ මූල්‍ය සහ කාර්යය ලැයිස්තුව මෙතැනින් බලන්න.")
    # ... කලින් තිබූ Dashboard Metrics කොටස ...

elif nav == "🎯 Goals":
    st.title("🎯 Saving Goals")
    # (කලින් Saving Goals කෝඩ් එක මෙතැනට)

elif nav == "👨‍💼 Admin":
    if st.session_state['role'] == "Admin":
        st.title("👨‍💼 Admin Panel")
        # (කලින් Admin Panel කෝඩ් එක මෙතැනට)
    else: st.error("Admin Only!")
