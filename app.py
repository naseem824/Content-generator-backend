import os
import google.generativeai as genai
from flask import Flask, render_template, request
from markupsafe import Markup
import markdown

app = Flask(__name__)

# --- Secure API Key and Model Configuration ---
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable not found.")

    genai.configure(api_key=gemini_api_key)
    
    generation_config = genai.GenerationConfig(temperature=0.4)
    model = genai.GenerativeModel(
        'gemini-1.5-pro-latest',
        generation_config=generation_config
    )
except Exception as e:
    print(f"🔴 FATAL ERROR: Could not configure Gemini API. Error: {e}")
    model = None

# --- Helper function to load a prompt file ---
def load_prompt_template(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"🔴 ERROR: Prompt file '{filename}' not found!")
        return f"ERROR: Core instructions file '{filename}' is missing."

# --- Web Page Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if not model:
        return render_template('result.html', generated_content="The Gemini API is not configured.")

    try:
        # --- Get all data from the form ---
        persona = request.form.get('persona', 'article')
        competitor_data = request.form.get('competitor_data', '').strip()
        brand_voice_file = request.files.get('brand_voice_file')

        # --- Read the optional brand voice file ---
        brand_voice_data = "No specific brand voice instructions provided."
        if brand_voice_file and brand_voice_file.filename != '':
            brand_voice_data = brand_voice_file.read().decode('utf-8')

        # --- Main Logic: Two-Step Prompting ---
        if persona == 'article':
            # --- Step 1: Generate the Strategic Brief ---
            print("INFO: Starting Article Generation - Step 1: Creating Brief")
            prompt_step1_template = load_prompt_template('prompt_article_step1.txt')
            competitor_word_count = len(competitor_data.split())
            target_word_count = max(int(competitor_word_count * 1.25), 1500)
            
            prompt_step1 = prompt_step1_template.format(
                brand_voice_data=brand_voice_data,
                target_word_count=target_word_count,
                competitor_data=competitor_data
            )
            
            brief_response = model.generate_content(prompt_step1)
            strategic_brief = brief_response.text
            
            # --- Step 2: Generate the Final Article using the Brief ---
            print("INFO: Starting Article Generation - Step 2: Writing Content")
            prompt_step2_template = load_prompt_template('prompt_article_step2.txt')
            
            final_prompt = prompt_step2_template.format(
                brand_voice_data=brand_voice_data,
                strategic_brief=strategic_brief,
                target_word_count=target_word_count
            )
            
            final_response = model.generate_content(final_prompt)
            final_output = final_response.text

        elif persona == 'copywriter':
            # --- Step 1: Generate the Conversion Brief ---
            print("INFO: Starting Copywriter Generation - Step 1: Creating Brief")
            prompt_step1_template = load_prompt_template('prompt_copywriter_step1.txt')

            prompt_step1 = prompt_step1_template.format(
                brand_voice_data=brand_voice_data,
                competitor_data=competitor_data
            )

            brief_response = model.generate_content(prompt_step1)
            strategic_brief = brief_response.text

            # --- Step 2: Generate the Final Copy using the Brief ---
            print("INFO: Starting Copywriter Generation - Step 2: Writing Content")
            prompt_step2_template = load_prompt_template('prompt_copywriter_step2.txt')
            
            final_prompt = prompt_step2_template.format(
                brand_voice_data=brand_voice_data,
                strategic_brief=strategic_brief
            )
            
            final_response = model.generate_content(final_prompt)
            final_output = final_response.text
            
        else:
            return render_template('result.html', generated_content="Invalid persona selected.")

        # --- Convert final markdown output to HTML and render ---
        html_content = Markup(markdown.markdown(final_output, extensions=['fenced_code', 'tables']))
        return render_template('result.html', generated_content=html_content)

    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(f"🔴 API ERROR: {e}")
        return render_template('result.html', generated_content=error_message)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
