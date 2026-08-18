from flask import Flask, request, render_template_string
import requests
import os
import csv

app = Flask(__name__)

API_KEY = os.getenv("OPENPIPE_API_KEY")
MODEL_ID = os.getenv("MODEL_ID")
HF_TOKEN = os.getenv("HF_TOKEN")

# Load return policy data
return_policies = {}
if os.path.exists("returns.csv"):
    with open("returns.csv", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            return_policies[row["product_id"].lower()] = row["return_policy"]

# Extract product ID from message
def extract_product_id(message):
    for product in return_policies:
        if product.lower() in message.lower():
            return product
    return None

# Generate caption using Hugging Face image captioning model
def generate_caption(image_url):
    try:
        print(f" Sending image to Hugging Face Inference API...")
        response = requests.post(
            "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning",
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            },
            json={"inputs": image_url}
        )

        result = response.json()
        # Log only the outcome — never the raw API payload, image data or
        # model response.
        print(f" Hugging Face API responded: HTTP {response.status_code}")

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        return "Unable to describe the image. Try a different photo."

    except Exception as e:
        print(f" Exception: {str(e)}")
        return f"Image captioning failed: {str(e)}"

# HTML interface
HTML = '''
<h2>AI Product Return Assistant</h2>
<form method="post">
  <textarea name="message" placeholder="Paste customer complaint here..." rows="5" cols="50"></textarea><br>
  <input type="text" name="image_url" placeholder="Paste image URL here (optional)" size="60"/><br>
  <input type="submit" value="Analyze">
</form>
{% if result %}
  <h3>Structured Output:</h3>
  <pre>{{ result }}</pre>
{% endif %}
'''

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        message = request.form.get("message", "")
        image_url = request.form.get("image_url", "").strip()

        product_id = extract_product_id(message)
        policy = return_policies.get(product_id, "No return policy found for this item.")
        image_caption = generate_caption(image_url) if image_url else "No image provided."

        prompt = (
            f"The customer submitted a product complaint and a photo.\n"
            f"Customer message: {message}\n"
            f"Product ID: {product_id or 'Unknown'}\n"
            f"Return Policy: {policy}\n\n"
            f"Please extract and respond with this JSON format:\n"
            f'{{ "issue": "...", "tone": "...", "urgency": "..." }}'
        )

        try:
            res = requests.post(
                "https://app.openpipe.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL_ID,
                    "messages": [{"role": "user", "content": prompt}],
                    "store": False,
                    "temperature": 0
                }
            )

            if res.status_code != 200:
                result = f"HTTP {res.status_code} Error:\n{res.text}"
            else:
                ai_result = res.json()["choices"][0]["message"]["content"]
                full_result = '{\n  "visual_issue": "' + image_caption.replace('"', '\\"') + '",\n' + ai_result.lstrip('{').rstrip('}') + '\n}'
                result = full_result

        except Exception as e:
            result = f" Exception: {str(e)}"

    return render_template_string(HTML, result=result)

# Bind to localhost by default; hosted deployments (Replit, Cloud Run, ...)
# set HOST/PORT in the environment instead.
host = os.getenv("HOST", "127.0.0.1")
port = int(os.getenv("PORT", "81"))
app.run(host=host, port=port)
