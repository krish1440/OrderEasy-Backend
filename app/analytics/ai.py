from google import genai as google_genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini using the new google.genai SDK
api_key = os.getenv("GEMINI_API_KEY")
GEMINI_CLIENT = google_genai.Client(api_key=api_key) if api_key else None

# Models prioritized by cost/performance
MODELS = [
    "models/gemini-2.5-flash",  # Primary: Fast & Balanced
    "models/gemini-2.0-flash-lite",  # Secondary: Cheaper/Faster
]


def generate_business_insights(data_summary: dict, org_name: str) -> str:
    """
    Generates business insights using Gemini with automatic model fallback.
    """
    if not GEMINI_CLIENT:
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
            response = GEMINI_CLIENT.models.generate_content(
                model=model_name, contents=prompt
            )
            return response.text

        except Exception as e:
            print(f"Model {model_name} failed: {str(e)}")
            last_error = e
            continue  # Try next model

    return f"All AI models failed. Last error: {str(last_error)}"
