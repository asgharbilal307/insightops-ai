import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


BASE_URL = "http://127.0.0.1:8000"


# -------------------------
# SESSION STATE
# -------------------------

if "token" not in st.session_state:
    st.session_state.token = None


# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="InsightOps AI",
    layout="wide"
)


# -------------------------
# TITLE
# -------------------------

st.title("InsightOps AI")
st.subheader("AI-Powered Incident Intelligence Platform")


# -------------------------
# LOGIN SIDEBAR
# -------------------------

st.sidebar.header("Authentication")

username = st.sidebar.text_input("Username")

password = st.sidebar.text_input(
    "Password",
    type="password"
)

if st.sidebar.button("Login"):

    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": username,
            "password": password
        }
    )

    if response.status_code == 200:

        token = response.json()["access_token"]

        st.session_state.token = token

        st.sidebar.success("Login successful")

    else:

        st.sidebar.error("Invalid credentials")


# -------------------------
# AUTH HEADERS
# -------------------------

headers = {}

if st.session_state.token:

    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }


# -------------------------
# SIDEBAR MENU
# -------------------------

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "Text Analysis",
        "Image Analysis",
        "Text Extraction",
        "Audio Analysis",
        "Multimodal AI",
        "Forecasting",
        "Alerts"
    ]
)


# -------------------------
# DASHBOARD
# -------------------------

if menu == "Dashboard":

    st.header("🚀 AI Incident Command Center")

    try:

        # -------------------------
        # FETCH DATA
        # -------------------------

        dashboard_response = requests.get(
            f"{BASE_URL}/reports/dashboard",
            headers=headers
        )

        incidents_response = requests.get(
            f"{BASE_URL}/ai/incidents",
            headers=headers
        )

        forecast_response = requests.get(
            f"{BASE_URL}/reports/forecast",
            headers=headers
        )

        alerts_response = requests.get(
            f"{BASE_URL}/reports/alerts",
            headers=headers
        )

        dashboard_data = dashboard_response.json()
        incidents = incidents_response.json()
        forecast_data = forecast_response.json()
        alerts_data = alerts_response.json()

        # -------------------------
        # KPI METRICS
        # -------------------------

        total_incidents = dashboard_data["total_incidents"]
        critical_incidents = dashboard_data["critical_incidents"]
        high_incidents = dashboard_data["high_incidents"]

        risk_score = min(
            100,
            (critical_incidents * 8) + (high_incidents * 4)
        )

        st.subheader("📊 Executive Overview")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Incidents",
            total_incidents
        )

        col2.metric(
            "Critical",
            critical_incidents
        )

        col3.metric(
            "High Severity",
            high_incidents
        )

        col4.metric(
            "AI Risk Score",
            f"{risk_score}%"
        )

        st.divider()

        # -------------------------
        # INCIDENT CATEGORY CHART
        # -------------------------

        st.subheader("📈 Incident Categories")

        categories = dashboard_data["categories"]

        category_df = pd.DataFrame({
            "Category": list(categories.keys()),
            "Count": list(categories.values())
        })

        fig = px.bar(
            category_df,
            x="Category",
            y="Count",
            title="Incident Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # -------------------------
        # FORECASTING
        # -------------------------

        st.subheader("AI Forecasting")

        if "forecast_next_7_days" in forecast_data:

            forecast_values = forecast_data["forecast_next_7_days"]

            forecast_df = pd.DataFrame({
                "Day": list(range(1, 8)),
                "Predicted Incidents": forecast_values
            })

            forecast_fig = px.line(
                forecast_df,
                x="Day",
                y="Predicted Incidents",
                markers=True,
                title="Predicted Incident Trend"
            )

            st.plotly_chart(
                forecast_fig,
                use_container_width=True
            )

        st.divider()

        # -------------------------
        # LIVE INCIDENT FEED
        # -------------------------

        st.subheader("📰 Live Incident Feed")

        if len(incidents) == 0:

            st.info("No incidents available")

        else:

            for incident in incidents[-5:]:

                severity = incident.get(
                    "severity",
                    "MEDIUM"
                )

                if severity == "CRITICAL":
                    st.error(
                        f" {incident['input_text']}"
                    )

                elif severity == "HIGH":
                    st.warning(
                        f" {incident['input_text']}"
                    )

                else:
                    st.info(
                        f"{incident['input_text']}"
                    )

        st.divider()

        # -------------------------
        # ALERTS PANEL
        # -------------------------

        st.subheader("Active Alerts")

        alerts = alerts_data["alerts"]

        if len(alerts) == 0:

            st.success(
                "No active operational alerts"
            )

        else:

            for alert in alerts:

                st.error(alert)

        st.divider()

        # -------------------------
        # AI INSIGHTS
        # -------------------------

        st.subheader("AI Insights")

        if total_incidents > 5:

            st.warning(
                "Incident frequency increasing. Potential infrastructure instability detected."
            )

        if critical_incidents > 2:

            st.error(
                "High critical incident count detected. Immediate operational review recommended."
            )

        if risk_score > 70:

            st.error(
                "AI Risk Score extremely elevated."
            )

        else:

            st.success(
                "Operational environment appears stable."
            )

    except Exception as e:

        st.error(str(e))


# -------------------------
# TEXT ANALYSIS
# -------------------------

elif menu == "Text Analysis":

    st.header("AI Text Analysis")

    text = st.text_area(
        "Enter Incident Text"
    )

    if st.button("Analyze Text"):

        payload = {
            "text": text
        }

        response = requests.post(
            f"{BASE_URL}/ai/analyze",
            json=payload,
            headers=headers
        )

        st.json(response.json())


# -------------------------
# IMAGE ANALYSIS
# -------------------------

elif menu == "Image Analysis":

    st.header("Image Incident Analysis")

    image = st.file_uploader(
        "Upload Image",
        type=["png", "jpg", "jpeg"]
    )

    if image:

        files = {
            "file": image
        }

        response = requests.post(
            f"{BASE_URL}/ai/analyze/image",
            files=files,
            headers=headers
        )

        st.json(response.json())


# -------------------------
# TEXT EXTRACTION
# -------------------------

elif menu == "Text Extraction":

    st.header("Extract Text from Image")

    image = st.file_uploader(
        "Upload Image with Text",
        type=["png", "jpg", "jpeg"]
    )

    if image:

        files = {
            "file": image
        }

        response = requests.post(
            f"{BASE_URL}/ai/extract-text",
            files=files,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            extracted_text = data.get("extracted_text", "")
            
            st.success("Text Extracted Successfully!")
            st.text_area("Extracted Text", extracted_text, height=200)
        else:
            st.error(f"Error: {response.text}")


# -------------------------
# AUDIO ANALYSIS
# -------------------------

elif menu == "Audio Analysis":

    st.header("Audio Incident Analysis")

    audio = st.file_uploader(
        "Upload Audio",
        type=["wav", "mp3"]
    )

    if audio:

        files = {
            "file": audio
        }

        response = requests.post(
            f"{BASE_URL}/ai/analyze/audio",
            files=files,
            headers=headers
        )

        if response.status_code == 200:

            st.success("Audio Analysis Complete")

            st.json(response.json())

        else:

            st.error(f"Error: {response.text}")


# -------------------------
# MULTIMODAL AI
# -------------------------

elif menu == "Multimodal AI":

    st.header("Multimodal Incident Intelligence")

    text = st.text_area(
        "Incident Description"
    )

    image = st.file_uploader(
        "Upload Screenshot",
        type=["png", "jpg", "jpeg"]
    )

    audio = st.file_uploader(
        "Upload Audio",
        type=["wav", "mp3"]
    )

    if st.button("Run Multimodal Analysis"):

        files = {}

        if image:
            files["image"] = image

        if audio:
            files["audio"] = audio

        response = requests.post(
            f"{BASE_URL}/ai/analyze/multimodal",
            data={"text": text},
            files=files,
            headers=headers
        )

        st.json(response.json())


# -------------------------
# FORECASTING
# -------------------------

elif menu == "Forecasting":

    st.header("Incident Forecasting")

    response = requests.get(
        f"{BASE_URL}/reports/forecast",
        headers=headers
    )

    st.write(response.status_code)
    st.write(response.text)


    if response.status_code != 200:

        st.error(response.json()["detail"])

    else:

        data = response.json()

        if "forecast_next_7_days" in data:

            forecast = data["forecast_next_7_days"]

            df = pd.DataFrame({
                "Day": list(range(1, 8)),
                "Predicted Incidents": forecast
            })

            st.line_chart(
                df.set_index("Day")
            )

            st.metric(
                "Average Daily Incidents",
                data["average_daily_incidents"]
            )

        else:

            st.warning(data["message"])


# -------------------------
# ALERTS
# -------------------------

elif menu == "Alerts":

    st.header("Active Alerts")

    response = requests.get(
        f"{BASE_URL}/reports/alerts",
        headers=headers
    )

    if response.status_code != 200:

        st.error(response.json()["detail"])

    else:

        data = response.json()

        alerts = data["alerts"]

        if len(alerts) == 0:

            st.success("No active alerts")

        else:

            for alert in alerts:

                st.error(alert)