import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime

# පිටුවේ සැකසුම්
st.set_page_config(page_title="My Wallet Pro", page_icon="💰", layout="wide")

# ලස්සන පෙනුම සඳහා CSS (Custom Styling)
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "data.csv"

# දත්ත කියවීම
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
    df['දිනය'] = pd.to_datetime(df['දිනය']).dt.date
else:
    df = pd.DataFrame(columns=["දිනය", "වර්ගය", "විස්තරය", "මුදල"])

# --- SIDEBAR (දත්ත ඇතුළත් කිරීම) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2489/2489756.png", width=100)
    st.title("My Wallet Pro")
    st.markdown("---")
    
    with st.form("entry_form", clear_on_submit=True):
        date = st.date_input("📅 දිනය", datetime.now())
        category = st.selectbox("📂 වර්ගය", [
            "🍱 කෑම බීම", 
            "⛽ පෙට්‍රල්/බයික්", 
            "💵 ආදායම (Income)", 
            "🔌 බිල්පත්", 
            "🛍️ ෂොපින්", 
            "🏥 සෞඛ්‍ය", 
            "⚙️ වෙනත්"
        ])
        desc = st.text_input("📝 විස්තරය (උදා: දිවා ආහාරය)")
        amount = st.number_input("💰 මුදල (රු.)", min_value=0, step=100)
        submit = st.form_submit_button("ඇතුළත් කරන්න ✨")

    if submit:
        if amount > 0:
            new_row = pd.DataFrame([[date, category, desc, amount]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(FILE_NAME, index=False)
            st.success("සාර්ථකව එකතු වුණා!")
            st.rerun()
        else:
            st.warning("කරුණාකර මුදලක් ඇතුළත් කරන්න.")

# --- MAIN DASHBOARD ---
st.title("📊 මගේ මුදල් පාලකය")

if not df.empty:
    # ගණනය කිරීම්
    df['මුදල'] = pd.to_numeric(df['මුදල'])
    income = df[df["වර්ගය"] == "💵 ආදායම (Income)"]["මුදල"].sum()
    expense = df[df["වර්ගය"] != "💵 ආදායම (Income)"]["මුදල"].sum()
    balance = income - expense

    # Summary Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("මුළු ආදායම", f"රු. {income:,.2f}", delta_color="normal")
    col2.metric("මුළු වියදම", f"රු. {expense:,.2f}", delta="-"+str(expense), delta_color="inverse")
    col3.metric("අතේ ඇති ඉතිරිය", f"රු. {balance:,.2f}", delta=str(balance))

    st.markdown("---")

    # Charts Section
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("📈 වියදම් බෙදී ඇති ආකාරය")
        exp_df = df[df["වර්ගය"] != "💵 ආදායම (Income)"]
        if not exp_df.empty:
            fig = px.pie(exp_df, values='මුදල', names='වර්ගය', hole=0.4,
                         color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.subheader("📅 මෑතකාලීන ගනුදෙනු")
        st.dataframe(df.sort_values(by="දිනය", ascending=False).head(10), use_container_width=True)

    # Search & Filter
    st.markdown("---")
    st.subheader("🔍 සියලුම දත්ත සෙවීම")
    search_term = st.text_input("විස්තරය අනුව සොයන්න...")
    if search_term:
        display_df = df[df['විස්තරය'].str.contains(search_term, case=False, na=False)]
    else:
        display_df = df

    st.table(display_df)

    # Report Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 සම්පූර්ණ Report එක ලබාගන්න (Excel/CSV)",
        data=csv,
        file_name=f'Wallet_Report_{datetime.now().strftime("%Y-%m")}.csv',
        mime='text/csv',
    )

else:
    st.info("👋 සාදරයෙන් පිළිගන්නවා! ඔබගේ පළමු ගනුදෙනුව වම්පස ඇති පැනලය (Sidebar) මගින් ඇතුළත් කරන්න.")

# Footer
st.markdown("<br><hr><center>Made with ❤️ for Better Budgeting</center>", unsafe_allow_html=True)
