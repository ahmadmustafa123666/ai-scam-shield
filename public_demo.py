"""Privacy-friendly public Streamlit demo for AI Scam Shield.

Unlike the local app.py, this public version never saves visitor messages,
history, or feedback. It only analyses submitted text for the current page.
"""

import streamlit as st

from scam_shield import analyze_message


EXAMPLE_MESSAGES = {
    "banking": "Urgent: Your bank account has been suspended. Send your OTP immediately to restore access.",
    "link": "Your parcel is waiting. Pay the delivery fee now at http://fake-courier-payment.com/verify.",
    "normal": "Hi, I will reach home around 6 pm. Please let me know if you need anything.",
}


def load_example(example_name):
    """Place a safe sample message into the text area."""
    st.session_state.message_input = EXAMPLE_MESSAGES[example_name]


st.set_page_config(
    page_title="AI Scam Shield | Public demo",
    page_icon=":material/shield:",
    layout="wide",
)


with st.sidebar:
    st.title("AI Scam Shield")
    st.badge("Public demo", icon=":material/public:", color="blue")
    st.caption("Privacy-first analysis. Submitted messages are not saved as history.")

    st.header("How it works")
    st.markdown(
        "1. Paste an SMS or message.\n"
        "2. The model and safety rules analyse it.\n"
        "3. Review the risk and recommended action."
    )

    st.header("Use safely")
    st.caption("Use sample text only. Never paste real OTPs, passwords, card numbers, or banking details.")

    st.header("What this checks")
    st.caption("Urgency, requests for sensitive information, links, phone numbers, email addresses, and scam patterns.")


with st.container(border=True):
    st.title("AI Scam Shield", text_alignment="left")
    st.write("A safer second opinion before you reply, click a link, call a number, or share information.")
    with st.container(horizontal=True, gap="xsmall"):
        st.badge("Public demo", icon=":material/public:", color="blue")
        st.badge("No saved message history", icon=":material/lock:", color="green")
        st.badge("Explainable results", icon=":material/visibility:", color="orange")


st.space("small")
st.header("Check a message")
st.caption("Paste a message below. Use sample messages only — never paste a real OTP, password, or card number.")

st.subheader("Try a safe example")
example_one, example_two, example_three = st.columns(3)
example_one.button(
    "Banking / OTP scam",
    icon=":material/account_balance:",
    on_click=load_example,
    args=("banking",),
    width="stretch",
)
example_two.button(
    "Suspicious link",
    icon=":material/link:",
    on_click=load_example,
    args=("link",),
    width="stretch",
)
example_three.button(
    "Normal message",
    icon=":material/chat:",
    on_click=load_example,
    args=("normal",),
    width="stretch",
)

with st.form("message_check_form", border=True):
    message = st.text_area(
        "Message to check",
        placeholder="For example: Your bank account is suspended. Send your OTP immediately.",
        height=150,
        key="message_input",
    )
    submitted = st.form_submit_button(
        "Analyse message",
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
    st.header("Analysis result")

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
        st.caption(f"Model confidence: {result['confidence']:.2f}% · {result['decision_reason']}")

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


with st.expander("About this demo", icon=":material/info:"):
    st.write(
        "AI Scam Shield combines a machine-learning SMS classifier with safety rules "
        "that look for urgency, requests for sensitive information, suspicious links, "
        "and contact details."
    )
    st.markdown(
        "- **ML model:** TF-IDF text features with logistic regression.\n"
        "- **Safety rules:** Add context that a text-only model can miss.\n"
        "- **Privacy:** This public demo does not store submitted messages as history or feedback.\n"
        "- **Important:** Treat results as a safety warning, not proof. Verify unexpected requests through official channels."
    )


st.caption("Educational demo only. Do not rely on it as the sole basis for financial or security decisions.")
