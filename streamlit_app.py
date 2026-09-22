import streamlit as st
import pandas as pd
from app.services.journal_service import JournalService

st.set_page_config(
    page_title="LaporJurnal - Verifikasi Jurnal Ilmiah",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark & Light Mode Compatible Status Badges
st.markdown("""
<style>
    /* High-contrast status badges compatible with Dark and Light modes */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.025em;
        color: #ffffff !important;
    }
    .badge-safe {
        background-color: #059669 !important;
    }
    .badge-predator {
        background-color: #dc2626 !important;
    }
    .badge-clone {
        background-color: #d97706 !important;
    }
    .badge-review {
        background-color: #2563eb !important;
    }
    .badge-pending {
        background-color: #4b5563 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Backend Service
service = JournalService()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

def render_status_badge(status):
    st_clean = str(status).strip().lower()
    if st_clean == "aman":
        return '<span class="badge badge-safe">Aman</span>'
    elif st_clean == "predator":
        return '<span class="badge badge-predator">Predator</span>'
    elif st_clean == "clone":
        return '<span class="badge badge-clone">Klon / Hijacked</span>'
    elif st_clean == "review":
        return '<span class="badge badge-review">Dalam Review</span>'
    else:
        return '<span class="badge badge-pending">Menunggu Validasi</span>'

# Sidebar Navigation
st.sidebar.markdown("### LaporJurnal")
st.sidebar.caption("Platform Verifikasi & Integritas Publikasi Ilmiah")
st.sidebar.divider()

if st.session_state.authenticated:
    user = st.session_state.user
    role = st.session_state.role
    display_name = user.get('full_name') or user.get('username')
    st.sidebar.markdown(f"Pengguna: **{display_name}**")
    st.sidebar.caption(f"Hak Akses: **{role.upper()}**")
    st.sidebar.divider()

    if role == "user":
        menu = st.sidebar.radio(
            "Navigasi Pengguna",
            ["Laporan Saya", "Buat Laporan Baru", "Pengaturan Akun", "Cek Status Jurnal"]
        )
    elif role == "validator":
        menu = st.sidebar.radio(
            "Navigasi Validator",
            ["Antrean Laporan", "Laporan Ditangani", "Statistik Kurasi", "Cek Status Jurnal"]
        )
    elif role == "admin":
        menu = st.sidebar.radio(
            "Navigasi Administrator",
            ["Ringkasan Sistem", "Manajemen Laporan", "Manajemen Validator", "Manajemen Pengguna", "Cek Status Jurnal"]
        )

    st.sidebar.divider()
    if st.sidebar.button("Keluar (Logout)", use_container_width=True):
        logout()
else:
    menu = st.sidebar.radio(
        "Menu Utama",
        ["Cek Status Jurnal", "Portal Autentikasi", "Panduan Integritas"]
    )
    st.sidebar.info("Silakan masuk atau daftar akun untuk mengajukan laporan dan melakukan kurasi jurnal.")

# ----------------- VIEW 1: CEK STATUS JURNAL (PUBLIK) -----------------
if menu == "Cek Status Jurnal":
    st.title("Pencarian & Verifikasi Status Jurnal")
    st.caption("Periksa catatan laporan integritas dan hasil kurasi validator akademik sebelum melakukan submit naskah artikel ilmiah.")

    search_method = st.radio("Metode Pencarian:", ["Berdasarkan URL Jurnal", "Berdasarkan Nama Jurnal"], horizontal=True)

    if search_method == "Berdasarkan URL Jurnal":
        search_query = st.text_input("URL Jurnal Ilmiah:", placeholder="Contoh: https://journal-example.org/index.php")
    else:
        search_query = st.text_input("Nama Jurnal Ilmiah:", placeholder="Contoh: International Journal of Advanced Science")

    col_btn, col_empty = st.columns([1, 4])
    with col_btn:
        submit_search = st.button("Periksa Database", type="primary", use_container_width=True)

    if submit_search and search_query.strip():
        if search_method == "Berdasarkan URL Jurnal":
            results = service.check_journal_url(search_query)
        else:
            results = service.search_by_journal_name(search_query)

        if not results:
            st.info(f"Tidak ditemukan catatan laporan untuk kata kunci: '{search_query}'.")
            st.caption("Catatan: Ketidakhadiran laporan tidak menjamin jurnal 100% aman. Tetap lakukan pengecekan pada indeksasi resmi seperti SINTA, Scopus, DOAJ, atau Web of Science.")
        else:
            st.success(f"Ditemukan {len(results)} catatan verifikasi terkait:")
            for item in results:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.subheader(item.get("journal_name", "Nama Jurnal Tidak Diketahui"))
                        st.markdown(f"**URL:** [{item.get('journal_url')}]({item.get('journal_url')})")
                        st.markdown(f"**Indikasi / Alasan Pelapor:** {item.get('reason', '-')}")
                        st.caption(f"Tanggal Pengajuan: {item.get('tanggal_laporan', '-')} | Pelapor: {item.get('full_name', '-')}")
                    with c2:
                        st.markdown(f"**Status Proses:**<br>{render_status_badge(item.get('status_laporan'))}", unsafe_allow_html=True)
                        st.write("")
                        if item.get("status_jurnal"):
                            st.markdown(f"**Hasil Kurasi:**<br>{render_status_badge(item.get('status_jurnal'))}", unsafe_allow_html=True)

                    if item.get("feedback"):
                        st.info(f"**Catatan Evaluasi Kurator:**\n\n{item.get('feedback')}")

                    val = item.get("validator_info")
                    if val:
                        with st.expander("Informasi Validator / Penelaah Akademik"):
                            st.markdown(f"**Nama:** {val.get('full_name')} ({val.get('academic_position', '-')})")
                            st.markdown(f"**Institusi:** {val.get('instancy', '-')}")
                            links = []
                            if pd.notna(val.get("scopus_url")) and str(val.get("scopus_url")).strip():
                                links.append(f"[Scopus Profile]({val['scopus_url']})")
                            if pd.notna(val.get("sinta_url")) and str(val.get("sinta_url")).strip():
                                links.append(f"[SINTA Profile]({val['sinta_url']})")
                            if pd.notna(val.get("google_scholar_url")) and str(val.get("google_scholar_url")).strip():
                                links.append(f"[Google Scholar]({val['google_scholar_url']})")
                            if links:
                                st.markdown(" | ".join(links))

# ----------------- VIEW 2: PORTAL AUTENTIKASI (LOGIN & REGISTER) -----------------
elif menu == "Portal Autentikasi":
    st.title("Portal Akses Akun")
    st.caption("Silakan masuk menggunakan kredensial terdaftar atau buat akun pengguna baru.")

    tab_login, tab_register = st.tabs(["Masuk Akun", "Daftar Pengguna Baru"])

    with tab_login:
        col_log1, col_log2 = st.columns([1, 1])
        with col_log1:
            with st.form("form_login"):
                st.subheader("Masuk ke Sistem")
                login_user = st.text_input("Username:")
                login_pass = st.text_input("Password:", type="password")
                btn_login = st.form_submit_button("Masuk", type="primary", use_container_width=True)

                if btn_login:
                    if not login_user.strip() or not login_pass.strip():
                        st.error("Username dan password tidak boleh kosong.")
                    else:
                        role, user_data = service.authenticate(login_user, login_pass)
                        if role:
                            st.session_state.authenticated = True
                            st.session_state.user = user_data
                            st.session_state.role = role
                            st.success(f"Autentikasi berhasil. Selamat datang, {user_data.get('full_name', login_user)}.")
                            st.rerun()
                        else:
                            st.error(user_data)
        with col_log2:
            with st.container(border=True):
                st.markdown("#### Informasi Akses Peran")
                st.markdown("""
                - **Pengguna (User):** Pelaporan jurnal mencurigakan dan pelacakan status laporan.
                - **Validator:** Penelaahan berkas, evaluasi kriteria ilmiah, dan pemberian status kurasi.
                - **Administrator:** Pengawasan platform, manajemen validator, dan rekapitulasi data.
                """)

    with tab_register:
        st.subheader("Formulir Pendaftaran Pengguna")
        st.caption("Pendaftaran akun publik ditujukan bagi akademisi, peneliti, dan mahasiswa untuk melaporkan jurnal ilmiah.")
        with st.form("form_register"):
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                reg_user = st.text_input("Username (Minimal 8 karakter alfanumerik):")
                reg_pwd = st.text_input("Password (Minimal 8 karakter):", type="password")
                reg_name = st.text_input("Nama Lengkap Beserta Gelar:")
            with r_col2:
                reg_email = st.text_input("Alamat Email Institusi / Aktif:")
                reg_inst = st.text_input("Institusi / Perguruan Tinggi:")

            btn_reg = st.form_submit_button("Daftarkan Akun", type="primary")

            if btn_reg:
                ok, msg = service.register_user(reg_user, reg_pwd, reg_name, reg_email, reg_inst)
                if ok:
                    st.success(f"{msg} Silakan beralih ke tab 'Masuk Akun' untuk login.")
                else:
                    st.error(msg)

# ----------------- VIEW 3: PANDUAN INTEGRITAS -----------------
elif menu == "Panduan Integritas":
    st.title("Panduan Kriteria Identifikasi Jurnal")
    st.caption("Pedoman umum dalam mengenali praktik jurnal predator dan jurnal kloning (hijacked journal).")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        with st.container(border=True):
            st.markdown("### Ciri-Ciri Jurnal Predator")
            st.write("Praktik penerbitan yang mengabaikan standar peer-review dan berorientasi semata pada biaya APC (Article Processing Charge):")
            st.markdown("""
            - **Proses Peer-Review Kilat:** Menjanjikan penerimaan (LOA) dalam 1-3 hari tanpa review substantif.
            - **Dewan Editor Fiktif:** Mencantumkan nama ilmuwan terkemuka tanpa izin atau konfirmasi bersangkutan.
            - **Klaim Metrik Palsu:** Mempublikasikan nilai Impact Factor yang tidak terdaftar di Clarivate Analytics / Scopus.
            - **Undangan Spam Massal:** Mengirimkan undangan email submit naskah yang agresif di luar bidang keahlian penulis.
            """)

    with col_g2:
        with st.container(border=True):
            st.markdown("### Ciri-Ciri Jurnal Kloning (Hijacked)")
            st.write("Situs web palsu yang menduplikasi nama dan nomor ISSN jurnal bereputasi sah:")
            st.markdown("""
            - **Domain Berbeda:** Domain tidak terdaftar pada portal resmi ISSN International Centre atau Scopus Source.
            - **Arsip Terputus:** Riwayat penerbitan volume tahun-tahun sebelumnya kosong atau tidak konsisten.
            - **Metode Pembayaran Pribadi:** Meminta pengiriman biaya publikasi ke rekening perorangan atau transfer non-institusi.
            - **Tautan Eksternal Rusak:** Banyak menu navigasi atau pedoman penulisan yang mengarah ke halaman kosong.
            """)

# ----------------- USER DASHBOARD: LAPORAN SAYA -----------------
elif menu == "Laporan Saya" and st.session_state.role == "user":
    st.title("Pelacakan Laporan Saya")
    st.caption("Pantau status penelaahan atas laporan dugaan jurnal predator/klon yang telah Anda ajukan.")
    user_id = st.session_state.user["user_id"]

    stats = service.get_user_stats(user_id)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Laporan", stats["total"])
    m2.metric("Menunggu Validasi", stats["pending"])
    m3.metric("Sedang Ditelaah", stats["review"])
    m4.metric("Selesai Dikurasi", stats["done"])

    st.divider()
    df = service.get_user_reports(user_id)
    if df.empty:
        st.info("Anda belum memiliki riwayat pengajuan laporan jurnal.")
    else:
        h_col1, h_col2 = st.columns([3, 1])
        with h_col1:
            st.subheader(f"Riwayat Pengajuan ({len(df)})")
        with h_col2:
            csv_user = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Unduh Rekapitulasi (CSV)",
                data=csv_user,
                file_name="riwayat_laporan_pengguna.csv",
                mime="text/csv",
                use_container_width=True
            )

        for _, row in df.iterrows():
            with st.expander(f"[ID: {row['report_id']}] {row['journal_name']} - Status: {str(row['status_laporan']).upper()}"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**URL Jurnal:** [{row['journal_url']}]({row['journal_url']})")
                    st.write(f"**Alasan Pengajuan:** {row['reason']}")
                    st.write(f"**Tanggal Pengajuan:** {row['tanggal_laporan']}")
                    st.write(f"**Status Anonim:** {'Ya' if row['is_anonymous'] else 'Tidak'}")
                with c2:
                    st.markdown(f"**Status Alur:**<br>{render_status_badge(row['status_laporan'])}", unsafe_allow_html=True)
                    st.write("")
                    if pd.notna(row.get('status_jurnal')) and str(row.get('status_jurnal')).strip():
                        st.markdown(f"**Hasil Kurasi:**<br>{render_status_badge(row['status_jurnal'])}", unsafe_allow_html=True)
                    if pd.notna(row.get('feedback')) and str(row.get('feedback')).strip():
                        st.write(f"**Feedback:** {row['feedback']}")

                if row['status_laporan'] == "pending":
                    st.divider()
                    st.markdown("##### Tindakan Laporan Pending")
                    act_col1, act_col2 = st.columns(2)
                    with act_col1:
                        with st.popover("Edit Data Laporan"):
                            new_jname = st.text_input("Nama Jurnal", value=row['journal_name'], key=f"jn_{row['report_id']}")
                            new_jurl = st.text_input("URL Jurnal", value=row['journal_url'], key=f"ju_{row['report_id']}")
                            new_reason = st.text_area("Alasan Pelaporan", value=row['reason'], key=f"re_{row['report_id']}")
                            if st.button("Simpan Perubahan", key=f"save_{row['report_id']}"):
                                ok, msg = service.update_report(row['report_id'], new_jname, new_jurl, new_reason)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    with act_col2:
                        with st.popover("Batalkan / Hapus Laporan"):
                            st.warning("Apakah Anda yakin ingin membatalkan dan menghapus laporan ini?")
                            if st.button("Konfirmasi Hapus", type="primary", key=f"del_{row['report_id']}"):
                                ok, msg = service.delete_report(row['report_id'])
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

# ----------------- USER DASHBOARD: BUAT LAPORAN BARU -----------------
elif menu == "Buat Laporan Baru" and st.session_state.role == "user":
    st.title("Pengajuan Laporan Jurnal Ilmiah")
    st.caption("Laporkan indikasi praktik jurnal predator atau klon untuk divalidasi oleh kurator akademik.")

    with st.container(border=True):
        st.markdown("#### Ketentuan Pengajuan Laporan")
        st.markdown("""
        1. Pastikan URL jurnal diawali dengan protokol yang valid (`http://` atau `https://`).
        2. Berikan alasan dan bukti indikasi yang jelas (misalnya: waktu review 1 hari, biaya mencurigakan, atau domain yang berbeda dengan portal resmi).
        3. Opsi anonim akan menyembunyikan identitas Anda pada kartu pencarian publik.
        """)

    user = st.session_state.user
    with st.form("form_submit_report"):
        j_name = st.text_input("Nama Jurnal Ilmiah:")
        j_url = st.text_input("URL Situs Web Jurnal:", placeholder="https://domain-jurnal.org/...")
        j_reason = st.text_area("Uraian Alasan & Bukti Indikasi:", placeholder="Jelaskan temuan kejanggalan proses editorial atau korespondensi...")
        is_anon = st.checkbox("Ajukan sebagai pelapor anonim (Nama tidak ditampilkan ke publik)")

        btn_send = st.form_submit_button("Kirim Laporan", type="primary")

        if btn_send:
            ok, msg, rep_id = service.submit_report(
                user["user_id"],
                user.get("full_name", user["username"]),
                j_name,
                j_url,
                j_reason,
                is_anon
            )
            if ok:
                st.success(f"{msg} (Nomor Laporan ID: {rep_id})")
            else:
                st.error(msg)

# ----------------- USER DASHBOARD: PENGATURAN AKUN -----------------
elif menu == "Pengaturan Akun" and st.session_state.role == "user":
    st.title("Pengaturan Profil & Akun")
    st.caption("Kelola informasi kontak akun dan perbarui kata sandi keamanan Anda.")
    user = st.session_state.user

    tab_profile, tab_security = st.tabs(["Perbarui Profil", "Ganti Password"])

    with tab_profile:
        with st.form("form_update_profile"):
            pf_name = st.text_input("Nama Lengkap:", value=user.get("full_name", ""))
            pf_email = st.text_input("Alamat Email:", value=user.get("email", ""))
            pf_inst = st.text_input("Institusi / Universitas:", value=user.get("instancy", ""))
            btn_pf = st.form_submit_button("Simpan Perubahan Profil")

            if btn_pf:
                ok, msg = service.update_user_profile(user["user_id"], pf_name, pf_email, pf_inst)
                if ok:
                    st.success(msg)
                    st.session_state.user["full_name"] = pf_name
                    st.session_state.user["email"] = pf_email
                    st.session_state.user["instancy"] = pf_inst
                else:
                    st.error(msg)

    with tab_security:
        with st.form("form_change_password"):
            cur_pwd = st.text_input("Password Saat Ini:", type="password")
            new_pwd = st.text_input("Password Baru (Minimal 8 karakter):", type="password")
            cf_pwd = st.text_input("Konfirmasi Password Baru:", type="password")
            btn_pwd = st.form_submit_button("Perbarui Password")

            if btn_pwd:
                if new_pwd != cf_pwd:
                    st.error("Konfirmasi password baru tidak cocok.")
                else:
                    ok, msg = service.change_user_password(user["user_id"], cur_pwd, new_pwd)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# ----------------- VALIDATOR: ANTREAN PENDING -----------------
elif menu == "Antrean Laporan" and st.session_state.role == "validator":
    st.title("Antrean Laporan Masuk")
    st.caption("Daftar laporan dugaan jurnal yang menunggu verifikasi dari kurator akademik.")
    validator_id = st.session_state.user["validator_id"]

    pending_df = service.get_pending_reports()
    if pending_df.empty:
        st.info("Tidak ada antrean laporan pending saat ini. Semua laporan telah tertangani.")
    else:
        st.subheader(f"Tersedia {len(pending_df)} Laporan dalam Antrean:")
        for _, row in pending_df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"#### [ID: {row['report_id']}] {row['journal_name']}")
                    st.markdown(f"**URL:** [{row['journal_url']}]({row['journal_url']})")
                    st.write(f"**Alasan Pengajuan:** {row['reason']}")
                    st.caption(f"Pelapor: {row['full_name']} | Tanggal: {row['tanggal_laporan']}")
                with c2:
                    st.write("")
                    st.write("")
                    if st.button("Ambil untuk Telaah", key=f"claim_{row['report_id']}", type="primary", use_container_width=True):
                        ok, msg = service.claim_report(row['report_id'], validator_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

# ----------------- VALIDATOR: LAPORAN DITANGANI -----------------
elif menu == "Laporan Ditangani" and st.session_state.role == "validator":
    st.title("Manajemen Telaah Validator")
    st.caption("Laporan yang telah Anda klaim untuk proses verifikasi editorial dan status kurasi akhir.")
    validator_id = st.session_state.user["validator_id"]

    val_reports = service.get_validator_reports(validator_id)
    if val_reports.empty:
        st.info("Anda belum mengambil laporan dari antrean. Silakan buka menu 'Antrean Laporan' untuk memulai penelaahan.")
    else:
        v_col1, v_col2 = st.columns([3, 1])
        with v_col1:
            st.caption("Kelola evaluasi substantif dan hasil kurasi jurnal.")
        with v_col2:
            val_csv = val_reports.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Unduh Data Telaah (CSV)",
                data=val_csv,
                file_name=f"telaah_validator_{validator_id}.csv",
                mime="text/csv",
                use_container_width=True
            )

        tab_review, tab_done = st.tabs(["Sedang Ditelaah (Review)", "Selesai Dikurasi (Done)"])

        with tab_review:
            under_review = val_reports[val_reports["status_laporan"] == "review"]
            if under_review.empty:
                st.info("Tidak ada laporan yang sedang aktif dalam proses telaah.")
            else:
                for _, row in under_review.iterrows():
                    with st.expander(f"[ID: {row['report_id']}] {row['journal_name']}", expanded=True):
                        st.write(f"**URL Jurnal:** [{row['journal_url']}]({row['journal_url']})")
                        st.write(f"**Alasan Pengajuan:** {row['reason']}")
                        st.caption(f"Pelapor: {row['full_name']} | Tanggal Pengajuan: {row['tanggal_laporan']}")

                        st.markdown("##### Formulir Penilaian Kurator")
                        with st.form(f"val_form_{row['report_id']}"):
                            decision = st.selectbox(
                                "Keputusan Status Integritas Jurnal:",
                                ["aman", "predator", "clone"],
                                format_func=lambda x: {"aman": "Aman (Terverifikasi)", "predator": "Predator (Terindikasi Melanggar)", "clone": "Klon / Hijacked (Tiruan)"}[x]
                            )
                            feedback = st.text_area("Catatan Evaluasi & Dasar Pertimbangan Ilmiah:")
                            btn_val = st.form_submit_button("Simpan Keputusan Kurasi", type="primary")

                            if btn_val:
                                ok, msg = service.validate_report(row['report_id'], decision, feedback)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                        if st.button("Kembalikan Laporan ke Antrean Pending", key=f"revert_{row['report_id']}"):
                            ok, msg = service.mark_as_pending(row['report_id'])
                            if ok:
                                st.success(msg)
                                st.rerun()

        with tab_done:
            done_reports = val_reports[val_reports["status_laporan"] == "done"]
            if done_reports.empty:
                st.info("Belum ada laporan yang diselesaikan.")
            else:
                for _, row in done_reports.iterrows():
                    with st.expander(f"[ID: {row['report_id']}] {row['journal_name']} - {str(row['status_jurnal']).upper()}"):
                        st.write(f"**URL Jurnal:** [{row['journal_url']}]({row['journal_url']})")
                        st.write(f"**Status Kurasi:** {row['status_jurnal']}")
                        st.write(f"**Catatan Evaluasi:** {row['feedback']}")

                        with st.popover("Revisi Keputusan Kurasi"):
                            with st.form(f"rev_form_{row['report_id']}"):
                                new_decision = st.selectbox(
                                    "Status Jurnal:",
                                    ["aman", "predator", "clone"],
                                    index=["aman", "predator", "clone"].index(row['status_jurnal']) if row['status_jurnal'] in ["aman", "predator", "clone"] else 0
                                )
                                new_fb = st.text_area("Catatan Evaluasi:", value=row.get('feedback', ''))
                                if st.form_submit_button("Simpan Perubahan"):
                                    ok, msg = service.validate_report(row['report_id'], new_decision, new_fb)
                                    if ok:
                                        st.success(msg)
                                        st.rerun()

# ----------------- VALIDATOR: STATISTIK -----------------
elif menu == "Statistik Kurasi" and st.session_state.role == "validator":
    st.title("Kinerja & Statistik Kurasi")
    st.caption("Ringkasan aktivitas dan kontribusi penelaahan jurnal Anda.")
    val_id = st.session_state.user["validator_id"]
    stats = service.get_validator_stats(val_id)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Antrean Publik Tersedia", stats["available_pending"])
    c2.metric("Sedang Anda Telaah", stats["review"])
    c3.metric("Telah Selesai Dikurasi", stats["done"])
    c4.metric("Total Anda Tangani", stats["total_handled"])

    st.divider()
    st.subheader("Distribusi Penanganan Laporan")
    stat_df = pd.DataFrame({
        "Status Penanganan": ["Sedang Ditelaah", "Selesai Dikurasi"],
        "Jumlah Laporan": [stats["review"], stats["done"]]
    }).set_index("Status Penanganan")
    st.bar_chart(stat_df)

# ----------------- ADMIN: RINGKASAN SISTEM -----------------
elif menu == "Ringkasan Sistem" and st.session_state.role == "admin":
    st.title("Ringkasan Operasional Platform")
    st.caption("Metrik agregat pengguna, kurator, dan volume laporan verifikasi jurnal.")
    stats = service.get_system_stats()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Laporan Terdata", stats["total_reports"])
    c2.metric("Total Pengguna Terdaftar", stats["total_users"])
    c3.metric("Total Validator Aktif", stats["total_validators"])

    st.divider()
    st.subheader("Distribusi Status Alur Laporan")
    c4, c5, c6 = st.columns(3)
    c4.metric("Menunggu Validasi", stats["pending_reports"])
    c5.metric("Dalam Proses Review", stats["review_reports"])
    c6.metric("Selesai Ditelaah", stats["done_reports"])

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("##### Alur Proses Laporan")
        rep_chart_df = pd.DataFrame({
            "Tahapan": ["Pending", "Review", "Done"],
            "Jumlah": [stats["pending_reports"], stats["review_reports"], stats["done_reports"]]
        }).set_index("Tahapan")
        st.bar_chart(rep_chart_df)

    with chart_col2:
        st.markdown("##### Klasifikasi Hasil Kurasi")
        all_reps = service.get_all_reports()
        if not all_reps.empty and "status_jurnal" in all_reps.columns:
            curated = all_reps[all_reps["status_laporan"] == "done"]
            if not curated.empty:
                counts = curated["status_jurnal"].value_counts().reset_index()
                counts.columns = ["Klasifikasi", "Jumlah"]
                st.bar_chart(counts.set_index("Klasifikasi"))
            else:
                st.info("Belum ada laporan yang selesai dikurasi.")
        else:
            st.info("Data kurasi belum tersedia.")

# ----------------- ADMIN: MANAJEMEN LAPORAN -----------------
elif menu == "Manajemen Laporan" and st.session_state.role == "admin":
    st.title("Manajemen Seluruh Laporan")
    st.caption("Pengawasan terpusat atas seluruh berkas laporan dalam basis data.")
    reports_df = service.get_all_reports()

    if reports_df.empty:
        st.info("Basis data laporan masih kosong.")
    else:
        st.markdown("##### Filter & Penelusuran")
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])

        with f_col1:
            kw_search = st.text_input("Pencarian Kata Kunci (Jurnal / URL / Pelapor):", "")
        with f_col2:
            status_filter = st.selectbox("Status Alur:", ["Semua", "pending", "review", "done"])
        with f_col3:
            jurnal_filter = st.selectbox("Hasil Kurasi:", ["Semua", "aman", "predator", "clone", "belum_dinilai"])

        filtered_df = reports_df.copy()

        if kw_search.strip():
            kw = kw_search.strip().lower()
            mask = (
                filtered_df["journal_name"].astype(str).str.lower().str.contains(kw) |
                filtered_df["journal_url"].astype(str).str.lower().str.contains(kw) |
                filtered_df["full_name"].astype(str).str.lower().str.contains(kw)
            )
            filtered_df = filtered_df[mask]

        if status_filter != "Semua":
            filtered_df = filtered_df[filtered_df["status_laporan"] == status_filter]

        if jurnal_filter != "Semua":
            if jurnal_filter == "belum_dinilai":
                filtered_df = filtered_df[filtered_df["status_jurnal"].isna() | (filtered_df["status_jurnal"].astype(str).str.strip() == "")]
            else:
                filtered_df = filtered_df[filtered_df["status_jurnal"] == jurnal_filter]

        top_col1, top_col2 = st.columns([3, 1])
        with top_col1:
            st.write(f"Menampilkan **{len(filtered_df)}** dari **{len(reports_df)}** rekaman laporan:")
        with top_col2:
            csv_export = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Unduh Rekap Laporan (CSV)",
                data=csv_export,
                file_name="rekap_laporan_lengkap.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.dataframe(
            filtered_df,
            column_config={
                "report_id": st.column_config.NumberColumn("ID", format="%d"),
                "journal_url": st.column_config.LinkColumn("Tautan Jurnal"),
                "journal_name": st.column_config.TextColumn("Nama Jurnal"),
                "status_laporan": st.column_config.TextColumn("Status Alur"),
                "status_jurnal": st.column_config.TextColumn("Hasil Kurasi"),
                "tanggal_laporan": st.column_config.TextColumn("Tanggal Pengajuan")
            },
            use_container_width=True,
            hide_index=True
        )

# ----------------- ADMIN: KELOLA VALIDATOR -----------------
elif menu == "Manajemen Validator" and st.session_state.role == "admin":
    st.title("Manajemen Validator Akademik")
    st.caption("Pendaftaran akun penelaah kredibel dan pengaturan profil keanggotaan kurator.")
    tab_val_list, tab_val_add = st.tabs(["Daftar Kurator Terdaftar", "Pendaftaran Kurator Baru"])

    with tab_val_list:
        vals_df = service.get_all_validators()
        if vals_df.empty:
            st.info("Belum ada validator yang terdaftar dalam sistem.")
        else:
            e_col1, e_col2 = st.columns([3, 1])
            with e_col1:
                st.write(f"Total Kurator Terdaftar: **{len(vals_df)}**")
            with e_col2:
                csv_vals = vals_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Unduh Data Kurator (CSV)",
                    data=csv_vals,
                    file_name="data_validator.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            for _, v in vals_df.iterrows():
                with st.expander(f"[ID: {v['validator_id']}] {v['full_name']} (@{v['username']})"):
                    st.write(f"**Email:** {v['email']} | **Institusi:** {v['instancy']} | **Jabatan Fungsional:** {v['academic_position']}")
                    st.write(f"**Profil Akademik:** Scopus: {v.get('scopus_url', '-')} | SINTA: {v.get('sinta_url', '-')} | Scholar: {v.get('google_scholar_url', '-')}")

                    b1, b2, b3 = st.columns(3)
                    with b1:
                        with st.popover("Edit Profil"):
                            with st.form(f"edit_val_{v['validator_id']}"):
                                ef_name = st.text_input("Nama Lengkap & Gelar", value=v['full_name'])
                                ef_email = st.text_input("Email", value=v['email'])
                                ef_instancy = st.text_input("Institusi", value=v['instancy'])
                                ef_pos = st.text_input("Jabatan Fungsional", value=v['academic_position'])
                                ef_scopus = st.text_input("Scopus URL", value=v['scopus_url'])
                                ef_sinta = st.text_input("Sinta URL", value=v['sinta_url'])
                                ef_scholar = st.text_input("Scholar URL", value=v['google_scholar_url'])
                                if st.form_submit_button("Simpan Perubahan"):
                                    ok, msg = service.update_validator_info(v['validator_id'], ef_name, ef_email, ef_instancy, ef_pos, ef_scopus, ef_sinta, ef_scholar)
                                    if ok:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    with b2:
                        with st.popover("Reset Password"):
                            with st.form(f"reset_val_{v['validator_id']}"):
                                new_pwd = st.text_input("Password Baru (Min. 8 Karakter)", type="password")
                                if st.form_submit_button("Reset Password"):
                                    ok, msg = service.change_validator_password(v['validator_id'], new_pwd)
                                    if ok:
                                        st.success(msg)
                                    else:
                                        st.error(msg)
                    with b3:
                        with st.popover("Hapus Akun Validator"):
                            st.warning(f"Hapus kurator {v['full_name']}?")
                            if st.button("Konfirmasi Hapus", key=f"del_val_{v['validator_id']}", type="primary"):
                                service.delete_validator(v['validator_id'])
                                st.success("Akun validator berhasil dihapus.")
                                st.rerun()

    with tab_val_add:
        st.subheader("Registrasi Kurator Akademik Baru")
        st.caption("Validator harus merupakan akademisi atau peneliti terverifikasi dengan rekam jejak publikasi ilmiah.")
        with st.form("form_add_val"):
            v_user = st.text_input("Username (Min. 8 karakter alfanumerik):")
            v_pass = st.text_input("Password (Min. 8 karakter):", type="password")
            v_name = st.text_input("Nama Lengkap Beserta Gelar Akademik:")
            v_email = st.text_input("Email Resmi / Institusi:")
            v_inst = st.text_input("Institusi Afiliasi:")
            v_pos = st.text_input("Jabatan Fungsional Akademik (cth: Lektor Kepala / Guru Besar):")
            v_scopus = st.text_input("URL Profil Scopus:", placeholder="https://www.scopus.com/authid/detail.uri?authorId=...")
            v_sinta = st.text_input("URL Profil SINTA:", placeholder="https://sinta.kemdikbud.go.id/authors/profile/...")
            v_scholar = st.text_input("URL Profil Google Scholar:", placeholder="https://scholar.google.com/citations?user=...")

            submit_val = st.form_submit_button("Daftarkan Validator", type="primary")
            if submit_val:
                ok, msg = service.register_validator(v_user, v_pass, v_name, v_email, v_inst, v_pos, v_scopus, v_sinta, v_scholar)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# ----------------- ADMIN: KELOLA PENGGUNA -----------------
elif menu == "Manajemen Pengguna" and st.session_state.role == "admin":
    st.title("Manajemen Pengguna Terdaftar")
    st.caption("Daftar pengguna umum yang memiliki hak mengajukan laporan ke sistem.")
    users_df = service.get_all_users()
    if users_df.empty:
        st.info("Belum ada akun pengguna terdaftar.")
    else:
        u_col1, u_col2 = st.columns([3, 1])
        with u_col1:
            st.write(f"Total Pengguna Terdaftar: **{len(users_df)}**")
        with u_col2:
            csv_users = users_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Unduh Data Pengguna (CSV)",
                data=csv_users,
                file_name="data_pengguna.csv",
                mime="text/csv",
                use_container_width=True
            )

        for _, u in users_df.iterrows():
            with st.expander(f"[ID: {u['user_id']}] {u['full_name']} (@{u['username']})"):
                st.write(f"**Email:** {u['email']} | **Institusi:** {u['instancy']}")
                with st.popover("Hapus Akun Pengguna"):
                    st.warning(f"Hapus pengguna @{u['username']}?")
                    if st.button("Konfirmasi Hapus", key=f"del_user_{u['user_id']}", type="primary"):
                        service.delete_user(u['user_id'])
                        st.success("Akun pengguna berhasil dihapus.")
                        st.rerun()
