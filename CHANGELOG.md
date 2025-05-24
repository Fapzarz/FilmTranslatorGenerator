# Changelog

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a name="english"></a>
<details open>
<summary><strong>English</strong></summary>

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.0.0] - 2025-05-24

### Added
- **Integrated Security System**: All security functions moved from standalone script to `utils/crypto.py`
- **Comprehensive Cryptographic Module**: Complete module documentation with security features
- **Automated Security Checks**: Built-in API key protection and vulnerability detection
- **Latest Anthropic Models**: Added support for Claude-4 series models:
  - `claude-opus-4-20250514` - Latest Claude 4 Opus model
  - `claude-sonnet-4-20250514` - Latest Claude 4 Sonnet model
- **Advanced GPU Optimization**: Comprehensive GPU acceleration enhancements:
  - Real-time hardware detection and optimal settings recommendation
  - Automatic memory management and cleanup
  - Performance monitoring with detailed analytics and suggestions
  - Smart batch size optimization based on available GPU memory
- **Windows Notifications System**: Native Windows notification integration:
  - Processing completion notifications with sound alerts
  - Queue completion statistics and timing information
  - Error notifications with detailed troubleshooting info
  - Configurable notification preferences and urgency levels

### Changed  
- **Security Architecture**: Consolidated security functions into crypto module for better organization
- **Code Structure**: Improved modularity with cleaner separation of concerns
- **Documentation**: Enhanced crypto module documentation with complete function descriptions

### Fixed
- **Security Vulnerabilities**: Resolved all exposed API key issues automatically
- **Code Organization**: Eliminated standalone security files for cleaner project structure
- **Import Dependencies**: Added missing `anthropic` dependency to requirements.txt

### Security
- **API Key Encryption**: All API keys now automatically encrypted using machine-specific keys
- **Vulnerability Prevention**: Proactive security scanning and automatic fixes
- **Zero Configuration Security**: Security features work out-of-the-box without user intervention

## [3.0.0-RC1] - 2025-05-20

### Added
- Dokumentasi lengkap dalam format HTML dengan panduan API, fitur lanjutan, dan troubleshooting
- Implementasi enkripsi API key untuk keamanan data sensitif
- Validasi input yang komprehensif di seluruh aplikasi

### Changed
- Refaktorisasi kode dengan memisahkan modul berdasarkan fungsi terkait
- Pembaruan antarmuka pengguna dengan tampilan yang lebih modern

### Fixed
- Masalah keamanan dengan penyimpanan API key
- Berbagai bug dan peningkatan stabilitas aplikasi

## [3.0.0-ALPHA 1] - 2025-05-19

### Added
- **Complete UI Framework Migration**: Rebuilt the entire application using PySide6 (Qt) framework, replacing the previous Tkinter implementation:
  - Modern, responsive UI with better controls and layout capabilities
  - Native look and feel across different platforms
  - Improved video handling with proper hardware acceleration
  - Support for more complex UI components and interactions
- **Advanced Subtitle Editor Dialog**: Complete overhaul of the subtitle editing experience:
  - Large video player with direct playback controls
  - Millisecond precision timing controls
  - Table view with all subtitle segments
  - Real-time subtitle preview directly on video
  - CPS (Characters Per Second) and CPL (Characters Per Line) readability indicators
  - Improved styling options and preview
  - Undo/Redo functionality for all editing operations

### Changed
- **Complete Architectural Overhaul**: Major refactoring of the application's architecture for the PySide6 migration:
  - Reorganized code structure with clear separation between UI and logic
  - Introduced dialog-based workflows for complex operations
  - Redesigned managers system for better modularity
  - Created new module structure with dedicated directories for dialogs and managers
- **Enhanced Subtitle Display**: Replaced QLabel-based overlay with QGraphicsView architecture for more reliable subtitle rendering:
  - Subtitle text now consistently visible on top of video content in all environments
  - Maintains proper font size regardless of video scaling
  - Automatic adjustment of subtitle position and style during playback
  - Proper word-wrapping and alignment for multi-line subtitles
- **Main UI Simplification**: Removed embedded video player from main window, replaced with dedicated advanced editor dialog
- **Improved Code Structure**: Further modularized subtitle editing and display code

### Fixed
- Video player control issues where playback controls were occasionally unresponsive
- Audio continuing to play after closing the editor dialog
- Subtitle overlay display issues on different platforms
- Layout problems with the video control panel

## [2.5.10] - 2025-05-20

### Changed
- **Refactored `PreviewManager`**: Moved video preview and preview-with-subtitles logic from `gui/app.py` to the new `gui/preview_manager.py` module for better modularity.
- **Code Cleanup in `gui/app.py`**: Removed residual code (commented-out methods and old logic blocks) related to functionalities previously moved to `ShortcutManager` and `PreviewManager`, resulting in a leaner `AppGUI` class.
- **Notebook Button Configuration**: Ensured that buttons within the notebook tabs (Copy, Save As, Preview with Subtitles, Apply Editor Changes) in `gui/app.py` are correctly configured to call their respective methods, including those from the new `PreviewManager` and existing `EditorManager`.

### Improved
- Improved code organization and maintainability by further decoupling functionalities from `gui/app.py`.

## [2.5.5] - 2025-05-17

### Changed
- **Major Code Refactoring**: Significantly refactored the `gui/app.py` module by splitting its functionalities into several dedicated manager and styler modules:
  - `gui/main_layout.py`: Handles the creation of left and right UI panes.
  - `gui/project_manager.py`: Manages project saving and loading logic.
  - `gui/queue_manager.py`: Controls video queue management logic.
  - `gui/video_processor.py`: Contains video processing logic and Whisper model loading.
  - `gui/subtitle_styler.py`: Manages subtitle styling, style preview, and application to SRT files.
  - `gui/editor_manager.py`: Handles logic for loading, parsing, and applying changes from the subtitle editor.
- This refactoring improves code organization, maintainability, and scalability.

### Fixed
- Corrected video path retrieval in the `preview_video` function in `gui/app.py`.
- Removed an unused `re` import from `gui/app.py`.
- Removed a redundant `_update_queue_statistics` method from `gui/app.py` as its functionality is handled by `gui/queue_manager.py`.

### Improved
- Subtitle editor now automatically refreshes its content after applying changes, showing the parsed and cleaned segments.
- Configuration saving is no longer triggered on every subtitle style change for a specific video; style data is saved with project or main configuration saves.

## [2.2.5] - 2025-05-13

### Added
- **Multiple Gemini Models Support**: Added ability to choose between Gemini models:
  - `gemini-2.5-flash-preview-04-17` (default): Optimized for faster response
  - `gemini-2.5-pro-exp-03-25`: Higher quality for more complex translations
- **Improved UI Layout**: Enhanced panel proportions and better subtitle style preview
  - Adjusted left panel width for better visibility of controls
  - Fixed subtitle style preview positioning to properly center text
  - Added automatic repositioning on window resize for subtitle preview

### Fixed
- Indentation issues in `backend/translate.py` related to batch translation
- Improved error handling for subtitle style preview
- Fixed layout issues with queue panel display
- Corrected configuration loading for subtitle styles

## [2.2.0] - 2025-05-12

### Added
- **Multiple Translation API Support**: Integration with several translation API providers:
  - OpenAI (GPT-4.1, GPT-4o, GPT-3.5-turbo, etc.)
  - Anthropic Claude (Claude 3 Opus, Claude 3.5 Sonnet, etc.) 
  - DeepSeek (via DeepSeek-chat)
- **Translation Provider Selection UI**: Dynamic provider selection dialog with provider-specific configurations
- **API Key & Model Storage**: All API keys and model selections for each provider stored in configuration
- **Dynamic UI**: Self-adapting interface based on the selected translation provider, displaying relevant inputs and options

### Changed
- Refactored translation functions to support various API providers
- Configuration structure expanded to store settings for all translation providers
- Improvements to code formatting and indentation across the project

### Fixed
- Indentation errors and `try-except-finally` structure in `process_video_thread`
- Various linting issues in `backend/translate.py`
- Variable naming consistency across the application

## [2.1.1] - 2025-05-11

### Fixed
- `UnboundLocalError` for `progress_action_frame` in `gui/app.py` due to incorrect widget definition and packing order in `create_main_frame`.
- `NameError` for `APP_VERSION` in `gui/app.py` due to not being imported from `config.py` (before eventually being removed from the UI).
- Ongoing fix attempts for indentation errors and `try-except-finally` structure in `process_video_thread` within `gui/app.py` detected by the linter.

## [2.1] - 2025-05-11

### Added
- **Video Queue Management**: Add, remove, and process multiple video files sequentially.
- **Basic Subtitle Editor**: Edit generated subtitle text and timestamps directly within the application.
- **Project Save & Load**: Save queue state, processed data, and settings to a project file (.ftgproj) and load it back.
- **Gemini API Parameter Customization**: Configure Temperature, Top-P, and Top-K for Gemini API through Advanced Settings.
- **Preview Video with Subtitles**: Open selected video with generated temporary subtitle file.
- **Enhanced UI Layout**: Adopted a more structured panel-based layout using PanedWindow to improve user experience.

### Changed
- Application version label removed from UI status bar.
- Default Gemini API model verified with `gemini-2.5-flash-preview-04-17` version.

### Fixed
- `KeyError` when loading default configuration for Gemini API parameters.
- Various indentation and `try-except` structure errors in `gui/app.py` (detected by linter).
- `NameError` for `APP_VERSION` in `gui/app.py` when displaying version label (before removal).

## [2.0] - 2025-05-10

### Added
- Modern UI design using Sun Valley theme (sv-ttk)
- Video preview with thumbnails
- Multi-format output support (SRT, VTT, TXT)
- Side-by-side comparison of original text with translation
- Enhanced progress tracking
- Advanced settings dialog
- About application menu and documentation
- Modular code structure implementation:
  - `config.py`: Configuration settings and constants
  - `utils/`: Formatting and media handling utilities
  - `backend/`: Transcription and translation functionality
  - `gui/`: UI components and main application class
- Responsive interface with minimum window size settings
- Customizable theme system (light/dark) and accent colors
- More detailed documentation available on [GitHub](https://github.com/Fapzarz/FilmTranslatorGenerator)

### Changed
- Code structure refactored from monolithic to modular
- New, more intuitive and modern interface
- Improved error handling and fallback support for translation
- Enhanced translation batch size settings
- Expanded settings system
- Optimized subtitle generation process

## [1.1] - 2025-05-05

### Added
- Faster-Whisper model selection feature (tiny, base, small, medium, large-v2, large-v3).
- Device selection feature (cuda/cpu) and computation type (float16, int8, etc.) for Faster-Whisper.
- Automatic settings storage (API Key, model, device, computation type, target language) to `config.json` file.
- Automatic settings loading from `config.json` when application starts.
- Automatic Whisper model reloading if settings are changed by the user.
- This `CHANGELOG.md` file.
- `LICENSE` file (MIT).

### Changed
- Updated `README.md` with new features and instructions.
- Updated `requirements.txt`.
- Moved `_load_config` call in `__init__` to fix `AttributeError`.
- Application window size adjusted to accommodate new options.

### Removed
- Previous subtitle start time offset logic (delay 300ms).
- Explicit VRAM cleanup function after transcription (model now managed by reload logic).

## [1.0] - 2025-05-04

### Added
- Basic functionality: Video transcription with Faster-Whisper (`large-v2`).
- Translation with Google Gemini API (`gemini-2.5-flash-preview-04-17`) in batches.
- SRT file generation.
- Basic GUI using Tkinter.
- Basic error handling.
- API Key storage to `config.json` (initial version).
- `.gitignore` file.
- File `requirements.txt` awal.

</details>

<a name="bahasa-indonesia"></a>
<details>
<summary><strong>Bahasa Indonesia</strong></summary>

Semua perubahan penting pada proyek ini akan didokumentasikan dalam file ini.

Format didasarkan pada [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.0.0] - 2025-05-24

### Ditambahkan
- ** Sistem Keamanan Terpadu **: Semua fungsi keamanan dipindahkan dari skrip mandiri ke `utils/crypto.py`
- ** Modul Kriptografi Komprehensif **: Dokumentasi Modul Lengkap dengan Fitur Keamanan
- ** Pemeriksaan Keamanan Otomatis **: Perlindungan kunci API bawaan dan deteksi kerentanan
- **Model Anthropic Terbaru**: Menambahkan dukungan untuk model Claude-4 series:  - `claude-opus-4-20250514` - Model Claude 4 Opus terbaru  - `claude-sonnet-4-20250514` - Model Claude 4 Sonnet terbaru- **Optimasi GPU Lanjutan**: Peningkatan akselerasi GPU yang komprehensif:  - Deteksi hardware real-time dan rekomendasi pengaturan optimal  - Manajemen memori otomatis dan pembersihan  - Monitoring performa dengan analitik detail dan saran  - Optimasi batch size cerdas berdasarkan memori GPU tersedia- **Sistem Notifikasi Windows**: Integrasi notifikasi Windows asli:  - Notifikasi penyelesaian processing dengan alert suara  - Statistik penyelesaian queue dan informasi waktu  - Notifikasi error dengan info troubleshooting detail  - Preferensi notifikasi yang dapat dikonfigurasi dan tingkat urgensi
- **Advanced GPU Optimization**: Comprehensive GPU acceleration enhancements:
  - Real-time hardware detection and optimal settings recommendation
  - Automatic memory management and cleanup
  - Performance monitoring with detailed analytics and suggestions
  - Smart batch size optimization based on available GPU memory
- **Windows Notifications System**: Native Windows notification integration:
  - Processing completion notifications with sound alerts
  - Queue completion statistics and timing information
  - Error notifications with detailed troubleshooting info
  - Configurable notification preferences and urgency levels

### diubah
- ** Arsitektur Keamanan **: Fungsi Keamanan Konsolidasi menjadi Modul Crypto untuk Organisasi yang Lebih Baik
- ** Struktur kode **: Modularitas yang ditingkatkan dengan pemisahan kekhawatiran yang lebih bersih
- ** Dokumentasi **: Dokumentasi Modul Crypto yang Ditingkatkan dengan Deskripsi Fungsi Lengkap

### Tetap
- ** Kerentanan Keamanan **: Menyelesaikan semua masalah kunci API yang terpapar secara otomatis
- ** Organisasi kode **: Menghilangkan file keamanan mandiri untuk struktur proyek yang lebih bersih
- ** Dependensi Impor **: Menambahkan ketergantungan `antropik` yang hilang ke persyaratan.txt

### Keamanan
- ** Enkripsi Kunci API **: Semua tombol API sekarang secara otomatis dienkripsi menggunakan tombol spesifik mesin
- ** Pencegahan Kerentanan **: Pemindaian Keamanan Proaktif dan Perbaikan Otomatis
-** Keamanan Konfigurasi Nol **: Fitur Keamanan Bekerja di luar kotak tanpa intervensi pengguna

## [3.0.0-RC1] - 2025-05-20

### Added
- Dokumentasi lengkap dalam format HTML dengan panduan API, fitur lanjutan, dan troubleshooting
- Implementasi enkripsi API key untuk keamanan data sensitif
- Validasi input yang komprehensif di seluruh aplikasi

### Changed
- Refaktorisasi kode dengan memisahkan modul berdasarkan fungsi terkait
- Pembaruan antarmuka pengguna dengan tampilan yang lebih modern

### Fixed
- Masalah keamanan dengan penyimpanan API key
- Berbagai bug dan peningkatan stabilitas aplikasi

## [3.0.0-ALPHA 1] - 2025-05-19

### Added
- **Migrasi Framework UI Lengkap**: Membangun ulang seluruh aplikasi menggunakan framework PySide6 (Qt), menggantikan implementasi Tkinter sebelumnya:
  - UI modern dan responsif dengan kontrol dan kemampuan tata letak yang lebih baik
  - Tampilan dan nuansa yang native di berbagai platform
  - Penanganan video yang ditingkatkan dengan akselerasi hardware yang tepat
  - Dukungan untuk komponen dan interaksi UI yang lebih kompleks
- **Dialog Editor Subtitle Lanjutan**: Perombakan lengkap pengalaman pengeditan subtitle:
  - Pemutar video besar dengan kontrol pemutaran langsung
  - Kontrol timing dengan presisi milidetik
  - Tampilan tabel dengan semua segmen subtitle
  - Pratinjau subtitle real-time langsung pada video
  - Indikator keterbacaan CPS (Characters Per Second) dan CPL (Characters Per Line)
  - Opsi dan pratinjau gaya yang ditingkatkan
  - Fungsi Undo/Redo untuk semua operasi pengeditan

### Changed
- **Perombakan Arsitektur Lengkap**: Refaktorisasi besar pada arsitektur aplikasi untuk migrasi PySide6:
  - Struktur kode yang diorganisir ulang dengan pemisahan yang jelas antara UI dan logika
  - Memperkenalkan alur kerja berbasis dialog untuk operasi kompleks
  - Mendesain ulang sistem manajer untuk modularitas yang lebih baik
  - Membuat struktur modul baru dengan direktori khusus untuk dialog dan manajer
- **Peningkatan Tampilan Subtitle**: Menggantikan overlay berbasis QLabel dengan arsitektur QGraphicsView untuk rendering subtitle yang lebih andal:
  - Teks subtitle sekarang konsisten terlihat di atas konten video di semua lingkungan
  - Mempertahankan ukuran font yang tepat terlepas dari penskalaan video
  - Penyesuaian otomatis posisi dan gaya subtitle selama pemutaran
  - Pemotongan kata dan perataan yang tepat untuk subtitle multi-baris
- **Penyederhanaan UI Utama**: Menghapus pemutar video yang tertanam dari jendela utama, digantikan dengan dialog editor lanjutan khusus
- **Peningkatan Struktur Kode**: Modularisasi lebih lanjut pada kode pengeditan dan tampilan subtitle

### Fixed
- Masalah kontrol pemutar video di mana kontrol pemutaran terkadang tidak responsif
- Audio yang terus memutar setelah menutup dialog editor
- Masalah tampilan overlay subtitle di berbagai platform
- Masalah tata letak dengan panel kontrol video

## [2.5.10] - 2025-05-20

### Changed
- **Refaktorisasi `PreviewManager`**: Memindahkan logika pratinjau video dan pratinjau video dengan subtitle dari `gui/app.py` ke modul baru `gui/preview_manager.py` untuk modularitas yang lebih baik.
- **Pembersihan Kode di `gui/app.py`**: Menghapus sisa kode (metode yang dikomentari dan blok logika lama) yang terkait dengan fungsionalitas yang sebelumnya dipindahkan ke `ShortcutManager` dan `PreviewManager`, menghasilkan kelas `AppGUI` yang lebih ramping.
- **Konfigurasi Tombol Notebook**: Memastikan bahwa tombol-tombol di dalam tab notebook (Salin, Simpan Sebagai, Pratinjau dengan Subtitle, Terapkan Perubahan Editor) di `gui/app.py` dikonfigurasi dengan benar untuk memanggil metode masing-masing, termasuk metode dari `PreviewManager` yang baru dan `EditorManager` yang sudah ada.

### Improved
- Peningkatan organisasi dan keterbacaan kode dengan lebih lanjut memisahkan fungsionalitas dari `gui/app.py`.

## [2.5.5] - 2025-05-17

### Changed
- **Major Code Refactoring**: Melakukan refaktorisasi signifikan pada modul `gui/app.py` dengan memecah fungsionalitasnya ke beberapa modul manager dan styler khusus:
  - `gui/main_layout.py`: Menangani pembuatan panel UI kiri dan kanan.
  - `gui/project_manager.py`: Mengelola logika penyimpanan dan pemuatan proyek.
  - `gui/queue_manager.py`: Mengontrol logika manajemen antrean video.
  - `gui/video_processor.py`: Berisi logika pemrosesan video dan pemuatan model Whisper.
  - `gui/subtitle_styler.py`: Mengelola logika styling subtitle, pratinjau gaya, dan penerapan ke file SRT.
  - `gui/editor_manager.py`: Menangani logika untuk memuat, mem-parsing, dan menerapkan perubahan dari editor subtitle.
- Refaktorisasi ini meningkatkan organisasi kode, kemudahan pemeliharaan, dan skalabilitas.

### Fixed
- Memperbaiki pengambilan path video pada fungsi `preview_video` di `gui/app.py`.
- Menghapus impor `re` yang tidak digunakan dari `gui/app.py`.
- Menghapus metode `_update_queue_statistics` yang redundan dari `gui/app.py` karena fungsionalitasnya ditangani oleh `gui/queue_manager.py`.

### Improved
- Editor subtitle sekarang secara otomatis menyegarkan kontennya setelah menerapkan perubahan, menampilkan segmen yang telah di-parse dan dibersihkan.
- Penyimpanan konfigurasi tidak lagi dipicu pada setiap perubahan gaya subtitle untuk video tertentu; data gaya disimpan bersama dengan penyimpanan proyek atau konfigurasi utama.

## [2.2.5] - 2025-05-13

### Added
- **Dukungan Berbagai Model Gemini**: Menambahkan kemampuan untuk memilih antara model Gemini:
  - `gemini-2.5-flash-preview-04-17` (default): Direkayasa untuk respons yang lebih cepat
  - `gemini-2.5-pro-exp-03-25`: Kualitas yang lebih tinggi untuk terjemahan yang lebih kompleks
- **Peningkatan Tata Letak UI**: Peningkatan proporsi panel dan preview style subtitle yang lebih baik
  - Lebar panel kiri disesuaikan untuk keterlihatan kontrol yang lebih baik
  - Posisi preview style subtitle diperbaiki untuk menampilkan teks yang benar-benar berpusat
  - Penambahan pemindahan otomatis pada ukuran jendela untuk preview subtitle

### Fixed
- Masalah indentasi di `backend/translate.py` yang berkaitan dengan terjemahan batch
- Peningkatan penanganan error untuk preview style subtitle
- Masalah layout dengan tampilan antrean
- Pengaturan konfigurasi yang benar untuk style subtitle

## [2.2.0] - 2025-05-12

### Added
- **Dukungan Berbagai API Terjemahan**: Integrasi dengan beberapa provider API terjemahan:
  - OpenAI (GPT-4.1, GPT-4o, GPT-3.5-turbo, dll.)
  - Anthropic Claude (Claude 3 Opus, Claude 3.5 Sonnet, dll.) 
  - DeepSeek (melalui DeepSeek-chat)
- **UI Pemilihan Provider Terjemahan**: Dialog pemilihan provider yang dinamis dengan konfigurasi spesifik untuk setiap provider
- **Penyimpanan API Key & Model**: Semua API key dan pemilihan model setiap provider disimpan dalam konfigurasi
- **UI Dinamis**: Antarmuka yang menyesuaikan diri dengan provider terjemahan yang dipilih, menampilkan input dan opsi yang relevan

### Changed
- Refactor fungsi terjemahan untuk mendukung berbagai provider API
- Struktur konfigurasi diperluas untuk menyimpan pengaturan semua provider terjemahan
- Perbaikan pada format dan indentasi kode di seluruh proyek

### Fixed
- Kesalahan indentasi dan struktur `try-except-finally` di `process_video_thread`
- Berbagai masalah linting di `backend/translate.py`
- Konsistensi penamaan variabel di seluruh aplikasi

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
- **Peningkatan Tata Letak UI**: Mengadopsi tata letak berbasis panel yang lebih terstruktur menggunakan PanedWindow untuk meningkatkan pengalaman pengguna.

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

</details>
