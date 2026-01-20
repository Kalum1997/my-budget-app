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
from fpdf import FPDF
import base64

# --- APP CONFIG ---
st.set_page_config(page_title="Nexus Ultra Pro", page_icon="💎", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'username': "", 'role': "User", 
        'theme': "dark", 'currency': "LKR"
    })

# --- STYLING (Glassmorphism & Gradients) ---
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
    
    # Create default admin if not exists
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
        st_lottie(anim, height=400)
    with col2:
        st.title("💎 Nexus Ultra Pro")
        st.subheader("Professional Wealth Intelligence")
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
        None, ["Dashboard", "Transactions", "Budgeting", "Savings Goals", "Reports", "Settings"],
        icons=['speedometer2', 'cash-stack', 'pie-chart', 'trophy', 'file-earmark-bar-graph', 'gear'],
        menu_icon="cast", default_index=0, orientation="vertical"
    )
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- LOAD DATA ---
def get_data(file):
    df = pd.read_csv(DB_FILES[file])
    return df[df['u'] == st.session_state.username]

# --- 1. DASHBOARD ---
if selected == "Dashboard":
    st.markdown(f"## 🚀 {st.session_state.username}'s Intelligence Overview")
    df_t = get_data("trans")
    
    # Quick Stats
    inc = df_t[df_t['type'] == "Income"]['amt'].sum()
    exp = df_t[df_t['type'] == "Expense"]['amt'].sum()
    bal = inc - exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Balance", f"{st.session_state.currency} {bal:,.0f}")
    c2.metric("Income (Month)", f"{inc:,.0f}", delta_color="normal")
    c3.metric("Expenses (Month)", f"{exp:,.0f}", delta_color="inverse")
    c4.metric("Savings Rate", f"{(bal/inc*100 if inc>0 else 0):.1f}%")

    

[Image of financial dashboard charts]


    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader("📈 Spending Trend")
        if not df_t.empty:
            df_t['date'] = pd.to_datetime(df_t['date'])
            trend = df_t.groupby('date')['amt'].sum().reset_index()
            fig = px.area(trend, x='date', y='amt', line_shape='smooth', color_discrete_sequence=['#00f2fe'])
            st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("🍔 Expense by Category")
        if not df_t[df_t['type']=="Expense"].empty:
            fig_pie = px.pie(df_t[df_t['type']=="Expense"], values='amt', names='cat', hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)

# --- 2. TRANSACTIONS ---
elif selected == "Transactions":
    st.title("💰 Transaction Intelligence")
    
    with st.expander("➕ Add New Entry", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        t_type = c1.selectbox("Type", ["Expense", "Income"])
        t_cat = c2.selectbox("Category", ["Salary", "Food", "Transport", "Rent", "Bills", "Health", "Leisure", "Other"])
        t_amt = c3.number_input("Amount", min_value=0.0)
        t_meth = c4.selectbox("Method", ["Cash", "Bank Transfer", "Card", "Wallet"])
        t_desc = st.text_input("Description / Notes")
        t_date = st.date_input("Date", date.today())
        
        if st.button("Confirm Transaction"):
            df = pd.read_csv(DB_FILES["trans"])
            new_t = pd.DataFrame([[st.session_state.username, str(t_date), t_cat, t_desc, t_amt, t_type, t_meth]], columns=df.columns)
            pd.concat([df, new_t]).to_csv(DB_FILES["trans"], index=False)
            st.balloons()
            st.rerun()

    st.subheader("📜 Recent History")
    st.dataframe(get_data("trans").sort_values('date', ascending=False), use_container_width=True)

# --- 3. BUDGETING ---
elif selected == "Budgeting":
    st.title("🎯 Budget Planning")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Set Category Limits")
        b_cat = st.selectbox("Category", ["Food", "Transport", "Bills", "Leisure"])
        b_lim = st.number_input("Monthly Limit", min_value=0)
        if st.button("Set Budget"):
            bdf = pd.read_csv(DB_FILES["budget"])
            # Update if exists, else add
            bdf = bdf[~((bdf['u'] == st.session_state.username) & (bdf['cat'] == b_cat))]
            new_b = pd.DataFrame([[st.session_state.username, b_cat, b_lim]], columns=bdf.columns)
            pd.concat([bdf, new_b]).to_csv(DB_FILES["budget"], index=False)
            st.success("Budget Updated!")

    with c2:
        st.subheader("Budget vs Actual")
        bdf = get_data("budget")
        tdf = get_data("trans")
        for idx, row in bdf.iterrows():
            spent = tdf[(tdf['cat'] == row['cat']) & (tdf['type'] == "Expense")]['amt'].sum()
            pct = min(spent/row['limit'], 1.0) if row['limit'] > 0 else 0
            st.write(f"**{row['cat']}** (Limit: {row['limit']})")
            color = "red" if spent > row['limit'] else "green"
            st.progress(pct)
            st.markdown(f"<span style='color:{color}'>{spent:,.0f} spent of {row['limit']:,.0f}</span>", unsafe_allow_html=True)

# --- 4. SAVINGS GOALS ---
elif selected == "Savings Goals":
    st.title("🏆 Achievement Goals")
    
    
    with st.form("goal_form"):
        gn = st.text_input("Goal Name (e.g. New Car, iPhone)")
        gt = st.number_input("Target Amount", min_value=1)
        gd = st.date_input("Deadline")
        if st.form_submit_button("Launch Goal"):
            df = pd.read_csv(DB_FILES["goals"])
            new_g = pd.DataFrame([[st.session_state.username, gn, gt, 0, str(gd)]], columns=df.columns)
            pd.concat([df, new_g]).to_csv(DB_FILES["goals"], index=False)
            st.rerun()

    st.divider()
    goals = get_data("goals")
    for idx, row in goals.iterrows():
        st.subheader(f"🎯 {row['name']}")
        prog = (row['current']/row['target'])
        st.progress(min(prog, 1.0))
        st.write(f"Progress: {row['current']:,.0f} / {row['target']:,.0f} ({prog*100:.1f}%)")
        add = st.number_input("Add to Savings", min_value=0, key=f"goal_{idx}")
        if st.button("Deposit", key=f"btn_{idx}"):
            df = pd.read_csv(DB_FILES["goals"])
            df.loc[(df['u'] == st.session_state.username) & (df['name'] == row['name']), 'current'] += add
            df.to_csv(DB_FILES["goals"], index=False)
            st.rerun()

# --- 5. REPORTS ---
elif selected == "Reports":
    st.title("📊 Financial Intelligence Reports")
    df = get_data("trans")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Export to Excel"):
            df.to_excel("Financial_Report.xlsx", index=False)
            st.success("Excel generated!")
            
    with c2:
        if st.button("Generate AI Suggestion"):
            exp = df[df['type']=="Expense"]['amt'].sum()
            inc = df[df['type']=="Income"]['amt'].sum()
            if exp > inc * 0.7:
                st.warning("🤖 AI: ඔබේ වියදම් ආදායමෙන් 70% ඉක්මවා ඇත. අනවශ්‍ය වියදම් අඩු කරන්න!")
            else:
                st.success("🤖 AI: ඔබේ මූල්‍ය තත්ත්වය යහපත් මට්ටමක පවතී. දිගටම ඉතිරි කරන්න!")

# --- 6. SETTINGS ---
elif selected == "Settings":
    st.title("⚙️ System Configuration")
    new_theme = st.selectbox("Theme Mode", ["dark", "light"], index=0 if st.session_state.theme=="dark" else 1)
    if st.button("Apply Theme"):
        st.session_state.theme = new_theme
        st.rerun()
    
    st.divider()
    if st.button("🗑️ Reset All My Data", type="primary"):
        tdf = pd.read_csv(DB_FILES["trans"])
        tdf[tdf['u'] != st.session_state.username].to_csv(DB_FILES["trans"], index=False)
        st.success("Data wiped.")

# Floating Button Simulation
st.markdown('<div class="fab">＋</div>', unsafe_allow_html=True)
