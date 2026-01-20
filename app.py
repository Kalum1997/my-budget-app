import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="වියදම් පාලකය", layout="centered")
st.title("💰 මගේ මාසික වියදම් පාලකය")

# Google Sheets සම්බන්ධතාවය
conn = st.connection("gsheets", type=GSheetsConnection)

# Sheet එකේ ඇති දත්ත කියවීම (Cache එක නැති කිරීමට ttl=0 දමන්න)
df = conn.read(ttl=0)

# Sidebar එකෙන් දත්ත ඇතුළත් කිරීම
with st.sidebar:
    st.header("නව ගනුදෙනුව")
    date = st.date_input("දිනය")
    category = st.selectbox("වර්ගය", ["කෑම බීම", "පෙට්‍රල්/බයික්", "ආදායම (Income)", "බිල්පත්", "වෙනත්"])
    desc = st.text_input("විස්තරය")
    amount = st.number_input("මුදල", min_value=0)
    
    if st.button("ඇතුළත් කරන්න"):
        # අලුත් පේළිය සෑදීම
        new_row = pd.DataFrame([{
            "දිනය": str(date),
            "වර්ගය": category,
            "විස්තරය": desc,
            "මුදල": amount
        }])
        
        # දැනට තියෙන දත්ත වලට අලුත් පේළිය එකතු කිරීම
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # Google Sheet එක Update කිරීම
        conn.update(data=updated_df)
        
        st.success("දත්ත සාර්ථකව Sheet එකට එකතු වුණා!")
        st.rerun()

# Dashboard එක
if not df.empty:
    # මුදල් ගණනය කිරීම (මුදල column එක number එකක් බව තහවුරු කරගන්න)
    df['මුදල'] = pd.to_numeric(df['මුදල'])
    income = df[df["වර්ගය"] == "ආදායම (Income)"]["මුදල"].sum()
    expense = df[df["වර්ගය"] != "ආදායම (Income)"]["මුදල"].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("මුළු ආදායම", f"රු. {income}")
    col2.metric("මුළු වියදම", f"රු. {expense}")
    st.metric("ඉතිරි මුදල (Profit)", f"රු. {income - expense}")
    
    st.divider()
    st.subheader("📝 ගනුදෙනු ලැයිස්තුව")
    st.dataframe(df, use_container_width=True)
else:
    st.info("තවම දත්ත කිසිවක් නැත. Sidebar එකෙන් ඇතුළත් කරන්න.")
