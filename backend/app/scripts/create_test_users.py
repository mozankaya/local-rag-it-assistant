from app.core.security import get_password_hash
from app.db.database import Base, SessionLocal, engine
from app.models.user import User


TEST_USERS = [
    {
        "email": "admin@izeltas.local",
        "full_name": "Admin User",
        "password": "Admin123!",
        "role": "admin",
    },
    {
        "email": "user@izeltas.local",
        "full_name": "Test User",
        "password": "User123!",
        "role": "user",
    },
]


def create_or_update_user(
    email: str,
    full_name: str,
    password: str,
    role: str,
) -> None:
    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.email == email).first()

        if existing_user:
            existing_user.full_name = full_name
            existing_user.hashed_password = get_password_hash(password)
            existing_user.role = role
            existing_user.is_active = True
        else:
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(password),
                role=role,
                is_active=True,
            )

            db.add(user)

        db.commit()

    finally:
        db.close()


def main() -> None:
    Base.metadata.create_all(bind=engine)

    for user_data in TEST_USERS:
        create_or_update_user(**user_data)

    print("Test users created successfully.")
    print("Admin: admin@izeltas.local / Admin123!")
    print("User : user@izeltas.local / User123!")


if __name__ == "__main__":
    main()