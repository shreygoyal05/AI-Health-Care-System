from flask import Flask, request, jsonify, render_template
import pyttsx3
import os

app = Flask(__name__)

# Text-to-Speech Engine Initialization
engine = pyttsx3.init()

@app.route('/')
def home():
    return render_template('index.html')  # You'll create a simple index.html

# Endpoint to receive health data
@app.route('/health-data', methods=['POST'])
def health_data():
    data = request.json
    print("Received health data:", data)
    # You can process heart rate, BP, etc. here
    return jsonify({"status": "Health data received", "data": data})

# Endpoint to trigger fall alert
@app.route('/fall-alert', methods=['POST'])
def fall_alert():
    data = request.json
    print("FALL ALERT:", data)
    return jsonify({"status": "Fall alert received", "message": "Caregiver has been notified!"})

# Endpoint to trigger voice reminder
@app.route('/send-reminder', methods=['POST'])
def send_reminder():
    data = request.json
    message = data.get("message", "This is your reminder.")
    engine.say(message)
    engine.runAndWait()
    return jsonify({"status": "Reminder sent", "message": message})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
