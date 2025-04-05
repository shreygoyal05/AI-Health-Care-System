from flask import Flask, request, jsonify, render_template
import pyttsx3
import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import sqlite3
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)  # Uses default templates folder (now containing index.html and profile.html)

# Initialize the text-to-speech engine (moved inside function for thread safety)
def init_tts_engine():
    return pyttsx3.init()

# Home route with template rendering
@app.route('/')
def home():
    try:
        return render_template('index.html')  # Renders index.html from templates folder
    except Exception as e:
        return jsonify({"error": f"Template error: {str(e)}"}), 500

# Profile route with template rendering
@app.route('/profile')
def profile():
    try:
        return render_template('profile.html')  # Renders profile.html from templates folder
    except Exception as e:
        return jsonify({"error": f"Template error: {str(e)}"}), 500

# Endpoint to receive health data
@app.route('/health-data', methods=['POST'])
def health_data():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.json
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid data format"}), 400
    
    # Extract and validate health data
    heart_rate = data.get("heart_rate")
    bp = data.get("bp")
    if not heart_rate or not bp:
        return jsonify({"error": "Heart rate and blood pressure are required"}), 400
    try:
        heart_rate = int(heart_rate)
        if heart_rate < 0 or heart_rate > 200:
            return jsonify({"error": "Invalid heart rate (0-200 bpm)"}), 400
    except ValueError:
        return jsonify({"error": "Heart rate must be a number"}), 400

    # Simple analysis
    status = "Normal"
    if heart_rate > 100:
        status = "High (Tachycardia)"
    elif heart_rate < 60:
        status = "Low (Bradycardia)"

    # Save to SQLite database
    conn = sqlite3.connect('health_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS health_records 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT,
                      heart_rate INTEGER,
                      blood_pressure TEXT,
                      status TEXT)''')
    cursor.execute('''INSERT INTO health_records (timestamp, heart_rate, blood_pressure, status)
                      VALUES (?, ?, ?, ?)''', 
                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), heart_rate, bp, status))
    conn.commit()
    conn.close()

    print("Received health data:", data)
    return jsonify({"status": "Health data processed", "data": {"heart_rate": heart_rate, "blood_pressure": bp}, "analysis": status})

# Endpoint to trigger fall alert
@app.route('/fall-alert', methods=['POST'])
def fall_alert():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.json
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid data format"}), 400
    
    # Extract location
    location = data.get("location")
    if not location:
        return jsonify({"error": "Location is required"}), 400

    # Email configuration (replace with your details)
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")

    # Email content
    subject = "URGENT: Fall Alert"
    body = f"A fall has been detected at {location} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        # Send email using SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
    except Exception as e:
        return jsonify({"error": f"Failed to send alert: {str(e)}"}), 500

    print("FALL ALERT:", data)
    return jsonify({"status": "Fall alert sent", "message": "Caregiver has been notified via email!"})

# Endpoint to trigger voice reminder
@app.route('/send-reminder', methods=['POST'])
def send_reminder():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.json
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid data format"}), 400
    message = data.get("message", "This is your reminder.")
    if not isinstance(message, str):
        return jsonify({"error": "Message must be a string"}), 400
    try:
        engine = init_tts_engine()  # Initialize engine per request
        engine.say(message)
        engine.runAndWait()
        engine.stop()  # Clean up engine after use
        return jsonify({"status": "Reminder sent", "message": message})
    except Exception as e:
        return jsonify({"error": f"Failed to send reminder: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)  # Bind to all interfaces for testing