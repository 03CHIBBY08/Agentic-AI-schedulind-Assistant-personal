from datetime import datetime, timedelta
import os
import json
import requests
from agent import Agent
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class CalendarManager:
    def __init__(self):
        self.calendars = self._initialize_dummy_calendars()

    def _initialize_dummy_calendars(self):
        base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        return {
            "alice@example.com": [
                {"id": "event1", "title": "Team Standup", "start": (base_date + timedelta(hours=0)).isoformat(), "end": (base_date + timedelta(hours=1)).isoformat(), "description": "Daily team standup meeting"},
                {"id": "event2", "title": "Client Meeting", "start": (base_date + timedelta(hours=3)).isoformat(), "end": (base_date + timedelta(hours=4)).isoformat(), "description": "Meeting with client"},
                {"id": "event3", "title": "Lunch", "start": (base_date + timedelta(hours=5)).isoformat(), "end": (base_date + timedelta(hours=6)).isoformat(), "description": "Lunch break"}
            ],
            "bob@example.com": [
                {"id": "event4", "title": "Code Review", "start": (base_date + timedelta(hours=1)).isoformat(), "end": (base_date + timedelta(hours=2)).isoformat(), "description": "Review PRs"},
                {"id": "event5", "title": "Planning", "start": (base_date + timedelta(hours=4)).isoformat(), "end": (base_date + timedelta(hours=5)).isoformat(), "description": "Sprint planning"}
            ],
            "charlie@example.com": [
                {"id": "event6", "title": "Design Review", "start": (base_date + timedelta(hours=2)).isoformat(), "end": (base_date + timedelta(hours=3)).isoformat(), "description": "UI Review"},
                {"id": "event7", "title": "Docs", "start": (base_date + timedelta(hours=6)).isoformat(), "end": (base_date + timedelta(hours=7)).isoformat(), "description": "Write docs"}
            ]
        }

    def get_google_calendar_service(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = Flow.from_client_config(
                    {
                        "installed": {
                            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost"]
                        }
                    },
                    scopes=SCOPES
                )
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
            if os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"):
                return self.fetch_events_from_google(email, now, later)
            else:
                return self.calendars.get(email, [])
        except Exception as e:
            print(f"Google Calendar fetch failed: {e}")
            return self.calendars.get(email, [])

    def normalize_events(self, events):
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
        all_events = []
        for attendee in attendees:
            calendar = self.get_user_calendar(attendee)
            all_events.extend(calendar)
        return self.normalize_events(all_events)

    def agent_slot_score(self, slot, agents):
        return 9  # Stub scoring

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
        if agents:
            scored = [(slot, self.agent_slot_score(slot, agents)) for slot in available_slots]
            scored.sort(key=lambda x: -x[1])
            return [s[0] for s in scored]
        return available_slots

    def get_attendee_events(self, attendees):
        return {attendee: self.get_user_calendar(attendee) for attendee in attendees}

def generate_polite_message_with_llm(prompt):
    response = requests.post(
        "http://localhost:3000/generate",
        json={"prompt": prompt, "max_tokens": 100}
    )
    return response.json()["text"]
