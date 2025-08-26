import os
import json
import markdown
from markupsafe import Markup
from flask import Flask, render_template, request

# Import Vertex AI libraries
import vertexai
from vertexai.generative_models import GenerativeModel, Tool
from google.oauth2 import service_account

app = Flask(__name__)

# --- Helper function to load a prompt file (no changes needed) ---
def load_prompt_template(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"🔴 ERROR: Prompt file '{filename}' not found!")
        return f"ERROR: Core instructions file '{filename}' is missing."

# --- Web Page Routes (no changes needed) ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    # --- LAZY INITIALIZATION: Configure the model INSIDE the request ---
    model = None # Start with model as None
    try:
        PROJECT_ID = os.getenv("GCP_PROJECT_ID")
        GCP_JSON_CREDENTIALS = os.getenv("GCP_SERVICE_ACCOUNT_JSON")

        if not PROJECT_ID or not GCP_JSON_CREDENTIALS:
            raise ValueError("GCP_PROJECT_ID and GCP_SERVICE_ACCOUNT_JSON environment variables are required.")

        credentials_info = json.loads(GCP_JSON_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        # Initialize Vertex AI for this request
        vertexai.init(project=PROJECT_ID, location="us-central1", credentials=credentials)

        tool = Tool.from_google_search_retrieval()
        
        model = GenerativeModel(
            "gemini-1.5-pro-001",
            tools=[tool]
        )
        print("✅ Vertex AI and Gemini Model configured successfully for this request.")

    except Exception as e:
        print(f"🔴 FATAL ERROR on request: Could not configure Vertex AI. Error: {e}")
        # If initialization fails, show the error on the page
        return render_template('result.html', generated_content=f"Error configuring Vertex AI: {e}")

    # --- From here, the two-step logic remains the same ---
    try:
        persona = request.form.get('persona', 'article')
        competitor_data = request.form.get('competitor_data', '').strip()
        brand_data_file = request.files.get('brand_data_file')

        brand_data = "No specific brand data or voice instructions provided."
        if brand_data_file and brand_data_file.filename != '':
            brand_data = brand_data_file.read().decode('utf-8')

        prompt_step1_template = load_prompt_template('prompt_strategist_step1.txt')
        
        if persona == 'article':
            target_word_count = max(int(len(competitor_data.split()) * 1.25), 1500)
        else:
            target_word_count = 0 

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
        error_message = f"An error occurred during generation: {e}"
        print(f"🔴 API ERROR: {e}")
        return render_template('result.html', generated_content=error_message)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
