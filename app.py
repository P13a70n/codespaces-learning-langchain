import io
import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
load_dotenv(ROOT / ".env")

st.set_page_config(page_title="Daybook | Sales Intelligence", page_icon="D", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root { --ink: #18221f; --muted: #46514b; --paper: #f4f5ef; --green: #176b50; --lime: #d1eb72; --line: #dfe3da; }
    html, body, [class*="css"] { font-family: 'Manrope', sans-serif; color: var(--ink); }
    .stApp { background: var(--paper); --text-color: #18221f; --secondary-text-color: #46514b; }
    .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp [data-testid="stMarkdownContainer"] { color: var(--ink); }
    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stMetricLabel"] { color: var(--muted) !important; }
    .stApp input, .stApp textarea, .stApp [data-testid="stDateInput"] *, .stApp [data-testid="stSelectbox"] *, .stApp [data-baseweb="calendar"] * { color: var(--ink) !important; }
    .stApp input, .stApp textarea { background-color: #fff; }
    .stApp [data-testid="stDateInput"] input, .stApp [data-testid="stDateInput"] button { background: #111 !important; border-color: #111 !important; color: #fff !important; -webkit-text-fill-color: #fff !important; }
    .stApp [data-testid="stDateInput"] input:hover, .stApp [data-testid="stDateInput"] input:focus, .stApp [data-testid="stDateInput"] button:hover, .stApp [data-testid="stDateInput"] button:focus { background: #252525 !important; border-color: #252525 !important; color: #fff !important; -webkit-text-fill-color: #fff !important; }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button { background:#111 !important; border-color:#111 !important; color:#fff !important; -webkit-text-fill-color:#fff !important; }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover, [data-testid="stSidebar"] [data-testid="stFileUploader"] button:focus, [data-testid="stSidebar"] [data-testid="stFileUploader"] button:active { background:#252525 !important; border-color:#252525 !important; color:#fff !important; -webkit-text-fill-color:#fff !important; }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div { background:#fff !important; border-color:#64716a !important; }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] *, [data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] [role="option"] { color:#18221f !important; -webkit-text-fill-color:#18221f !important; }
    [data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] [role="option"] { background:#fff !important; }
    [data-baseweb="popover"] [role="option"]:hover, [data-baseweb="popover"] [role="option"][aria-selected="true"] { background:#e9eee5 !important; color:#18221f !important; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #e9eee5; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] h1 { font-size: 1.35rem; }
    .brand { display:flex; align-items:center; gap:12px; margin: 0 0 2rem; }
    .brand-mark { width:38px; height:38px; display:grid; place-items:center; background:var(--green); color:white; font-weight:800; border-radius:10px; }
    .brand-name { font-size:1.1rem; font-weight:800; line-height:1.1; }
    .brand-sub { color:var(--muted); font: .68rem 'DM Mono', monospace; margin-top:4px; }
    .eyebrow { color:var(--green); text-transform:uppercase; font:500 .72rem 'DM Mono', monospace; letter-spacing:.08em; }
    .report-title { font-size:2rem; line-height:1.15; font-weight:800; margin:.35rem 0 .25rem; }
    .report-subtitle { color:var(--muted); margin-bottom:1.5rem; }
    [data-testid="stMetric"] { background:white; padding:1rem 1.1rem; border:1px solid var(--line); border-radius:8px; }
    [data-testid="stMetricLabel"] { color:var(--muted); }
    [data-testid="stMetricValue"] { font-size:1.65rem; }
    .section-title { font-size:1.05rem; font-weight:800; margin:1rem 0 .4rem; }
    div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:8px; }
    .stButton > button[kind="primary"] { background:var(--green); border-color:var(--green); }
    .stButton > button { border-radius:6px; }
    [data-testid="stSidebar"] .stButton > button { background:#111; border-color:#111; color:#fff; }
    [data-testid="stSidebar"] .stButton > button:hover, [data-testid="stSidebar"] .stButton > button:focus, [data-testid="stSidebar"] .stButton > button:active { background:#252525; border-color:#252525; color:#fff; }
    </style>
    <div class="brand"><div class="brand-mark">D</div><div><div class="brand-name">Daybook</div><div class="brand-sub">SALES INTELLIGENCE</div></div></div>
    """,
    unsafe_allow_html=True,
)


ALIASES = {
    "date": {"date", "orderdate", "salesdate", "transactiondate", "day"},
    "sales": {"sales", "revenue", "amount", "total", "totalsales", "salesamount", "netrevenue"},
    "product": {"product", "item", "productname", "sku"},
    "region": {"region", "territory", "location", "market"},
    "quantity": {"quantity", "qty", "units", "unitssold"},
    "order_id": {"orderid", "transactionid", "invoice", "invoicenumber"},
    "channel": {"channel", "saleschannel", "source"},
}


def normalized_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def standardize(frame, source):
    rename = {}
    normalized = {normalized_name(column): column for column in frame.columns}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                rename[normalized[alias]] = target
                break
    frame = frame.rename(columns=rename).copy()
    if "date" not in frame or "sales" not in frame:
        raise ValueError("Could not identify date and sales columns")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
    frame["sales"] = pd.to_numeric(frame["sales"].astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
    if "quantity" not in frame:
        frame["quantity"] = 1
    frame["quantity"] = pd.to_numeric(frame["quantity"], errors="coerce").fillna(0)
    for column in ("product", "region", "channel", "order_id"):
        if column not in frame:
            frame[column] = "Unknown"
        frame[column] = frame[column].fillna("Unknown").astype(str)
    frame["source"] = source
    return frame.dropna(subset=["date", "sales"])


@st.cache_data(show_spinner=False)
def load_sales(folder):
    DATA_DIR.mkdir(exist_ok=True)
    frames, issues = [], []
    paths = sorted(path for path in Path(folder).glob("*") if path.suffix.lower() in {".csv", ".xlsx", ".xls"} and not path.name.startswith("~$"))
    for path in paths:
        try:
            if path.suffix.lower() == ".csv":
                source_frames = [("", pd.read_csv(path))]
            elif path.suffix.lower() == ".xlsx":
                source_frames = list(pd.read_excel(path, sheet_name=None).items())
            else:
                source_frames = [("", pd.read_excel(path))]
            for sheet, frame in source_frames:
                label = f"{path.name} / {sheet}" if sheet else path.name
                frames.append(standardize(frame, label))
        except Exception as error:
            issues.append(f"{path.name}: {error}")
    if not frames:
        return pd.DataFrame(), issues
    return pd.concat(frames, ignore_index=True), issues


def money(value):
    return f"${value:,.2f}"


def create_llm(provider, model):
    if provider == "OpenRouter":
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Set OPENROUTER_API_KEY in your .env file first.")
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.2,
        )
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.2,
    )


with st.sidebar:
    st.markdown("### Daybook")
    page = st.radio("Page", ["Daily report", "About"], label_visibility="collapsed")
    uploaded_files = st.file_uploader("Add a CSV or PDF", type=["csv", "pdf"], accept_multiple_files=True)
    st.caption("CSV files join the sales report. PDFs can be analyzed as text.")
    st.divider()
    st.markdown("### AI analysis")
    provider = st.selectbox("AI provider", ["OpenRouter", "Ollama"])
    default_model = "openai/gpt-4o-mini" if provider == "OpenRouter" else "llama3.1"
    model = st.text_input("Model", value=default_model)
    st.caption("OpenRouter uses OPENROUTER_API_KEY from .env. Ollama must be running locally.")
    if st.button("Refresh files", width="stretch"):
        load_sales.clear()
        st.rerun()
    st.divider()
    st.caption(f"Reading sales files from `{DATA_DIR.name}/`")


sales, load_issues = load_sales(str(DATA_DIR))
uploaded_sales = []
uploaded_pdfs = []
upload_issues = []
for uploaded_file in uploaded_files or []:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            uploaded_sales.append(standardize(pd.read_csv(io.BytesIO(uploaded_file.getvalue())), f"Upload: {uploaded_file.name}"))
        else:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
            text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
            if text:
                uploaded_pdfs.append((uploaded_file.name, text))
            else:
                upload_issues.append(f"{uploaded_file.name}: no extractable text was found (scanned PDFs need OCR).")
    except Exception as error:
        upload_issues.append(f"{uploaded_file.name}: {error}")
if uploaded_sales:
    sales = pd.concat([sales, *uploaded_sales], ignore_index=True) if not sales.empty else pd.concat(uploaded_sales, ignore_index=True)

if load_issues:
    for issue in load_issues:
        st.warning(issue)
for issue in upload_issues:
    st.warning(issue)

if page == "About":
    st.markdown('<div class="eyebrow">About Daybook</div><div class="report-title">Sales data, turned into a daily brief.</div>', unsafe_allow_html=True)
    st.markdown("Daybook reads sales files, calculates daily performance, and uses LangChain with OpenRouter or Ollama to write optional analyst notes.")
    st.subheader("What it does")
    st.markdown("- Combines supported sales files and summarizes net sales, order count, average order, and units sold.\n- Shows recent sales trends, top products, and regional results.\n- Creates an AI analysis with practical actions and lets you download the daily brief.")
    st.subheader("Add new data")
    st.markdown("Use **Add a CSV or PDF** in the left sidebar. Uploaded CSVs need recognizable date and sales/revenue columns and are added to the report for this session. PDFs are read as text and can be analyzed separately; PDF figures are not automatically converted into dashboard totals. Files placed in `data/` are loaded when the app starts or when you select **Refresh files**.")
    if uploaded_pdfs:
        st.subheader("PDF analysis")
        selected_pdf = st.selectbox("PDF to analyze", [name for name, _ in uploaded_pdfs])
        pdf_name, pdf_text = next(item for item in uploaded_pdfs if item[0] == selected_pdf)
        pdf_fingerprint = f"{pdf_name}:{len(pdf_text)}:{pdf_text[:200]}"
        if st.button("Analyze PDF", type="primary"):
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You analyze business documents. Summarize the document's purpose, key sales or performance findings, notable numbers, and useful follow-up questions. Do not invent facts. State when content may be incomplete."),
                ("human", "Analyze this uploaded PDF text ({filename}). The text may be truncated.\n\n{text}"),
            ])
            try:
                response = (prompt | create_llm(provider, model)).invoke({"filename": pdf_name, "text": pdf_text[:16000]})
                st.session_state["pdf_analysis"] = response.content
                st.session_state["pdf_analysis_fingerprint"] = pdf_fingerprint
            except Exception as error:
                st.error(f"Could not analyze PDF: {error}")
        if st.session_state.get("pdf_analysis_fingerprint") == pdf_fingerprint:
            st.markdown(st.session_state["pdf_analysis"])
    else:
        st.info("Upload a text-based PDF in the sidebar to analyze it. Scanned image PDFs require OCR before their text can be read.")
    st.stop()

if sales.empty:
    st.markdown('<div class="eyebrow">Your daily sales desk</div><div class="report-title">No sales files found</div><div class="report-subtitle">Add CSV, XLSX, or XLS files with a date column and a sales or revenue column to the data folder.</div>', unsafe_allow_html=True)
    st.info("Run `python generate_sample_data.py` to create a sample dataset, then refresh files.")
    st.stop()

available_dates = sorted(sales["date"].dropna().unique())
default_day = available_dates[-1]
selected_day = st.date_input("Report date", value=default_day, min_value=available_dates[0], max_value=available_dates[-1])
day_data = sales[sales["date"] == selected_day]
previous_data = sales[sales["date"] == (pd.Timestamp(selected_day) - pd.Timedelta(days=1)).date()]

st.markdown('<div class="eyebrow">Daily sales brief</div>', unsafe_allow_html=True)
st.markdown(f'<div class="report-title">{pd.Timestamp(selected_day).strftime("%A, %B %-d, %Y")}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="report-subtitle">{len(day_data):,} transactions across {day_data["source"].nunique()} source file(s)</div>', unsafe_allow_html=True)

total_sales = day_data["sales"].sum()
prior_sales = previous_data["sales"].sum()
change = ((total_sales - prior_sales) / prior_sales * 100) if prior_sales else None
order_count = day_data.loc[day_data["order_id"] != "Unknown", "order_id"].nunique()
if not order_count:
    order_count = len(day_data)
average_order = total_sales / order_count if order_count else 0

metric_cols = st.columns(4)
metric_cols[0].metric("Net sales", money(total_sales), f"{change:+.1f}% vs prior day" if change is not None else "No prior-day comparison")
metric_cols[1].metric("Orders", f"{order_count:,}")
metric_cols[2].metric("Average order", money(average_order))
metric_cols[3].metric("Units sold", f"{day_data['quantity'].sum():,.0f}")

left, right = st.columns([1.45, 1])
with left:
    st.markdown('<div class="section-title">Sales trend</div>', unsafe_allow_html=True)
    trend = sales.groupby("date", as_index=True)["sales"].sum().sort_index().tail(30)
    st.line_chart(trend, color="#176b50", height=260)
with right:
    st.markdown('<div class="section-title">Top products</div>', unsafe_allow_html=True)
    products = day_data.groupby("product")["sales"].sum().sort_values(ascending=False).head(7)
    if not products.empty:
        st.bar_chart(products, color="#8eaa3e", horizontal=True, height=260)
    else:
        st.caption("No transactions for this date.")

detail_col, report_col = st.columns([1.15, 1])
with detail_col:
    st.markdown('<div class="section-title">Regional breakdown</div>', unsafe_allow_html=True)
    regions = day_data.groupby("region", as_index=False).agg(Sales=("sales", "sum"), Orders=("order_id", "nunique"), Units=("quantity", "sum"))
    st.dataframe(regions.sort_values("Sales", ascending=False), width="stretch", hide_index=True)
    with st.expander("Transactions for this date"):
        st.dataframe(day_data[["order_id", "product", "region", "quantity", "sales", "channel", "source"]], width="stretch", hide_index=True)

with report_col:
    st.markdown('<div class="section-title">Analyst notes</div>', unsafe_allow_html=True)
    st.caption("AI receives daily aggregates only, not transaction-level rows.")
    if st.button("Generate AI analysis", type="primary", width="stretch"):
        summary = {
            "date": str(selected_day),
            "sales": round(float(total_sales), 2),
            "prior_day_sales": round(float(prior_sales), 2),
            "orders": int(order_count),
            "units": round(float(day_data["quantity"].sum()), 2),
            "top_products": {str(name): round(float(value), 2) for name, value in products.items()},
            "regional_sales": {str(name): round(float(value), 2) for name, value in day_data.groupby("region")["sales"].sum().items()},
        }
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a concise sales operations analyst. Explain the daily result, notable drivers, and 2 practical actions. Avoid inventing causes; label uncertainty. Use short headings and bullets."),
                ("human", "Analyze these aggregate daily sales metrics: {summary}"),
            ])
            response = (prompt | create_llm(provider, model)).invoke({"summary": summary})
            st.session_state["analysis"] = response.content
            st.session_state["analysis_date"] = str(selected_day)
        except Exception as error:
            st.error(f"Could not generate analysis: {error}")
    analysis = st.session_state.get("analysis")
    if analysis and st.session_state.get("analysis_date") == str(selected_day):
        st.markdown(analysis if isinstance(analysis, str) else str(analysis))
    else:
        st.caption("Generate an analysis to add context and suggested actions to this report.")

report_text = f"# Daybook daily sales brief\n\nDate: {selected_day}\n\n- Net sales: {money(total_sales)}\n- Orders: {order_count:,}\n- Average order: {money(average_order)}\n- Units sold: {day_data['quantity'].sum():,.0f}\n\n## Sales by region\n"
for _, row in regions.sort_values("Sales", ascending=False).iterrows():
    report_text += f"- {row['region']}: {money(row['Sales'])} ({row['Orders']} orders)\n"
if st.session_state.get("analysis_date") == str(selected_day):
    report_text += f"\n## Analyst notes\n{st.session_state['analysis']}\n"
st.download_button("Download daily report", data=report_text, file_name=f"daybook-{selected_day}.md", mime="text/markdown")