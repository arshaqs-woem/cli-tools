from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import redis
import json
import plivo

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://arshaq.s@localhost/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
SESSION_TTL = 1800  # 30 minutes


# ── Models ──────────────────────────────────────────────────────────────────

class CallLog(db.Model):
    __tablename__ = "call_logs"

    id = db.Column(db.Integer, primary_key=True)
    caller_number = db.Column(db.String(20), nullable=False)
    called_number = db.Column(db.String(20), nullable=False)
    call_status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "caller_number": self.caller_number,
            "called_number": self.called_number,
            "call_status": self.call_status,
            "created_at": self.created_at.isoformat(),
        }


with app.app_context():
    db.create_all()


# ── Helpers ──────────────────────────────────────────────────────────────────

def xml_response(xml_str):
    return app.response_class(xml_str, mimetype="text/xml")


def speak_and_get_digits(message, action_url):
    return f"""<Response>
    <GetDigits action="{action_url}" method="POST" numDigits="1" timeout="10" retries="1">
        <Speak>{message}</Speak>
    </GetDigits>
    <Redirect method="POST">{action_url}</Redirect>
</Response>"""


# ── IVR Routes ───────────────────────────────────────────────────────────────

@app.route("/answer", methods=["POST"])
def answer():
    caller = request.form.get("From", "unknown")
    called = request.form.get("To", "unknown")
    call_uuid = request.form.get("CallUUID", "unknown")

    # Store session in Redis
    try:
        session = {
            "caller": caller,
            "called": called,
            "call_uuid": call_uuid,
            "step": "main_menu",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        r.setex(f"session:{caller}", SESSION_TTL, json.dumps(session))
    except Exception as e:
        print(f"Redis error: {e}")

    # Log call start in PostgreSQL
    try:
        log = CallLog(caller_number=caller, called_number=called, call_status="in_progress")
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"DB error: {e}")

    ngrok_url = request.host_url.rstrip("/")
    xml = speak_and_get_digits(
        "Welcome to Acme Corp. Press 1 for Sales, Press 2 for Support, Press 3 to hear your caller I D.",
        f"{ngrok_url}/handle-input"
    )
    return xml_response(xml)


@app.route("/handle-input", methods=["POST"])
def handle_input():
    caller = request.form.get("From", "unknown")
    digit = request.form.get("Digit", "")
    ngrok_url = request.host_url.rstrip("/")

    # Read session from Redis
    session = None
    try:
        data = r.get(f"session:{caller}")
        if data:
            session = json.loads(data)
    except Exception as e:
        print(f"Redis error: {e}")

    def update_call_log(status):
        try:
            log = CallLog.query.filter_by(
                caller_number=caller, call_status="in_progress"
            ).order_by(CallLog.created_at.desc()).first()
            if log:
                log.call_status = status
                db.session.commit()
        except Exception as e:
            print(f"DB error: {e}")

    def update_session_step(step):
        try:
            if session:
                session["step"] = step
                r.setex(f"session:{caller}", SESSION_TTL, json.dumps(session))
        except Exception as e:
            print(f"Redis error: {e}")

    if digit == "1":
        update_session_step("routed_sales")
        update_call_log("routed_sales")
        return xml_response("<Response><Speak>Connecting to sales. Goodbye.</Speak></Response>")

    elif digit == "2":
        update_session_step("routed_support")
        update_call_log("routed_support")
        return xml_response("<Response><Speak>Connecting to support. Goodbye.</Speak></Response>")

    elif digit == "3":
        update_session_step("caller_id")
        spoken = caller.replace("+", "").replace(" ", ", ")
        return xml_response(f"<Response><Speak>Your caller I D is {spoken}. Goodbye.</Speak></Response>")

    else:
        xml = speak_and_get_digits(
            "Invalid option. Press 1 for Sales, Press 2 for Support, Press 3 to hear your caller I D.",
            f"{ngrok_url}/handle-input"
        )
        return xml_response(xml)


# ── Other Routes ─────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/call-logs", methods=["GET"])
def call_logs():
    logs = CallLog.query.order_by(CallLog.created_at.desc()).all()
    return jsonify([log.to_dict() for log in logs])


@app.route("/log-call", methods=["POST"])
def log_call():
    data = request.get_json()
    log = CallLog(
        caller_number=data["caller_number"],
        called_number=data["called_number"],
        call_status=data["call_status"],
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"message": "Call logged", "id": log.id}), 201


@app.route("/call-history/<phone_number>", methods=["GET"])
def call_history(phone_number):
    logs = CallLog.query.filter_by(caller_number=phone_number)\
        .order_by(CallLog.created_at.desc()).all()
    if not logs:
        return jsonify({"message": "No calls found", "calls": []}), 404
    return jsonify({"phone_number": phone_number, "total_calls": len(logs), "calls": [l.to_dict() for l in logs]})


@app.route("/start-session/<caller_id>", methods=["POST"])
def start_session(caller_id):
    session = {
        "caller_id": caller_id,
        "step": "greeting",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    r.setex(f"session:{caller_id}", SESSION_TTL, json.dumps(session))
    return jsonify({"message": "Session started", "session": session})


@app.route("/get-session/<caller_id>", methods=["GET"])
def get_session(caller_id):
    data = r.get(f"session:{caller_id}")
    if not data:
        return jsonify({"error": "Session not found or expired"}), 404
    return jsonify(json.loads(data))


@app.route("/update-session/<caller_id>/<step>", methods=["POST"])
def update_session(caller_id, step):
    data = r.get(f"session:{caller_id}")
    if not data:
        return jsonify({"error": "Session not found or expired"}), 404
    session = json.loads(data)
    session["step"] = step
    ttl = r.ttl(f"session:{caller_id}")
    r.setex(f"session:{caller_id}", ttl, json.dumps(session))
    return jsonify({"message": "Session updated", "session": session})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
