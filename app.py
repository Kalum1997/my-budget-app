import streamlit as st
import pandas as pd
import os, hashlib
import plotly.express as px
from datetime import date
from streamlit_option_menu import option_menu

# --------------------------------------------------
# APP CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Nexus Ultra Pro",
    page_icon="💎",
    layout="wide"
)

# --------------------------------------------------
# SESSION STATE (Default: Light Mode)
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": False,
        "username": "",
        "role": "User",
        "theme": "light",  # මෙතන 'light' ලෙස වෙනස් කළා
        "currency": "LKR"
    })

# --------------------------------------------------
# THEME ENGINE
# --------------------------------------------------
def apply_theme():
    dark = st.session_state.theme == "dark"
    bg = "#0e1117" if dark else "#f4f6fa"
    card = "#1e2130" if dark else "#ffffff"
    text = "#ffffff" if dark else "#1f2937"
    sub_text = "#9ca3af" if dark else "#4b5563"

    st.markdown(f"""
    <style>
    .stApp {{ background:{bg}; color:{text}; }}
    [data-testid="metric-container"] {{
        background:{card} !important;
        border: 1px solid {"#30363d" if dark else "#e5e7eb"};
        border-radius:20px;
        padding:20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }}
    .stDataFrame {{ background:{card}; border-radius:10px; }}
    .fab {{
        position:fixed;
        bottom:25px; right:25px;
        width:60px; height:60px;
        border-radius:50%;
        background:linear-gradient(135deg,#6366f1,#a855f7);
        color:white;
        font-size:32px;
        display:flex;
        align-items:center;
        justify-content:center;
        box-shadow:0 10px 25px rgba(99,102,241,0.4);
        z-index: 1000;
        cursor: pointer;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------
DB = {
    "users": "users.csv",
    "trans": "transactions.csv",
    "budget": "budget.csv",
    "goals": "goals.csv"
}

def init_db():
    if not os.path.exists(DB["users"]):
        pd.DataFrame(columns=["u","p","r","cur"]).to_csv(DB["users"], index=False)
    if not os.path.exists(DB["trans"]):
        pd.DataFrame(columns=["u","date","type","category","amount","method","note"]).to_csv(DB["trans"], index=False)
    if not os.path.exists(DB["budget"]):
        pd.DataFrame(columns=["u","category","limit"]).to_csv(DB["budget"], index=False)
    if not os.path.exists(DB["goals"]):
        pd.DataFrame(columns=["u","name","target","current"]).to_csv(DB["goals"], index=False)

init_db()

# --------------------------------------------------
# AUTH SYSTEM
# --------------------------------------------------
def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login(u,p):
    df = pd.read_csv(DB["users"])
    row = df[(df.u == u) & (df.p == hash_pw(p))]
    if not row.empty:
        st.session_state.update({
            "logged_in": True,
            "username": u,
            "role": row.iloc[0]["r"],
            "currency": row.iloc[0]["cur"]
        })
        return True
    return False

# --------------------------------------------------
# LOGIN / REGISTER UI
# --------------------------------------------------
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>💎 Nexus Ultra Pro</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        with tab1:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("Login", use_container_width=True):
                if login(u,p): st.rerun()
                else: st.error("Invalid credentials")

        with tab2:
            nu = st.text_input("New Username", key="reg_u")
            np = st.text_input("New Password", type="password", key="reg_p")
            cur = st.selectbox("Currency",["LKR","USD","EUR"], key="reg_cur")
            if st.button("Create Account", use_container_width=True):
                df = pd.read_csv(DB["users"])
                if nu in df.u.values:
                    st.warning("User already exists")
                else:
                    new_user = pd.DataFrame([[nu, hash_pw(np), "User", cur]], columns=df.columns)
                    pd.concat([df, new_user], ignore_index=True).to_csv(DB["users"], index=False)
                    st.success("Account created! Please Login.")
    st.stop()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.title("NEXUS PRO")
    page = option_menu(
        None,
        ["Dashboard", "Transactions", "Budget", "Goals", "Settings"],
        icons=["speedometer2", "cash-stack", "pie-chart", "trophy", "gear"],
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "5!important"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px"}
        }
    )
    st.divider()
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --------------------------------------------------
# DATA LOAD HELPER
# --------------------------------------------------
def load_user_data(db_name):
    df = pd.read_csv(DB[db_name])
    return df[df.u == st.session_state.username]

# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------
if page == "Dashboard":
    st.header(f"👋 Welcome back, {st.session_state.username}")
    
    df = load_user_data("trans")
    inc = df[df.type == "Income"].amount.sum()
    exp = df[df.type == "Expense"].amount.sum()
    bal = inc - exp

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Balance", f"{st.session_state.currency} {bal:,.0f}")
    c2.metric("Total Income", f"{inc:,.0f}")
    c3.metric("Total Expense", f"{exp:,.0f}")
    c4.metric("Savings Ratio", f"{(bal/inc*100 if inc else 0):.1f}%")

    if not df.empty:
        st.subheader("Spending Analysis")
        df["date"] = pd.to_datetime(df["date"])
        # Area chart for cashflow
        fig = px.area(df.sort_values("date"), x="date", y="amount", color="type",
                     color_discrete_map={"Income": "#10b981", "Expense": "#ef4444"},
                     template="plotly_white" if st.session_state.theme == "light" else "plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transactions recorded yet. Add your first transaction!")

# --------------------------------------------------
# TRANSACTIONS PAGE
# --------------------------------------------------
elif page == "Transactions":
    st.header("💰 Transaction Ledger")

    with st.expander("➕ Add New Transaction", expanded=False):
        c1, c2, c3 = st.columns(3)
        t_type = c1.selectbox("Transaction Type", ["Income", "Expense"])
        cat = c2.selectbox("Category", ["Salary", "Food", "Transport", "Bills", "Shopping", "Health", "Other"])
        amt = c3.number_input("Amount", min_value=0.0, step=100.0)

        c1, c2 = st.columns(2)
        method = c1.selectbox("Payment Method", ["Cash", "Card", "Bank Transfer", "Digital Wallet"])
        note = c2.text_input("Add a Note")

        if st.button("Save Transaction", use_container_width=True):
            df_all = pd.read_csv(DB["trans"])
            new_entry = pd.DataFrame([[
                st.session_state.username, str(date.today()),
                t_type, cat, amt, method, note
            ]], columns=df_all.columns)
            pd.concat([df_all, new_entry], ignore_index=True).to_csv(DB["trans"], index=False)
            st.success("Transaction recorded successfully!")
            st.rerun()

    st.subheader("History")
    user_df = load_user_data("trans").iloc[::-1] # Show newest first
    st.dataframe(user_df, use_container_width=True, hide_index=True)

# --------------------------------------------------
# BUDGET PAGE
# --------------------------------------------------
elif page == "Budget":
    st.header("🎯 Budgeting")
    
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.subheader("Set Limit")
        b_cat = st.selectbox("Select Category", ["Food", "Transport", "Bills", "Shopping", "Entertainment"])
        limit = st.number_input("Monthly Limit Amount", min_value=0.0)

        if st.button("Update Budget", use_container_width=True):
            df_b = pd.read_csv(DB["budget"])
            # Remove existing for this category if any
            df_b = df_b[~((df_b.u == st.session_state.username) & (df_b.category == b_cat))]
            new_b = pd.DataFrame([[st.session_state.username, b_cat, limit]], columns=df_b.columns)
            pd.concat([df_b, new_b], ignore_index=True).to_csv(DB["budget"], index=False)
            st.success(f"Budget set for {b_cat}")
            st.rerun()

    with col_b:
        st.subheader("Active Budgets")
        st.dataframe(load_user_data("budget"), use_container_width=True, hide_index=True)

# --------------------------------------------------
# GOALS PAGE
# --------------------------------------------------
elif page == "Goals":
    st.header("🏆 Savings Goals")
    
    with st.form("goal_form"):
        g_name = st.text_input("What are you saving for?")
        g_target = st.number_input("Target Amount", min_value=1.0)
        if st.form_submit_button("Create Goal"):
            df_g = pd.read_csv(DB["goals"])
            new_goal = pd.DataFrame([[st.session_state.username, g_name, g_target, 0.0]], columns=df_g.columns)
            pd.concat([df_g, new_goal], ignore_index=True).to_csv(DB["goals"], index=False)
            st.success("New goal added to your list!")
            st.rerun()

    st.subheader("My Goals")
    goals_df = load_user_data("goals")
    for index, row in goals_df.iterrows():
        st.write(f"**{row['name']}**")
        progress = float(row['current'] / row['target'])
        st.progress(min(progress, 1.0))
        st.caption(f"{row['current']:,.0f} / {row['target']:,.0f} {st.session_state.currency}")

# --------------------------------------------------
# SETTINGS PAGE
# --------------------------------------------------
elif page == "Settings":
    st.header("⚙️ Personalization")
    st.write(f"Logged in as: **{st.session_state.username}**")
    
    mode_label = "Dark Mode 🌙" if st.session_state.theme == "light" else "Light Mode ☀️"
    if st.button(mode_label):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

# Floating Action Button visual
st.markdown('<div class="fab">＋</div>', unsafe_allow_html=True)
