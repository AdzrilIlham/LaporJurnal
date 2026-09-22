from utils import clear_screen

def show_main_menu():
    clear_screen()
    print("\n=== Main Menu ===")
    print("1. Login")
    print("2. Register")
    print("3. Check Journal URL")
    print("4. Exit")

def show_user_menu():
    clear_screen()
    print("\n=== User Menu ===")
    print("1. Report Journal")
    print("2. Track Reports")
    print("3. Settings") 
    print("4. Logout")

def show_validator_menu():
    clear_screen()
    print("\n=== Validator Menu ===")
    print("1. View Pending Reports")
    print("2. View Accepted Reports")
    print("3. Logout")

def show_admin_menu():
    clear_screen()
    print("\n=== Admin Menu ===")
    print("1. Register Validator")
    print("2. View All Reports")  
    print("3. View All Users")    
    print("4. View All Validators") 
    print("5. Logout")
