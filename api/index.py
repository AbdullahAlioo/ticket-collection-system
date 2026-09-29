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
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

# Configure logging
logging.basicConfig(level=logging.INFO)

# Path configuration
api_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(api_dir)

app = Flask(
    __name__,
    template_folder=os.path.join(root_dir, 'templates'),
    static_folder=os.path.join(root_dir, 'static')
)
app.secret_key = os.environ.get("SESSION_SECRET", "ticket-collection-secret-key-2025")

# ----------------- CORS SUPPORT -----------------
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ----------------- DATABASE / PERSISTENCE LAYER -----------------
# If MONGO_URI is set in Vercel Environment Variables, MongoDB Atlas is used (Persistent).
# Otherwise, it falls back to /tmp/data/*.json for local testing.
MONGO_URI = os.environ.get("MONGO_URI")
db = None

if MONGO_URI:
    try:
        from pymongo import MongoClient
        import certifi
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client.ticket_system
        logging.info("Connected to MongoDB Atlas successfully.")
    except Exception as e:
        logging.error(f"MongoDB connection failed: {e}")
        db = None

DATA_DIR = "/tmp/data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

TICKETS_FILE = os.path.join(DATA_DIR, "tickets.json")
WAITING_LIST_FILE = os.path.join(DATA_DIR, "waiting_list.json")
ENQUIRIES_FILE = os.path.join(DATA_DIR, "enquiries.json")


def load_data(collection_name, file_path):
    if db is not None:
        try:
            return list(db[collection_name].find({}, {"_id": 0}))
        except Exception as e:
            logging.error(f"Error loading from MongoDB {collection_name}: {e}")
            return []
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logging.error(f"Error loading {file_path}: {e}")
        return []


def save_record(collection_name, file_path, item):
    if db is not None:
        try:
            db[collection_name].insert_one(item.copy())
            return True
        except Exception as e:
            logging.error(f"Error inserting into MongoDB {collection_name}: {e}")
            return False
    try:
        items = load_data(collection_name, file_path)
        items.append(item)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving to {file_path}: {e}")
        return False


def delete_record(collection_name, file_path, id_key, id_val):
    if db is not None:
        try:
            res = db[collection_name].delete_one({id_key: id_val})
            return res.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting from MongoDB {collection_name}: {e}")
            return False
    try:
        items = load_data(collection_name, file_path)
        new_items = [item for item in items if item.get(id_key) != id_val]
        if len(new_items) < len(items):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(new_items, f, indent=2, ensure_ascii=False)
            return True
        return False
    except Exception as e:
        logging.error(f"Error deleting from {file_path}: {e}")
        return False


# ----------------- VALIDATION HELPERS -----------------
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(email and re.match(pattern, email.strip()))


def validate_phone(phone):
    if not phone:
        return True  # phone is optional in inquiries
    pattern = r'^[\+\(\)\-\s\d]{7,20}$'
    return bool(re.match(pattern, phone.strip()))


# ----------------- ROUTES -----------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/inquiry', methods=['GET', 'POST', 'OPTIONS'])
def submit_inquiry():
    """Endpoint called by your website inquiry form & modal"""
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

        if save_record("enquiries", ENQUIRIES_FILE, inquiry_data):
            return jsonify({
                "success": True,
                "message": "Inquiry submitted successfully",
                "inquiry_id": inquiry_data["id"]
            }), 200
        else:
            return jsonify({"success": False, "message": "Failed to save inquiry"}), 500

    except Exception as e:
        logging.error(f"Error submitting inquiry: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/wait/<email>')
def add_to_waiting_list(email):
    try:
        if not validate_email(email):
            return jsonify({"success": False, "message": "Invalid email format"}), 400

        waiting_list = load_data("waiting_list", WAITING_LIST_FILE)
        if any(entry.get('email') == email.lower().strip() for entry in waiting_list):
            return jsonify({"success": False, "message": "Email already in waiting list"}), 409

        entry_data = {
            "id": str(uuid.uuid4()),
            "email": email.lower().strip(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "website": request.args.get('website', '')
        }

        if save_record("waiting_list", WAITING_LIST_FILE, entry_data):
            return jsonify({
                "success": True,
                "message": "Added to waiting list successfully",
                "entry_id": entry_data["id"]
            })
        return jsonify({"success": False, "message": "Failed to save to waiting list"}), 500
    except Exception as e:
        logging.error(f"Error adding to waiting list: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@app.route('/admin')
def admin():
    """Admin dashboard with persistent inquiries and tickets"""
    try:
        tickets = load_data("tickets", TICKETS_FILE)
        enquiries = load_data("enquiries", ENQUIRIES_FILE)
        waiting_list = load_data("waiting_list", WAITING_LIST_FILE)

        return render_template(
            'admin.html',
            tickets=tickets,
            total_tickets=len(tickets),
            enquiries=enquiries,
            total_enquiries=len(enquiries),
            waiting_list=waiting_list,
            total_waiting=len(waiting_list)
        )
    except Exception as e:
        logging.error(f"Error in admin route: {e}")
        return jsonify({"success": False, "message": f"Error loading admin page: {str(e)}"}), 500


@app.route('/delete_inquiry/<inquiry_id>', methods=['POST'])
def delete_inquiry(inquiry_id):
    if delete_record("enquiries", ENQUIRIES_FILE, "id", inquiry_id):
        flash(f"Inquiry deleted successfully", "success")
    else:
        flash("Inquiry not found or could not be deleted", "warning")
    return redirect(url_for('admin'))


@app.route('/delete_waiting_entry/<entry_id>', methods=['POST'])
def delete_waiting_entry(entry_id):
    if delete_record("waiting_list", WAITING_LIST_FILE, "id", entry_id):
        flash("Waiting list entry deleted successfully", "success")
    else:
        flash("Entry not found", "warning")
    return redirect(url_for('admin'))


@app.route('/delete_ticket/<ticket_number>', methods=['POST'])
def delete_ticket(ticket_number):
    if delete_record("tickets", TICKETS_FILE, "ticket_number", ticket_number):
        flash(f"Ticket {ticket_number} deleted successfully", "success")
    else:
        flash("Ticket not found", "warning")
    return redirect(url_for('admin'))


@app.route('/export/excel')
def export_excel():
    try:
        tickets = load_data("tickets", TICKETS_FILE)
        if not tickets:
            flash("No ticket data available to export", "warning")
            return redirect(url_for('admin'))

        wb = Workbook()
        ws = wb.active
        ws.title = "Ticket Data"

        headers = ['Email', 'Phone', 'Name', 'Tickets', 'Ticket Number', 'Country', 'Region', 'Timestamp']
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center')

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        for row, ticket in enumerate(tickets, 2):
            ws.cell(row=row, column=1, value=ticket.get('email', ''))
            ws.cell(row=row, column=2, value=ticket.get('phone', ''))
            ws.cell(row=row, column=3, value=ticket.get('name', ''))
            ws.cell(row=row, column=4, value=ticket.get('tickets', ''))
            ws.cell(row=row, column=5, value=ticket.get('ticket_number', ''))
            ws.cell(row=row, column=6, value=ticket.get('country', ''))
            ws.cell(row=row, column=7, value=ticket.get('region', ''))
            ws.cell(row=row, column=8, value=ticket.get('timestamp', ''))

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 50)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        wb.save(temp_file.name)
        temp_file.close()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f"ticket_data_{timestamp}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logging.error(f"Error exporting Excel: {e}")
        flash("Error exporting data to Excel", "error")
        return redirect(url_for('admin'))


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
