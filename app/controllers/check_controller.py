import pandas as pd
from utils import clear_screen, is_valid_url
from app.services.journal_service import JournalService
from tabulate import tabulate

class CheckController:
    def __init__(self, report_file="database/tb_report.csv", service=None):
        self.service = service if service is not None else JournalService(report_path=report_file)
        # Expose models for compatibility with tests
        self.report_model = self.service.report_model
        self.user_model = self.service.user_model
        self.validator_model = self.service.validator_model

    def check_journal_url(self, journal_url):
        clear_screen()
        if not is_valid_url(journal_url) and not journal_url.startswith("http"):
            print("Error: Please enter a valid URL starting with 'http://' or 'https://'.")
            return

        try:
            results = self.service.check_journal_url(journal_url)
            if not results:
                print("Journal information not found for the provided URL.")
                return

            print("\n=== Reports with the Same URL ===")
            display_rows = []
            for item in results:
                display_rows.append({
                    "report_id": item.get("report_id"),
                    "full_name": item.get("full_name"),
                    "status_laporan": item.get("status_laporan"),
                    "tanggal_laporan": item.get("tanggal_laporan")
                })
            print(tabulate(display_rows, headers="keys", tablefmt="grid"))

            while True:
                report_id = input("\nEnter Report ID to view details or 0 to return: ").strip()
                if report_id == "0":
                    return

                matched_item = next((it for it in results if str(it.get("report_id")) == report_id), None)
                if matched_item:
                    self.display_report_details(matched_item)
                    break
                else:
                    print("Invalid Report ID. Please try again.")

        except Exception as e:
            print(f"Error: {e}")

    def display_report_details(self, report):
        """Menampilkan detail laporan yang dipilih sesuai format."""
        try:
            user_id = str(report.get("user_id", "")).split(".")[0]
            val_info = report.get("validator_info")
            if val_info is None:
                val_id_raw = report.get("validator_id", "")
                val_id = str(val_id_raw).split(".")[0] if pd.notna(val_id_raw) and str(val_id_raw).strip() != "" else None
                validator = self.validator_model.get_by_id("validator_id", val_id) if val_id else None
            else:
                validator = val_info

            user = self.user_model.get_by_id("user_id", user_id) if user_id else None

            print("\n=== Report Details ===")
            print(f"Report ID: {report.get('report_id', 'N/A')}")
            print(f"Date Submitted: {report.get('tanggal_laporan', 'N/A')}")
            print(f"Journal Name: {report.get('journal_name', 'N/A')}")
            print(f"Journal URL: {report.get('journal_url', 'N/A')}")

            if user is not None:
                print(f"Nama Pelapor: {user.get('full_name', 'N/A')}")
                print(f"Instansi Pelapor: {user.get('instancy', 'N/A')}")
            else:
                print(f"Nama Pelapor: {report.get('full_name', 'N/A')}")
                print("Instansi Pelapor: N/A")

            print(f"Reason: {report.get('reason', 'N/A')}")

            print("\n=== Review Result ===")
            if validator is not None:
                print(f"Nama Validator: {validator.get('full_name', 'N/A')}")
                print(f"Instansi Validator: {validator.get('instancy', 'N/A')}")
                print("Profile Validator:")
                if pd.notna(validator.get('scopus_url')) and validator.get('scopus_url'):
                    print(f"- {validator.get('scopus_url')}")
                if pd.notna(validator.get('sinta_url')) and validator.get('sinta_url'):
                    print(f"- {validator.get('sinta_url')}")
                if pd.notna(validator.get('google_scholar_url')) and validator.get('google_scholar_url'):
                    print(f"- {validator.get('google_scholar_url')}")
            else:
                print("Nama Validator: N/A")
                print("Instansi Validator: N/A")
                print("Profile Validator: N/A")

            status_jurnal = report.get("status_jurnal")
            feedback = report.get("feedback")
            print(f"Status Laporan: {report.get('status_laporan', 'N/A')}")
            print(f"Status Jurnal: {status_jurnal if pd.notna(status_jurnal) and str(status_jurnal).strip() else 'N/A'}")
            print(f"Feedback: {feedback if pd.notna(feedback) and str(feedback).strip() else 'N/A'}")

        except Exception as e:
            print(f"Error displaying report details: {e}")
