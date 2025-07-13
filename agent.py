class Agent:
    def __init__(self, email, role, preferences=None):
        self.email = email
        self.role = role
        self.preferences = preferences or {}

    def priority(self):
        # Example: manager > lead > member > intern
        role_priority = {"manager": 3, "lead": 2, "member": 1, "intern": 0}
        return role_priority.get(self.role, 0)

    def __repr__(self):
        return f"Agent(email={self.email}, role={self.role}, preferences={self.preferences})" 