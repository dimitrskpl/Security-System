import time

ALERT_LEVELS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

ALERT_LEVELS_DISPLAY = {
    1: "Low",
    2: "Medium",
    3: "High",
}

ALERT_SYMBOLS = {
    1: "ℹ️",
    2: "⚠️",
    3: "🚨",
}


class Alert:
    def __init__(self, id, message, level):
        self.id = id
        self.message = message
        self.timestamp = time.time()
        self.level = level  # high, medium, low
        self.symbol = ALERT_SYMBOLS[level]

    def __str__(self):
        return f"{self.symbol} Alert: {self.message} at {time.ctime(self.timestamp)}"
