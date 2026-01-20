import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ඇප් එකේ නම සහ පෙනුම
st.set_page_config(page_title="වියදම් පාලකය", layout="centered")
st.title("📊 මගේ මාසික වියදම් පාලකය")

# දත්ත සේව් කරන්න file එකක් හැදීම
FILE_NAME = "my_expenses.csv"
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["දිනය", "වර්ගය", "විස්තරය", "මුදල"])
    df.to_csv(FILE_NAME, index=False)

# පැත්තක තියෙන Menu එක (Sidebar)
st.sidebar.header("නව දත්ත ඇතුළත් කරන්න")
date = st.sidebar.date_input("දිනය", datetime.now())
cat = st.sidebar.selectbox("වර්ගය", ["කෑම බීම", "පෙට්‍රල්/බයික්", "ආදායම (Income)", "බිල්පත්", "වෙනත්"])
desc = st.sidebar.text_input("විස්තරය")
amt = st.sidebar.number_input("මුදල (රු.)", min_value=0)

if st.sidebar.button("ඇතුළත් කරන්න"):
    new_data = pd.DataFrame([[date, cat, desc, amt]], columns=["දිනය", "වර්ගය", "විස්තරය", "මුදල"])
    new_data.to_csv(FILE_NAME, mode='a', header=False, index=False)
    st.sidebar.success("දත්ත ඇතුළත් කළා!")
    st.rerun()

# දත්ත කියවීම සහ පෙන්වීම
df = pd.read_csv(FILE_NAME)

# ගණනය කිරීම්
income = df[df["වර්ගය"] == "ආදායම (Income)"]["මුදල"].sum()
expense = df[df["වර්ගය"] != "ආදායම (Income)"]["මුදල"].sum()
profit = income - expense

# ප්‍රධාන Dashboard එක
col1, col2, col3 = st.columns(3)
col1.metric("මුළු ආදායම", f"රු. {income}")
col2.metric("මුළු වියදම", f"රු. {expense}")
col3.metric("ලාභය/ඉතිරිය", f"රු. {profit}")

st.divider()

# දත්ත වගුව සහ ප්‍රස්තාරය
if not df.empty:
    st.subheader("📝 ගනුදෙනු ලැයිස්තුව")
    st.dataframe(df, use_container_width=True)
    
    st.subheader("📈 වියදම් විශ්ලේෂණය")
    chart_data = df[df["වර්ගය"] != "ආදායම (Income)"].groupby("වර්ගය")["මුදල"].sum()
    st.bar_chart(chart_data)
else:
    st.info("තවම දත්ත ඇතුළත් කර නැත.")