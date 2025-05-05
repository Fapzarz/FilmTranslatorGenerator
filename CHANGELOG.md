# Changelog

Semua perubahan penting pada proyek ini akan didokumentasikan dalam file ini.

Format didasarkan pada [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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

## [1.0] - 2025-05-04 (Tanggal Perkiraan)

### Added
- Fungsionalitas dasar: Transkripsi video dengan Faster-Whisper (`large-v2`).
- Terjemahan dengan Google Gemini API (`gemini-2.5-flash-preview-04-17`) secara batch.
- Pembuatan file SRT.
- GUI dasar menggunakan Tkinter.
- Penanganan error dasar.
- Penyimpanan API Key ke `config.json` (versi awal).
- File `.gitignore`.
- File `requirements.txt` awal.
