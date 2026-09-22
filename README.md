# LaporJurnal - Platform Verifikasi & Pelaporan Integritas Jurnal Ilmiah

LaporJurnal adalah sistem informasi berbasis Python yang dirancang untuk membantu akademisi, peneliti, dan mahasiswa dalam mengidentifikasi, melaporkan, serta menelaah indikasi praktik jurnal ilmiah predator dan jurnal kloning (*hijacked journal*).

Aplikasi ini menyediakan dua mode antarmuka terpadu:
1. **Web GUI Modern (Streamlit):** Antarmuka grafis interaktif dengan visualisasi data, kartu verifikasi resmi, dan tata letak responsif yang mendukung Dark Mode maupun Light Mode.
2. **Interactive CLI (Command Line Interface):** Antarmuka terminal berbasis teks untuk pengoperasian cepat di lingkungan shell.

---

## Fitur Utama Berdasarkan Peran

### 1. Tamu & Publik (Tanpa Autentikasi)
* **Pencarian Cerdas Jurnal:** Memeriksa status jurnal berdasarkan URL (dilengkapi algoritma normalisasi domain, protokol, dan trailing slash) atau berdasarkan nama jurnal.
* **Kartu Hasil Verifikasi:** Menampilkan riwayat status alur (*Pending*, *Dalam Review*, *Selesai*), hasil kurasi (*Aman*, *Predator*, *Kloning*), dan catatan telaah kurator.
* **Informasi Kurator:** Menampilkan identitas validator penelaah beserta tautan profil ilmiah resmi (Scopus, SINTA, Google Scholar).
* **Portal Autentikasi Terpadu:** Tab masuk akun dan registrasi mandiri untuk pengguna baru.
* **Panduan Integritas Akademik:** Pedoman komprehensif mengenai ciri-ciri spesifik jurnal predator dan jurnal kloning.

### 2. Pengguna (User)
* **Pengajuan Laporan Jurnal:** Formulir pelaporan dengan opsi pelapor anonim untuk menjaga kerahasiaan identitas.
* **Dasbor Laporan Saya:** Pelacakan status berkas laporan secara real-time disertai indikator metrik.
* **Manajemen Laporan Pending:** Kemudahan untuk mengubah data (*edit*) atau membatalkan (*delete*) pengajuan selama laporan belum diambil oleh validator.
* **Ekspor Data Mandiri:** Mengunduh seluruh riwayat laporan pribadi dalam format CSV.
* **Pengaturan Akun:** Pembaruan profil informasi kontak dan pembaruan kata sandi.

### 3. Validator / Kurator Akademik
* **Antrean Klaim Laporan:** Memilih dan mengambil laporan masuk yang berstatus pending untuk ditelaah.
* **Proses Evaluasi Kurasi:** Memberikan penilaian integritas ilmiah (*Aman*, *Predator*, *Kloning*) dilengkapi catatan pertimbangan substantif.
* **Fleksibilitas Alur Telaah:** Opsi mengembalikan berkas ke antrean pending jika diperlukan atau merevisi hasil kurasi yang telah tersimpan.
* **Dasbor Statistik Kinerja:** Metrik agregat penanganan laporan disertai grafik visual aktivitas telaah.
* **Ekspor Rekapitulasi Telaah:** Mengunduh arsip laporan yang ditangani ke dalam format CSV.

### 4. Administrator
* **Ringkasan Operasional Sistem:** Monitoring menyeluruh atas metrik total laporan, total pengguna, dan total validator.
* **Visualisasi Data Analitik:** Grafik interaktif distribusi alur laporan dan proporsi klasifikasi hasil kurasi.
* **Manajemen Seluruh Laporan:** Tabel interaktif dengan konfigurasi tautan langsung (`st.column_config`), filter multi-kriteria (status alur, status kurasi, pencarian kata kunci), serta fitur unduh rekap CSV.
* **Manajemen Validator:** Pendaftaran akun validator baru lengkap dengan tautan profil Scopus/SINTA/Scholar, pengeditan profil, pengaturan ulang kata sandi, dan penghapusan akun.
* **Manajemen Pengguna:** Pengawasan akun terdaftar dan penghapusan pengguna non-aktif.

---

## Arsitektur & Keamanan Teknis

* **Service-Oriented Architecture (SOA):** Seluruh logika bisnis diisolasi di dalam `app/services/journal_service.py`. Baik Streamlit Web GUI maupun Terminal CLI menggunakan service layer yang sama (*single source of truth*), mencegah inkonsistensi aturan validasi.
* **Data Concurrency & Resilience:** Berkas data dikelola melalui `app/models/CSVModel.py` yang menerapkan teknik **atomic write** (`tempfile` + `os.replace`) dan **cross-process file locking** (`fcntl` dengan thread-level fallback). Mekanisme ini mencegah kerusakan berkas (*data corruption*) dan benturan saat banyak pengguna mengakses web secara bersamaan.
* **Pengamanan Kredensial:** Kata sandi di-hash menggunakan algoritma standar industri **PBKDF2-HMAC-SHA256** dengan 100.000 iterasi dan *random cryptographic salt* 16-byte, dilengkapi mekanisme otomatis peningkatan hash (*auto-upgrade*) dari data lama.
* **Theme Adaptive UI:** Seluruh komponen antarmuka web dibangun menggunakan elemen native Streamlit yang menyesuaikan kontras secara otomatis pada Dark Mode maupun Light Mode.

---

## Struktur Direktori

```text
laporjurnal-GUI/
├── app/
│   ├── controllers/         # Controller CLI (Auth, Report, Admin, Check)
│   ├── models/              # CSVModel dengan atomic write & file lock
│   ├── services/            # Backend JournalService (Business logic layer)
│   └── views/               # Tampilan menu terminal CLI
├── database/                # Berkas penyimpanan data CSV
│   ├── tb_admin.csv         # Data kredensial administrator
│   ├── tb_report.csv        # Rekam data laporan jurnal
│   ├── tb_user.csv          # Data pengguna terdaftar
│   └── tb_validator.csv     # Data kurator akademik
├── tests/                   # Rangkaian pengujian otomatis (Unit tests)
│   └── test_app.py
├── .gitignore               # Konfigurasi pengecualian file Git
├── main.py                  # Entry point aplikasi Terminal CLI
├── requirements.txt         # Daftar dependensi pustaka Python
├── streamlit_app.py         # Entry point aplikasi Web GUI (Streamlit)
└── utils.py                 # Utilitas validasi URL/email, hashing, & normalisasi
```

---

## Panduan Instalasi & Penggunaan

### 1. Prasyarat Sistem
* Python versi 3.12 atau yang lebih baru.
* Git terpasang di sistem operasi.

### 2. Kloning Repositori
```bash
git clone https://github.com/AdzrilIlham/LaporJurnal.git
cd LaporJurnal
```

### 3. Pembuatan Lingkungan Virtual (Virtual Environment)
Direkomendasikan menggunakan virtual environment agar dependensi terisolasi:

```bash
python3.12 -m venv .venv
source .venv/bin/activate  # Untuk Linux/macOS
# .venv\Scripts\activate   # Untuk Windows
```

### 4. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 5. Menjalankan Aplikasi Web GUI
Untuk membuka aplikasi antarmuka web Streamlit pada peramban (*browser*):

```bash
streamlit run streamlit_app.py
```
Aplikasi secara otomatis akan terbuka di alamat default: `http://localhost:8501`.

### 6. Menjalankan Aplikasi Terminal CLI
Untuk menjalankan antarmuka baris perintah interaktif pada terminal:

```bash
python main.py
```

### 7. Menjalankan Pengujian Otomatis (Unit Testing)
Seluruh modul validasi, model penyimpanan atomik, service layer, dan controller dapat diuji dengan perintah:

```bash
python -m unittest discover tests
```

---

## Kredensial Akun Pengujian Default

Untuk keperluan pengujian sistem, tersedia akun bawaan berikut di dalam database:

| Peran | Username | Password | Keterangan |
|---|---|---|---|
| **Administrator** | `admin1` | `admin123` | Akses penuh manajemen platform & validator |
| **Validator** | `validator1` | `12345678` | Akses penelaahan & kurasi antrean laporan |

*(Catatan: Akun pengguna baru dapat dibuat langsung secara mandiri melalui tab pendaftaran pada Portal Autentikasi).*
