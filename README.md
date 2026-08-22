# Publish the AI Scam Shield public demo

This public version uses `public_demo.py`. It analyses a visitor's current
message but does not save check history or feedback.

## Files that must be in the GitHub repository

```text
AI-Scam-Shield/
├── public_demo.py
├── scam_shield.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml
└── models/
    ├── spam_model.pkl
    └── tfidf_vectorizer.pkl
```

Do not upload `.venv`, `ai_scam_shield.db`, `check_history.csv`,
`feedback.csv`, `.streamlit/secrets.toml`, or model backup files. The provided
`.gitignore` excludes them.

## Deploy with Streamlit Community Cloud

1. Create a public GitHub repository named `AI-Scam-Shield`.
2. Put the required files above into that repository and commit them.
3. Go to `https://share.streamlit.io`, sign in with GitHub, and select
   **Create app**.
4. Choose the repository and set the entrypoint file to `public_demo.py`.
5. In **Advanced settings**, select Python 3.12 and click **Deploy**.

The public Streamlit demo does not require FastAPI or n8n. Those services can
be deployed separately later when you want a public automation endpoint.
