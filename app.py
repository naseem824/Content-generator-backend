import os
import google.generativeai as genai
from flask import Flask, render_template, request
from markupsafe import Markup
import markdown

# This sets up your web application
app = Flask(__name__)

# --- Secure API Key Configuration ---
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable not found. Please set it in Railway or your environment.")

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

except Exception as e:
    print(f"🔴 FATAL ERROR: Could not configure Gemini API. Error: {e}")
    model = None

# --- Helper Function ---
def load_core_instructions():
    """Reads the 'prompt.txt' file."""
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print("🔴 ERROR: prompt.txt file not found!")
        return "ERROR: Core instructions file (prompt.txt) is missing."

# --- Web Page Routes ---
@app.route('/')
def index():
    """Renders the main page with the input form."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Handles the form submission and generates the content."""
    
    if not model:
        error_message = "The Gemini API is not configured. Check the server logs and your API key."
        return render_template('result.html', generated_content=error_message)

    competitor_data = request.form.get('competitor_data', '').strip()
    core_instructions = load_core_instructions()
    final_prompt = f"{core_instructions}\n\n# User-Provided Raw Competitor Data\n\n---\n\n{competitor_data}"
    
    try:
        response = model.generate_content(final_prompt)
        html_content = Markup(markdown.markdown(response.text, extensions=['fenced_code', 'tables']))
        return render_template('result.html', generated_content=html_content)

    except Exception as e:
        error_message = f"An error occurred while communicating with the Gemini API: {e}"
        print(f"🔴 API ERROR: {e}")
        return render_template('result.html', generated_content=error_message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
