from app.controllers.auth_controller import AuthController
from app.controllers.report_controller import ReportController
from app.controllers.admin_controller import AdminController
from app.controllers.check_controller import CheckController
from app.views.auth_view import show_main_menu, show_user_menu, show_validator_menu, show_admin_menu
from utils import clear_screen
import time

def user_menu(auth, report_controller):
    while True:
        user_id = auth.get_current_user_id()

        # Statistik + menu user
        report_controller.view_user_statistics(user_id)
        show_user_menu()
        
        choice = input("Choose an option: ").strip()

        if choice == "1":
            full_name = auth.current_user["full_name"]
            report_controller.report_journal(user_id, full_name)
            input("\nPress Enter to return to the user menu...")
        elif choice == "2":
            report_controller.track_reports(user_id)
            input("\nPress Enter to return to the user menu...")
        elif choice == "3":  # Opsi Settings
            auth.user_settings()  # Panggil fungsi user_settings dari AuthController
            input("\nPress Enter to return to the user menu...")
        elif choice == "4":  # Opsi Logout
            print("Logging out...")
            time.sleep(2)
            break
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

def validator_menu(auth, report_controller):
    validator_id = auth.current_user.get("validator_id") #ambil validator_id yang sedang login
    while True:        
        # statistik + menu validator
        report_controller.show_validator_statistics(validator_id)
        show_validator_menu()
        
        choice = input("Choose an option: ").strip()

        if choice == "1":
            clear_screen()
            report_controller.list_pending_reports(validator_id)
        elif choice == "2":
            clear_screen()
            report_controller.list_accepted_reports(validator_id)
        elif choice == "3":
            print("Logging out...")
            time.sleep(2)
            break
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

def admin_menu(auth):
    admin_controller = AdminController()  # AdminController init
    while True:
        
        clear_screen()
        # statistik + admin menu
        admin_controller.view_statistics()
        show_admin_menu()
        
        choice = input("Choose an option: ").strip()

        if choice == "1":
            auth.register_validator()
            input("\nPress Enter to return to the admin menu...")
        elif choice == "2":
            admin_controller.view_all_reports() 
            input("\nPress Enter to return to the admin menu...")
        elif choice == "3":
            admin_controller.view_all_users()  
            input("\nPress Enter to return to the admin menu...")
        elif choice == "4":
            admin_controller.view_all_validators() 
            input("\nPress Enter to return to the admin menu...")
        elif choice == "5":
            print("Logging out...")
            time.sleep(2)
            break
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

def main():
    auth = AuthController()
    report_controller = ReportController("database/tb_report.csv")
    check_controller = CheckController("database/tb_report.csv") 

    while True:
        clear_screen()
        show_main_menu()
        choice = input("Choose an option: ")

        if choice == "1": # Login
            clear_screen()
            role = auth.login()
            if role == "user":
                user_menu(auth, report_controller)
            elif role == "validator":
                validator_menu(auth, report_controller)
            elif role == "admin":
                admin_menu(auth)
        elif choice == "2":  # Register User
            auth.register_user()
            input("\nPress Enter to return to the main menu...")
        elif choice == "3":  # Check Journal URL
            journal_url = input("Enter the journal URL to check: ").strip()
            check_controller.check_journal_url(journal_url)  # Panggil fungsi untuk memeriksa URL
            input("\nPress Enter to return to the main menu...")
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")
            input("\nPress Enter to try again...")

if __name__ == "__main__":
    main()
