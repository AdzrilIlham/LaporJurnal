import pandas as pd
from utils import clear_screen, hash_password, get_password_input
from app.controllers.auth_controller import AuthController
from app.services.journal_service import JournalService
from tabulate import tabulate

def _safe_str_id(val):
    if pd.isna(val) or val is None or str(val).strip() in ("", "nan", "None"):
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

class AdminController:
    def __init__(self, service=None):
        self.service = service if service is not None else JournalService()
        self.report_model = self.service.report_model
        self.user_model = self.service.user_model
        self.validator_model = self.service.validator_model
        self.auth_controller = AuthController(service=self.service)

    def view_statistics(self):
        try:
            stats = self.service.get_system_stats()
            print("=== Statistics ===")
            print(f"Total Laporan: {stats['total_reports']}")
            print(f"Jumlah User: {stats['total_users']}")
            print(f"Jumlah Validator: {stats['total_validators']}")
            print(f"Laporan Pending: {stats['pending_reports']}")
            print(f"Laporan Review: {stats['review_reports']}")
            print(f"Laporan Sukses: {stats['done_reports']}")
        except Exception as e:
            print(f"Error: {e}")

    def view_all_reports(self):
        clear_screen()
        while True:
            print("\n=== All Reports ===")
            try:
                report_data = self.service.get_all_reports()
                if report_data.empty:
                    print("No reports found.")
                    return
                else:
                    display_cols = [c for c in ["report_id", "journal_name", "journal_url", "status_laporan"] if c in report_data.columns]
                    print(tabulate(report_data[display_cols], headers="keys", tablefmt="fancy_grid"))

                    while True:
                        report_id = input("\nEnter Report ID to view details or 0 to return: ").strip()
                        if report_id == "0":
                            return
                        elif report_id.isdigit():
                            report_id_num = int(report_id)
                            if report_id_num in report_data["report_id"].values:
                                self.view_report_details(report_id_num)
                                break
                            else:
                                print("Report ID not found. Please try again.")
                        else:
                            print("Invalid input. Please enter a valid Report ID or 0 to return.")
            except Exception as e:
                print(f"Error: {e}")

    def view_report_details(self, report_id):
        try:
            report = self.report_model.get_by_id("report_id", report_id)
            if report is None:
                print("Report not found.")
                return

            user_id = _safe_str_id(report.get("user_id", ""))
            val_id = _safe_str_id(report.get("validator_id", ""))

            user = self.user_model.get_by_id("user_id", user_id) if user_id else None
            validator = self.validator_model.get_by_id("validator_id", val_id) if val_id else None

            print("\n=== Report Details ===")
            print(f"Report ID: {report['report_id']}")
            print(f"Date Submitted: {report['tanggal_laporan']}")
            print(f"Journal Name: {report['journal_name']}")
            print(f"Journal URL: {report['journal_url']}")
            print(f"Nama Pelapor: {user['full_name'] if user is not None else report.get('full_name', 'N/A')}")
            print(f"Instansi Pelapor: {user['instancy'] if user is not None else 'N/A'}")
            print(f"Reason: {report['reason']}")

            print("\n=== Review Result ===")
            if validator is not None:
                print(f"Nama Validator: {validator['full_name']}")
                print(f"Instansi Validator: {validator['instancy']}")
                print("Profile Validator:")
                if pd.notna(validator.get('scopus_url')):
                    print(f"- {validator['scopus_url']}")
                if pd.notna(validator.get('sinta_url')):
                    print(f"- {validator['sinta_url']}")
                if pd.notna(validator.get('google_scholar_url')):
                    print(f"- {validator['google_scholar_url']}")
            else:
                print("Nama Validator: N/A")
                print("Instansi Validator: N/A")
                print("Profile Validator: N/A")

            print(f"Status Laporan: {report['status_laporan']}")
            print(f"Status Jurnal: {report['status_jurnal'] if not pd.isna(report['status_jurnal']) else 'N/A'}")
            print(f"Feedback: {report['feedback'] if not pd.isna(report['feedback']) else 'N/A'}")

            while True:
                choice = input("\nPress 0 to return to the report list: ").strip()
                if choice == "0":
                    return
                else:
                    print("Invalid input. Please press 0 to return.")
        except Exception as e:
            print(f"Error: {e}")

    def view_all_users(self):
        clear_screen()
        print("\n=== All Users ===")
        try:
            user_data = self.service.get_all_users()
            if user_data.empty:
                print("No users found.")
                return
            else:
                display_cols = [c for c in ["user_id", "full_name", "instancy"] if c in user_data.columns]
                print(tabulate(user_data[display_cols], headers="keys", tablefmt="fancy_grid"))

                while True:
                    user_id = input("\nEnter User ID to view details, delete, or 0 to return: ").strip()
                    if not user_id.isdigit():
                        print("Invalid input. Please enter a valid User ID (number) or 0 to return.")
                        continue

                    user_id_num = int(user_id)
                    if user_id_num == 0:
                        return
                    elif user_id_num in user_data["user_id"].values:
                        self.view_user_details(user_id_num)
                        break
                    else:
                        print("User ID not found. Please try again.")
        except Exception as e:
            print(f"Error: {e}")

    def view_user_details(self, user_id):
        clear_screen()
        try:
            user = self.user_model.get_by_id("user_id", user_id)
            if user is None:
                print("User not found.")
                return

            print("\n=== User Details ===")
            print(f"User ID: {user['user_id']}")
            print(f"Username: {user['username']}")
            print(f"Full Name: {user['full_name']}")
            print(f"Email: {user['email']}")
            print("Password: ******** [Protected]")
            print(f"Instancy: {user['instancy']}")
            print(f"Role: {user['role']}")

            while True:
                print("\nOptions:")
                print("1. Delete User")
                print("2. Return to User List")
                choice = input("Choose an option: ").strip()

                if choice == "1":
                    self.delete_user(user_id)
                    break
                elif choice == "2":
                    self.view_all_users()
                    return
                else:
                    print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"Error: {e}")

    def view_all_validators(self):
        clear_screen()
        print("\n=== All Validators ===")
        try:
            validator_data = self.service.get_all_validators()
            if validator_data.empty:
                print("No validators found.")
                return
            else:
                display_cols = [c for c in ["validator_id", "full_name", "instancy"] if c in validator_data.columns]
                print(tabulate(validator_data[display_cols], headers="keys", tablefmt="fancy_grid"))

                while True:
                    val_id = input("\nEnter Validator ID to view details, delete, or 0 to return: ").strip()
                    if not val_id.isdigit():
                        print("Invalid input. Please enter a valid Validator ID (number) or 0 to return.")
                        continue

                    val_id_num = int(val_id)
                    if val_id_num == 0:
                        return
                    elif val_id_num in validator_data["validator_id"].values:
                        self.view_validator_details(val_id_num)
                        break
                    else:
                        print("Validator ID not found. Please try again.")
        except Exception as e:
            print(f"Error: {e}")

    def view_validator_details(self, validator_id):
        try:
            validator = self.validator_model.get_by_id("validator_id", validator_id)
            if validator is None:
                print("Validator not found.")
                return

            print("\n=== Validator Details ===")
            print(f"Validator ID: {validator['validator_id']}")
            print(f"Username: {validator['username']}")
            print(f"Full Name: {validator['full_name']}")
            print(f"Email: {validator['email']}")
            print("Password: ******** [Protected]")
            print(f"Instancy: {validator['instancy']}")
            print(f"Academic Position: {validator['academic_position']}")
            print(f"Scopus URL: {validator['scopus_url']}")
            print(f"Sinta URL: {validator['sinta_url']}")
            print(f"Google Scholar URL: {validator['google_scholar_url']}")

            while True:
                print("\nOptions:")
                print("1. Edit Information Validator")
                print("2. Edit Password Validator")
                print("3. Delete Validator")
                print("4. Return to Validator List")
                choice = input("Choose an option: ").strip()

                if choice == "1":
                    self.edit_validator_information(validator_id)
                    return
                elif choice == "2":
                    self.edit_validator_password(validator_id)
                    return
                elif choice == "3":
                    self.delete_validator(validator_id)
                    return
                elif choice == "4":
                    self.view_all_validators()
                    return
                else:
                    print("Invalid choice. Please try again.")
        except Exception as e:
            print(f"Error: {e}")

    def edit_validator_information(self, validator_id):
        try:
            validator = self.validator_model.get_by_id("validator_id", validator_id)
            if validator is None:
                print("Validator not found.")
                return

            print("\n=== Edit Validator ===")
            print(f"Validator ID: {validator['validator_id']} (Cannot be changed)")

            new_full_name = input(f"Enter new full name (current: {validator['full_name']}): ").strip() or validator['full_name']

            while True:
                new_email = input(f"Enter new email (current: {validator['email']}): ").strip()
                if new_email:
                    if not self.auth_controller.is_valid_email(new_email):
                        print("Invalid email format. Please enter a valid email address.")
                    else:
                        break
                else:
                    new_email = validator['email']
                    break

            new_instancy = input(f"Enter new instancy (current: {validator['instancy']}): ").strip() or validator['instancy']
            new_pos = input(f"Enter new academic position (current: {validator['academic_position']}): ").strip() or validator['academic_position']

            scopus_url = validator.get('scopus_url', '')
            sinta_url = validator.get('sinta_url', '')
            scholar_url = validator.get('google_scholar_url', '')

            while True:
                print("\nDo you want to edit URLs?")
                print("1. Edit Scopus URL")
                print("2. Edit Sinta URL")
                print("3. Edit Google Scholar URL")
                print("4. Skip URL editing")
                url_choice = input("Choose an option: ").strip()

                if url_choice == "1":
                    scopus_url = self.auth_controller.get_valid_url("Scopus", scopus_url)
                elif url_choice == "2":
                    sinta_url = self.auth_controller.get_valid_url("Sinta", sinta_url)
                elif url_choice == "3":
                    scholar_url = self.auth_controller.get_valid_url("Google Scholar", scholar_url)
                elif url_choice == "4":
                    break
                else:
                    print("Invalid choice. Please try again.")

            ok, msg = self.service.update_validator_info(
                validator_id, new_full_name, new_email, new_instancy, new_pos,
                scopus_url, sinta_url, scholar_url
            )
            if ok:
                print("Validator information has been updated successfully.")
            else:
                print(f"Update failed: {msg}")

        except Exception as e:
            print(f"Error: {e}")

    def edit_validator_password(self, validator_id):
        try:
            print("\n=== Edit Validator Password ===")
            while True:
                new_password = get_password_input("Enter new password: ")
                if self.auth_controller.is_valid_password(new_password):
                    break
                else:
                    print("Invalid password. Password must be at least 8 characters long.")

            ok, msg = self.service.change_validator_password(validator_id, new_password)
            if ok:
                print("Validator password updated successfully.")
            else:
                print(f"Failed to update password: {msg}")
        except Exception as e:
            print(f"Error: {e}")

    def delete_validator(self, validator_id):
        try:
            self.service.delete_validator(validator_id)
            print(f"Validator with ID {validator_id} has been deleted successfully.")
        except Exception as e:
            print(f"Error deleting validator: {e}")

    def delete_user(self, user_id):
        try:
            self.service.delete_user(user_id)
            print(f"User with ID {user_id} has been deleted successfully.")
        except Exception as e:
            print(f"Error deleting user: {e}")
