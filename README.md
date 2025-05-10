# Film Translator Generator v2.0

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a name="english"></a>
<details open>
<summary><strong>English</strong></summary>

## Description

A simple desktop application for transcribing audio from video files using Faster-Whisper and translating the text using Google Gemini API to generate subtitle files in various formats.

### Features

*   Modern user interface with Sun Valley theme (sv-ttk)
*   Video preview with thumbnails and information
*   **Multiple Output Format Support:** Choose between `SRT`, `VTT`, or `TXT` formats
*   **Side-by-Side Comparison:** View original text and translation side-by-side
*   **Whisper Model Selection:** Choose between `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`
*   **Device & Computation Selection:** Choose `cuda` or `cpu` and the appropriate computation type (`float16`, `int8`, etc.)
*   **Advanced Settings:** Configure batch size, theme, accent color, and automatic features
*   **Modular Structure:** Code organized in separate modules for easier development
*   Video transcription using Faster-Whisper
*   Text translation using Google Gemini API (`gemini-2.5-flash-preview-04-17`)
*   Comprehensive settings storage in `config.json`

### Requirements

*   Python 3.8+
*   `ffmpeg` (Must be installed and in your system PATH. Download from [https://ffmpeg.org/](https://ffmpeg.org/))
*   CUDA Toolkit & cuDNN (Recommended for GPU acceleration with Faster-Whisper. Ensure compatible versions are installed)
*   Google Gemini API Key (Get from [Google AI Studio](https://aistudio.google.com/app/apikey))

### Installation

1.  **Clone repository:**
    ```bash
    git clone https://github.com/Fapzarz/FilmTranslatorGenerator.git
    cd FilmTranslatorGenerator
    ```
2.  **(Recommended) Create and activate virtual environment:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```
    ```bash
    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Ensure `ffmpeg` is installed** and its path is correct in your system environment variables
5.  **Ensure CUDA Toolkit and cuDNN are installed** correctly if you want to use GPU acceleration (highly recommended for large models)

### Usage

1.  Run the application:
    ```bash
    python main.py
    ```
2.  In the application window:
    *   Click "Browse..." to select your video file
    *   Enter your Google Gemini API Key (will be saved for future use)
    *   Select the target translation language and output format
    *   Select Whisper settings (Model, Device, Compute Type)
    *   Click "Generate Subtitles"
3.  Wait for the transcription and translation process to complete. Status will be displayed in the "Log" tab
    *   *Note:* Downloading the Faster-Whisper model may take a long time when run for the first time
4.  Once complete, you can view the results in the "Output" tab and compare the original text with the translation in the "Original vs Translation" tab
5.  Use the "Save As" button to save the results to a file

### Code Structure

This project uses a modular structure to facilitate development and maintenance:

*   `main.py`: Application entry point
*   `config.py`: Configuration settings and constants
*   `utils/`: Formatting and media handling utilities
*   `backend/`: Transcription and translation functionality
*   `gui/`: UI components and main application class

### License

This project is licensed under the [MIT License](LICENSE).

### Documentation

More detailed documentation is available in the [GitHub repository](https://github.com/Fapzarz/FilmTranslatorGenerator).

</details>

<a name="bahasa-indonesia"></a>
<details>
<summary><strong>Bahasa Indonesia</strong></summary>

## Deskripsi

Aplikasi desktop sederhana untuk mentranskripsi audio dari file video menggunakan Faster-Whisper dan menerjemahkan teksnya menggunakan Google Gemini API untuk menghasilkan file subtitle dalam berbagai format.

### Fitur

*   Antarmuka pengguna modern dengan tema Sun Valley (sv-ttk)
*   Pratinjau video dengan thumbnail dan informasi
*   **Dukungan Multiple Output Format:** Pilih antara format `SRT`, `VTT`, atau `TXT`
*   **Perbandingan Side-by-Side:** Lihat teks asli dan terjemahan secara berdampingan
*   **Pilihan Model Whisper:** Pilih antara `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`
*   **Pilihan Perangkat & Komputasi:** Pilih `cuda` atau `cpu` dan tipe komputasi yang sesuai (`float16`, `int8`, dll.)
*   **Pengaturan Lanjutan:** Atur ukuran batch, tema, warna aksen, dan fitur otomatis
*   **Struktur Modular:** Kode diatur dalam modul terpisah untuk memudahkan pengembangan
*   Transkripsi video menggunakan Faster-Whisper
*   Terjemahan teks menggunakan Google Gemini API (`gemini-2.5-flash-preview-04-17`)
*   Penyimpanan pengaturan yang komprehensif di `config.json`

### Persyaratan

*   Python 3.8+
*   `ffmpeg` (Harus terinstal dan ada di PATH sistem Anda. Unduh dari [https://ffmpeg.org/](https://ffmpeg.org/))
*   CUDA Toolkit & cuDNN (Direkomendasikan untuk akselerasi GPU dengan Faster-Whisper. Pastikan versi kompatibel terinstal)
*   Google Gemini API Key (Dapatkan dari [Google AI Studio](https://aistudio.google.com/app/apikey))

### Instalasi

1.  **Clone repository:**
    ```bash
    git clone https://github.com/Fapzarz/FilmTranslatorGenerator.git
    cd FilmTranslatorGenerator
    ```
2.  **(Direkomendasikan) Buat dan aktifkan virtual environment:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```
    ```bash
    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Instal dependensi Python:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Pastikan `ffmpeg` terinstal** dan path-nya sudah benar di environment variable sistem Anda
5.  **Pastikan CUDA Toolkit dan cuDNN terinstal** dengan benar jika Anda ingin menggunakan akselerasi GPU (sangat direkomendasikan untuk model besar)

### Penggunaan

1.  Jalankan aplikasi:
    ```bash
    python main.py
    ```
2.  Di jendela aplikasi:
    *   Klik "Browse..." untuk memilih file video Anda
    *   Masukkan Google Gemini API Key Anda (akan disimpan untuk penggunaan berikutnya)
    *   Pilih bahasa target terjemahan dan format output
    *   Pilih pengaturan Whisper (Model, Device, Compute Type)
    *   Klik "Generate Subtitles"
3.  Tunggu proses transkripsi dan terjemahan selesai. Status akan ditampilkan di tab "Log"
    *   *Catatan:* Pengunduhan model Faster-Whisper mungkin memakan waktu lama saat pertama kali dijalankan
4.  Setelah selesai, Anda dapat melihat hasil di tab "Output" dan membandingkan teks asli dengan terjemahan di tab "Original vs Translation"
5.  Gunakan tombol "Save As" untuk menyimpan hasil ke file

### Struktur Kode

Proyek ini menggunakan struktur modular untuk memudahkan pengembangan dan pemeliharaan:

*   `main.py`: Entry point aplikasi
*   `config.py`: Pengaturan konfigurasi dan konstanta
*   `utils/`: Utilitas pemformatan dan penanganan media
*   `backend/`: Fungsionalitas transkripsi dan terjemahan
*   `gui/`: Komponen UI dan kelas aplikasi utama

### Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).

### Dokumentasi

Dokumentasi lebih lengkap tersedia di [GitHub repository](https://github.com/Fapzarz/FilmTranslatorGenerator).

</details>
