import streamlit as st
import json, re, os
from pathlib import Path
from io import BytesIO

st.set_page_config(page_title="FinalCheck", page_icon="✓", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1100px; padding-top: 2rem;}
.fc-card {border:1px solid #ddd; border-radius:14px; padding:18px; margin:8px 0;}
.small {color:#666; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

st.title("FinalCheck")
st.caption("Compare an approved source against a final draft before it goes out.")

with st.sidebar:
    st.header("What V1 checks")
    st.write("Dates & times")
    st.write("Money & prices")
    st.write("URLs & emails")
    st.write("Numbers")
    st.write("Names / capitalized phrases")
    st.write("Required phrases")
    st.divider()
    st.caption("V1 is deterministic: it does not invent corrections. AI semantic checking is the next layer.")

def extract_text(uploaded):
    if uploaded is None:
        return ""
    name = uploaded.name.lower()
    data = uploaded.getvalue()
    if name.endswith(".txt") or name.endswith(".md"):
        return data.decode("utf-8", errors="ignore")
    if name.endswith(".docx"):
        from docx import Document
        doc = Document(BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    return ""

MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
patterns = {
    "Dates": rf"\b{MONTHS}\s+\d{{1,2}}(?:,\s*\d{{4}})?\b|\b\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}}\b",
    "Times": r"\b\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)\b",
    "Money": r"(?:CAD\s*)?\$\s?\d[\d,]*(?:\.\d{1,2})?",
    "URLs": r"https?://[^\s<>\]\)]+|www\.[^\s<>\]\)]+",
    "Emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "Numbers": r"\b\d+(?:,\d{3})*(?:\.\d+)?\b",
}

def clean(v):
    return re.sub(r"\s+", " ", v.strip().rstrip(".,;:"))

def extract(text):
    out = {}
    for key, pat in patterns.items():
        vals = [clean(x if isinstance(x, str) else x[0]) for x in re.findall(pat, text, flags=re.I)]
        out[key] = list(dict.fromkeys(vals))
    # Useful proper-name/phrase heuristic: 2–5 consecutive capitalized words.
    names = re.findall(r"\b(?:[A-Z][A-Za-zÀ-ÿ'’.-]+(?:\s+|$)){2,5}", text)
    out["Names / phrases"] = list(dict.fromkeys(clean(x) for x in names if len(clean(x)) > 5))
    return out

def norm(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())

def compare(source, draft):
    s, d = extract(source), extract(draft)
    rows = []
    for category in ["Dates","Times","Money","URLs","Emails","Numbers","Names / phrases"]:
        sn = {norm(x): x for x in s[category]}
        dn = {norm(x): x for x in d[category]}
        for k, original in sn.items():
            if k and k not in dn:
                # Skip numbers that are substrings of dates/times/money to reduce noise
                if category == "Numbers":
                    if any(norm(original) in norm(x) for c in ["Dates","Times","Money"] for x in s[c]):
                        continue
                rows.append({
                    "status":"Needs review",
                    "category":category,
                    "source":original,
                    "draft":"Not found exactly",
                    "reason":f"Source value is not present exactly in the final draft."
                })
    return rows, s, d

tab1, tab2 = st.tabs(["New Check", "How it works"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Approved source")
        src_file = st.file_uploader("Upload source", type=["pdf","docx","txt","md"], key="src")
        src_text_manual = st.text_area("Or paste approved source text", height=180, key="src_text")
    with c2:
        st.subheader("2. Final draft")
        draft_file = st.file_uploader("Upload draft", type=["pdf","docx","txt","md"], key="draft")
        draft_text_manual = st.text_area("Or paste final draft text", height=180, key="draft_text")

    st.subheader("3. Required phrases (optional)")
    required = st.text_area(
        "One required phrase per line — e.g. sponsor acknowledgement, disclaimer, approved credit line",
        placeholder="Presented by ABC Corp\nAdmission is free",
        height=100
    )

    if st.button("Run FinalCheck", type="primary", use_container_width=True):
        source = src_text_manual.strip() or extract_text(src_file)
        draft = draft_text_manual.strip() or extract_text(draft_file)
        if not source or not draft:
            st.error("Please provide both an approved source and a final draft.")
        else:
            issues, sdata, ddata = compare(source, draft)
            for phrase in [x.strip() for x in required.splitlines() if x.strip()]:
                if norm(phrase) not in norm(draft):
                    issues.append({
                        "status":"Missing",
                        "category":"Required phrase",
                        "source":phrase,
                        "draft":"Not found",
                        "reason":"Required phrase is missing from the final draft."
                    })

            score = max(0, 100 - min(100, len(issues)*8))
            a,b,c = st.columns(3)
            a.metric("Pre-flight score", f"{score}%")
            b.metric("Issues to review", len(issues))
            c.metric("Checks", sum(len(v) for v in sdata.values()))

            if not issues:
                st.success("No exact-value inconsistencies were detected by the V1 checker.")
            else:
                st.warning("Review these items before publishing.")
                for i, issue in enumerate(issues, 1):
                    with st.expander(f"{i}. {issue['category']}: {issue['source']}"):
                        st.write(f"**Source:** {issue['source']}")
                        st.write(f"**Draft:** {issue['draft']}")
                        st.write(issue["reason"])

            report = {
                "product":"FinalCheck V1",
                "score":score,
                "issues":issues,
                "source_entities":sdata,
                "draft_entities":ddata,
            }
            st.download_button(
                "Download QA report",
                json.dumps(report, indent=2, ensure_ascii=False),
                file_name="finalcheck_report.json",
                mime="application/json",
                use_container_width=True
            )

with tab2:
    st.markdown("""
### The product loop
1. Upload the approved source.
2. Upload the final version.
3. FinalCheck extracts high-risk facts.
4. It flags source facts that disappeared or changed.
5. A human reviews only the flagged items.

### Why this V1 is intentionally small
The first version proves the core value without email access, CRM integrations, accounts, billing, or a database. It is designed for testing with real communications documents before investing in a full SaaS.

### Next product layer
After validation, add an LLM-based semantic comparison with source citations, image/PDF visual checks, team accounts, saved projects, and Stripe billing.
""")
