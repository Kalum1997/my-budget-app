import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Budget Tracker", layout="centered")
st.title("💰 මගේ මාසික වියදම් පාලකය")

# දත්ත ගොනුව පරීක්ෂා කිරීම
FILE_NAME = "data.csv"

# දත්ත කියවීම
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(columns=["දිනය", "වර්ගය", "විස්තරය", "මුදල"])

# Sidebar එකෙන් දත්ත ඇතුළත් කිරීම
with st.sidebar:
    st.header("නව ගනුදෙනුව")
    date = st.date_input("දිනය")
    category = st.selectbox("වර්ගය", ["කෑම බීම", "පෙට්‍රල්/බයික්", "ආදායම (Income)", "බිල්පත්", "වෙනත්"])
    desc = st.text_input("විස්තරය")
    amount = st.number_input("මුදල", min_value=0)
    
    if st.button("ඇතුළත් කරන්න"):
        new_row = pd.DataFrame([[str(date), category, desc, amount]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        # දත්ත සේව් කිරීම
        df.to_csv(FILE_NAME, index=False)
        st.success("දත්ත සාර්ථකව සේව් වුණා!")
        st.rerun()

# Dashboard
if not df.empty:
    df['මුදල'] = pd.to_numeric(df['මුදල'])
    income = df[df["වර්ගය"] == "ආදායම (Income)"]["මුදල"].sum()
    expense = df[df["වර්ගය"] != "ආදායම (Income)"]["මුදල"].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("ආදායම", f"රු. {income}")
    col2.metric("වියදම", f"රු. {expense}")
    st.metric("ඉතිරිය", f"රු. {income - expense}")
    
    st.divider()
    st.dataframe(df, use_container_width=True)
    
    # දත්ත සියල්ල මකා දැමීමට බොත්තමක් (අවශ්‍ය නම් පමණක්)
    if st.button("සියලු දත්ත මකන්න"):
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
            st.rerun()
else:
    st.info("තවම දත්ත නැත. Sidebar එකෙන් ඇතුළත් කරන්න.")
