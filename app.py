import os
import google.generativeai as genai
from flask import Flask, render_template, request, Markup
import markdown

app = Flask(__name__)

try:
    gemini_api_key = os.getenv("AIzaSyAiN9JE2iuYc3q2h2wgzJ6RfWfLVGHQNl8")
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
except Exception as e:
    print(f"ERROR: Could not configure Gemini API. Check API key. Error: {e}")
    model = None

def load_core_instructions():
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return "ERROR: Core instructions file (prompt.txt) is missing."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if not model:
        return "Error: Gemini API is not configured.", 500

    competitor_data = request.form.get('competitor_data', '').strip()
    core_instructions = load_core_instructions()
    final_prompt = f"{core_instructions}\n\n# User-Provided Raw Competitor Data\n\n---\n\n{competitor_data}"

    try:
        response = model.generate_content(final_prompt)
        html_content = Markup(markdown.markdown(response.text, extensions=['fenced_code', 'tables']))
        return render_template('result.html', generated_content=html_content)
    except Exception as e:
        return f"An error occurred with the API: {e}", 500
