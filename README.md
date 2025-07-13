# AMD AI Sprint Hackathon - Track 2: Agentic AI Scheduling Assistant

## 🎯 Project Goal
Build a backend Flask application that intelligently schedules meetings by finding common available time slots among attendees.

## 🛠 Tech Stack
- **Python 3**
- **Flask** (serving on port 5000)
- **JSON** input/output
- **In-memory calendar data** (simulated)
- **Optional**: GPT/Claude integration for polite message generation

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation
1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
```bash
python app.py
```

The server will start on `http://localhost:5000`

## 📋 API Endpoints

### POST /schedule
Schedules a meeting by finding common available time slots.

**Input JSON Format:**
```json
{
  "sender": "user@example.com",
  "attendees": ["attendee1@example.com", "attendee2@example.com"],
  "subject": "Project Discussion",
  "content": "Let's discuss the new project requirements"
}
```

**Output JSON Format:**
```json
{
  "eventStart": "2024-01-15T10:00:00Z",
  "eventEnd": "2024-01-15T11:00:00Z",
  "duration": 60,
  "attendeeEvents": {
    "attendee1@example.com": [...],
    "attendee2@example.com": [...]
  },
  "responseMessage": "Meeting scheduled successfully!",
  "metadata": {
    "schedulingAlgorithm": "conflict-free",
    "timestamp": "2024-01-15T09:00:00Z"
  }
}
```

### GET /health
Health check endpoint to verify the service is running.

## 🧱 Development Progress

- [x] Basic Flask app setup
- [x] /schedule endpoint (basic structure)
- [x] /health endpoint
- [ ] Dummy calendar data for 3 users
- [ ] Meeting scheduling logic
- [ ] Conflict-free time slot finding
- [ ] Input validation and error handling
- [ ] LLM integration for polite messages
- [ ] Additional endpoints (/available-slots, /calendar/<email>)

## 🤝 Contributing
This is a hackathon project for AMD AI Sprint - Track 2.

## 📝 License
Hackathon project - educational purposes. 