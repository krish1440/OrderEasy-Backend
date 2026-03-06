from google import genai as google_genai

client = google_genai.Client(api_key="AIzaSyD31rKgEe9Qo0rJYy8MqaMqZpNTVjcE-cU")
try:
    response = client.models.generate_content(
        model='models/gemini-2.0-flash-lite',
        contents='Say hello world in one line'
    )
    print("SUCCESS")
    print(response.text)
except Exception as e:
    print("FAILED")
    print(str(e))
