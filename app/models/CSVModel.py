import os
import tempfile
import threading
from contextlib import contextmanager
import pandas as pd

_process_locks = {}
_global_lock = threading.Lock()

def _get_thread_lock(file_path):
    with _global_lock:
        norm = os.path.abspath(file_path)
        if norm not in _process_locks:
            _process_locks[norm] = threading.Lock()
        return _process_locks[norm]

class CSVModel:
    def __init__(self, file_path):
        self.file_path = file_path

    @contextmanager
    def _file_lock(self, exclusive=True):
        """Context manager penguncian thread dan file system (fcntl) cross-process."""
        t_lock = _get_thread_lock(self.file_path)
        t_lock.acquire()
        lock_file_path = f"{self.file_path}.lock"
        dir_name = os.path.dirname(self.file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        lock_fd = None
        try:
            try:
                import fcntl
                lock_fd = open(lock_file_path, "a")
                flags = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
                fcntl.flock(lock_fd, flags)
            except Exception:
                pass
            yield
        finally:
            if lock_fd:
                try:
                    import fcntl
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    lock_fd.close()
                except Exception:
                    pass
            t_lock.release()

    def read_data(self):
        """Membaca data dari file CSV secara aman."""
        if not os.path.exists(self.file_path):
            return pd.DataFrame()
        try:
            return pd.read_csv(self.file_path)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
        except Exception as e:
            print(f"Error reading {self.file_path}: {e}")
            return pd.DataFrame()

    def write_data(self, data):
        """Menulis data ke file CSV secara atomik menggunakan file sementara dan os.replace."""
        try:
            dir_name = os.path.dirname(self.file_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            target_dir = dir_name if dir_name else "."
            with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, suffix=".tmp") as tf:
                temp_name = tf.name
                data.to_csv(tf, index=False)
                tf.flush()
                os.fsync(tf.fileno())

            os.replace(temp_name, self.file_path)
        except Exception as e:
            print(f"Error writing data to {self.file_path}: {e}")
            if 'temp_name' in locals() and os.path.exists(temp_name):
                try:
                    os.remove(temp_name)
                except Exception:
                    pass

    def get_all(self):
        """Mengambil seluruh data."""
        return self.read_data()

    def find_by(self, column, value):
        """Mencari data berdasarkan kolom dan nilai tertentu."""
        data = self.read_data()
        if data.empty or column not in data.columns:
            return pd.DataFrame()
        return data[data[column].astype(str).str.strip() == str(value).strip()]

    def get_by_id(self, column, value):
        """Mengambil satu baris berdasarkan kolom ID."""
        matches = self.find_by(column, value)
        if not matches.empty:
            return matches.iloc[0]
        return None

    def insert_row(self, row_dict):
        """Menambahkan satu baris baru ke file CSV dengan proteksi file lock."""
        with self._file_lock(exclusive=True):
            data = self.read_data()
            new_df = pd.DataFrame([row_dict])
            data = pd.concat([data, new_df], ignore_index=True)
            self.write_data(data)
            return data

    def update_row(self, id_column, id_value, updates):
        """Memperbarui baris berdasarkan kolom ID dengan proteksi file lock."""
        with self._file_lock(exclusive=True):
            data = self.read_data()
            if data.empty or id_column not in data.columns:
                return False
            mask = data[id_column].astype(str).str.strip() == str(id_value).strip()
            if not mask.any():
                return False
            for col, val in updates.items():
                if col in data.columns:
                    if data[col].dtype != "object" and isinstance(val, str):
                        data[col] = data[col].astype("object")
                    data.loc[mask, col] = val
            self.write_data(data)
            return True

    def delete_data(self, column, value):
        """Menghapus data dari file CSV berdasarkan kolom dan nilai dengan proteksi file lock."""
        with self._file_lock(exclusive=True):
            try:
                data = self.read_data()
                if data.empty or column not in data.columns:
                    return
                data = data[data[column].astype(str).str.strip() != str(value).strip()]
                self.write_data(data)
            except Exception as e:
                print(f"Error deleting data: {e}")
