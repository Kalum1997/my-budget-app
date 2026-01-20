import streamlit as st
import pandas as pd
import os
import hashlib
import plotly.express as px
from datetime import datetime

# පිටුවේ සැකසුම් සහ UI පෙනුම
st.set_page_config(page_title="Ultimate Money Manager", page_icon="💳", layout="wide")

# ලස්සන පෙනුම සඳහා CSS
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    div.stButton > button:first-child { background-color: #007bff; color: white; width: 100%; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- දත්ත පද්ධති කළමනාකරණය ---
USER_DB = "users_db.csv"
DATA_DB = "transactions_db.csv"

def init_files():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256("password123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Admin", True]], columns=["username", "password", "role", "approved"]).to_csv(USER_DB, index=False)
    if not os.path.exists(DATA_DB):
        pd.DataFrame(columns=["username", "දිනය", "වර්ගය", "විස්තරය", "මුදල"]).to_csv(DATA_DB, index=False)

init_files()

# Session State කළමනාකරණය
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': "", 'role': ""})

# --- උපකාරක Functions ---
def make_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

# --- LOGIN / REGISTER SYSTEM ---
if not st.session_state['logged_in']:
    st.title("🛡️ Secure Access Control")
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])
    
    with tab1:
        u = st.text_input("Username", key="l_user")
        p = st.text_input("Password", type="password", key="l_pass")
        if st.button("Log In"):
            df_u = pd.read_csv(USER_DB)
            user_data = df_u[df_u['username'] == u]
            if not user_data.empty and user_data.iloc[0]['password'] == make_hash(p):
                if user_data.iloc[0]['approved']:
                    st.session_state.update({'logged_in': True, 'username': u, 'role': user_data.iloc[0]['role']})
                    st.rerun()
                else: st.error("🛑 ඔබගේ ගිණුම තවම Admin විසින් අනුමත කර නැත.")
            else: st.error("❌ Username හෝ Password වැරදියි.")

    with tab2:
        new_u = st.text_input("New Username", key="r_user")
        new_p = st.text_input("New Password", type="password", key="r_pass")
        if st.button("Register Now"):
            df_u = pd.read_csv(USER_DB)
            if new_u in df_u['username'].values: st.warning("⚠️ මෙම නම දැනටමත් පවතී.")
            else:
                new_user = pd.DataFrame([[new_u, make_hash(new_p), "User", False]], columns=df_u.columns)
                pd.concat([df_u, new_user]).to_csv(USER_DB, index=False)
                st.success("✅ ලියාපදිංචිය සාර්ථකයි! Admin අනුමැතිය ලැබෙන තෙක් රැඳී සිටින්න.")

# --- ඇප් එක ඇතුළත (LOGGED IN) ---
else:
    # Sidebar පාලනය
    with st.sidebar:
        st.title(f"👤 {st.session_state['username']}")
        st.write(f"Role: {st.session_state['role']}")
        if st.button("🚪 Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.divider()
        
        mode = "My Dashboard"
        if st.session_state['role'] == "Admin":
            mode = st.radio("🛠️ පාලක පුවරුව", ["Admin Control", "Personal Expenses"])

    # --- 1. ADMIN INTERFACE ---
    if mode == "Admin Control":
        st.title("👨‍💼 Admin Management")
        df_u = pd.read_csv(USER_DB)
        
        st.subheader("👥 User Approval Requests")
        for i, row in df_u.iterrows():
            if row['username'] != 'admin':
                col1, col2, col3 = st.columns([3, 1, 1])
                status = "✅ Active" if row['approved'] else "⏳ Pending"
                col1.write(f"**{row['username']}** | Status: {status}")
                if not row['approved']:
                    if col2.button("Approve", key=f"app_{i}"):
                        df_u.at[i, 'approved'] = True
                        df_u.to_csv(USER_DB, index=False)
                        st.rerun()
                if col3.button("Remove", key=f"rem_{i}"):
                    df_u.drop(i).to_csv(USER_DB, index=False)
                    st.rerun()
        
        st.divider()
        st.subheader("📊 Global System Overview")
        all_data = pd.read_csv(DATA_DB)
        st.write(f"මුළු පරිශීලකයින් සංඛ්‍යාව: {len(df_u)}")
        st.write(f"මුළු ගනුදෙනු සංඛ්‍යාව: {len(all_data)}")

    # --- 2. USER INTERFACE (PERSONAL DASHBOARD) ---
    else:
        st.title(f"📈 {st.session_state['username']}'s Financial Hub")
        
        # දත්ත පූරණය
        all_data = pd.read_csv(DATA_DB)
        df = all_data[all_data['username'] == st.session_state['username']].copy()
        
        # දත්ත ඇතුළත් කිරීම (Sidebar)
        with st.sidebar:
            st.subheader("➕ නව ගනුදෙනුව")
            with st.form("add_form", clear_on_submit=True):
                d = st.date_input("දිනය", datetime.now())
                c = st.selectbox("වර්ගය", ["💵 ආදායම", "🍔 ආහාර", "⛽ ඉන්ධන", "🏠 කුලිය", "💡 බිල්පත්", "🛍️ ෂොපින්", "🏥 සෞඛ්‍ය", "⚙️ වෙනත්"])
                desc = st.text_input("විස්තරය")
                amt = st.number_input("මුදල (රු.)", min_value=0)
                if st.form_submit_button("Add Record"):
                    new_rec = pd.DataFrame([[st.session_state['username'], str(d), c, desc, amt]], columns=all_data.columns)
                    pd.concat([all_data, new_rec]).to_csv(DATA_DB, index=False)
                    st.success("සාර්ථකයි!")
                    st.rerun()

        # Dashboard UI
        if not df.empty:
            df['මුදල'] = pd.to_numeric(df['මුදල'])
            inc = df[df["වර්ගය"] == "💵 ආදායම"]["මුදල"].sum()
            exp = df[df["වර්ගය"] != "💵 ආදායම"]["මුදල"].sum()
            bal = inc - exp

            # Cards
            m1, m2, m3 = st.columns(3)
            m1.metric("මුළු ආදායම", f"රු. {inc:,.0f}")
            m2.metric("මුළු වියදම", f"රු. {exp:,.0f}", delta=f"-{exp:,.0f}", delta_color="inverse")
            m3.metric("ඉතිරිය", f"රු. {bal:,.0f}", delta=f"{bal:,.0f}")

            st.divider()
            
            # Analytics
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("📊 වියදම් විශ්ලේෂණය")
                exp_df = df[df["වර්ගය"] != "💵 ආදායම"]
                if not exp_df.empty:
                    fig = px.pie(exp_df, values='මුදල', names='වර්ගය', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.subheader("📑 මෑතකාලීන ලැයිස්තුව")
                st.dataframe(df.tail(10), use_container_width=True)

            # Monthly Report
            st.divider()
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Monthly Report", csv, "report.csv", "text/csv")
        else:
            st.info("👋 තවම දත්ත නැත. අලුත් ගනුදෙනුවක් ඇතුළත් කර ආරම්භ කරන්න.")
