# Film Translator Generator

Aplikasi desktop sederhana untuk mentranskripsi audio dari file video menggunakan Faster-Whisper dan menerjemahkan teksnya menggunakan Google Gemini API untuk menghasilkan file subtitle (.srt).

## Fitur

*   Antarmuka pengguna grafis (GUI) menggunakan Tkinter (`app_gui.py`).
*   Transkripsi video menggunakan model `large-v2` dari Faster-Whisper (dioptimalkan untuk kecepatan).
*   Terjemahan teks menggunakan Google Gemini API (`gemini-2.5-flash-preview-04-17`).
*   Mengirim teks ke Gemini dalam batch untuk efisiensi.
*   Penyesuaian waktu mulai subtitle untuk mengurangi *delay*.
*   Pemilihan bahasa target terjemahan melalui dropdown.
*   Menghasilkan output dalam format file SubRip (`.srt`).

## Persyaratan

*   Python 3.8+
*   `ffmpeg` (Harus terinstal dan ada di PATH sistem Anda. Unduh dari [https://ffmpeg.org/](https://ffmpeg.org/))
*   CUDA Toolkit & cuDNN (Direkomendasikan untuk akselerasi GPU dengan Faster-Whisper. Pastikan versi kompatibel terinstal).
*   Google Gemini API Key (Dapatkan dari [Google AI Studio](https://aistudio.google.com/app/apikey)).

## Instalasi

1.  **Clone repository:**
    ```bash
    git clone <URL_REPOSITORY_ANDA>
    cd <NAMA_FOLDER_PROYEK>
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
4.  **Pastikan `ffmpeg` terinstal** dan path-nya sudah benar di environment variable sistem Anda.
5.  **Pastikan CUDA Toolkit dan cuDNN terinstal** dengan benar jika Anda ingin menggunakan akselerasi GPU (sangat direkomendasikan untuk model `large-v2`).

## Penggunaan

1.  Jalankan aplikasi:
    ```bash
    python app_gui.py
    ```
2.  Di jendela aplikasi:
    *   Klik "Browse..." untuk memilih file video Anda.
    *   Masukkan Google Gemini API Key Anda.
    *   Pilih bahasa target terjemahan dari dropdown.
    *   Klik "Generate Subtitles".
3.  Tunggu proses transkripsi dan terjemahan selesai. Status akan ditampilkan di area log.
    *   *Catatan:* Pengunduhan model Faster-Whisper (`large-v2`) mungkin memakan waktu lama saat pertama kali dijalankan.
4.  Setelah selesai, dialog "Save As" akan muncul untuk menyimpan file `.srt`. Hasil SRT juga akan ditampilkan di GUI.

## Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).
