import streamlit as st
import PyPDF2
import json
import os
import google.generativeai as genai
from duckduckgo_search import DDGS

# Configure Page
st.set_page_config(page_title="Fact-Check Agent", layout="wide")
st.title("🛡️ Automated Fact-Checking Agent")
st.markdown("Upload a marketing PDF. This tool acts as a **Truth Layer**, extracting claims and cross-referencing them against the live web to flag inaccuracies.")

# Initialize Gemini
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.text_input("Enter Gemini API Key (or set in secrets):", type="password")

if not api_key:
    st.warning("Please provide a Gemini API Key to continue.")
    st.stop()

genai.configure(api_key=api_key)
# Use the reliable gemini-pro model
model = genai.GenerativeModel('gemini-pro')
ddgs = DDGS()

def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def extract_claims(text):
    prompt = f"""
    You are an expert fact-checker. Extract the specific, verifiable claims from the following text.
    Focus on statistics, dates, financial figures, and technical metrics.
    Return ONLY a valid JSON list of strings representing the claims. Do not include markdown blocks or any other text.
    Example: ["Our software increases speed by 50%", "Founded in 2021"]
    
    TEXT:
    {text}
    """
    response = model.generate_content(prompt)
    try:
        # Clean response string if it contains markdown formatting
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        claims = json.loads(cleaned_response)
        if isinstance(claims, list):
            return claims
        else:
            return []
    except Exception as e:
        st.error(f"Failed to parse claims: {str(e)}")
        return []

def verify_claim(claim):
    # 1. Search the web
    results = ddgs.text(claim, max_results=3)
    context = ""
    for r in results:
        context += f"Source: {r['href']}\nContent: {r['body']}\n\n"
        
    if not context:
        return {"status": "False", "reason": "No evidence found on the live web.", "source": "N/A"}
        
    # 2. Ask LLM to evaluate claim against search context
    eval_prompt = f"""
    You are an expert fact-checker. Evaluate the following CLAIM based strictly on the provided SEARCH_RESULTS from the live web.
    
    CLAIM: "{claim}"
    
    SEARCH_RESULTS:
    {context}
    
    Classify the claim into exactly one of these categories:
    - Verified (matches data)
    - Inaccurate (partially true or outdated)
    - False (contradicts the data or no evidence found)
    
    Return ONLY a valid JSON object with the keys "status" and "reason". Do not use markdown blocks.
    Example: {{"status": "Inaccurate", "reason": "The search shows speed increased by 30%, not 50%."}}
    """
    
    eval_response = model.generate_content(eval_prompt)
    try:
        cleaned_eval = eval_response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned_eval)
        # Add the primary source link
        result['source'] = results[0]['href'] if results else "N/A"
        return result
    except Exception as e:
        return {"status": "Error", "reason": "Failed to analyze claim.", "source": "N/A"}

uploaded_file = st.file_uploader("Upload Marketing PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Start Fact-Checking"):
        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(uploaded_file)
            
        if not text.strip():
            st.error("No text found in the PDF.")
            st.stop()
            
        with st.spinner("Identifying claims..."):
            claims = extract_claims(text)
            
        if not claims:
            st.warning("No verifiable claims found in the document.")
            st.stop()
            
        st.subheader("Verification Results")
        
        progress_bar = st.progress(0)
        for i, claim in enumerate(claims):
            with st.spinner(f"Verifying claim: {claim[:50]}..."):
                verification = verify_claim(claim)
                
                status = verification.get("status", "Unknown")
                reason = verification.get("reason", "")
                source = verification.get("source", "N/A")
                
                # Format output based on status
                if status == "Verified":
                    st.success(f"✅ **Verified:** {claim}")
                    st.caption(f"**Reason:** {reason} | **Source:** {source}")
                elif status == "Inaccurate":
                    st.warning(f"⚠️ **Inaccurate:** {claim}")
                    st.caption(f"**Reason:** {reason} | **Source:** {source}")
                else:
                    st.error(f"❌ **False/Unverified:** {claim}")
                    st.caption(f"**Reason:** {reason} | **Source:** {source}")
                    
            progress_bar.progress((i + 1) / len(claims))
        st.balloons()
