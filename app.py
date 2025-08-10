from flask import Flask, request, jsonify
from dotenv import load_dotenv
load_dotenv()
import os
from gemini_utils import process_user_message, format_response


app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return (
        "<h2>Cultura API is running!</h2>"
        "<p>Send a POST request to <code>/cultura</code> with a JSON body:<br>"
        "<pre>{\n  &quot;message&quot;: &quot;Your question here&quot;\n}</pre>"
        "to get a vibe-aligned recommendation.</p>"
    )

@app.route('/cultura', methods=['GET'])
def cultura_get():
    return (
        "<h2>Cultura API Endpoint</h2>"
        "<p>This endpoint only accepts POST requests with a JSON body:<br>"
        "<pre>{\n  &quot;message&quot;: &quot;Your question here&quot;\n}</pre>"
        "</p>"
    )

@app.route('/cultura', methods=['POST'])
def cultura():
    data = request.get_json()
    user_msg = data.get('message', '')
    if not user_msg:
        return jsonify({'error': 'No message provided'}), 400
    try:
        user_id = 'web_user'  # In production, use real user/session ID
        reply = process_user_message(user_msg, user_id)
        formatted_reply = format_response(reply)
        return jsonify({'response': formatted_reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 