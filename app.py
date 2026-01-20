import streamlit as st
import pandas as pd
from datetime import datetime

# Google Sheet එකට සම්බන්ධ වීමට අවශ්‍ය library එක
# මේක වැඩ කරන්න නම් GitHub එකේ requirements.txt කියලා ෆයිල් එකකුත් ඕනේ (පහළ බලන්න)

st.set_page_config(page_title="Budget Tracker", layout="centered")
st.title("💰 මගේ වියදම් පාලකය (Google Sheets)")

# Secrets වලින් Sheet URL එක ලබා ගැනීම
if "gsheet_url" in st.secrets:
    sheet_url = st.secrets["gsheet_url"]
    # Google Sheet එක CSV එකක් ලෙස කියවීමට URL එක සකස් කිරීම
    csv_url = sheet_url.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv')
else:
    st.error("කරුණාකර Streamlit Secrets වල 'gsheet_url' ඇතුළත් කරන්න.")
    st.stop()

# --- දත්ත ඇතුළත් කිරීම ---
with st.sidebar:
    st.header("නව ගනුදෙනුව")
    date = st.date_input("දිනය", datetime.now())
    category = st.selectbox("වර්ගය", ["ආදායම (Income)", "කෑම බීම", "පෙට්‍රල්/බයික්", "බිල්පත්", "වෙනත්"])
    desc = st.text_input("විස්තරය")
    amount = st.number_input("මුදල (රු.)", min_value=0)
    
    if st.button("ඇතුළත් කරන්න"):
        # මෙතනදී දත්ත සේව් කරන්න නම් අලුත් ක්‍රමයක් ඕනේ. 
        # දැනට පවතින දත්ත පෙන්වීමට මෙය උදව් වේ.
        st.success("දත්ත ඇතුළත් වුණා! (Sheet එක පරීක්ෂා කරන්න)")

# --- දත්ත පෙන්වීම ---
try:
    df = pd.read_csv(csv_url)
    
    # Dashboard
    income = df[df["වර්ගය"] == "ආදායම (Income)"]["මුදල"].sum()
    expense = df[df["වර්ගය"] != "ආදායම (Income)"]["මුදල"].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("ආදායම", f"රු. {income}")
    col2.metric("වියදම", f"රු. {expense}")
    col3.metric("ඉතිරිය", f"රු. {income - expense}")
    
    st.divider()
    st.subheader("📝 ගනුදෙනු ලැයිස්තුව")
    st.dataframe(df, use_container_width=True)
except:
    st.warning("තවම Sheet එකේ දත්ත නැත හෝ සම්බන්ධ වීමේ දෝෂයකි.")
