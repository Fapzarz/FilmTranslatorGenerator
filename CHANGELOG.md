# Changelog

Semua perubahan penting pada proyek ini akan didokumentasikan dalam file ini.

Format didasarkan pada [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.1.1] - 2025-05-11

### Fixed
- `UnboundLocalError` untuk `progress_action_frame` di `gui/app.py` karena urutan definisi dan pemaketan widget yang salah dalam `create_main_frame`.
- `NameError` untuk `APP_VERSION` di `gui/app.py` karena tidak diimpor dari `config.py` (sebelum akhirnya dihapus dari UI).
- Upaya perbaikan berkelanjutan untuk kesalahan indentasi dan struktur `try-except-finally` di `process_video_thread` dalam `gui/app.py` yang terdeteksi oleh linter.


## [2.1] - 2025-05-11

### Added
- **Manajemen Antrean Video**: Tambah, hapus, dan proses beberapa file video secara berurutan.
- **Editor Subtitle Dasar**: Edit teks dan timestamp subtitle yang dihasilkan langsung di aplikasi.
- **Simpan & Muat Proyek**: Simpan status antrean, data terproses, dan pengaturan ke file proyek (.ftgproj) dan muat kembali.
- **Kustomisasi Parameter Gemini API**: Atur Temperature, Top-P, dan Top-K untuk API Gemini melalui Pengaturan Lanjutan.
- **Pratinjau Video dengan Subtitle**: Buka video yang dipilih dengan file subtitle sementara yang dihasilkan.
- **Peningkatan Tata Letak UI**: Mengadopsi tata letak berbasis panel yang lebih terstruktur (mirip Adobe) menggunakan PanedWindow untuk meningkatkan pengalaman pengguna.

### Changed
- Label versi aplikasi dihapus dari status bar UI.
- Model default Gemini API diverifikasi menggunakan versi `gemini-2.5-flash-preview-04-17`.

### Fixed
- `KeyError` saat memuat konfigurasi default untuk parameter Gemini API.
- Berbagai kesalahan indentasi dan struktur `try-except` di `gui/app.py` (terdeteksi oleh linter).
- `NameError` untuk `APP_VERSION` di `gui/app.py` saat menampilkan label versi (sebelum dihapus).

## [2.0] - 2025-05-10

### Added
- Desain UI modern menggunakan tema Sun Valley (sv-ttk)
- Pratinjau video dengan thumbnail
- Dukungan multi-format output (SRT, VTT, TXT)
- Perbandingan teks asli dengan terjemahan secara side-by-side
- Pelacakan progres yang ditingkatkan
- Dialog pengaturan lanjutan
- Menu tentang aplikasi (About) dan dokumentasi
- Implementasi struktur kode modular:
  - `config.py`: Pengaturan konfigurasi dan konstanta
  - `utils/`: Utilitas pemformatan dan penanganan media
  - `backend/`: Fungsionalitas transkripsi dan terjemahan
  - `gui/`: Komponen UI dan kelas aplikasi utama
- Antarmuka yang responsif dengan pengaturan ukuran minimum jendela
- Sistem tema (terang/gelap) dan warna aksen yang dapat dikustomisasi
- Dokumentasi lebih lengkap tersedia di [GitHub](https://github.com/Fapzarz/FilmTranslatorGenerator)

### Changed
- Struktur kode direfaktor dari monolitik menjadi modular
- Antarmuka baru yang lebih intuitif dan modern
- Peningkatan penanganan error dan dukungan fallback untuk terjemahan
- Peningkatan pengaturan ukuran batch terjemahan
- Sistem pengaturan yang diperluas
- Proses pembuatan subtitle yang dioptimalkan

## [1.1] - 2025-05-05

### Added
- Fitur pemilihan model Faster-Whisper (tiny, base, small, medium, large-v2, large-v3).
- Fitur pemilihan perangkat (cuda/cpu) dan tipe komputasi (float16, int8, dll.) untuk Faster-Whisper.
- Penyimpanan otomatis pengaturan (API Key, model, perangkat, tipe komputasi, bahasa target) ke file `config.json`.
- Pemuatan otomatis pengaturan dari `config.json` saat aplikasi dimulai.
- Pemuatan ulang model Whisper secara otomatis jika pengaturan diubah oleh pengguna.
- File `CHANGELOG.md` ini.
- File `LICENSE` (MIT).

### Changed
- Memperbarui `README.md` dengan fitur baru dan instruksi.
- Memperbarui `requirements.txt`.
- Memindahkan pemanggilan `_load_config` di `__init__` untuk memperbaiki `AttributeError`.
- Ukuran jendela aplikasi disesuaikan untuk mengakomodasi opsi baru.

### Removed
- Logika offset waktu mulai subtitle (delay 300ms) yang sebelumnya ditambahkan.
- Fungsi pembersihan VRAM eksplisit setelah transkripsi (model sekarang dikelola oleh logika pemuatan ulang).

## [1.0] - 2025-05-04

### Added
- Fungsionalitas dasar: Transkripsi video dengan Faster-Whisper (`large-v2`).
- Terjemahan dengan Google Gemini API (`gemini-2.5-flash-preview-04-17`) secara batch.
- Pembuatan file SRT.
- GUI dasar menggunakan Tkinter.
- Penanganan error dasar.
- Penyimpanan API Key ke `config.json` (versi awal).
- File `.gitignore`.
- File `requirements.txt` awal.
