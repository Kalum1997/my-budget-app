import streamlit as st
import pandas as pd
import os
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# --- APP CONFIG ---
st.set_page_config(page_title="Nexus Pro - Wealth & Productivity", page_icon="💎", layout="wide")

# --- CUSTOM CSS FOR PREMIUM UI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: #f8f9fa; }
    .metric-card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-bottom: 5px solid #6366f1; }
    .status-pill { padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    div.stButton > button { background: #6366f1; color: white; border-radius: 12px; width: 100%; font-weight: 600; border: none; height: 3.5rem; }
    </style>
    """, unsafe_allow_html=True)

# --- DB INITIALIZATION ---
FILES = {
    "users": "users_pro.csv",
    "trans": "trans_pro.csv",
    "tasks": "tasks_pro.csv",
    "savings": "savings_pro.csv",
    "config": "config_pro.csv",
    "cats": "custom_cats.csv"
}

def init_dbs():
    if not os.path.exists(FILES["users"]):
        admin_pw = hashlib.sha256("password123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Admin", True]], columns=["username", "password", "role", "approved"]).to_csv(FILES["users"], index=False)
    
    defaults = {
        "trans": ["username", "date", "cat", "desc", "amt", "type"],
        "tasks": ["username", "task", "status", "priority", "date"],
        "savings": ["username", "goal", "target", "current"],
        "config": ["username", "monthly_limit"],
        "cats": ["username", "cat_name"]
    }
    for key, cols in defaults.items():
        if not os.path.exists(FILES[key]): pd.DataFrame(columns=cols).to_csv(FILES[key], index=False)

init_dbs()

# --- AUTH SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': "", 'role': ""})

def make_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

# --- LOGIN / REGISTER ---
if not st.session_state['logged_in']:
    st.title("💎 Nexus Pro Management")
    st.info("ඔබේ මූල්‍ය සහ එදිනෙදා වැඩ පාලනය කරන එකම තැන.")
    t1, t2 = st.tabs(["🔑 ඇතුළු වන්න", "📝 ලියාපදිංචි වන්න"])
    
    with t1:
        u = st.text_input("පරිශීලක නම (Username)")
        p = st.text_input("මුරපදය (Password)", type="password")
        if st.button("Log In"):
            udf = pd.read_csv(FILES["users"])
            res = udf[(udf['username']==u) & (udf['password']==make_hash(p))]
            if not res.empty:
                if res.iloc[0]['approved']:
                    st.session_state.update({'logged_in': True, 'username': u, 'role': res.iloc[0]['role']})
                    st.rerun()
                else: st.error("Admin තවම ඔබව Approve කර නැත.")
            else: st.error("නම හෝ මුරපදය වැරදියි.")
    with t2:
        nu = st.text_input("අලුත් නමක්")
        np = st.text_input("අලුත් මුරපදයක්", type="password")
        if st.button("Register"):
            udf = pd.read_csv(FILES["users"])
            if nu in udf['username'].values: st.warning("මෙම නම දැනටමත් පවතී.")
            else:
                new_u = pd.DataFrame([[nu, make_hash(np), "User", False]], columns=udf.columns)
                pd.concat([udf, new_u]).to_csv(FILES["users"], index=False)
                st.success("ලියාපදිංචිය සාර්ථකයි! Admin අනුමත කරන තෙක් රැඳී සිටින්න.")
    st.stop()

# --- MAIN NAVIGATION ---
st.sidebar.markdown(f"### 👋 Welcome, {st.session_state['username']}")
nav = st.sidebar.radio("Navigation", ["🏠 Dashboard", "💰 Wallet", "✅ Tasks & Goals", "⚙️ Settings", "👨‍💼 Admin Panel" if st.session_state['role']=="Admin" else "🏠 Dashboard"])

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 1. HOME DASHBOARD ---
if nav == "🏠 Dashboard":
    st.title(f"🚀 {st.session_state['username']}'s Pulse")
    tdf = pd.read_csv(FILES["trans"])
    user_tdf = tdf[tdf['username'] == st.session_state['username']]
    inc = user_tdf[user_tdf['type']=="Income"]['amt'].sum()
    exp = user_tdf[user_tdf['type']=="Expense"]['amt'].sum()
    
    tkdf = pd.read_csv(FILES["tasks"])
    user_tkdf = tkdf[tkdf['username'] == st.session_state['username']]
    comp_tasks = len(user_tkdf[user_tkdf['status']=="Done"])
    total_tasks = len(user_tkdf)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><h4>💵 අතේ ඇති මුදල</h4><h2>රු. {inc-exp:,.0f}</h2></div>", unsafe_allow_html=True)
    with c2:
        score = "Perfect" if inc > exp*2 else "Average"
        st.markdown(f"<div class='metric-card'><h4>📊 මූල්‍ය මට්ටම</h4><h2>{score}</h2></div>", unsafe_allow_html=True)
    with c3:
        prog = (comp_tasks/total_tasks*100) if total_tasks > 0 else 0
        st.markdown(f"<div class='metric-card'><h4>✅ වැඩ අවසන් කිරීම</h4><h2>{prog:.0f}%</h2></div>", unsafe_allow_html=True)

    st.divider()
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("🗓️ මෑතකාලීන ගනුදෙනු")
        st.dataframe(user_tdf.tail(5), use_container_width=True)
    with col_b:
        st.subheader("💡 Motivation")
        st.info("අද දවස ඊයේට වඩා සාර්ථක කරගන්න උපරිමයෙන් උත්සාහ කරන්න! 💪")

# --- 2. WALLET ---
elif nav == "💰 Wallet":
    st.title("💸 Wallet Manager")
    tdf = pd.read_csv(FILES["trans"])
    
    # Get Categories
    custom_cats = pd.read_csv(FILES["cats"])
    user_cats = custom_cats[custom_cats['username'] == st.session_state['username']]['cat_name'].tolist()
    default_cats = ["Food", "Rent", "Salary", "Fuel", "Bills", "Health", "Other"]
    final_cats = sorted(list(set(default_cats + user_cats)))

    with st.expander("➕ නව ගනුදෙනුවක් ඇතුළත් කරන්න"):
        c1, c2, c3 = st.columns(3)
        t_type = c1.selectbox("වර්ගය", ["Expense", "Income"])
        t_cat = c2.selectbox("Category", final_cats)
        t_amt = c3.number_input("Amount (Rs.)", min_value=0)
        t_desc = st.text_input("විස්තරය")
        if st.button("Save to Wallet"):
            new_t = pd.DataFrame([[st.session_state['username'], str(datetime.now().date()), t_cat, t_desc, t_amt, t_type]], columns=tdf.columns)
            pd.concat([tdf, new_t]).to_csv(FILES["trans"], index=False)
            st.success("සේව් වුණා!")
            st.rerun()

    user_tdf = tdf[tdf['username'] == st.session_state['username']]
    st.subheader("📊 වියදම් විස්තර")
    fig = px.bar(user_tdf[user_tdf['type']=="Expense"], x='cat', y='amt', color='cat', title="Category wise Expense")
    st.plotly_chart(fig, use_container_width=True)

# --- 3. TASKS & GOALS ---
elif nav == "✅ Tasks & Goals":
    st.title("🎯 Tasks & Savings")
    tab_tasks, tab_save = st.tabs(["📝 Daily Tasks", "🐷 Saving Goals"])
    with tab_tasks:
        tkdf = pd.read_csv(FILES["tasks"])
        user_tk = tkdf[tkdf['username'] == st.session_state['username']]
        with st.form("task_form"):
            t_name = st.text_input("කරන්න තියෙන වැඩේ?")
            t_prio = st.select_slider("වැදගත්කම (Priority)", options=["Low", "Medium", "High"])
            if st.form_submit_button("Add Task"):
                new_tk = pd.DataFrame([[st.session_state['username'], t_name, "Pending", t_prio, str(datetime.now().date())]], columns=tkdf.columns)
                pd.concat([tkdf, new_tk]).to_csv(FILES["tasks"], index=False)
                st.rerun()
        for i, r in user_tk.iterrows():
            col1, col2 = st.columns([0.8, 0.2])
            if r['status'] == "Pending":
                col1.warning(f"**{r['task']}** (Priority: {r['priority']})")
                if col2.button("Complete", key=f"tk_{i}"):
                    tkdf.at[i, 'status'] = "Done"
                    tkdf.to_csv(FILES["tasks"], index=False)
                    st.rerun()
            else: col1.success(f"~~{r['task']}~~ (Done ✅)")

    with tab_save:
        sdf = pd.read_csv(FILES["savings"])
        user_s = sdf[sdf['username'] == st.session_state['username']]
        with st.expander("🎯 අලුත් ඉලක්කයක් (Saving Goal)"):
            g_name = st.text_input("Goal Name")
            g_target = st.number_input("Target Amount", min_value=1)
            if st.button("Set Goal"):
                new_g = pd.DataFrame([[st.session_state['username'], g_name, g_target, 0]], columns=sdf.columns)
                pd.concat([sdf, new_g]).to_csv(FILES["savings"], index=False)
                st.rerun()
        for i, r in user_s.iterrows():
            st.write(f"**{r['goal']}**")
            st.progress(min(r['current']/r['target'], 1.0))
            st.write(f"රු. {r['current']} / {r['target']}")
            up_amt = st.number_input(f"මුදල් එකතු කරන්න ({r['goal']})", min_value=0, key=f"s_{i}")
            if st.button("Update Goal", key=f"btn_{i}"):
                sdf.at[i, 'current'] += up_amt
                sdf.to_csv(FILES["savings"], index=False)
                st.rerun()

# --- 4. SETTINGS ---
elif nav == "⚙️ Settings":
    st.title("⚙️ User Settings")
    st.subheader(f"Profile: {st.session_state['username']} ({st.session_state['role']})")
    
    st.divider()
    
    # Tab for Settings
    stab1, stab2, stab3 = st.tabs(["📊 Financial Limits", "📂 Custom Categories", "🔐 Security"])
    
    with stab1:
        st.subheader("මාසික වියදම් සීමාව")
        conf_df = pd.read_csv(FILES["config"])
        user_conf = conf_df[conf_df['username'] == st.session_state['username']]
        current_limit = user_conf.iloc[0]['monthly_limit'] if not user_conf.empty else 0
        
        new_limit = st.number_input("මාසික වියදම් සීමාව (රු.)", value=int(current_limit))
        if st.button("Limit එක Update කරන්න"):
            if not user_conf.empty:
                conf_df.loc[conf_df['username'] == st.session_state['username'], 'monthly_limit'] = new_limit
            else:
                new_row = pd.DataFrame([[st.session_state['username'], new_limit]], columns=conf_df.columns)
                conf_df = pd.concat([conf_df, new_row])
            conf_df.to_csv(FILES["config"], index=False)
            st.success("වියදම් සීමාව සාර්ථකව Update කළා!")

    with stab2:
        st.subheader("ඔබේම Categories සාදාගන්න")
        cat_df = pd.read_csv(FILES["cats"])
        user_cats = cat_df[cat_df['username'] == st.session_state['username']]
        
        c_col1, c_col2 = st.columns([2,1])
        with c_col1:
            new_cat_name = st.text_input("අලුත් Category නම (උදා: සුරතල් සතුන්)")
            if st.button("Add Category"):
                if new_cat_name:
                    new_cat_row = pd.DataFrame([[st.session_state['username'], new_cat_name]], columns=cat_df.columns)
                    pd.concat([cat_df, new_cat_row]).to_csv(FILES["cats"], index=False)
                    st.rerun()
        with c_col2:
            st.write("දැනට පවතින වර්ග:")
            for idx, r in user_cats.iterrows():
                st.write(f"• {r['cat_name']}")

    with stab3:
        st.subheader("මුරපදය වෙනස් කරන්න (Change Password)")
        old_p = st.text_input("පරණ මුරපදය", type="password")
        new_p = st.text_input("අලුත් මුරපදය", type="password")
        if st.button("Password එක Update කරන්න"):
            udf = pd.read_csv(FILES["users"])
            idx = udf.index[(udf['username'] == st.session_state['username']) & (udf['password'] == make_hash(old_p))].tolist()
            if idx:
                udf.at[idx[0], 'password'] = make_hash(new_p)
                udf.to_csv(FILES["users"], index=False)
                st.success("මුරපදය සාර්ථකව වෙනස් කළා!")
            else: st.error("පරණ මුරපදය වැරදියි!")

# --- 5. ADMIN PANEL ---
elif nav == "👨‍💼 Admin Panel":
    st.title("👨‍💼 Global Administration")
    udf = pd.read_csv(FILES["users"])
    for i, r in udf.iterrows():
        if r['username'] != 'admin':
            c1, c2, c3 = st.columns([2,1,1])
            status = "Approved ✅" if r['approved'] else "Pending ⏳"
            c1.write(f"**{r['username']}** | {status}")
            if not r['approved'] and c2.button("Approve", key=f"a_{i}"):
                udf.at[i, 'approved'] = True
                udf.to_csv(FILES["users"], index=False)
                st.rerun()
            if c3.button("Delete", key=f"d_{i}"):
                udf.drop(i).to_csv(FILES["users"], index=False)
                st.rerun()
