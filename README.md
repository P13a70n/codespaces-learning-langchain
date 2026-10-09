# Daybook | Sales Intelligence

Daybook is a Streamlit sales desk that combines daily reporting with optional LangChain analysis through OpenRouter or a local Ollama model. It automatically reads supported sales files from `data/`, normalizes common column names, and creates a daily brief with sales, order, unit, regional, and product views.

## Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_sample_data.py
streamlit run app.py
```

Then open the local URL printed by Streamlit. The generated sample contains 90 days of fictional orders. To use your own data, place `.csv`, `.xlsx`, or `.xls` files in `data/`. Excel workbooks with multiple sheets are read sheet by sheet. Each sheet needs a recognizable date column and a sales/revenue/amount column; common alternatives such as `Order Date`, `Total Sales`, `Qty`, and `Order ID` are recognized. Use **Refresh files** after replacing or adding data.

The left sidebar includes an **About** view and an **Add a CSV or PDF** uploader. Uploaded CSVs are included in the current session's sales report. Uploaded PDFs can be analyzed as text from the About view; their figures are not automatically added to sales totals, and scanned PDFs need OCR first. Uploaded files are kept in memory for the session. Files in `data/` remain the persistent source for the dashboard.

## AI providers

The dashboard works without AI for metrics, charts, and report downloads. In the sidebar, choose OpenRouter or Ollama to add analyst notes.

- OpenRouter: the key is read from `OPENROUTER_API_KEY` in `.env`; the default model is `openai/gpt-4o-mini`.
- Ollama: start Ollama and pull the model you select (default `llama3.1`). Set `OLLAMA_BASE_URL` in `.env` if Ollama is not at `http://localhost:11434`.

Copy `.env.example` to `.env` to configure credentials. `.env` is ignored by git. AI analysis sends only daily aggregate metrics (not transaction rows) to the selected provider. Reports can be downloaded as Markdown from the dashboard.

## Daily use

Start `streamlit run app.py` each day after the sales files are updated. Daybook loads files at startup, selects the latest available sales date by default, and provides an on-demand report. For scheduled delivery, run the app on a machine that stays online and use an external scheduler to trigger report generation or extend the project with an email destination.