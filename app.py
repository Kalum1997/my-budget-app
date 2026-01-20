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
        "theme": "light", 
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
    # Columns වල නම් වලට spaces නැති බව තහවුරු කරගන්න
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
# AUTH SYSTEM (Fixed AttributeError logic)
# --------------------------------------------------
def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login(u,p):
    if not os.path.exists(DB["users"]): return False
    df = pd.read_csv(DB["users"])
    # ['u'] ආකාරයට පාවිච්චි කිරීමෙන් AttributeError මගහැරේ
    row = df[(df['u'] == u) & (df['p'] == hash_pw(p))]
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
            u_input = st.text_input("Username", key="l_u")
            p_input = st.text_input("Password", type="password", key="l_p")
            if st.button("Login", use_container_width=True):
                if login(u_input, p_input): 
                    st.rerun()
                else: 
                    st.error("Invalid Username or Password")

        with tab2:
            nu = st.text_input("New Username", key="r_u")
            np = st.text_input("New Password", type="password", key="r_p")
            cur = st.selectbox("Currency", ["LKR","USD","EUR"], key="r_c")
            if st.button("Create Account", use_container_width=True):
                df_u = pd.read_csv(DB["users"])
                if nu in df_u['u'].values:
                    st.warning("Username already exists")
                else:
                    new_user = pd.DataFrame([[nu, hash_pw(np), "User", cur]], columns=["u","p","r","cur"])
                    pd.concat([df_u, new_user], ignore_index=True).to_csv(DB["users"], index=False)
                    st.success("Success! Please Login.")
    st.stop()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.title("NEXUS PRO")
    page = option_menu(
        None, ["Dashboard", "Transactions", "Budget", "Goals", "Settings"],
        icons=["speedometer2", "cash-stack", "pie-chart", "trophy", "gear"],
        default_index=0
    )
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if page == "Dashboard":
    st.header(f"📊 {st.session_state.username}'s Dashboard")
    df_t = pd.read_csv(DB["trans"])
    user_df = df_t[df_t['u'] == st.session_state.username]

    inc = user_df[user_df['type'] == "Income"]['amount'].sum()
    exp = user_df[user_df['type'] == "Expense"]['amount'].sum()
    bal = inc - exp

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Balance", f"{st.session_state.currency} {bal:,.0f}")
    c2.metric("Total Income", f"{inc:,.0f}")
    c3.metric("Total Expense", f"{exp:,.0f}")
    c4.metric("Savings %", f"{(bal/inc*100 if inc > 0 else 0):.1f}%")

    if not user_df.empty:
        user_df['date'] = pd.to_datetime(user_df['date'])
        fig = px.line(user_df.sort_values('date'), x='date', y='amount', color='type', markers=True)
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# TRANSACTIONS
# --------------------------------------------------
elif page == "Transactions":
    st.header("💰 Transactions")
    with st.expander("➕ Add Entry"):
        c1, c2, c3 = st.columns(3)
        t_type = c1.selectbox("Type", ["Income", "Expense"])
        cat = c2.selectbox("Category", ["Salary", "Food", "Transport", "Bills", "Health", "Other"])
        amt = c3.number_input("Amount", min_value=0.0)
        
        if st.button("Save Transaction", use_container_width=True):
            all_t = pd.read_csv(DB["trans"])
            new_t = pd.DataFrame([[st.session_state.username, str(date.today()), t_type, cat, amt, "Cash", ""]], columns=all_t.columns)
            pd.concat([all_t, new_t], ignore_index=True).to_csv(DB["trans"], index=False)
            st.rerun()

    df_t = pd.read_csv(DB["trans"])
    st.dataframe(df_t[df_t['u'] == st.session_state.username], use_container_width=True)

# --------------------------------------------------
# BUDGET
# --------------------------------------------------
elif page == "Budget":
    st.header("🎯 Budget")
    cat = st.selectbox("Category", ["Food", "Transport", "Bills", "Other"])
    limit = st.number_input("Monthly Limit", min_value=0)
    if st.button("Set Budget"):
        df_b = pd.read_csv(DB["budget"])
        df_b = df_b[~((df_b['u'] == st.session_state.username) & (df_b['category'] == cat))]
        new_b = pd.DataFrame([[st.session_state.username, cat, limit]], columns=df_b.columns)
        pd.concat([df_b, new_b], ignore_index=True).to_csv(DB["budget"], index=False)
        st.success("Budget Saved!")

# --------------------------------------------------
# GOALS
# --------------------------------------------------
elif page == "Goals":
    st.header("🏆 Goals")
    name = st.text_input("Goal Name")
    target = st.number_input("Target Amount", min_value=1)
    if st.button("Create"):
        df_g = pd.read_csv(DB["goals"])
        new_g = pd.DataFrame([[st.session_state.username, name, target, 0]], columns=df_g.columns)
        pd.concat([df_g, new_g], ignore_index=True).to_csv(DB["goals"], index=False)
        st.rerun()

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------
elif page == "Settings":
    st.header("⚙️ Settings")
    if st.button("Toggle Dark/Light Mode"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

st.markdown('<div class="fab">＋</div>', unsafe_allow_html=True)
