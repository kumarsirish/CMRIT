import streamlit as st
from tyl_dashboard import render_tyl_analysis_dashboard
from teacher_load_dashboard import render_teacher_load_dashboard


def main():
    st.set_page_config(page_title="Dashboard Home", layout="wide")

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "tyl_dashboard"

    if st.session_state["current_page"] == "tyl_dashboard":
        render_tyl_analysis_dashboard()
    elif st.session_state["current_page"] == "teacher_load_dashboard":
        render_teacher_load_dashboard()
    else:
        st.title("Home")
        st.subheader("Dashboards")

        dashboard_options = [
            "TYL Analysis Dashboard",
            "Teacher Load Dashboard",
        ]

        selected_dashboard = st.selectbox("Select dashboard", dashboard_options)

        if st.button("Open Dashboard"):
            if selected_dashboard == "TYL Analysis Dashboard":
                st.session_state["current_page"] = "tyl_dashboard"
                st.rerun()
            elif selected_dashboard == "Teacher Load Dashboard":
                st.session_state["current_page"] = "teacher_load_dashboard"
                st.rerun()

        st.info("More dashboards can be added later in this menu.")


if __name__ == "__main__":
    main()
