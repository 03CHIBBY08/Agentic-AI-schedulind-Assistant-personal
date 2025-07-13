import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import json
from typing import Dict
from calendar_manager import CalendarManager
from llm_negotiator import llm_negotiation_message
from agent import Agent
import uuid
import time
from flask import Flask, render_template

app = Flask(__name__)
CORS(app)
calendar_manager = CalendarManager()
logging.basicConfig(level=logging.INFO)
AGENT_VERSION = "1.0"
IST = timezone(timedelta(hours=5, minutes=30))

# --- Helper Functions ---
def parse_and_validate_input(data: Dict) -> Dict:
    required_fields = ["Request_id", "Datetime", "Location", "From", "Attendees", "Subject", "EmailContent"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    if not isinstance(data["Attendees"], list) or len(data["Attendees"]) == 0:
        raise ValueError("Attendees must be a non-empty list")
    for attendee in data["Attendees"]:
        if not isinstance(attendee, dict) or "email" not in attendee:
            raise ValueError("Each attendee must be a dict with an 'email' key")
    return data

def get_attendee_emails(attendees, sender):
    emails = [a["email"] for a in attendees]
    if sender not in emails:
        emails.append(sender)
    return emails

def build_agents(attendees):
    # For demo, assign 'manager' to alice, 'member' to others
    agents = []
    for a in attendees:
        role = "manager" if a["email"].startswith("alice") else "member"
        agents.append(Agent(a["email"], role))
    return agents

def format_datetime(dt):
    if not dt:
        return None
    # Always output in ISO format with +05:30
    return dt.astimezone(IST).isoformat()

def build_attendee_events(attendees):
    result = []
    for attendee in attendees:
        email = attendee["email"]
        events = calendar_manager.get_user_calendar(email)
        formatted_events = []
        for event in events:
            formatted_events.append({
                "startTime": format_datetime(datetime.fromisoformat(event["start"])),
                "endTime": format_datetime(datetime.fromisoformat(event["end"])),
                "attendees": [email],
                "Summary": event["title"]
            })
        result.append({
            "email": email,
            "events": formatted_events
        })
    return result

def find_and_score_slots(attendee_emails, duration, agents):
    slots = calendar_manager.find_available_slots(attendee_emails, duration_minutes=duration, agents=agents)
    scored = [(slot, 9 if i == 0 else 7) for i, slot in enumerate(slots)]
    return scored

def build_output_json(request_data, attendee_events, polite_message, event_start, event_end, duration, slot_score_val, processing_time, conflict_resolution):
    return {
        "Request_id": request_data["Request_id"],
        "From": request_data["From"],
        "Attendees": attendee_events,
        "Subject": request_data["Subject"],
        "EmailContent": polite_message,
        "EventStart": format_datetime(event_start),
        "EventEnd": format_datetime(event_end),
        "Duration_mins": str(duration),
        "MetaData": {
            "agent_version": AGENT_VERSION,
            "conflict_resolution": conflict_resolution,
            "processing_time": f"{processing_time:.2f}s",
            "slot_score": slot_score_val
        }
    }

# --- Main Assistant Function ---
def your_meeting_assistant(input_json: Dict) -> Dict:
    start_time = time.time()
    try:
        request_data = parse_and_validate_input(input_json)
        sender = request_data["From"]
        attendees = request_data["Attendees"]
        subject = request_data["Subject"]
        duration = 60  # Default to 60 min, or parse from request if present
        attendee_emails = get_attendee_emails(attendees, sender)
        agents = build_agents(attendees)
        scored_slots = find_and_score_slots(attendee_emails, duration, agents)
        attendee_events = build_attendee_events(attendees)
        if scored_slots:
            (event_start, event_end), slot_score_val = scored_slots[0]
            polite_message = f"Your meeting '{subject}' is confirmed for {format_datetime(event_start)} to {format_datetime(event_end)}."
            conflict_resolution = "none"
        else:
            event_start = event_end = None
            slot_score_val = 0
            alt_slots = calendar_manager.find_available_slots(attendee_emails, duration_minutes=duration)
            alt_slots_fmt = [f"{format_datetime(s[0])} - {format_datetime(s[1])}" for s in alt_slots[:3]]
            conflict_details = {
                "attendees": ', '.join(attendee_emails),
                "requested_time": request_data["Datetime"],
                "conflict_reason": "No common free slot for all attendees.",
                "suggested_slots": '; '.join(alt_slots_fmt) if alt_slots_fmt else "No alternatives found"
            }
            polite_message = llm_negotiation_message(conflict_details)
            conflict_resolution = "LLM"
        processing_time = time.time() - start_time
        output = build_output_json(
            request_data,
            attendee_events,
            polite_message,
            event_start,
            event_end,
            duration,
            slot_score_val,
            processing_time,
            conflict_resolution
        )
        return output
    except Exception as e:
        logging.exception("Error in your_meeting_assistant")
        return {"status": "error", "message": str(e)}

# --- Flask Endpoint ---
@app.route('/schedule', methods=['POST'])
def schedule_meeting():
    data = request.get_json()
    result = your_meeting_assistant(data)
    status = 200 if 'status' not in result or result['status'] != 'error' else 400
    return jsonify(result), status

@app.route('/available-slots', methods=['POST'])
def get_available_slots():
    """
    Endpoint to get available time slots for specified attendees
    """
    try:
        data = request.get_json()
        if not data or 'attendees' not in data:
            return jsonify({"status": "error", "message": "Missing attendees in request"}), 400
        attendees = data['attendees']
        duration = data.get('duration', 60)
        available_slots = calendar_manager.find_available_slots(attendees=attendees, duration_minutes=duration)
        slots_formatted = []
        for start, end in available_slots:
            slots_formatted.append({
                "start": start.isoformat(),
                "end": end.isoformat(),
                "duration_minutes": int((end - start).total_seconds() / 60)
            })
        return jsonify({"status": "success", "availableSlots": slots_formatted, "totalSlots": len(slots_formatted)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500

@app.route('/calendar/<email>', methods=['GET'])
def get_user_calendar(email):
    """
    Endpoint to get calendar events for a specific user
    """
    try:
        events = calendar_manager.get_user_calendar(email)
        return jsonify({"status": "success", "email": email, "events": events, "totalEvents": len(events)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500

@app.route('/')
def send_frontend():
    return render_template('index.html')
    # return send_from_directory('frontend', path)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat(), "service": "AMD AI Sprint - Agentic AI Scheduling Assistant"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 