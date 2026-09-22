import unittest
import os
import tempfile
import threading
import pandas as pd
from utils import (
    hash_password,
    verify_password,
    is_valid_username,
    is_valid_password,
    is_valid_email,
    is_valid_url,
    normalize_url
)
from app.models.CSVModel import CSVModel
from app.controllers.auth_controller import AuthController
from app.controllers.report_controller import ReportController, _safe_str_id
from app.controllers.admin_controller import AdminController
from app.controllers.check_controller import CheckController
from app.services.journal_service import JournalService

class TestUtils(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        pwd = "SecretPassword123!"
        hashed = hash_password(pwd)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_legacy_plaintext_verification(self):
        plain = "myPlaintextPass"
        self.assertTrue(verify_password(plain, plain))
        self.assertFalse(verify_password("otherPass", plain))

    def test_username_validation(self):
        self.assertTrue(is_valid_username("valid_user.1"))
        self.assertTrue(is_valid_username("administrator"))
        self.assertFalse(is_valid_username("short"))  # < 8
        self.assertFalse(is_valid_username("invalid user"))  # space
        self.assertFalse(is_valid_username("user@name"))  # invalid char

    def test_password_validation(self):
        self.assertTrue(is_valid_password("12345678"))
        self.assertFalse(is_valid_password("1234567"))  # < 8

    def test_email_validation(self):
        self.assertTrue(is_valid_email("user@example.com"))
        self.assertTrue(is_valid_email("test.user+tag@domain.co.id"))
        self.assertFalse(is_valid_email("invalid-email"))
        self.assertFalse(is_valid_email("user@.com"))

    def test_url_validation(self):
        self.assertTrue(is_valid_url("https://journal.example.com/article"))
        self.assertTrue(is_valid_url("http://example.org"))
        self.assertFalse(is_valid_url("ftp://example.com"))
        self.assertFalse(is_valid_url("https://example .com"))
        self.assertFalse(is_valid_url("http://a.b"))  # < 10 chars

    def test_normalize_url(self):
        self.assertEqual(normalize_url("https://www.example.com/"), "example.com")
        self.assertEqual(normalize_url("http://example.com"), "example.com")
        self.assertEqual(normalize_url("https://example.com/path/"), "example.com/path")
        self.assertEqual(normalize_url(""), "")

    def test_safe_str_id(self):
        self.assertEqual(_safe_str_id(1.0), "1")
        self.assertEqual(_safe_str_id("2.0"), "2")
        self.assertEqual(_safe_str_id(3), "3")
        self.assertEqual(_safe_str_id(None), "")
        self.assertEqual(_safe_str_id("nan"), "")

class TestCSVModel(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        self.temp_file.close()
        self.model = CSVModel(self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
        lock_file = f"{self.temp_file.name}.lock"
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except Exception:
                pass

    def test_crud_operations(self):
        # Insert
        row1 = {"id": 1, "name": "Journal A", "status": "pending"}
        row2 = {"id": 2, "name": "Journal B", "status": "done"}
        self.model.insert_row(row1)
        self.model.insert_row(row2)

        data = self.model.get_all()
        self.assertEqual(len(data), 2)

        # Find by
        found = self.model.find_by("status", "pending")
        self.assertEqual(len(found), 1)
        self.assertEqual(found.iloc[0]["name"], "Journal A")

        # Get by id
        item = self.model.get_by_id("id", 2)
        self.assertIsNotNone(item)
        self.assertEqual(item["name"], "Journal B")

        # Update
        updated = self.model.update_row("id", 1, {"status": "review"})
        self.assertTrue(updated)
        item_updated = self.model.get_by_id("id", 1)
        self.assertEqual(item_updated["status"], "review")

        # Delete
        self.model.delete_data("id", 1)
        data_after_del = self.model.get_all()
        self.assertEqual(len(data_after_del), 1)
        self.assertIsNone(self.model.get_by_id("id", 1))

    def test_concurrent_writes(self):
        num_threads = 5
        rows_per_thread = 4

        def worker(t_idx):
            for r in range(rows_per_thread):
                row_id = t_idx * 100 + r
                self.model.insert_row({"id": row_id, "title": f"Thread {t_idx} Row {r}"})

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        final_data = self.model.get_all()
        self.assertEqual(len(final_data), num_threads * rows_per_thread)

class TestIntegration(unittest.TestCase):
    def test_models_and_controllers_instantiation(self):
        auth = AuthController()
        self.assertIsNotNone(auth.service)
        self.assertIsNotNone(auth.user_model)
        self.assertIsNotNone(auth.validator_model)
        self.assertIsNotNone(auth.admin_model)

        report_ctrl = ReportController("database/tb_report.csv")
        self.assertIsNotNone(report_ctrl.service)
        self.assertIsNotNone(report_ctrl.report_model)

        admin_ctrl = AdminController()
        self.assertIsNotNone(admin_ctrl.service)
        self.assertIsNotNone(admin_ctrl.report_model)

        check_ctrl = CheckController("database/tb_report.csv")
        self.assertIsNotNone(check_ctrl.service)
        self.assertIsNotNone(check_ctrl.report_model)

    def test_database_files_exist_and_readable(self):
        for path in ["database/tb_user.csv", "database/tb_admin.csv", "database/tb_validator.csv", "database/tb_report.csv"]:
            self.assertTrue(os.path.exists(path), f"File {path} does not exist")
            df = pd.read_csv(path)
            self.assertGreater(len(df.columns), 0)

class TestJournalService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.user_file = os.path.join(self.temp_dir.name, "users.csv")
        self.val_file = os.path.join(self.temp_dir.name, "validators.csv")
        self.adm_file = os.path.join(self.temp_dir.name, "admins.csv")
        self.rep_file = os.path.join(self.temp_dir.name, "reports.csv")

        self.service = JournalService(
            user_path=self.user_file,
            validator_path=self.val_file,
            admin_path=self.adm_file,
            report_path=self.rep_file
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_user_and_report_lifecycle(self):
        # 1. Register User
        ok, msg = self.service.register_user(
            "test_user_1", "password123", "Test User", "test@domain.com", "Test Inst"
        )
        self.assertTrue(ok, msg)

        # 2. Authenticate
        role, user = self.service.authenticate("test_user_1", "password123")
        self.assertEqual(role, "user")
        user_id = user["user_id"]

        # 3. Submit Report
        ok, msg, rep_id = self.service.submit_report(
            user_id, "Test User", "Journal of AI", "https://ai-journal.fake.org", "Too fast review", False
        )
        self.assertTrue(ok)

        # 4. Check user stats
        stats = self.service.get_user_stats(user_id)
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["pending"], 1)

        # 5. Smart Search: URL normalization & Journal Name Search
        # Match with trailing slash and different scheme
        res_norm = self.service.check_journal_url("http://ai-journal.fake.org/")
        self.assertEqual(len(res_norm), 1)
        self.assertEqual(res_norm[0]["report_id"], rep_id)

        # Search by keyword
        res_kw = self.service.search_by_journal_name("journal")
        self.assertEqual(len(res_kw), 1)
        self.assertEqual(res_kw[0]["report_id"], rep_id)

        # 6. Validator actions
        val_ok, _ = self.service.register_validator(
            "validator_doc", "password123", "Dr. Validator", "val@domain.com", "Univ", "Professor", "", "", ""
        )
        self.assertTrue(val_ok)

        val_role, val_data = self.service.authenticate("validator_doc", "password123")
        self.assertEqual(val_role, "validator")
        val_id = val_data["validator_id"]

        # Claim report
        claim_ok, _ = self.service.claim_report(rep_id, val_id)
        self.assertTrue(claim_ok)

        # Validate report
        val_res, _ = self.service.validate_report(rep_id, "predator", "Confirmed suspicious fee structure.")
        self.assertTrue(val_res)

        # Check report state now
        rep_final = self.service.report_model.get_by_id("report_id", rep_id)
        self.assertEqual(rep_final["status_laporan"], "done")
        self.assertEqual(rep_final["status_jurnal"], "predator")

        # 7. System stats
        sys_stats = self.service.get_system_stats()
        self.assertEqual(sys_stats["total_reports"], 1)
        self.assertEqual(sys_stats["done_reports"], 1)
        self.assertEqual(sys_stats["total_users"], 1)
        self.assertEqual(sys_stats["total_validators"], 1)

if __name__ == "__main__":
    unittest.main()
