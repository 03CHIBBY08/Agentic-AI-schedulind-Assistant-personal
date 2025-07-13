from datetime import datetime, timedelta
import json
import requests
from agent import Agent
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class CalendarManager:
    def __init__(self):
        self.calendars = self._initialize_dummy_calendars()

    def _initialize_dummy_calendars(self):
        base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        calendars = {
            "alice@example.com": [
                {"id": "event1", "title": "Team Standup", "start": (base_date + timedelta(hours=0)).isoformat(), "end": (base_date + timedelta(hours=1)).isoformat(), "description": "Daily team standup meeting"},
                {"id": "event2", "title": "Client Meeting", "start": (base_date + timedelta(hours=3)).isoformat(), "end": (base_date + timedelta(hours=4)).isoformat(), "description": "Meeting with client about project requirements"},
                {"id": "event3", "title": "Lunch Break", "start": (base_date + timedelta(hours=5)).isoformat(), "end": (base_date + timedelta(hours=6)).isoformat(), "description": "Lunch break"}
            ],
            "bob@example.com": [
                {"id": "event4", "title": "Code Review", "start": (base_date + timedelta(hours=1)).isoformat(), "end": (base_date + timedelta(hours=2)).isoformat(), "description": "Code review session"},
                {"id": "event5", "title": "Product Planning", "start": (base_date + timedelta(hours=4)).isoformat(), "end": (base_date + timedelta(hours=5)).isoformat(), "description": "Product planning meeting"}
            ],
            "charlie@example.com": [
                {"id": "event6", "title": "Design Review", "start": (base_date + timedelta(hours=2)).isoformat(), "end": (base_date + timedelta(hours=3)).isoformat(), "description": "Design review meeting"},
                {"id": "event7", "title": "Documentation", "start": (base_date + timedelta(hours=6)).isoformat(), "end": (base_date + timedelta(hours=7)).isoformat(), "description": "Documentation work"}
            ]
        }
        return calendars

    def get_google_calendar_service(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return build('calendar', 'v3', credentials=creds)

    def fetch_events_from_google(self, email, time_min, time_max):
        service = self.get_google_calendar_service()
        events_result = service.events().list(
            calendarId=email,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        formatted = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            formatted.append({
                'id': event['id'],
                'title': event.get('summary', 'Busy'),
                'start': start,
                'end': end,
                'description': event.get('description', '')
            })
        return formatted

    def get_user_calendar(self, email):
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            later = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
            # Only use Google Calendar if credentials.json exists
            if os.path.exists('credentials.json'):
                return self.fetch_events_from_google(email, now, later)
            else:
                return self.calendars.get(email, [])
        except Exception as e:
            print(f"Google Calendar fetch failed: {e}")
            return self.calendars.get(email, [])

    def normalize_events(self, events):
        """Convert event times to datetime objects and sort."""
        normalized = []
        for event in events:
            try:
                start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(event['end'].replace('Z', '+00:00'))
                normalized.append((start, end))
            except Exception:
                continue
        return sorted(normalized, key=lambda x: x[0])

    def get_busy_intervals(self, attendees):
        """Get all busy intervals for a list of attendees."""
        all_events = []
        for attendee in attendees:
            calendar = self.get_user_calendar(attendee)
            all_events.extend(calendar)
        return self.normalize_events(all_events)

    def agent_slot_score(self, slot, agents):
        """Score a slot based on agent priorities (stub: can be improved)."""
        # Example: prioritize slots where managers are free
        # For now, just return 9 for all slots
        return 9

    def find_available_slots(self, attendees, duration_minutes=60, start_time=None, end_time=None, agents=None):
        if not start_time:
            start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        if not end_time:
            end_time = start_time.replace(hour=17, minute=0, second=0, microsecond=0)
        busy = self.get_busy_intervals(attendees)
        available_slots = []
        current_time = start_time
        for event_start, event_end in busy:
            if current_time + timedelta(minutes=duration_minutes) <= event_start:
                available_slots.append((current_time, current_time + timedelta(minutes=duration_minutes)))
            current_time = max(current_time, event_end)
        if current_time + timedelta(minutes=duration_minutes) <= end_time:
            available_slots.append((current_time, current_time + timedelta(minutes=duration_minutes)))
        # Agent-based scoring (if agents provided)
        if agents:
            scored = [(slot, self.agent_slot_score(slot, agents)) for slot in available_slots]
            scored.sort(key=lambda x: -x[1])
            return [s[0] for s in scored]
        return available_slots

    def get_attendee_events(self, attendees):
        attendee_events = {}
        for attendee in attendees:
            attendee_events[attendee] = self.get_user_calendar(attendee)
        return attendee_events 

def generate_polite_message_with_llm(prompt):
    response = requests.post(
        "http://localhost:3000/generate",
        json={"prompt": prompt, "max_tokens": 100}
    )
    return response.json()["text"] 