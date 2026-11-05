
import streamlit as st

st.set_page_config(
    page_title="Bank Test",
    page_icon="🏦"
)

st.title("🏦 Bank Management System")

st.success("Streamlit is working successfully!")

st.write("Welcome to your banking application.")

name = st.text_input("Enter your name")

if st.button("Submit"):
    st.write(f"Welcome, {name}!")
