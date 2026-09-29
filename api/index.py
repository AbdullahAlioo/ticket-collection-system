import os
import json
import logging
from datetime import datetime
import tempfile
import re
import uuid

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    flash,
    redirect,
    url_for,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

api_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(api_dir)

app = Flask(
    __name__,
    template_folder=os.path.join(root_dir, 'templates'),
    static_folder=os.path.join(root_dir, 'static')
)
app.secret_key = os.environ.get("SESSION_SECRET", "ticket-secret-2025")

# Enable CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# MongoDB connection helper
def get_db():
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        logging.warning("No MONGO_URI found in environment variables.")
        return None
    try:
        from pymongo import MongoClient
        import certifi
        client = MongoClient(
            mongo_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )
        return client.get_database("daycare_db")
    except Exception as e:
        logging.error(f"MongoDB connection error: {e}")
        return None

def save_record(collection_name, item):
    db = get_db()
    if db is not None:
        try:
            db[collection_name].insert_one(item.copy())
            return True, None
        except Exception as e:
            return False, f"MongoDB error: {str(e)}"

    # Fallback to local /tmp storage
    try:
        data_dir = "/tmp/data"
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, f"{collection_name}.json")
        items = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
        items.append(item)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True, None
    except Exception as e:
        return False, f"File write error: {str(e)}"

def load_data(collection_name):
    db = get_db()
    if db is not None:
        try:
            return list(db[collection_name].find({}, {"_id": 0}))
        except Exception as e:
            logging.error(f"MongoDB load error: {e}")
    try:
        file_path = f"/tmp/data/{collection_name}.json"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"File load error: {e}")
    return []

# Validation
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(email and re.match(pattern, email.strip()))

# Inquiry endpoint
@app.route('/inquiry', methods=['GET', 'POST', 'OPTIONS'])
def submit_inquiry():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        if request.method == 'GET':
            email = request.args.get('email', '').strip()
            name = request.args.get('name', '').strip()
            phone = request.args.get('phone', '').strip()
            interest = request.args.get('interest', '').strip()
            message = request.args.get('message', '').strip()
            source = request.args.get('source', '').strip()
        else:
            data = request.get_json(silent=True) or {}
            email = data.get('email', '').strip()
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            interest = data.get('interest', '').strip()
            message = data.get('message', '').strip()
            source = data.get('source', '').strip()

        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400

        if not validate_email(email):
            return jsonify({"success": False, "message": "Invalid email format"}), 400

        inquiry_data = {
            "id": str(uuid.uuid4()),
            "name": name or "Not provided",
            "email": email.lower(),
            "phone": phone or "",
            "enquiry_type": interest or "General",
            "message": message or "",
            "source": source or "website",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        success, err_msg = save_record("enquiries", inquiry_data)
        if success:
            return jsonify({
                "success": True,
                "message": "Inquiry submitted successfully",
                "inquiry_id": inquiry_data["id"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to save inquiry",
                "error_detail": err_msg
            }), 500

    except Exception as e:
        logging.error(f"Error submitting inquiry: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin')
def admin():
    tickets = load_data("tickets")
    enquiries = load_data("enquiries")
    waiting_list = load_data("waiting_list")

    return render_template(
        'admin.html',
        tickets=tickets,
        total_tickets=len(tickets),
        enquiries=enquiries,
        total_enquiries=len(enquiries),
        waiting_list=waiting_list,
        total_waiting=len(waiting_list)
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


