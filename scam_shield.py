"""Shared scam-analysis logic used by both Streamlit and the API.

Keeping this code outside app.py means the browser interface and n8n always
receive the same prediction, warning signs, category, and advice.
"""

from functools import lru_cache
from pathlib import Path
import re

import joblib


# The project directory is the directory containing this file.
PROJECT_FOLDER = Path(__file__).resolve().parent
MODEL_FOLDER = PROJECT_FOLDER / "models"


# Each warning sign contributes to the safety risk score.  Stronger signals,
# such as an OTP or a request for bank details, receive more weight.
WARNING_WEIGHTS = {
    "Prize or lottery language": 10,
    "Urgency or pressure tactics": 20,
    "Request for sensitive financial information": 30,
    "Money or payment-related language": 10,
    "Suspicious or clickable link language": 20,
    "Suspicious URL detected": 20,
    "Phone number detected": 5,
    "Email address detected": 5,
}

# Detect common web links without ever visiting them.  This recognises links
# with http(s), www, and common short/plain domains such as bit.ly/example.
URL_PATTERN = re.compile(
    r"(?i)(?<!@)\b(?:(?:https?://|www\.)[^\s<>()\[\]{}\"']+|"
    r"(?:[a-z0-9-]+\.)+(?:com|org|net|io|co|ly|info|biz|me|xyz|online|site|app|link)"
    r"(?:/[^\s<>()\[\]{}\"']*)?)"
)
EMAIL_PATTERN = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{7,10}(?!\w)")


@lru_cache(maxsize=1)
def load_model():
    """Load the trained classifier and its matching TF-IDF vectorizer once."""
    model_path = MODEL_FOLDER / "spam_model.pkl"
    vectorizer_path = MODEL_FOLDER / "tfidf_vectorizer.pkl"

    if not model_path.exists() or not vectorizer_path.exists():
        raise FileNotFoundError(
            "Model files were not found. Expected models/spam_model.pkl and "
            "models/tfidf_vectorizer.pkl next to this file."
        )

    return joblib.load(model_path), joblib.load(vectorizer_path)


def detect_warning_signs(message):
    """Return human-readable clues that appear in the message."""
    text = message.lower()
    warning_signs = []

    if any(word in text for word in ["won", "winner", "prize", "lottery", "reward", "congratulations"]):
        warning_signs.append("Prize or lottery language")
    if any(word in text for word in ["urgent", "immediately", "act now", "hurry", "limited time", "right now"]):
        warning_signs.append("Urgency or pressure tactics")
    if any(word in text for word in ["bank details", "bank account", "credit card", "debit card", "otp", "pin", "password"]):
        warning_signs.append("Request for sensitive financial information")
    if any(word in text for word in ["$", "£", "€", "cash", "payment", "money", "transfer"]):
        warning_signs.append("Money or payment-related language")
    if any(word in text for word in ["http://", "https://", "www.", "click here", "click the link"]):
        warning_signs.append("Suspicious or clickable link language")
    if detect_urls(message):
        warning_signs.append("Suspicious URL detected")
    if detect_phone_numbers(message):
        warning_signs.append("Phone number detected")
    if detect_email_addresses(message):
        warning_signs.append("Email address detected")

    return warning_signs


def detect_urls(message):
    """Return unique URLs found in a message without opening them."""
    urls = []
    email_spans = [(match.start(), match.end()) for match in EMAIL_PATTERN.finditer(message)]
    for match in URL_PATTERN.finditer(message):
        # Reject a domain-shaped fragment inside an email address, for example
        # "bank.com" inside "help@fake-bank.com".
        if any(start <= match.start() < end for start, end in email_spans):
            continue
        # Sentence punctuation is usually not part of a link.
        url = match.group(0).rstrip(".,!?;:)]}")
        if url and url not in urls:
            urls.append(url)
    return urls


def detect_phone_numbers(message):
    """Find likely phone numbers without calling or validating them."""
    phone_numbers = []
    for match in PHONE_PATTERN.findall(message):
        digits = re.sub(r"\D", "", match)
        if 7 <= len(digits) <= 15 and match not in phone_numbers:
            phone_numbers.append(match)
    return phone_numbers


def detect_email_addresses(message):
    """Find email-shaped text without sending mail or checking the address."""
    return list(dict.fromkeys(EMAIL_PATTERN.findall(message)))


def detect_scam_category(message):
    """Return the first matching rule-based scam category."""
    text = message.lower()
    categories = [
        ("🎁 Prize / Lottery Scam", ["won", "winner", "prize", "lottery", "reward", "congratulations"]),
        ("🏦 Banking / Financial Scam", ["bank account", "bank details", "otp", "pin", "debit card", "credit card", "account suspended", "verify account"]),
        ("🔐 Phishing / Credential Theft", ["password", "login", "verify your account", "click here", "click the link", "http://", "https://", "www."]),
        ("💼 Job Scam", ["job offer", "work from home", "earn daily", "easy income", "hiring", "vacancy", "salary", "recruitment"]),
        ("💰 Investment Scam", ["investment", "invest", "crypto", "bitcoin", "profit", "guaranteed return", "double your money"]),
        ("📦 Delivery / Parcel Scam", ["parcel", "package", "delivery", "courier", "shipment", "delivery fee"]),
        ("👤 Impersonation Scam", ["police", "government", "tax department", "customs", "your boss", "ceo", "family member"]),
    ]

    for category, words in categories:
        if any(word in text for word in words):
            return category
    return "⚠️ General Suspicious Message"


def get_recommended_action(scam_category):
    """Give advice that matches the rule-based category."""
    actions = {
        "🎁 Prize / Lottery Scam": "Do not send money or provide personal information to claim the prize. Ignore the message, block the sender, and report it if possible.",
        "🏦 Banking / Financial Scam": "Do not provide your OTP, PIN, card number, password, or bank details. Contact your bank through its official phone number or website.",
        "🔐 Phishing / Credential Theft": "Do not click suspicious links or enter login details. Open the official website or app yourself and verify the request there.",
        "💼 Job Scam": "Do not pay registration, processing, training, or interview fees. Verify the company and vacancy through its official website.",
        "💰 Investment Scam": "Do not transfer money or cryptocurrency based on guaranteed-profit claims. Verify the platform and avoid unrealistic returns.",
        "📦 Delivery / Parcel Scam": "Do not pay unexpected delivery fees or open unknown tracking links. Check directly through the courier's official website.",
        "👤 Impersonation Scam": "Do not send money or sensitive information. Contact the person or organization using a trusted, independent channel.",
    }
    return actions.get(
        scam_category,
        "Do not reply, click unknown links, send money, or share sensitive information until you independently verify the sender.",
    )


def calculate_risk_score(spam_probability, warning_signs):
    """Combine the ML spam probability with clear rule-based warning signs.

    The ML model contributes up to 50 points.  The warning signs contribute
    the other 50 points (or more before the final cap).  This lets a message
    such as "send your OTP immediately" be treated cautiously even when a
    small training dataset gives it a weak ham prediction.
    """
    model_points = spam_probability * 0.5
    warning_points = sum(WARNING_WEIGHTS.get(sign, 0) for sign in warning_signs)

    # Urgency plus a request for sensitive information is especially risky.
    if (
        "Urgency or pressure tactics" in warning_signs
        and "Request for sensitive financial information" in warning_signs
    ):
        warning_points += 10

    return round(min(100, model_points + warning_points), 2)


def analyze_message(message):
    """Run the complete existing AI Scam Shield analysis and return JSON-safe data."""
    cleaned_message = message.strip()
    if not cleaned_message:
        raise ValueError("message must not be empty")

    model, tfidf = load_model()
    message_tfidf = tfidf.transform([cleaned_message])
    model_prediction = str(model.predict(message_tfidf)[0]).lower()
    probabilities = model.predict_proba(message_tfidf)[0]
    warning_signs = detect_warning_signs(cleaned_message)
    suspicious_urls = detect_urls(cleaned_message)
    phone_numbers = detect_phone_numbers(cleaned_message)
    email_addresses = detect_email_addresses(cleaned_message)

    # Use the probability for the spam class, not simply the highest class.
    classes = [str(label).lower() for label in model.classes_]
    spam_probability = (
        float(probabilities[classes.index("spam")] * 100)
        if "spam" in classes
        else 0.0
    )
    model_confidence = float(max(probabilities) * 100)
    risk_score = calculate_risk_score(spam_probability, warning_signs)
    risk_level = "HIGH" if risk_score >= 70 else "MEDIUM" if risk_score >= 40 else "LOW"

    # A high score can override a weak ham prediction; the original model
    # prediction is returned too, so the decision remains transparent.
    is_scam = model_prediction == "spam" or risk_score >= 70
    prediction = "spam" if is_scam else "ham"
    scam_category = detect_scam_category(cleaned_message) if is_scam else None

    if model_prediction == "spam":
        decision_reason = "The ML model classified this message as spam."
    elif is_scam:
        decision_reason = "High-risk warning signs overrode the ML model's ham prediction."
    else:
        decision_reason = "The ML model and risk score both indicate low concern."

    return {
        "message": cleaned_message,
        "prediction": prediction,
        "model_prediction": model_prediction,
        "is_scam": is_scam,
        "confidence": round(model_confidence, 2),
        "spam_probability": round(spam_probability, 2),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "decision_reason": decision_reason,
        "warning_signs": warning_signs,
        "suspicious_urls": suspicious_urls,
        "phone_numbers": phone_numbers,
        "email_addresses": email_addresses,
        "scam_category": scam_category,
        "recommended_action": get_recommended_action(scam_category) if is_scam else None,
    }
