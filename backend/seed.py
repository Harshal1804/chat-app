"""Run once at startup to seed default rooms."""
import time
from sqlalchemy import text
from database import engine, SessionLocal
from models import Base, Room

def wait_for_db(retries=10, delay=3):
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database is ready")
            return True
        except Exception as e:
            print(f"⏳ Waiting for DB... ({i+1}/{retries}): {e}")
            time.sleep(delay)
    return False

def seed():
    if not wait_for_db():
        print("❌ Could not connect to database")
        return

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    defaults = [
        ("general",    "The main hangout room 💬"),
        ("tech-talk",  "Dev discussions & code 💻"),
        ("random",     "Anything goes 🎲"),
    ]

    for name, desc in defaults:
        if not db.query(Room).filter(Room.name == name).first():
            db.add(Room(name=name, description=desc))
            print(f"  🚀 Created room: {name}")

    db.commit()
    db.close()
    print("✅ Seeding complete")

if __name__ == "__main__":
    seed()
