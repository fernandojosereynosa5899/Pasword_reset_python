from backen import models
from backen.main import SessionLocal

def view_database():
    db = SessionLocal()

    print("\n--- Tabla: USERS ---")
    users = db.query(models.User).all()
    for u in users:
        print(f"ID: {u.id} | Email: {u.email} | Password Hash: {u.hashed_password[:15]}...")


        print("\n--- Tabla: RESET TOKENS ---")

        tokens = db.query(models.ResetToken).all()
        for t in tokens:
            print(f"Token Hash: {t.token_hash[:10]}... | Email: {t.user_email} | Expira: {t.expires_at} | Usado: {t.used}")

            db.close()

if __name__ == "__main__":
    view_database()