import logging
from flask import Flask, request, jsonify
from twilio.rest import Client
import sqlite3
import os

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)

# --- Twilio Setup ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio sandbox number
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- Database Setup ---
DB_FILE = "reports.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            species TEXT,
            location TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()
    logging.info("Database initialized")

init_db()

# --- Routes ---
@app.route("/webhook", methods=["POST"])
def webhook():
    logging.info("📞 Webhook called from ElevenLabs")

    try:
        data = request.json
        logging.info(f"Incoming data: {data}")

        # Example: Extract fields from ElevenLabs payload
        name = data.get("name", "Unknown")
        phone = data.get("phone", "")
        phone = "+91" + phone
        species = data.get("species", "Unknown")
        location = data.get("location", "")
        notes = data.get("injury", "")

        logging.info("Saving report to database...")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reports (name, phone, species, location, notes) VALUES (?, ?, ?, ?, ?)",
            (name, phone, species, location, notes),
        )
        conn.commit()
        conn.close()
        logging.info("✅ Report saved to database")

        # Send WhatsApp confirmation
        if phone:
            logging.info(f"Sending WhatsApp confirmation to {phone}...")
            message = client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=f"Thank you {name}. We have recorded your report of an injured {species} at {location}. Our team will contact you soon.",
                to=f"whatsapp:{phone}"
            )
            logging.info(f"✅ WhatsApp message sent: SID={message.sid}")
        else:
            logging.warning("⚠ No phone number provided. Skipping WhatsApp message.")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logging.exception("❌ Error processing webhook")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logging.info("🚀 Starting Flask app...")
    app.run(port=8888, debug=True)
