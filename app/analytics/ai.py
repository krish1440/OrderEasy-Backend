import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Models prioritized by cost/performance
MODELS = [
    'gemini-2.5-flash',       # Primary: Fast & Balanced
    'gemini-2.5-flash-lite',  # Secondary: Cheaper/Faster
]

def generate_business_insights(data_summary: dict, org_name: str) -> str:
    """
    Generates business insights using Gemini with automatic model fallback.
    """
    if not api_key:
        return "Error: Gemini API Key not configured."

    prompt = f"""
    You are an expert Business Intelligence Analyst for '{org_name}'.
    
    Data Summary for {org_name}:
    {data_summary}

    Goal: Provide a strategic analysis of the data.
    
    FORMATTING RULES (STRICT):
    1. Start with a SINGLE BOLD HEADER line that summarizes the most critical issue or opportunity (e.g., "**Critical: Revenue dropping due to low retention**").
    2. Do NOT use "To/From/Date/Subject" headers.
    3. Do NOT mention "AI" or "Gemini".
    4. Provide 3 concise sections: Revenue Analysis, Inventory/Product Insights, and Recommendations.

    Strategic Analysis:
    """

    last_error = None

    for model_name in MODELS:
        try:
            print(f"Attempting generation with model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            # Return pure insight text
            return response.text
            
        except Exception as e:
            print(f"Model {model_name} failed: {str(e)}")
            last_error = e
            continue  # Try next model

    return f"All AI models failed. Last error: {str(last_error)}"