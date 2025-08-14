from app import app, db, User  # Make sure to import app too!

def list_users():
    users = User.query.all()
    
    if not users:
        print("No users found in the database.")
        return

    print(f"{'ID':<5} {'Name':<20} {'Email'}")
    print("-" * 50)
    for user in users:
        print(f"{user.id:<5} {user.name:<20} {user.email}")

if __name__ == '__main__':
    with app.app_context():  # ✅ use app, not db.app
        list_users()
