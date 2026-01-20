import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
import plotly.express as px

# පිටුවේ සැකසුම්
st.set_page_config(page_title="Multi-User Wallet Pro", page_icon="🔐", layout="wide")

# --- දත්ත ගොනු ---
USER_DB = "users.csv"
DATA_DB = "all_data.csv"

# දත්ත ගොනු පරීක්ෂාව
def init_dbs():
    if not os.path.exists(USER_DB):
        # මුලින්ම Admin කෙනෙක් හදනවා (Username: admin, Password: kalum1997)
        admin_pw = hashlib.sha256("password123".encode()).hexdigest()
        df_users = pd.DataFrame([["admin", admin_pw, "Admin", True]], columns=["username", "password", "role", "approved"])
        df_users.to_csv(USER_DB, index=False)
    if not os.path.exists(DATA_DB):
        pd.DataFrame(columns=["username", "දිනය", "වර්ගය", "විස්තරය", "මුදල"]).to_csv(DATA_DB, index=False)

init_dbs()

# --- උපකාරක Function ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# --- පද්ධතියට ඇතුළුවීම (Session State) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

# --- LOGIN / REGISTER PAGE ---
if not st.session_state['logged_in']:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        st.subheader("ඇතුළු වන්න")
        user = st.text_input("Username")
        passwd = st.text_input("Password", type='password')
        if st.button("Login"):
            df_u = pd.read_csv(USER_DB)
            user_row = df_u[df_u['username'] == user]
            
            if not user_row.empty:
                if check_hashes(passwd, user_row.iloc[0]['password']):
                    if user_row.iloc[0]['approved']:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user
                        st.session_state['role'] = user_row.iloc[0]['role']
                        st.success(f"සාදරයෙන් පිළිගන්නවා {user}!")
                        st.rerun()
                    else:
                        st.error("ඔබට තවම Admin විසින් අනුමැතිය (Approval) ලබා දී නැත.")
                else:
                    st.error("වැරදි Password එකක්.")
            else:
                st.error("මවැනි පරිශීලකයෙකු නැත.")

    with tab2:
        st.subheader("ගිණුමක් සාදන්න")
        new_user = st.text_input("New Username")
        new_passwd = st.text_input("New Password", type='password')
        if st.button("Register"):
            df_u = pd.read_csv(USER_DB)
            if new_user in df_u['username'].values:
                st.warning("මෙම නම දැනටමත් පවතී.")
            else:
                new_row = pd.DataFrame([[new_user, make_hashes(new_passwd), "User", False]], columns=df_u.columns)
                pd.concat([df_u, new_row], ignore_index=True).to_csv(USER_DB, index=False)
                st.info("පදිංචි කිරීම සාර්ථකයි! Admin අනුමත කරන තෙක් රැඳී සිටින්න.")

# --- LOGGED IN CONTENT ---
else:
    st.sidebar.title(f"👋 {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- ADMIN VIEW ---
    if st.session_state['role'] == "Admin":
        menu = st.sidebar.selectbox("පාලක පුවරුව", ["User Management", "My Expenses"])
        
        if menu == "User Management":
            st.title("👥 පරිශීලකයින් පාලනය")
            df_u = pd.read_csv(USER_DB)
            st.write("දැනට ඉන්න පරිශීලකයින්:")
            
            # Approve කරන්න ඕන අය පෙන්වීම
            for index, row in df_u.iterrows():
                if row['username'] != 'admin':
                    col1, col2, col3 = st.columns([2, 1, 1])
                    col1.write(f"**{row['username']}** (Status: {'Approved' if row['approved'] else 'Pending'})")
                    if not row['approved']:
                        if col2.button("Approve", key=f"app_{row['username']}"):
                            df_u.at[index, 'approved'] = True
                            df_u.to_csv(USER_DB, index=False)
                            st.rerun()
                    if col3.button("Delete", key=f"del_{row['username']}"):
                        df_u = df_u.drop(index)
                        df_u.to_csv(USER_DB, index=False)
                        st.rerun()
            st.stop() # Admin ට මේ පිටුවේදී වියදම් පේන්නේ නැත

    # --- USER VIEW (OR ADMIN EXPENSES) ---
    st.title(f"💰 {st.session_state['username']} ගේ පසුම්බිය")
    
    # දත්ත කියවීම (තමන්ගේ දත්ත පමණක්)
    all_df = pd.read_csv(DATA_DB)
    df = all_df[all_df['username'] == st.session_state['username']]

    with st.sidebar:
        st.header("නව ගනුදෙනුව")
        with st.form("my_form", clear_on_submit=True):
            date = st.date_input("දිනය", datetime.now())
            category = st.selectbox("වර්ගය", ["🍱 කෑම බීම", "⛽ පෙට්‍රල්", "💵 ආදායම", "🔌 බිල්පත්", "⚙️ වෙනත්"])
            desc = st.text_input("විස්තරය")
            amount = st.number_input("මුදල", min_value=0)
            if st.form_submit_button("එකතු කරන්න"):
                new_data = pd.DataFrame([[st.session_state['username'], str(date), category, desc, amount]], columns=all_df.columns)
                pd.concat([all_df, new_data], ignore_index=True).to_csv(DATA_DB, index=False)
                st.success("සේව් වුණා!")
                st.rerun()

    # Dashboard display (මෙහි පෙර පෙනුම එලෙසම තැබිය හැක)
    if not df.empty:
        income = df[df["වර්ගය"] == "💵 ආදායම"]["මුදල"].sum()
        expense = df[df["වර්ගය"] != "💵 ආදායම"]["මුදල"].sum()
        c1, c2 = st.columns(2)
        c1.metric("ආදායම", f"රු. {income}")
        c2.metric("වියදම", f"රු. {expense}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ඔබට තවම දත්ත නැත. අලුතින් ඇතුළත් කරන්න.")
