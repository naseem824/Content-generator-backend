import os
import json
import markdown
from markupsafe import Markup
from flask import Flask, render_template, request

# Import Vertex AI libraries
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

# --- Flask App with custom template folder ---
app = Flask(__name__, template_folder="template")

# --- Vertex AI and Model Configuration ---
try:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    LOCATION = "us-central1"

    gcp_json_credentials = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if not PROJECT_ID or not gcp_json_credentials:
        raise ValueError("GCP_PROJECT_ID and GCP_SERVICE_ACCOUNT_JSON env vars are required.")

    credentials_info = json.loads(gcp_json_credentials)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

    # Using Gemini model
    model = GenerativeModel("gemini-1.0-pro")
    print("✅ Vertex AI and Gemini Model configured successfully.")

except Exception as e:
    print(f"🔴 FATAL ERROR: Could not configure Vertex AI. Error: {e}")
    model = None

# --- Helper function to load prompt templates ---
def load_prompt_template(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"🔴 ERROR: Prompt file '{filename}' not found!")
        return f"ERROR: Core instructions file '{filename}' is missing."

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if not model:
        return render_template(
            'result.html',
            generated_content="⚠️ Vertex AI model is not configured. Check deploy logs."
        )

    try:
        persona = request.form.get('persona', 'article')
        competitor_data = request.form.get('competitor_data', '').strip()
        brand_data_file = request.files.get('brand_data_file')

        brand_data = "No specific brand data or voice instructions provided."
        if brand_data_file and brand_data_file.filename != '':
            brand_data = brand_data_file.read().decode('utf-8')

        prompt_step1_template = load_prompt_template('prompt_strategist_step1.txt')
        
        target_word_count = max(int(len(competitor_data.split()) * 1.25), 1500) if persona == 'article' else 0

        prompt_step1 = prompt_step1_template.format(
            brand_data=brand_data,
            target_word_count=target_word_count,
            competitor_data=competitor_data
        )

        print("INFO: Sending Step 1 prompt to Vertex AI...")
        brief_response = model.generate_content(prompt_step1)
        strategic_brief = brief_response.text

        print("INFO: Sending Step 2 prompt to Vertex AI...")
        if persona == 'article':
            prompt_step2_template = load_prompt_template('prompt_article_step2.txt')
            final_prompt = prompt_step2_template.format(
                brand_data=brand_data,
                strategic_brief=strategic_brief,
                target_word_count=target_word_count
            )
        else:
            prompt_step2_template = load_prompt_template('prompt_copywriter_step2.txt')
            final_prompt = prompt_step2_template.format(
                brand_data=brand_data,
                strategic_brief=strategic_brief
            )

        final_response = model.generate_content(final_prompt)
        final_output = final_response.text

        html_content = Markup(markdown.markdown(final_output, extensions=['fenced_code', 'tables']))
        return render_template('result.html', generated_content=html_content)

    except Exception as e:
        error_message = f"🔴 An error occurred during generation: {e}"
        print(error_message)
        return render_template('result.html', generated_content=error_message)

# --- Main Entry ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
