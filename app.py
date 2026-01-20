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
# SESSION STATE
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": False,
        "username": "",
        "role": "User",
        "theme": "dark",
        "currency": "LKR"
    })

# --------------------------------------------------
# THEME
# --------------------------------------------------
def apply_theme():
    dark = st.session_state.theme == "dark"
    bg = "#0e1117" if dark else "#f4f6fa"
    card = "#1e2130" if dark else "#ffffff"
    text = "#ffffff" if dark else "#000000"

    st.markdown(f"""
    <style>
    .stApp {{ background:{bg}; color:{text}; }}
    div[data-testid="metric-container"] {{
        background:{card};
        border-radius:20px;
        padding:20px;
        box-shadow:0 10px 30px rgba(0,0,0,.25);
    }}
    .fab {{
        position:fixed;
        bottom:25px; right:25px;
        width:60px; height:60px;
        border-radius:50%;
        background:linear-gradient(135deg,#00f2fe,#4facfe);
        color:white;
        font-size:32px;
        display:flex;
        align-items:center;
        justify-content:center;
        box-shadow:0 10px 25px rgba(0,0,0,.4);
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# --------------------------------------------------
# DATABASE FILES
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
        pd.DataFrame(columns=[
            "u","date","type","category","amount","method","note"
        ]).to_csv(DB["trans"], index=False)

    if not os.path.exists(DB["budget"]):
        pd.DataFrame(columns=["u","category","limit"]).to_csv(DB["budget"], index=False)

    if not os.path.exists(DB["goals"]):
        pd.DataFrame(columns=["u","name","target","current"]).to_csv(DB["goals"], index=False)

init_db()

# --------------------------------------------------
# AUTH FUNCTIONS
# --------------------------------------------------
def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login(u,p):
    df = pd.read_csv(DB["users"])
    row = df[(df.u==u) & (df.p==hash_pw(p))]
    if not row.empty:
        st.session_state.update({
            "logged_in":True,
            "username":u,
            "role":row.iloc[0]["r"],
            "currency":row.iloc[0]["cur"]
        })
        return True
    return False

# --------------------------------------------------
# LOGIN / REGISTER
# --------------------------------------------------
if not st.session_state.logged_in:
    col1,col2 = st.columns([1,1])

    with col2:
        st.title("💎 Nexus Ultra Pro")
        tab1,tab2 = st.tabs(["🔐 Login","📝 Register"])

        with tab1:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login"):
                if login(u,p): st.rerun()
                else: st.error("Invalid credentials")

        with tab2:
            nu = st.text_input("New Username")
            np = st.text_input("New Password", type="password")
            cur = st.selectbox("Currency",["LKR","USD","EUR"])
            if st.button("Create Account"):
                df = pd.read_csv(DB["users"])
                if nu in df.u.values:
                    st.warning("User exists")
                else:
                    new = pd.DataFrame([[nu,hash_pw(np),"User",cur]],columns=df.columns)
                    pd.concat([df,new]).to_csv(DB["users"],index=False)
                    st.success("Account created")

    st.stop()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.title("NEXUS PRO")
    page = option_menu(
        None,
        ["Dashboard","Transactions","Budget","Goals","Settings"],
        icons=["speedometer","cash","pie-chart","trophy","gear"],
        default_index=0
    )
    if st.button("Logout"):
        st.session_state.logged_in=False
        st.rerun()

# --------------------------------------------------
# DATA HELPERS
# --------------------------------------------------
def load(name):
    df = pd.read_csv(DB[name])
    return df[df.u==st.session_state.username]

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if page=="Dashboard":
    st.header("📊 Financial Overview")

    df = load("trans")
    inc = df[df.type=="Income"].amount.sum()
    exp = df[df.type=="Expense"].amount.sum()
    bal = inc-exp

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Balance", f"{bal:,.0f}")
    c2.metric("Income", f"{inc:,.0f}")
    c3.metric("Expense", f"{exp:,.0f}")
    c4.metric("Savings %", f"{(bal/inc*100 if inc else 0):.1f}%")

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        fig = px.area(df, x="date", y="amount", color="type")
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# TRANSACTIONS
# --------------------------------------------------
elif page=="Transactions":
    st.header("💰 Transactions")

    with st.expander("➕ Add Transaction"):
        c1,c2,c3 = st.columns(3)
        t_type = c1.selectbox("Type",["Income","Expense"])
        cat = c2.selectbox("Category",
            ["Salary","Food","Transport","Bills","Shopping","Health","Other"])
        amt = c3.number_input("Amount",min_value=0.0)

        method = st.selectbox("Payment",["Cash","Card","Bank","Wallet"])
        note = st.text_input("Note")

        if st.button("Save"):
            df = pd.read_csv(DB["trans"])
            new = pd.DataFrame([[
                st.session_state.username,
                str(date.today()),
                t_type,cat,amt,method,note
            ]], columns=df.columns)
            pd.concat([df,new]).to_csv(DB["trans"],index=False)
            st.success("Saved")
            st.rerun()

    st.dataframe(load("trans"), use_container_width=True)

# --------------------------------------------------
# BUDGET
# --------------------------------------------------
elif page=="Budget":
    st.header("🎯 Budget Planner")
    cat = st.selectbox("Category",["Food","Transport","Bills","Shopping"])
    limit = st.number_input("Monthly Limit",min_value=0)

    if st.button("Set Budget"):
        df = pd.read_csv(DB["budget"])
        df = df[~((df.u==st.session_state.username)&(df.category==cat))]
        new = pd.DataFrame([[st.session_state.username,cat,limit]],columns=df.columns)
        pd.concat([df,new]).to_csv(DB["budget"],index=False)
        st.success("Budget saved")

    st.dataframe(load("budget"))

# --------------------------------------------------
# GOALS
# --------------------------------------------------
elif page=="Goals":
    st.header("🏆 Savings Goals")
    name = st.text_input("Goal Name")
    target = st.number_input("Target Amount",min_value=1)

    if st.button("Create Goal"):
        df = pd.read_csv(DB["goals"])
        new = pd.DataFrame([[st.session_state.username,name,target,0]],columns=df.columns)
        pd.concat([df,new]).to_csv(DB["goals"],index=False)
        st.success("Goal added")

    st.dataframe(load("goals"))

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------
elif page=="Settings":
    st.header("⚙️ Settings")
    if st.button("Toggle Theme"):
        st.session_state.theme = "light" if st.session_state.theme=="dark" else "dark"
        st.rerun()

st.markdown('<div class="fab">＋</div>', unsafe_allow_html=True)
