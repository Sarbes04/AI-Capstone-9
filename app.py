
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template_string
import requests

from validate import validate_input, scan_output
from auth import token_required


app = Flask(__name__)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3"

SYSTEM_PROMPT = """
You are TechCorp's internal AI assistant.
Help employees with company documentation,
support tickets, and administrative workflows.
You are powered by Llama 3.
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>TechCorp AI Assistant</title>
    <style>
        body {
            font-family: Arial;
            max-width: 750px;
            margin: 40px auto;
            background: #f4f4f4;
        }
        #chat {
            background: white;
            padding: 20px;
            min-height: 300px;
            border-radius: 8px;
        }
        input { width: 75%; padding: 12px; }
        button { padding: 12px; }
        .user { color: blue; }
        .ai { color: green; white-space: pre-wrap; }
    </style>
</head>
<body>
    <h2>TechCorp Internal AI Assistant</h2>
    <div id="chat"></div>
    <br>
    <input id="message" placeholder="Ask me something...">
    <button onclick="sendMessage()">Send</button>

    <script>
        async function sendMessage() {
            const input = document.getElementById("message");
            const chat = document.getElementById("chat");
            const message = input.value;

            if (!message.trim()) return;

            chat.innerHTML +=
                '<p class="user"><b>You:</b> ' +
                message + '</p>';

            input.value = "";

            const response = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({message: message})
            });

            const data = await response.json();

            chat.innerHTML +=
                '<p class="ai"><b>AI:</b> ' +
                (data.response || data.error) + '</p>';
        }
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)


def generate_response(user_input, use_system_prompt=False):
    # Defence 1 and 2: Validate user input
    error = validate_input(user_input)

    if error:
        return jsonify({"error": error}), 400

    prompt = user_input

    if use_system_prompt:
        prompt = SYSTEM_PROMPT + "\nUser: " + user_input + "\nAssistant:"

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        result = response.json()

        model_output = result.get("response", "")

        # Defence 3: Scan model output
        output_error = scan_output(model_output)

        if output_error:
            return jsonify({"error": output_error}), 400

        return jsonify({"response": model_output}), 200

    except requests.RequestException:
        return jsonify({
            "error": "AI service is currently unavailable."
        }), 503


@app.route("/chat", methods=["POST"])
@token_required
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    if not isinstance(message, str):
        return jsonify({"error": "Message must be a string."}), 400

    return generate_response(message, use_system_prompt=True)


@app.route("/ask", methods=["POST"])
@token_required
def ask():
    data = request.get_json(silent=True) or {}
    user_input = data.get("question", "")

    if not isinstance(user_input, str):
        return jsonify({"error": "Question must be a string."}), 400

    return generate_response(user_input)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
