# AI Fact-Check Agent

An automated "Truth Layer" application designed to verify claims made in marketing PDFs. The tool extracts statistics, dates, and financial figures from a document, cross-references them against live web search results, and classifies the claims as Verified, Inaccurate, or False.

## Architecture
1. **Extraction:** `PyPDF2` reads the uploaded PDF.
2. **Analysis:** Google's Gemini 1.5 Flash LLM extracts specific, verifiable claims from the raw text.
3. **Verification:** `duckduckgo-search` pulls live web context for each claim.
4. **Classification:** Gemini acts as an evaluation agent, cross-referencing the live web data against the original claim to output a status and reason.

## Tech Stack
- **Frontend:** Streamlit
- **LLM:** Google Gemini 1.5 Flash API
- **Web Search:** DuckDuckGo Search API
- **PDF Parser:** PyPDF2

## How to Run Locally

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Gemini API key in Streamlit secrets or enter it in the UI.
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deployment
This app is ready to be deployed on **Streamlit Community Cloud**, Vercel, or Render. 
When deploying on Streamlit Cloud, add your `GEMINI_API_KEY` to the App Secrets in the dashboard.
