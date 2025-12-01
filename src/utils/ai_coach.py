"""
AI Coach - Ballistikk, vær og terreng forklaringer
OpenAI GPT-integrasjon med språkvalg
"""
import os
import requests

def get_ai_coach_response(question, lang="no"):
    """
    Returnerer et AI-basert svar på brukerens spørsmål om ballistikk, vær, terreng, skyting, osv.
    Språkvalg: "no" for norsk, "en" for engelsk.
    """
    api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
    if not api_key or api_key == "YOUR_OPENAI_API_KEY":
        return "OpenAI API-nøkkel mangler. Sett miljøvariabelen OPENAI_API_KEY."
    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if lang == "no":
        system_prompt = "Du er en ballistikk- og vær-ekspert for jegere og skyttere. Svar på norsk."
        user_prompt = f"Du er ekspert på ballistikk, vær, terreng og skyting. Svar kort, presist og med praktiske tips. Bruk norsk språk. Spørsmål: {question}"
    else:
        system_prompt = "You are a ballistics and weather expert for hunters and shooters. Answer in English."
        user_prompt = f"You are an expert in ballistics, weather, terrain and shooting. Answer briefly, precisely and with practical tips. Use English. Question: {question}"
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 200
    }
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AI-feil: {str(e)}"
