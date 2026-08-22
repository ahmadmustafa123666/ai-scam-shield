"""Privacy-friendly public Streamlit demo for AI Scam Shield.

Unlike the local app.py, this public version never saves visitor messages,
history, or feedback. It only analyses the submitted text for the current page.
"""

import streamlit as st

from scam_shield import analyze_message


st.set_page_config(
    page_title="AI Scam Shield | Public Demo",
    page_icon=":material/shield:",
    layout="wide",
)


with st.sidebar:
    st.title("AI Scam Shield")
    st.badge(
        "Public demo",
        icon=":material/public:",
        color="blue",
    )
    st.caption("Messages are analysed for this page only and are not saved as history.")

    st.subheader("How it works")
    st.markdown(
        "1. Paste an SMS or message.\n"
        "2. The model and safety rules analyse it.\n"
        "3. Review the risk and recommended action."
    )

    st.subheader("Use safely")
    st.caption("Do not paste passwords, card numbers, OTPs, or other real secrets.")


st.title("AI Scam Shield", text_alignment="left")
st.write("A public demo that helps identify suspicious SMS messages before you reply, click, call, or share information.")
st.markdown(
    ":blue-badge[:material/public: Public demo] "
    ":green-badge[:material/lock: No saved message history]"
)

st.subheader("Check a message")
with st.form("message_check_form", border=True):
    message = st.text_area(
        "Message to check",
        placeholder="Paste a message here, for example: Your bank account is suspended. Send your OTP immediately.",
        height=150,
    )
    submitted = st.form_submit_button(
        "Analyze message",
        type="primary",
        icon=":material/search:",
        width="stretch",
    )

if submitted:
    if not message.strip():
        st.warning("Enter a message before analysing it.", icon=":material/warning:")
    else:
        try:
            st.session_state.public_result = analyze_message(message)
        except (FileNotFoundError, ValueError) as error:
            st.error(str(error), icon=":material/error:")


result = st.session_state.get("public_result")
if result:
    st.subheader("Analysis result")
    with st.container(border=True):
        if result["is_scam"]:
            st.error("Suspicious message detected", icon=":material/gpp_maybe:")
        else:
            st.success("This message looks normal", icon=":material/check_circle:")

        risk_column, level_column, model_column = st.columns(3)
        risk_column.metric(
            "Risk score",
            f"{result['risk_score']:.0f}/100",
            icon=":material/speed:",
            border=True,
        )
        level_column.metric(
            "Risk level",
            result["risk_level"],
            icon=":material/flag:",
            border=True,
        )
        model_column.metric(
            "Model result",
            result["model_prediction"].upper(),
            icon=":material/psychology:",
            border=True,
        )
        st.caption(
            f"Model confidence: {result['confidence']:.2f}% · {result['decision_reason']}"
        )

    explanation_column, action_column = st.columns(2)
    with explanation_column:
        with st.container(border=True):
            st.subheader("Why this result")
            if result["is_scam"]:
                st.write(f"**Category:** {result['scam_category']}")
            if result["warning_signs"]:
                for sign in result["warning_signs"]:
                    st.write(f":material/warning: {sign}")
            else:
                st.caption("No obvious scam warning phrases were detected.")

    with action_column:
        with st.container(border=True):
            st.subheader("Recommended action")
            if result["is_scam"]:
                st.warning(result["recommended_action"], icon=":material/security:")
            else:
                st.info(
                    "Continue carefully. Verify unexpected requests using official contact details.",
                    icon=":material/info:",
                )

    if result["suspicious_urls"]:
        with st.expander("Detected links", icon=":material/link:"):
            st.warning("Do not open these links until you verify the sender.")
            for url in result["suspicious_urls"]:
                st.code(url)

    if result["phone_numbers"] or result["email_addresses"]:
        with st.expander("Detected contact details", icon=":material/contact_phone:"):
            st.warning("Do not call, text, or email these details until you verify the sender.")
            for phone_number in result["phone_numbers"]:
                st.code(phone_number)
            for email_address in result["email_addresses"]:
                st.code(email_address)


with st.expander("About this project", icon=":material/info:"):
    st.write(
        "AI Scam Shield combines a machine-learning SMS classifier with safety rules "
        "that look for urgency, sensitive-information requests, suspicious links, "
        "and contact details."
    )
    st.markdown(
        "- **ML model:** TF-IDF text features with logistic regression.\n"
        "- **Safety rules:** Add context that a text-only model can miss.\n"
        "- **Privacy:** This public demo does not store submitted messages as history or feedback.\n"
        "- **Important:** Treat results as a safety warning, not proof. Use official channels to verify unexpected requests."
    )


st.caption("This is an educational demo. Do not rely on it as the only basis for financial or security decisions.")
