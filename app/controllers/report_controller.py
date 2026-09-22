import time
import pandas as pd
from tabulate import tabulate
from utils import clear_screen, is_valid_url as check_url
from app.services.journal_service import JournalService

def _safe_str_id(val):
    """Mengonversi ID ke format string secara aman tanpa akhiran .0."""
    if pd.isna(val) or val is None or str(val).strip() in ("", "nan", "None"):
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

class ReportController:
    def __init__(self, report_file="database/tb_report.csv", service=None):
        self.service = service if service is not None else JournalService(report_path=report_file)
        self.report_model = self.service.report_model
        self.validator_model = self.service.validator_model
        self.user_model = self.service.user_model

    def report_journal(self, user_id, full_name):
        clear_screen()
        print("\n=== Report Journal ===")

        while True:
            is_anonymous_input = input("Do you want to report as anonymous? (Y/N): ").strip().lower()
            if is_anonymous_input == "y":
                is_anonymous = True
                reporter_name = "Anonymous"
                break
            elif is_anonymous_input == "n":
                is_anonymous = False
                reporter_name = full_name
                break
            else:
                print("Invalid choice. Please enter Y or N.")

        while True:
            journal_name = input("Enter journal name: ").strip()
            if journal_name:
                break
            print("Journal name cannot be empty. Please try again.")

        while True:
            journal_url = input("Enter journal URL: ").strip()
            if self.is_valid_url(journal_url):
                break
            print("Invalid URL. Must start with http:// or https://, contain a valid domain, and have no spaces.")

        while True:
            reason = input("Enter your reason for reporting: ").strip()
            if reason:
                break
            print("Reason cannot be empty. Please try again.")

        ok, msg, new_id = self.service.submit_report(
            user_id, reporter_name, journal_name, journal_url, reason, is_anonymous
        )

        if ok:
            print("\nReport submitted successfully!")
            print("\n=== Submitted Report ===")
            display_report = {
                "report_id": new_id,
                "user_id": user_id,
                "full_name": reporter_name,
                "journal_name": journal_name,
                "journal_url": journal_url,
                "reason": reason,
                "status_laporan": "pending"
            }
            print(tabulate([list(display_report.values())], headers=list(display_report.keys()), tablefmt="grid"))
        else:
            print(f"\nFailed to submit report: {msg}")

    def track_reports(self, user_id):
        clear_screen()
        while True:
            print("\n=== Tracking Reports ===")
            try:
                user_reports = self.service.get_user_reports(user_id)
                if user_reports.empty:
                    print("You have no reports to track.")
                    return

                display_cols = [c for c in ["report_id", "journal_name", "status_laporan", "tanggal_laporan"] if c in user_reports.columns]
                print(tabulate(user_reports[display_cols], headers="keys", tablefmt="grid"))

                report_id = input("\nEnter Report ID to view details or 0 to return: ").strip()
                if report_id == "0":
                    return

                matches = user_reports[user_reports["report_id"].apply(_safe_str_id) == report_id]
                if not matches.empty:
                    selected_report = matches.iloc[0].to_dict()
                    self.view_report_details(selected_report)

                    if selected_report.get("status_laporan") == "pending":
                        edit_choice = input("\nPress 1 to edit this report or 0 to return to Tracking Reports: ").strip()
                        if edit_choice == '1':
                            self.edit_report(selected_report)
                    else:
                        print("\nThis report cannot be edited as it is not pending.")
                        input("\nPress Enter to return to Tracking Reports...")
                        clear_screen()
                else:
                    print("Invalid Report ID. Please try again.")

            except Exception as e:
                print(f"Error: {e}")
                return

    def view_report_details(self, report):
        clear_screen()
        print("\n=== Report Details ===")
        try:
            print(f"Report ID: {report.get('report_id')}")
            print(f"Journal Name: {report.get('journal_name')}")
            print(f"Journal URL: {report.get('journal_url')}")
            print(f"Reason: {report.get('reason')}")
            print(f"Status Laporan: {report.get('status_laporan')}")
            status_jurnal = report.get('status_jurnal')
            feedback = report.get('feedback')
            print(f"Status Jurnal: {status_jurnal if pd.notna(status_jurnal) and str(status_jurnal).strip() else 'N/A'}")
            print(f"Feedback: {feedback if pd.notna(feedback) and str(feedback).strip() else 'N/A'}")
            print(f"Date Submitted: {report.get('tanggal_laporan')}")

            val_id = _safe_str_id(report.get("validator_id"))
            if val_id:
                validator = self.validator_model.get_by_id("validator_id", val_id)
                if validator is not None:
                    print("\n=== Validator Information ===")
                    print(f"Validator Name: {validator.get('full_name')}")
                    print(f"Validator Email: {validator.get('email')}")
                    print(f"Validator Institution: {validator.get('instancy')}")
                    print(f"Validator Position: {validator.get('academic_position')}")
                    print(f"Scopus Profile: {validator.get('scopus_url', 'N/A')}")
                    print(f"Sinta Profile: {validator.get('sinta_url', 'N/A')}")
                    print(f"Google Scholar Profile: {validator.get('google_scholar_url', 'N/A')}")
                else:
                    print("\nNo validator information found.")
            else:
                print("\nThis report has not been assigned to a validator.")

        except Exception as e:
            print(f"Error: {e}")

    def list_pending_reports(self, validator_id):
        print("\n=== Pending Reports ===")
        try:
            pending_reports = self.service.get_pending_reports()
            if pending_reports.empty:
                print("No pending reports available.")
                input("\nPress Enter to return to the Validator Menu...")
                return

            display_cols = [c for c in ["report_id", "tanggal_laporan", "journal_name", "journal_url"] if c in pending_reports.columns]
            print(tabulate(pending_reports[display_cols], headers="keys", tablefmt="grid"))

            report_id = input("\nEnter Report ID to view details, accept, or 0 to return: ").strip()
            if report_id == "0":
                return

            matches = pending_reports[pending_reports["report_id"].apply(_safe_str_id) == report_id]
            if not matches.empty:
                self.view_pending_report_details(matches.iloc[0].to_dict(), validator_id)
            else:
                print("Report ID not found. Please try again.")

        except Exception as e:
            print(f"Error: {e}")

    def view_pending_report_details(self, report, validator_id):
        print("\n=== Pending Report Details ===")
        try:
            report_id = report["report_id"]
            reporter_name = "Anonymous" if report.get("is_anonymous") else report.get("full_name")

            print(f"Report ID: {report_id}")
            print(f"Reporter Name: {reporter_name}")
            print(f"Journal Name: {report.get('journal_name')}")
            print(f"Journal URL: {report.get('journal_url')}")
            print(f"Reason: {report.get('reason')}")
            print(f"Date Submitted: {report.get('tanggal_laporan')}")

            choice = input("\nDo you want to accept this report for review? (Y/N): ").strip().lower()
            if choice == "y":
                ok, msg = self.service.claim_report(report_id, validator_id)
                if ok:
                    print(f"Report ID {report_id} has been accepted for review.")
                else:
                    print(f"Failed to claim report: {msg}")
            else:
                print("Report was not accepted.")

            input("\nPress Enter to return to the Validator Menu...")

        except Exception as e:
            print(f"Error: {e}")

    def list_accepted_reports(self, validator_id):
        print("\n=== Accepted Reports ===")
        try:
            accepted_reports = self.service.get_validator_reports(validator_id)
            if accepted_reports.empty:
                print("You have no accepted reports.")
                input("\nPress Enter to return to the Validator Menu...")
                return

            display_cols = [c for c in ["report_id", "journal_name", "status_laporan", "tanggal_laporan"] if c in accepted_reports.columns]
            print(tabulate(accepted_reports[display_cols], headers="keys", tablefmt="grid"))

            report_id = input("\nEnter Report ID to manage or 0 to return: ").strip()
            if report_id == "0":
                return

            matches = accepted_reports[accepted_reports["report_id"].apply(_safe_str_id) == report_id]
            if not matches.empty:
                self.manage_report(matches.iloc[0].to_dict(), validator_id)
            else:
                print("Invalid Report ID. Please try again.")

        except Exception as e:
            print(f"Error: {e}")
            input("\nPress Enter to return to the Validator Menu...")

    def manage_report(self, report, validator_id):
        while True:
            updated_report = self.report_model.get_by_id("report_id", report["report_id"])
            if updated_report is None:
                print("Report not found.")
                return
            updated_dict = updated_report.to_dict()

            print("\n=== Manage Report ===")
            print(f"Report ID: {updated_dict['report_id']}")
            reporter = "Anonymous" if updated_dict.get("is_anonymous") else updated_dict.get("full_name")
            print(f"Reporter Name: {reporter}")
            print(f"Journal Name: {updated_dict.get('journal_name')}")
            print(f"Journal URL: {updated_dict.get('journal_url')}")
            print(f"Reason: {updated_dict.get('reason')}")
            print(f"Status Laporan: {updated_dict.get('status_laporan')}")
            status_jurnal = updated_dict.get('status_jurnal')
            feedback = updated_dict.get('feedback')
            print(f"Status Jurnal: {status_jurnal if pd.notna(status_jurnal) and str(status_jurnal).strip() else 'N/A'}")
            print(f"Feedback: {feedback if pd.notna(feedback) and str(feedback).strip() else 'N/A'}")
            print(f"Date Submitted: {updated_dict.get('tanggal_laporan')}")

            print("\nOptions:")
            if updated_dict.get("status_laporan") == "review":
                print("1. Validate Report")
                print("2. Mark as Pending")
            elif updated_dict.get("status_laporan") == "done":
                print("1. Update Report")
            print("3. Return to Accepted Reports")

            choice = input("Choose an option: ").strip()

            if choice == "1":
                if updated_dict.get("status_laporan") == "review":
                    self.validate_report(updated_dict)
                    return
                elif updated_dict.get("status_laporan") == "done":
                    self.update_report(updated_dict)
                    return
            elif choice == "2" and updated_dict.get("status_laporan") == "review":
                self.mark_as_pending(updated_dict)
                return
            elif choice == "3":
                return
            else:
                print("Invalid choice. Please try again.")

    def validate_report(self, report):
        print("\n=== Validate Report ===")
        print("Options: aman, predator, clone")
        new_status = input("Enter new journal status: ").strip().lower()
        if new_status not in ["aman", "predator", "clone"]:
            print("Invalid status. Please choose from aman, predator, or clone.")
            return

        new_feedback = input("Enter your feedback: ").strip()

        ok, msg = self.service.validate_report(report["report_id"], new_status, new_feedback)
        if ok:
            print("Report validated successfully. The status has been updated to 'done'.")
        else:
            print(f"Failed to validate report: {msg}")
        input("\nPress Enter to return to Accepted Reports...")

    def update_report(self, report):
        print("\n=== Update Report ===")
        current_status = report.get("status_jurnal")
        print(f"Report ID: {report['report_id']}")
        print(f"Current Journal Status: {current_status if pd.notna(current_status) and str(current_status).strip() else 'N/A'}")

        new_status = input("Enter new journal status (aman, predator, clone): ").strip().lower()
        if new_status not in ["aman", "predator", "clone"]:
            print("Invalid status. Please choose from aman, predator, or clone.")
            return

        new_feedback = input("Enter new feedback: ").strip()

        ok, msg = self.service.validate_report(report["report_id"], new_status, new_feedback)
        if ok:
            print("Report updated successfully.")
        else:
            print(f"Failed to update report: {msg}")

    def mark_as_pending(self, report):
        print("\n=== Mark as Pending ===")
        confirm = input("Are you sure you want to mark this report as pending? (Y/N): ").strip().lower()
        if confirm != "y":
            print("Operation canceled.")
            return

        ok, msg = self.service.mark_as_pending(report["report_id"])
        if ok:
            print("Report marked as pending.")
        else:
            print(f"Failed: {msg}")
        input("\nPress Enter to return to Validator Menu...")

    def edit_report(self, report):
        clear_screen()
        print("\n=== Edit Report ===")
        print(f"Current Journal Name: {report.get('journal_name')}")
        print(f"Current Journal URL: {report.get('journal_url')}")
        print(f"Current Reason: {report.get('reason')}")
        print("\nOptions:")
        print("1. Edit Report")
        print("2. Delete Report")
        print("0. Return to Tracking Reports")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            new_journal_name = input("Enter new journal name (leave blank to keep current): ").strip()

            while True:
                new_journal_url = input("Enter new journal URL (leave blank to keep current): ").strip()
                if not new_journal_url:
                    break
                elif not self.is_valid_url(new_journal_url):
                    print("Invalid URL. Must start with http:// or https://, contain a valid domain, and have no spaces.")
                else:
                    break

            new_reason = input("Enter new reason (leave blank to keep current): ").strip()

            ok, msg = self.service.update_report(
                report["report_id"], new_journal_name, new_journal_url, new_reason
            )
            if ok:
                print("Report updated successfully. Redirecting...")
            else:
                print(f"Update info: {msg}")
            time.sleep(1)

        elif choice == "2":
            confirm = input("Are you sure you want to delete this report? (Y/N): ").strip().lower()
            if confirm == "y":
                ok, msg = self.service.delete_report(report["report_id"])
                if ok:
                    print("Report deleted successfully. Redirecting...")
                else:
                    print(f"Deletion failed: {msg}")
                time.sleep(1)
            else:
                print("Deletion canceled.")

    def view_user_statistics(self, user_id):
        try:
            stats = self.service.get_user_stats(user_id)
            print("=== Your Report Statistics ===")
            print(f"Total Laporan: {stats['total']}")
            print(f"Laporan Pending: {stats['pending']}")
            print(f"Laporan Review: {stats['review']}")
            print(f"Laporan Sukses: {stats['done']}")
        except Exception as e:
            print(f"Error: {e}")

    def show_validator_statistics(self, validator_id):
        print("\n=== Validator Statistics ===")
        try:
            stats = self.service.get_validator_stats(validator_id)
            print(f"Total Laporan Tersedia: {stats['available_pending']}")
            print(f"Laporan yang Sedang Direview: {stats['review']}")
            print(f"Laporan yang Sudah Selesai: {stats['done']}")
            print(f"Total Laporan Ditangani: {stats['total_handled']}")
        except Exception as e:
            print(f"Error: {e}")

    def is_valid_url(self, url):
        return check_url(url)
