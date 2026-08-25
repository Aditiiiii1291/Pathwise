import sys
import getpass
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, init_db
from app.models.user import User, UserRoleEnum
from app.services.auth import AuthService
from app.schemas.auth import UserCreate
from app.core.security import validate_username, validate_password_strength, normalize_username


def main():
    print("=" * 60)
    print("  PATHWISE — Initial Administrator Setup Script")
    print("=" * 60)

    init_db()
    db = SessionLocal()

    try:
        # 1. Prompt for Username
        while True:
            username = input("\nEnter admin username (3-30 chars): ").strip()
            valid_user, err_msg = validate_username(username)
            if not valid_user:
                print(f"  [!] Error: {err_msg}")
                continue

            available, avail_msg = AuthService.check_username_availability(db, username)
            if not available:
                print(f"  [!] Error: {avail_msg}")
                continue

            print(f"  [+] Username '{normalize_username(username)}' is available.")
            break

        # 2. Prompt for Display Name
        while True:
            display_name = input("Enter display name (e.g. Administrator): ").strip()
            if not display_name:
                print("  [!] Display name cannot be empty.")
                continue
            break

        # 3. Prompt for Password
        print("\nPassword Requirements:")
        print("  - At least 8 characters")
        print("  - At least one uppercase letter (A-Z)")
        print("  - At least one lowercase letter (a-z)")
        print("  - At least one number (0-9)")

        while True:
            password = getpass.getpass("\nEnter password: ")
            valid_pwd, pwd_errors = validate_password_strength(password)
            if not valid_pwd:
                for err in pwd_errors:
                    print(f"  [!] {err}")
                continue

            confirm_pwd = getpass.getpass("Confirm password: ")
            if password != confirm_pwd:
                print("  [!] Error: Passwords do not match.")
                continue

            break

        # 4. Create Admin Account
        payload = UserCreate(
            username=username,
            password=password,
            display_name=display_name,
            role=UserRoleEnum.ADMIN.value,
        )

        user = AuthService.create_user(db, payload)
        print("\n" + "=" * 60)
        print(f"  SUCCESS: Administrator account '{user.username}' created successfully!")
        print(f"  Role: {user.role} | ID: {user.id} | Name: {user.display_name}")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n[!] Failed to create administrator account: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
