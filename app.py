import streamlit as st
import pandas as pd
import os
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import requests
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
import base64

# --- APP CONFIG ---
st.set_page_config(page_title="Nexus Ultra Pro", page_icon="💎", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'username': "", 'role': "User", 
        'theme': "dark", 'currency': "LKR"
    })

# --- STYLING ---
def apply_theme():
    bg = "#0e1117" if st.session_state.theme == "dark" else "#f0f2f6"
    card = "#1e2130" if st.session_state.theme == "dark" else "#ffffff"
    text = "#ffffff" if st.session_state.theme == "dark" else "#000000"
    
    st.markdown(f"""
        <style>
        .stApp {{ background: {bg}; color: {text}; }}
        [data-testid="stMetricCard"] {{
            background: {card};
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }}
        .metric-card {{
            background: {card}; padding: 25px; border-radius: 20px;
            border-left: 5px solid #00f2fe; margin-bottom: 20px;
        }}
        .fab {{
            position: fixed; bottom: 30px; right: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; width: 60px; height: 60px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.3); z-index: 100;
        }}
        </style>
    """, unsafe_allow_html=True)

apply_theme()

# --- DB SYSTEM ---
DB_FILES = {
    "users": "nexus_users.csv", "trans": "nexus_trans.csv",
    "goals": "nexus_goals.csv", "budget": "nexus_budget.csv"
}

def init_db():
    for file, cols in [
        ("users", ["u", "p", "r", "cur"]), 
        ("trans", ["u", "date", "cat", "desc", "amt", "type", "method"]),
        ("goals", ["u", "name", "target", "current", "deadline"]),
        ("budget", ["u", "cat", "limit"])
    ]:
        if not os.path.exists(DB_FILES[file]):
            pd.DataFrame(columns=cols).to_csv(DB_FILES[file], index=False)
    
    udf = pd.read_csv(DB_FILES["users"])
    if "admin" not in udf['u'].values:
        admin_row = pd.DataFrame([["admin", hashlib.sha256("123".encode()).hexdigest(), "Admin", "LKR"]], columns=udf.columns)
        pd.concat([udf, admin_row]).to_csv(DB_FILES["users"], index=False)

init_db()

# --- AUTH FUNCTIONS ---
def login(u, p):
    udf = pd.read_csv(DB_FILES["users"])
    hashed = hashlib.sha256(p.encode()).hexdigest()
    user = udf[(udf['u'] == u) & (udf['p'] == hashed)]
    if not user.empty:
        st.session_state.update({'logged_in': True, 'username': u, 'role': user.iloc[0]['r'], 'currency': user.iloc[0]['cur']})
        return True
    return False

# --- UI COMPONENTS ---
def load_lottie(url):
    try: return requests.get(url).json()
    except: return None

# --- MAIN APP LOGIC ---
if not st.session_state.logged_in:
    col1, col2 = st.columns([1, 1])
    with col1:
        anim = load_lottie("https://lottie.host/802b1660-3948-4362-a548-56549a930129/Z7vP4U9W6y.json")
        if anim: st_lottie(anim, height=400)
    with col2:
        st.title("💎 Nexus Ultra Pro")
        choice = st.tabs(["🔒 Login", "📝 Register"])
        with choice[0]:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Unlock Dashboard"):
                if login(u, p): st.rerun()
                else: st.error("Access Denied.")
        with choice[1]:
            nu = st.text_input("New User")
            np = st.text_input("New Pass", type="password")
            cur = st.selectbox("Base Currency", ["LKR", "USD", "EUR"])
            if st.button("Create Account"):
                udf = pd.read_csv(DB_FILES["users"])
                if nu in udf['u'].values: st.warning("User exists.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(np.encode()).hexdigest(), "User", cur]], columns=udf.columns)
                    pd.concat([udf, new_u]).to_csv(DB_FILES["users"], index=False)
                    st.success("Account Created! Please Login.")
    st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.title("NEXUS PRO")
    selected = option_menu(
        None, ["Dashboard", "Transactions", "Budgeting", "Savings Goals", "Settings"],
        icons=['speedometer2', 'cash-stack', 'pie-chart', 'trophy', 'gear'],
        menu_icon="cast", default_index=0
    )
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- DATA LOAD ---
def get_data(file):
    df = pd.read_csv(DB_FILES[file])
    return df[df['u'] == st.session_state.username]

# --- 1. DASHBOARD ---
if selected == "Dashboard":
    st.markdown(f"## 🚀 {st.session_state.username}'s Overview")
    df_t = get_data("trans")
    
    inc = df_t[df_t['type'] == "Income"]['amt'].sum()
    exp = df_t[df_t['type'] == "Expense"]['amt'].sum()
    bal = inc - exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Balance", f"{st.session_state.currency} {bal:,.0f}")
    c2.metric("Income", f"{inc:,.0f}")
    c3.metric("Expenses", f"{exp:,.0f}")
    c4.metric("Savings %", f"{(bal/inc*100 if inc>0 else 0):.1f}%")

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader("📈 Spending Trend")
        if not df_t.empty:
            df_t['date'] = pd.to_datetime(df_t['date'])
            trend = df_t.groupby('date')['amt'].sum().reset_index()
            fig = px.area(trend, x='date', y='amt', color_discrete_sequence=['#00f2fe'])
            st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("🍔 Expense Share")
        if not df_t[df_t['type']=="Expense"].empty:
            fig_pie = px.pie(df_t[df_t['type']=="Expense"], values='amt', names='cat', hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)

# --- 2. TRANSACTIONS ---
elif selected == "Transactions":
    st.title("💰 Entries")
    with st.expander("➕ Add New Entry"):
        c1, c2, c3 = st.columns(3)
        t_type = c1.selectbox("Type", ["Expense", "Income"])
        t_cat = c2.selectbox("Category", ["Salary", "Food", "Transport", "Bills", "Health", "Other"])
        t_amt = c3.number_input("Amount", min_value=0.0)
        if st.button("Save Transaction"):
            df = pd.read_csv(DB_FILES["trans"])
            new_t = pd.DataFrame([[st.session_state.username, str(date.today()), t_cat, "", t_amt, t_type, "Cash"]], columns=df.columns)
            pd.concat([df, new_t]).to_csv(DB_FILES["trans"], index=False)
            st.rerun()
    st.dataframe(get_data("trans"), use_container_width=True)

# --- 3. BUDGETING ---
elif selected == "Budgeting":
    st.title("🎯 Budget")
    b_cat = st.selectbox("Category", ["Food", "Transport", "Bills"])
    b_lim = st.number_input("Limit", min_value=0)
    if st.button("Set"):
        bdf = pd.read_csv(DB_FILES["budget"])
        bdf = bdf[~((bdf['u'] == st.session_state.username) & (bdf['cat'] == b_cat))]
        new_b = pd.DataFrame([[st.session_state.username, b_cat, b_lim]], columns=bdf.columns)
        pd.concat([bdf, new_b]).to_csv(DB_FILES["budget"], index=False)
        st.success("Updated")

# --- 4. SAVINGS GOALS ---
elif selected == "Savings Goals":
    st.title("🏆 Goals")
    gn = st.text_input("Goal Name")
    gt = st.number_input("Target Amount", min_value=1)
    if st.button("Launch"):
        df = pd.read_csv(DB_FILES["goals"])
        new_g = pd.DataFrame([[st.session_state.username, gn, gt, 0, str(date.today())]], columns=df.columns)
        pd.concat([df, new_g]).to_csv(DB_FILES["goals"], index=False)
        st.rerun()

# --- 5. SETTINGS ---
elif selected == "Settings":
    st.title("⚙️ Settings")
    if st.button("Switch Theme"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

st.markdown('<div class="fab">＋</div>', unsafe_allow_html=True)
