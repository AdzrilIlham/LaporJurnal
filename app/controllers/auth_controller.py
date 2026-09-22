import time
from utils import (
    clear_screen,
    get_password_input,
    is_valid_username as check_username,
    is_valid_password as check_password,
    is_valid_email as check_email,
    get_valid_url as check_url
)
from app.services.journal_service import JournalService

class AuthController:
    def __init__(self, service=None):
        self.service = service if service is not None else JournalService()
        self.current_user = None
        # Expose models for compatibility with existing tests
        self.user_model = self.service.user_model
        self.validator_model = self.service.validator_model
        self.admin_model = self.service.admin_model

    def login(self):
        print("\n=== Login ===")
        while True:
            username = input("Enter username (or 0 to cancel): ").strip()
            if username == "0":
                return None
            password = get_password_input("Enter password: ")

            role, user_data = self.service.authenticate(username, password)
            if role:
                self.current_user = user_data
                display_name = user_data.get("full_name") or user_data.get("username", username)
                print(f"Login successful! Welcome, {display_name} ({role.capitalize()}). Redirecting...")
                time.sleep(1)
                return role
            else:
                print(f"{user_data} Please try again.")

    def register_user(self):
        clear_screen()
        print("\n=== Register User ===")

        while True:
            username = input("Enter username: ").strip()
            if not self.is_valid_username(username):
                print("Username must be at least 8 characters and can only contain letters, numbers, '_', and '.'.")
                continue

            user_df = self.user_model.read_data()
            if not user_df.empty and "username" in user_df.columns:
                if not user_df[user_df["username"] == username].empty:
                    print("Username already exists. Please choose another one.")
                    continue
            break

        while True:
            password = get_password_input("Enter password: ")
            if not self.is_valid_password(password):
                print("Password must be at least 8 characters.")
                continue
            break

        while True:
            full_name = input("Enter full name: ").strip()
            if not full_name:
                print("Full name cannot be empty. Please try again.")
                continue
            break

        while True:
            email = input("Enter email: ").strip()
            if not self.is_valid_email(email):
                print("Invalid email format. Please try again.")
                continue
            user_df = self.user_model.read_data()
            if not user_df.empty and "email" in user_df.columns:
                if not user_df[user_df["email"] == email].empty:
                    print("Email already exists. Please choose another one.")
                    continue
            break

        instancy = input("Enter instancy: ").strip()

        ok, msg = self.service.register_user(username, password, full_name, email, instancy)
        if ok:
            print("Registration successful!")
        else:
            print(f"Registration failed: {msg}")

    def register_validator(self):
        clear_screen()
        print("\n=== Register Validator ===")

        while True:
            username = input("Enter username: ").strip()
            if not self.is_valid_username(username):
                print("Username must be at least 8 characters and can only contain letters, numbers, '_', and '.'.")
                continue
            val_df = self.validator_model.read_data()
            if not val_df.empty and "username" in val_df.columns:
                if not val_df[val_df["username"] == username].empty:
                    print("Username already exists. Please choose another one.")
                    continue
            break

        while True:
            password = get_password_input("Enter password: ")
            if not self.is_valid_password(password):
                print("Password must be at least 8 characters.")
                continue
            break

        while True:
            full_name = input("Enter full name: ").strip()
            if not full_name:
                print("Full name cannot be empty. Please try again.")
            else:
                break

        while True:
            email = input("Enter email: ").strip()
            if not self.is_valid_email(email):
                print("Invalid email format. Please try again.")
                continue
            val_df = self.validator_model.read_data()
            if not val_df.empty and "email" in val_df.columns:
                if not val_df[val_df["email"] == email].empty:
                    print("Email already exists. Please choose another one.")
                    continue
            break

        while True:
            instancy = input("Enter instancy: ").strip()
            if not instancy:
                print("Instancy cannot be empty. Please try again.")
            else:
                break

        while True:
            academic_position = input("Enter academic position: ").strip()
            if not academic_position:
                print("Academic position cannot be empty. Please try again.")
            else:
                break

        scopus_url = self.get_valid_url("Scopus", "")
        sinta_url = self.get_valid_url("Sinta", "")
        google_scholar_url = self.get_valid_url("Google Scholar", "")

        ok, msg = self.service.register_validator(
            username, password, full_name, email, instancy,
            academic_position, scopus_url, sinta_url, google_scholar_url
        )
        if ok:
            print("Validator registration successful!")
        else:
            print(f"Validator registration failed: {msg}")

    def user_settings(self):
        if not self.current_user:
            print("You must be logged in to access settings.")
            return

        clear_screen()
        while True:
            print("\n=== User Settings ===")
            print("1. Edit Profile Information")
            print("2. Change Password")
            print("3. Return to User Menu")
            choice = input("Choose an option: ").strip()

            if choice == "1":
                self.edit_profile()
            elif choice == "2":
                self.change_password()
            elif choice == "3":
                break
            else:
                print("Invalid choice. Please try again.")

    def edit_profile(self):
        print("\n=== Edit Profile ===")
        user_id = self.current_user["user_id"]
        user = self.user_model.get_by_id("user_id", user_id)
        if user is None:
            print("User not found.")
            return

        print(f"Current Full Name: {user['full_name']}")
        print(f"Current Email: {user['email']}")
        print(f"Current Instancy: {user['instancy']}")

        new_full_name = input("Enter new full name (leave blank to keep current): ").strip()

        while True:
            new_email = input("Enter new email (leave blank to keep current): ").strip()
            if new_email:
                if not self.is_valid_email(new_email):
                    print("Invalid email format. Please enter a valid email address.")
                else:
                    break
            else:
                break

        new_instancy = input("Enter new instancy (leave blank to keep current): ").strip()

        ok, msg = self.service.update_user_profile(user_id, new_full_name, new_email, new_instancy)
        if ok:
            if new_full_name:
                self.current_user["full_name"] = new_full_name
            if new_email:
                self.current_user["email"] = new_email
            if new_instancy:
                self.current_user["instancy"] = new_instancy
            print("Profile updated successfully.")
        else:
            print(f"Update info: {msg}")

    def change_password(self):
        print("\n=== Change Password ===")
        user_id = self.current_user["user_id"]
        old_password = get_password_input("Enter your current password: ")

        while True:
            new_password = get_password_input("Enter new password: ")
            if self.is_valid_password(new_password):
                break
            else:
                print("Password must be at least 8 characters.")

        ok, msg = self.service.change_user_password(user_id, old_password, new_password)
        if ok:
            print("Password changed successfully.")
        else:
            print(f"Password change failed: {msg}")

    def is_valid_username(self, username):
        return check_username(username)

    def is_valid_password(self, password):
        return check_password(password)

    def is_valid_email(self, email):
        return check_email(email)

    def get_current_user_id(self):
        if self.current_user:
            return self.current_user.get("user_id")
        return None

    def get_valid_url(self, url_type, current_url):
        return check_url(url_type, current_url)
