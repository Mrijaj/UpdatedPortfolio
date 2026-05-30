from app import app, db

print("Starting database sync...")
with app.app_context():
    db.drop_all()
    db.create_all()
print("Database reset successfully! You can now delete this file.")