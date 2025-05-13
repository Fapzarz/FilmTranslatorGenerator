# Film Translator Generator

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a name="english"></a>
<details open>
<summary><strong>English</strong></summary>

## Description

A simple desktop application for transcribing audio from video files using Faster-Whisper and translating the text using Google Gemini API to generate subtitle files in various formats.

### Features

*   Modern user interface with Sun Valley theme (sv-ttk) and panel-based layout
*   **Video Queue Management**: Add, remove, and process multiple video files sequentially.
*   **Project Save/Load**: Save your current queue, processed data, and settings into a `.ftgproj` file and load it back later.
*   **Basic Subtitle Editor**: Edit the text and timestamps of generated subtitles directly within the application.
*   **Preview Video with Subtitles**: Attempt to open the selected video with its generated subtitles in your default media player.
*   **Multiple Translation API Support**: Choose between Google Gemini, OpenAI, Anthropic Claude, and DeepSeek for translations.
*   **Model Selection for Providers**: 
    *   Select specific models for Gemini (`gemini-2.5-flash-preview-04-17` or `gemini-2.5-pro-exp-03-25`)
    *   Choose from OpenAI models (GPT-4.1, GPT-4o, etc.) 
    *   Select Anthropic models (Claude 3 Opus, Claude 3.7 Sonnet, etc.)
*   Video preview with thumbnails and information
*   **Multiple Output Format Support:** Choose between `SRT`, `VTT`, or `TXT` formats
*   **Side-by-Side Comparison:** View original text and translation side-by-side
*   **Whisper Model Selection:** Choose between `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`
*   **Device & Computation Selection:** Choose `cuda` or `cpu` and the appropriate computation type (`float16`, `int8`, etc.)
*   **Advanced Gemini API Settings**: Customize Temperature, Top-P, and Top-K for translations.
*   **Advanced Settings:** Configure batch size, theme, accent color, and automatic features
*   **Modular Structure:** Code organized in separate modules for easier development
*   Video transcription using Faster-Whisper
*   Text translation using multiple AI providers:
    * Google Gemini API:
      * `gemini-2.5-flash-preview-04-17` (faster processing)
      * `gemini-2.5-pro-exp-03-25` (higher quality for complex translations)
    * OpenAI API (GPT-4.1, GPT-4o, GPT-3.5-turbo, etc.)
    * Anthropic API (Claude 3 Opus, Claude 3.5 Sonnet, etc.)
    * DeepSeek API (via DeepSeek-chat)
*   Comprehensive settings storage in `config.json`

### Requirements

*   Python 3.8+
*   `ffmpeg` (Must be installed and in your system PATH. Download from [https://ffmpeg.org/](https://ffmpeg.org/))
*   CUDA Toolkit & cuDNN (Recommended for GPU acceleration with Faster-Whisper. Ensure compatible versions are installed)
*   API Keys (Choose at least one based on your preferred translation provider):
*   Google Gemini API Key (Get from [Google AI Studio](https://aistudio.google.com/app/apikey))
    *   OpenAI API Key (Get from [OpenAI Platform](https://platform.openai.com/api-keys))
    *   Anthropic API Key (Get from [Anthropic Console](https://console.anthropic.com/))
    *   DeepSeek API Key (Get from [DeepSeek Platform](https://platform.deepseek.com/))

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
    *   Click "Add Video(s)" to select your video file(s)
    *   Select your preferred translation provider (Gemini, OpenAI, Anthropic, or DeepSeek)
    *   Enter the API Key for your selected provider
    *   If applicable, select the specific model for your provider
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

This project is licensed under the [GNU Affero General Public License v3 (AGPLv3)](LICENSE).

### Changelog

For a detailed history of changes, please see the [CHANGELOG.md](CHANGELOG.md) file.

### Documentation

More detailed documentation is available in the [GitHub repository](https://github.com/Fapzarz/FilmTranslatorGenerator).

</details>

<a name="bahasa-indonesia"></a>
<details>
<summary><strong>Bahasa Indonesia</strong></summary>

## Deskripsi

Aplikasi desktop sederhana untuk mentranskripsi audio dari file video menggunakan Faster-Whisper dan menerjemahkan teksnya menggunakan Google Gemini API untuk menghasilkan file subtitle dalam berbagai format.

### Fitur

*   Antarmuka pengguna modern dengan tema Sun Valley (sv-ttk) dan tata letak berbasis panel
*   **Manajemen Antrean Video**: Tambah, hapus, dan proses beberapa file video secara berurutan.
*   **Simpan/Muat Proyek**: Simpan antrean saat ini, data yang telah diproses, dan pengaturan ke dalam file `.ftgproj` dan muat kembali nanti.
*   **Editor Subtitle Dasar**: Edit teks dan stempel waktu dari subtitle yang dihasilkan langsung di dalam aplikasi.
*   **Pratinjau Video dengan Subtitle**: Coba buka video yang dipilih beserta subtitle yang dihasilkan di pemutar media default Anda.
*   **Dukungan Berbagai API Terjemahan**: Pilih antara Google Gemini, OpenAI, Anthropic Claude, dan DeepSeek untuk terjemahan.
*   **Pemilihan Model untuk Provider**: 
    *   Pilih model spesifik untuk Gemini (`gemini-2.5-flash-preview-04-17` atau `gemini-2.5-pro-exp-03-25`)
    *   Pilih dari model OpenAI (GPT-4.1, GPT-4o, dll.)
    *   Pilih model Anthropic (Claude 3 Opus, Claude 3.5 Sonnet, dll.)
*   Pratinjau video dengan thumbnail dan informasi
*   **Multiple Output Format Support:** Pilih antara format `SRT`, `VTT`, atau `TXT`
*   **Perbandingan Side-by-Side:** Lihat teks asli dan terjemahan secara berdampingan
*   **Pilihan Model Whisper:** Pilih antara `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`
*   **Pilihan Perangkat & Komputasi:** Pilih `cuda` atau `cpu` dan tipe komputasi yang sesuai (`float16`, `int8`, dll.)
*   **Pengaturan Lanjutan Gemini API**: Kustomisasi Temperature, Top-P, dan Top-K untuk terjemahan.
*   **Pengaturan Lanjutan:** Atur ukuran batch, tema, warna aksen, dan fitur otomatis
*   **Modular Structure:** Kode diatur dalam modul terpisah untuk memudahkan pengembangan
*   Transkripsi video menggunakan Faster-Whisper
*   Terjemahan teks menggunakan berbagai provider AI:
    * Google Gemini API:
      * `gemini-2.5-flash-preview-04-17` (pemrosesan lebih cepat)
      * `gemini-2.5-pro-exp-03-25` (kualitas lebih tinggi untuk terjemahan kompleks)
    * OpenAI API (GPT-4.1, GPT-4o, GPT-3.5-turbo, dll.)
    * Anthropic API (Claude 3 Opus, Claude 3.5 Sonnet, dll.) 
    * DeepSeek API (melalui DeepSeek-chat)
*   Penyimpanan pengaturan yang komprehensif di `config.json`

### Persyaratan

*   Python 3.8+
*   `ffmpeg` (Harus terinstal dan ada di PATH sistem Anda. Unduh dari [https://ffmpeg.org/](https://ffmpeg.org/))
*   CUDA Toolkit & cuDNN (Direkomendasikan untuk akselerasi GPU dengan Faster-Whisper. Pastikan versi kompatibel terinstal)
*   API Keys (Pilih setidaknya satu berdasarkan provider terjemahan yang Anda inginkan):
*   Google Gemini API Key (Dapatkan dari [Google AI Studio](https://aistudio.google.com/app/apikey))
    *   OpenAI API Key (Dapatkan dari [OpenAI Platform](https://platform.openai.com/api-keys))
    *   Anthropic API Key (Dapatkan dari [Anthropic Console](https://console.anthropic.com/))
    *   DeepSeek API Key (Dapatkan dari [DeepSeek Platform](https://platform.deepseek.com/))

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
    *   Klik "Add Video(s)" untuk menambahkan file video ke antrean
    *   Pilih provider terjemahan yang Anda inginkan (Gemini, OpenAI, Anthropic, atau DeepSeek)
    *   Masukkan API Key untuk provider yang Anda pilih
    *   Jika diperlukan, pilih model spesifik untuk provider Anda
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
*   `gui/`: UI components and main application class

### Lisensi

Proyek ini dilisensikan di bawah [GNU Affero General Public License v3 (AGPLv3)](LICENSE).

### Changelog

Untuk riwayat perubahan yang detail, silakan lihat file [CHANGELOG.md](CHANGELOG.md).

### Dokumentasi

Dokumentasi lebih lengkap tersedia di [GitHub repository](https://github.com/Fapzarz/FilmTranslatorGenerator).

</details>
