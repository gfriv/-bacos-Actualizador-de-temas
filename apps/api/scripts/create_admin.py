import argparse

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import User, UserRole
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update an initial admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", default="Administrador Abacos")
    args = parser.parse_args()

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email))
        if user is None:
            user = User(
                email=args.email,
                password_hash=hash_password(args.password),
                full_name=args.full_name,
                role=UserRole.admin,
            )
            db.add(user)
        else:
            user.password_hash = hash_password(args.password)
            user.full_name = args.full_name
            user.role = UserRole.admin
        db.commit()

    print(f"Admin ready: {args.email}")


if __name__ == "__main__":
    main()
