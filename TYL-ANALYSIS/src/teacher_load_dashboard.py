import streamlit as st


def render_teacher_load_dashboard():
    top_col1, top_col2 = st.columns([1, 6])
    with top_col1:
        if st.button("← Back to Home"):
            st.session_state["current_page"] = "home"
            st.rerun()

    with top_col2:
        st.title("Teacher Load Dashboard")

    st.caption("Work in progress")
    st.empty()
