import pandas as pd
from datetime import datetime
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

def _safe_str_id(val):
    if pd.isna(val) or val is None or str(val).strip() in ("", "nan", "None"):
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

class JournalService:
    def __init__(
        self,
        user_path="database/tb_user.csv",
        validator_path="database/tb_validator.csv",
        admin_path="database/tb_admin.csv",
        report_path="database/tb_report.csv"
    ):
        self.user_model = CSVModel(user_path)
        self.validator_model = CSVModel(validator_path)
        self.admin_model = CSVModel(admin_path)
        self.report_model = CSVModel(report_path)

    # ---------------- Auth & User Management ----------------
    def authenticate(self, username, password):
        username = str(username).strip()
        # 1. User
        user_df = self.user_model.read_data()
        if not user_df.empty and "username" in user_df.columns:
            matches = user_df[user_df["username"] == username]
            if not matches.empty:
                row = matches.iloc[0]
                if verify_password(password, str(row["password"])):
                    # Upgrade hash if still plaintext
                    if not str(row["password"]).startswith("pbkdf2_sha256$"):
                        self.user_model.update_row("user_id", row["user_id"], {"password": hash_password(password)})
                    return "user", row.to_dict()
                return None, "Password tidak cocok untuk pengguna ini."

        # 2. Validator
        val_df = self.validator_model.read_data()
        if not val_df.empty and "username" in val_df.columns:
            matches = val_df[val_df["username"] == username]
            if not matches.empty:
                row = matches.iloc[0]
                if verify_password(password, str(row["password"])):
                    if not str(row["password"]).startswith("pbkdf2_sha256$"):
                        self.validator_model.update_row("validator_id", row["validator_id"], {"password": hash_password(password)})
                    return "validator", row.to_dict()
                return None, "Password tidak cocok untuk validator ini."

        # 3. Admin
        adm_df = self.admin_model.read_data()
        if not adm_df.empty and "username" in adm_df.columns:
            matches = adm_df[adm_df["username"] == username]
            if not matches.empty:
                row = matches.iloc[0]
                if verify_password(password, str(row["password"])):
                    if not str(row["password"]).startswith("pbkdf2_sha256$"):
                        self.admin_model.update_row("admin_id", row["admin_id"], {"password": hash_password(password)})
                    return "admin", row.to_dict()
                return None, "Password tidak cocok untuk admin ini."

        return None, "Username tidak ditemukan."

    def register_user(self, username, password, full_name, email, instancy):
        if not is_valid_username(username):
            return False, "Username minimal 8 karakter dan hanya boleh berisi huruf, angka, '_', atau '.'."
        if not is_valid_password(password):
            return False, "Password minimal 8 karakter."
        if not full_name.strip():
            return False, "Nama lengkap tidak boleh kosong."
        if not is_valid_email(email):
            return False, "Format email tidak valid."

        user_df = self.user_model.read_data()
        if not user_df.empty:
            if not user_df[user_df["username"] == username].empty:
                return False, "Username sudah digunakan. Silakan gunakan yang lain."
            if not user_df[user_df["email"] == email].empty:
                return False, "Email sudah terdaftar. Silakan gunakan yang lain."
            new_id = int(user_df["user_id"].max() + 1)
        else:
            new_id = 1

        new_user = {
            "user_id": new_id,
            "username": username.strip(),
            "password": hash_password(password),
            "full_name": full_name.strip(),
            "email": email.strip(),
            "instancy": instancy.strip(),
            "role": "user"
        }
        self.user_model.insert_row(new_user)
        return True, "Registrasi user berhasil!"

    def update_user_profile(self, user_id, full_name, email, instancy):
        user = self.user_model.get_by_id("user_id", user_id)
        if user is None:
            return False, "User tidak ditemukan."

        updates = {}
        if full_name and full_name.strip():
            updates["full_name"] = full_name.strip()
        if email and email.strip():
            if not is_valid_email(email.strip()):
                return False, "Format email tidak valid."
            updates["email"] = email.strip()
        if instancy and instancy.strip():
            updates["instancy"] = instancy.strip()

        if updates:
            self.user_model.update_row("user_id", user_id, updates)
            return True, "Profil berhasil diperbarui."
        return False, "Tidak ada perubahan."

    def change_user_password(self, user_id, old_password, new_password):
        user = self.user_model.get_by_id("user_id", user_id)
        if user is None:
            return False, "User tidak ditemukan."
        if not verify_password(old_password, str(user["password"])):
            return False, "Password saat ini salah."
        if not is_valid_password(new_password):
            return False, "Password baru harus memiliki minimal 8 karakter."

        self.user_model.update_row("user_id", user_id, {"password": hash_password(new_password)})
        return True, "Password berhasil diperbarui."

    # ---------------- Validator Management (Admin) ----------------
    def register_validator(self, username, password, full_name, email, instancy, academic_position, scopus_url, sinta_url, google_scholar_url):
        if not is_valid_username(username):
            return False, "Username minimal 8 karakter dan hanya boleh berisi huruf, angka, '_', atau '.'."
        if not is_valid_password(password):
            return False, "Password minimal 8 karakter."
        if not full_name.strip():
            return False, "Nama lengkap tidak boleh kosong."
        if not is_valid_email(email):
            return False, "Format email tidak valid."

        for label, url in [("Scopus", scopus_url), ("Sinta", sinta_url), ("Google Scholar", google_scholar_url)]:
            if url and not is_valid_url(url):
                return False, f"URL {label} tidak valid."

        val_df = self.validator_model.read_data()
        if not val_df.empty:
            if not val_df[val_df["username"] == username].empty:
                return False, "Username validator sudah ada."
            if not val_df[val_df["email"] == email].empty:
                return False, "Email validator sudah terdaftar."
            new_id = int(val_df["validator_id"].max() + 1)
        else:
            new_id = 1

        new_val = {
            "validator_id": new_id,
            "username": username.strip(),
            "password": hash_password(password),
            "full_name": full_name.strip(),
            "email": email.strip(),
            "instancy": instancy.strip(),
            "academic_position": academic_position.strip(),
            "scopus_url": scopus_url.strip(),
            "sinta_url": sinta_url.strip(),
            "google_scholar_url": google_scholar_url.strip(),
            "role": "validator"
        }
        self.validator_model.insert_row(new_val)
        return True, "Registrasi validator berhasil!"

    def update_validator_info(self, validator_id, full_name, email, instancy, academic_position, scopus_url, sinta_url, google_scholar_url):
        val = self.validator_model.get_by_id("validator_id", validator_id)
        if val is None:
            return False, "Validator tidak ditemukan."

        if email and not is_valid_email(email):
            return False, "Format email tidak valid."
        for label, url in [("Scopus", scopus_url), ("Sinta", sinta_url), ("Google Scholar", google_scholar_url)]:
            if url and not is_valid_url(url):
                return False, f"URL {label} tidak valid."

        updates = {
            "full_name": full_name.strip(),
            "email": email.strip(),
            "instancy": instancy.strip(),
            "academic_position": academic_position.strip(),
            "scopus_url": scopus_url.strip(),
            "sinta_url": sinta_url.strip(),
            "google_scholar_url": google_scholar_url.strip()
        }
        self.validator_model.update_row("validator_id", validator_id, updates)
        return True, "Data validator berhasil diperbarui."

    def change_validator_password(self, validator_id, new_password):
        if not is_valid_password(new_password):
            return False, "Password baru harus memiliki minimal 8 karakter."
        self.validator_model.update_row("validator_id", validator_id, {"password": hash_password(new_password)})
        return True, "Password validator berhasil diubah."

    def delete_validator(self, validator_id):
        self.validator_model.delete_data("validator_id", validator_id)
        return True, "Validator berhasil dihapus."

    def delete_user(self, user_id):
        self.user_model.delete_data("user_id", user_id)
        return True, "User berhasil dihapus."

    # ---------------- Reports & Public Checking ----------------
    def get_all_reports(self):
        return self.report_model.read_data()

    def get_all_users(self):
        return self.user_model.read_data()

    def get_all_validators(self):
        return self.validator_model.read_data()

    def check_journal_url(self, journal_url):
        raw_url = str(journal_url).strip()
        norm_url = normalize_url(raw_url)
        report_df = self.report_model.read_data()
        if report_df.empty or "journal_url" not in report_df.columns:
            return []

        # Match either exact string or normalized URL (if norm_url is not empty)
        if norm_url:
            mask = (report_df["journal_url"].astype(str).str.strip() == raw_url) | (report_df["journal_url"].astype(str).apply(normalize_url) == norm_url)
        else:
            mask = report_df["journal_url"].astype(str).str.strip() == raw_url

        matches = report_df[mask]
        results = []
        for _, row in matches.iterrows():
            item = row.to_dict()
            # Attach validator details if present
            v_id = _safe_str_id(item.get("validator_id"))
            if v_id:
                val = self.validator_model.get_by_id("validator_id", v_id)
                item["validator_info"] = val.to_dict() if val is not None else None
            else:
                item["validator_info"] = None
            results.append(item)
        return results

    def search_by_journal_name(self, keyword):
        kw = str(keyword).strip().lower()
        if not kw:
            return []
        report_df = self.report_model.read_data()
        if report_df.empty or "journal_name" not in report_df.columns:
            return []

        matches = report_df[report_df["journal_name"].astype(str).str.lower().str.contains(kw, na=False)]
        results = []
        for _, row in matches.iterrows():
            item = row.to_dict()
            v_id = _safe_str_id(item.get("validator_id"))
            if v_id:
                val = self.validator_model.get_by_id("validator_id", v_id)
                item["validator_info"] = val.to_dict() if val is not None else None
            else:
                item["validator_info"] = None
            results.append(item)
        return results

    def submit_report(self, user_id, full_name, journal_name, journal_url, reason, is_anonymous):
        if not journal_name.strip():
            return False, "Nama jurnal tidak boleh kosong.", None
        if not is_valid_url(journal_url.strip()):
            return False, "URL jurnal tidak valid (harus dimulai http:// atau https://).", None
        if not reason.strip():
            return False, "Alasan pelaporan tidak boleh kosong.", None

        report_df = self.report_model.read_data()
        new_id = int(report_df["report_id"].max() + 1) if not report_df.empty and "report_id" in report_df.columns else 1

        new_report = {
            "report_id": new_id,
            "user_id": int(user_id),
            "full_name": "Anonymous" if is_anonymous else full_name.strip(),
            "is_anonymous": bool(is_anonymous),
            "journal_name": journal_name.strip(),
            "journal_url": journal_url.strip(),
            "reason": reason.strip(),
            "status_laporan": "pending",
            "tanggal_laporan": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "validator_id": None,
            "status_jurnal": "",
            "feedback": ""
        }
        self.report_model.insert_row(new_report)
        return True, "Laporan berhasil dikirim!", new_id

    def get_user_reports(self, user_id):
        df = self.report_model.read_data()
        if df.empty or "user_id" not in df.columns:
            return pd.DataFrame()
        return df[df["user_id"].apply(_safe_str_id) == str(user_id)]

    def update_report(self, report_id, journal_name, journal_url, reason):
        rep = self.report_model.get_by_id("report_id", report_id)
        if rep is None:
            return False, "Laporan tidak ditemukan."
        if rep["status_laporan"] != "pending":
            return False, "Hanya laporan berstatus 'pending' yang dapat diedit."
        if journal_url and not is_valid_url(journal_url):
            return False, "URL jurnal tidak valid."

        updates = {}
        if journal_name and journal_name.strip():
            updates["journal_name"] = journal_name.strip()
        if journal_url and journal_url.strip():
            updates["journal_url"] = journal_url.strip()
        if reason and reason.strip():
            updates["reason"] = reason.strip()

        if updates:
            self.report_model.update_row("report_id", report_id, updates)
            return True, "Laporan berhasil diperbarui."
        return False, "Tidak ada data yang diubah."

    def delete_report(self, report_id):
        rep = self.report_model.get_by_id("report_id", report_id)
        if rep is None:
            return False, "Laporan tidak ditemukan."
        if rep["status_laporan"] != "pending":
            return False, "Hanya laporan berstatus 'pending' yang dapat dihapus."

        self.report_model.delete_data("report_id", report_id)
        return True, "Laporan berhasil dihapus."

    # ---------------- Validator Functions ----------------
    def get_pending_reports(self):
        df = self.report_model.read_data()
        if df.empty or "status_laporan" not in df.columns:
            return pd.DataFrame()
        return df[df["status_laporan"] == "pending"]

    def claim_report(self, report_id, validator_id):
        rep = self.report_model.get_by_id("report_id", report_id)
        if rep is None:
            return False, "Laporan tidak ditemukan."
        if rep["status_laporan"] != "pending":
            return False, "Laporan ini sudah diambil atau selesai ditangani."

        self.report_model.update_row("report_id", report_id, {
            "status_laporan": "review",
            "validator_id": int(validator_id)
        })
        return True, f"Laporan ID {report_id} berhasil diambil untuk direview."

    def get_validator_reports(self, validator_id):
        df = self.report_model.read_data()
        if df.empty or "validator_id" not in df.columns:
            return pd.DataFrame()
        v_str = str(validator_id).strip()
        return df[
            (df["validator_id"].apply(_safe_str_id) == v_str) &
            (df["status_laporan"].isin(["review", "done"]))
        ]

    def validate_report(self, report_id, status_jurnal, feedback):
        if status_jurnal not in ["aman", "predator", "clone"]:
            return False, "Status jurnal harus dipilih dari: aman, predator, atau clone."

        self.report_model.update_row("report_id", report_id, {
            "status_jurnal": status_jurnal,
            "feedback": feedback.strip() if feedback else "",
            "status_laporan": "done"
        })
        return True, "Laporan berhasil divalidasi dan ditandai selesai."

    def mark_as_pending(self, report_id):
        self.report_model.update_row("report_id", report_id, {
            "status_laporan": "pending",
            "validator_id": ""
        })
        return True, "Laporan dikembalikan ke status pending."

    # ---------------- Statistics & Overview ----------------
    def get_user_stats(self, user_id):
        df = self.get_user_reports(user_id)
        return {
            "total": len(df),
            "pending": len(df[df["status_laporan"] == "pending"]) if not df.empty else 0,
            "review": len(df[df["status_laporan"] == "review"]) if not df.empty else 0,
            "done": len(df[df["status_laporan"] == "done"]) if not df.empty else 0
        }

    def get_validator_stats(self, validator_id):
        report_df = self.report_model.read_data()
        if report_df.empty:
            return {"available_pending": 0, "review": 0, "done": 0, "total_handled": 0}

        pending_count = len(report_df[report_df["status_laporan"] == "pending"])
        val_reports = report_df[report_df["validator_id"].apply(_safe_str_id) == str(validator_id)]
        review_count = len(val_reports[val_reports["status_laporan"] == "review"]) if not val_reports.empty else 0
        done_count = len(val_reports[val_reports["status_laporan"] == "done"]) if not val_reports.empty else 0

        return {
            "available_pending": pending_count,
            "review": review_count,
            "done": done_count,
            "total_handled": review_count + done_count
        }

    def get_system_stats(self):
        rep = self.report_model.read_data()
        users = self.user_model.read_data()
        vals = self.validator_model.read_data()

        return {
            "total_reports": len(rep),
            "total_users": len(users),
            "total_validators": len(vals),
            "pending_reports": len(rep[rep["status_laporan"] == "pending"]) if not rep.empty else 0,
            "review_reports": len(rep[rep["status_laporan"] == "review"]) if not rep.empty else 0,
            "done_reports": len(rep[rep["status_laporan"] == "done"]) if not rep.empty else 0
        }
