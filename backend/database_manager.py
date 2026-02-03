import os
import logging
from tinydb import TinyDB
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - Savant DB - %(message)s')

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'patient_logs.json')

class DatabaseManager:
    def __init__(self):
        self.patient_db = TinyDB(DB_FILE)
        logging.info("✓ DatabaseManager initialized (RAG disabled)")

    def log_patient_state(self, heart_rate, injury_detected, actions_taken):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "heart_rate": heart_rate,
            "injury_detected": injury_detected,
            "actions_taken": actions_taken
        }
        self.patient_db.insert(entry)
        logging.info("Patient state logged.")

    def get_logs(self):
        return self.patient_db.all()

if __name__ == "__main__":
    db = DatabaseManager()
    db.log_patient_state(120, "Hemorrhage", "Tourniquet applied")
    print(db.get_logs())
