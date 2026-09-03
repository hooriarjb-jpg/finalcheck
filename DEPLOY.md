# Deploy FinalCheck online

## You only need to do these account steps

### 1) Create a GitHub repository
- Go to GitHub and create a new repository named `finalcheck`
- Public is simplest for this MVP
- Upload **all files and folders from this package**, including the `.streamlit` folder

Your repository root should look like:

- app.py
- requirements.txt
- sample_approved_source.txt
- sample_final_draft.txt
- .gitignore
- .streamlit/
  - config.toml

### 2) Connect Streamlit Community Cloud
- Open Streamlit Community Cloud
- Sign in with GitHub
- Authorize Streamlit to access the repository

### 3) Deploy
Choose:
- Repository: `finalcheck`
- Branch: `main`
- Main file path: `app.py`

Click **Deploy**.

Streamlit will create a public URL ending in:

`streamlit.app`

## First online test
Upload:
- `sample_approved_source.txt` under Approved source
- `sample_final_draft.txt` under Final draft

Click **Run FinalCheck**.

The sample intentionally contains wrong time and price information so the checker has something to flag.

## Important
This is a validation MVP, not yet a production SaaS. Do not use confidential client documents in a public beta until authentication, privacy controls, retention rules, and production hosting have been designed.
