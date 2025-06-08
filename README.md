# 🎬 Film Translator Generator

[![Version](https://img.shields.io/badge/version-3.1.0-blue.svg)](https://github.com/Fapzarz/FilmTranslatorGenerator)
[![License](https://img.shields.io/badge/license-AGPLv3-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Qt](https://img.shields.io/badge/Qt-PySide6-green.svg)](https://pyside.org)

> 🚀 **Modern desktop application for automatic video transcription and translation**

A powerful, user-friendly desktop application that transcribes audio from video files using Faster-Whisper and translates text using multiple AI providers to generate professional subtitle files.

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🛠️ Requirements](#️-requirements)
- [📦 Installation](#-installation)
- [🚀 Quick Start](#-quick-start)
- [🎯 Usage Guide](#-usage-guide)
- [🏗️ Project Structure](#️-project-structure)
- [🔧 Configuration](#-configuration)
- [📚 Documentation](#-documentation)
- [📝 License](#-license)
- [🔄 Changelog](#-changelog)

---

## ✨ Features

### 🎨 **Modern User Interface**
- **Qt-based GUI** with Sun Valley theme for professional appearance
- **Panel-based layout** with intuitive organization
- **Dark/Light theme** support with customizable accent colors
- **Real-time preview** with thumbnails and video information

### 🎬 **Video Processing**
- **Batch processing** - Add, remove, and process multiple videos sequentially
- **Queue management** - Organize your workflow efficiently
- **Project save/load** - Save progress in `.ftgproj` format
- **Video preview** with integrated subtitle display

### 🎯 **Advanced Transcription**
- **Faster-Whisper models** (`tiny` to `large-v3`)
- **GPU acceleration** with CUDA support
- **Flexible compute types** (`float16`, `int8`, etc.)
- **Automatic device detection** and optimization

### 🌍 **Multi-Provider Translation**
Choose from industry-leading AI providers:

| Provider | Models | Features |
|----------|--------|----------|
| **🤖 Google Gemini** | `gemini-2.5-flash`, `gemini-2.5-pro` | Fast processing, high quality |
| **🧠 OpenAI** | GPT-4.1, GPT-4o, GPT-3.5-turbo | State-of-the-art language models |
| **🎭 Anthropic** | Claude 4 series, Claude 3.5 Sonnet | Advanced reasoning capabilities |
| **🔥 DeepSeek** | `deepseek-chat` | Cost-effective alternative |
| **🏠 Local Models** | HuggingFace, MarianMT | Privacy-focused, offline processing |

### 📝 **Subtitle Management**
- **Advanced subtitle editor** with millisecond precision
- **Multiple formats** - SRT, VTT, TXT output
- **Style customization** - Fonts, colors, positioning
- **Side-by-side comparison** - Original vs translated text
- **Real-time preview** - See changes instantly

### 🔒 **Security & Configuration**
- **Encrypted API key storage** with machine-specific encryption
- **Comprehensive settings** saved in `config.json`
- **Keyboard shortcuts** for power users
- **Batch size optimization** for performance tuning

---

## 🛠️ Requirements

### System Requirements
- **Python 3.8+** 🐍
- **Operating System**: Windows 10+, macOS 10.14+, Linux
- **Memory**: 4GB RAM minimum (8GB+ recommended for large models)
- **Storage**: 2GB+ free space for models and cache

### Essential Dependencies
```bash
# Core media processing
ffmpeg                    # Must be in system PATH

# GPU acceleration (recommended)
CUDA Toolkit 11.0+       # For GPU-accelerated transcription
cuDNN                     # Compatible with your CUDA version
```

### API Keys (Choose one or more)
| Service | Get API Key | Best For |
|---------|------------|----------|
| 🤖 **Google Gemini** | [AI Studio](https://aistudio.google.com/app/apikey) | General purpose, fast |
| 🧠 **OpenAI** | [Platform](https://platform.openai.com/api-keys) | High quality translations |
| 🎭 **Anthropic** | [Console](https://console.anthropic.com/) | Complex content |
| 🔥 **DeepSeek** | [Platform](https://platform.deepseek.com/) | Cost-effective |
| 🏠 **Local Model** | *No key required* | Privacy, offline use |

---

## 📦 Installation

### 1️⃣ Clone Repository
```bash
git clone https://github.com/Fapzarz/FilmTranslatorGenerator.git
cd FilmTranslatorGenerator
```

### 2️⃣ Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Verify System Dependencies
- ✅ **FFmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/) and add to PATH
- ✅ **CUDA** (optional): Install CUDA Toolkit and cuDNN for GPU acceleration

---

## 🚀 Quick Start

### Launch Application
```bash
python main.py
```

### First Run Setup
1. **🎬 Add Videos** - Click "Add Video(s)" to select your files
2. **🔑 Configure API** - Choose translation provider and enter API key
3. **🎯 Select Model** - Pick the appropriate model for your needs
4. **🌍 Set Language** - Choose target translation language
5. **⚙️ Configure Whisper** - Select model, device, and compute type
6. **▶️ Generate** - Click "Generate Subtitles" and wait for completion

---

## 🎯 Usage Guide

### Video Queue Management
- **➕ Add Videos**: Support for multiple video formats (MP4, AVI, MOV, etc.)
- **🗑️ Remove Videos**: Select and remove unwanted items
- **📊 Queue Statistics**: Monitor progress and completion status
- **💾 Save/Load Projects**: Preserve your workflow state

### Translation Configuration
```
Provider Selection → API Key → Model Selection → Language Settings
```

### Advanced Features
- **🎨 Subtitle Styling**: Customize appearance with fonts, colors, and positioning
- **📝 Editor Mode**: Fine-tune timing and text with precision controls
- **👁️ Preview Mode**: Watch video with generated subtitles
- **📋 Batch Processing**: Handle multiple files automatically

---

## 🏗️ Project Structure

```
FilmTranslatorGenerator/
├── 📁 backend/           # Core processing logic
│   ├── transcribe.py     # Whisper integration
│   └── translate.py      # Multi-provider translation
├── 📁 dialogs/           # UI dialog components
├── 📁 managers/          # Feature managers
│   ├── video_processor.py
│   ├── queue_manager.py
│   └── project_manager.py
├── 📁 utils/             # Utilities and helpers
│   ├── crypto.py         # Security functions
│   ├── format.py         # Subtitle formatting
│   └── media.py          # Media handling
├── 📁 docs/              # HTML documentation
├── 📄 main.py            # Application entry point
├── 📄 qt_app.py          # Main Qt application
├── 📄 config.py          # Configuration constants
└── 📄 requirements.txt   # Python dependencies
```

---

## 🔧 Configuration

### Settings Location
- **Main Config**: `config.json` (auto-created)
- **Projects**: `.ftgproj` files (save/load workflow state)

### Key Configuration Options
```json
{
  "translation_provider": "Gemini",
  "whisper_model": "large-v2",
  "device": "cuda",
  "theme": "dark",
  "batch_size": 500,
  "output_format": "srt"
}
```

### Security Features
- 🔐 **API keys encrypted** with machine-specific keys
- 🛡️ **Zero-configuration security** - works out of the box
- 🔒 **No data transmission** - keys stay on your machine

---

## 📚 Documentation

Comprehensive documentation available:

- 📖 **[User Guide](docs/index.html)** - Complete usage instructions
- 🔧 **[API Configuration](docs/api.html)** - Setup guides for all providers  
- 🚀 **[Advanced Features](docs/advanced.html)** - Power user features
- 🔍 **[Troubleshooting](docs/troubleshooting.html)** - Common issues and solutions

---

## 📝 License

This project is licensed under the **GNU Affero General Public License v3 (AGPLv3)**.

- ✅ **Free to use** for personal and commercial projects
- ✅ **Open source** - contribute and modify
- ✅ **Copyleft** - derivative works must also be open source

See the [LICENSE](LICENSE) file for full details.

---

## 🔄 Changelog

For detailed release history and changes, see [CHANGELOG.md](CHANGELOG.md).

### Latest Release - v3.1.0
- 🆕 Version bump to 3.1.0
- 📖 Modernized documentation
- ✨ Improved README structure

---

<div align="center">

### 🌟 **Made with ❤️ for the content creation community**

[🏠 Home](https://github.com/Fapzarz/FilmTranslatorGenerator) • [📚 Docs](docs/) • [🐛 Issues](https://github.com/Fapzarz/FilmTranslatorGenerator/issues) • [💡 Features](https://github.com/Fapzarz/FilmTranslatorGenerator/discussions)

</div>

---

## 🌏 Bahasa Indonesia

<details>
<summary><strong>Klik untuk melihat dokumentasi dalam Bahasa Indonesia</strong></summary>

## Deskripsi

Aplikasi desktop modern untuk transkripsi video otomatis dan terjemahan menggunakan AI terdepan.

### ✨ Fitur Utama

- 🎨 **Antarmuka Modern** dengan tema Sun Valley dan tata letak panel
- 🎬 **Pemrosesan Batch** - Kelola multiple video secara berurutan  
- 💾 **Simpan/Muat Proyek** - Simpan progress dalam format `.ftgproj`
- 📝 **Editor Subtitle Lanjutan** - Edit dengan presisi milidetik
- 👁️ **Preview Video** dengan subtitle terintegrasi
- 🌍 **Multi-Provider AI** - Gemini, OpenAI, Anthropic, DeepSeek, Local
- 🔒 **Keamanan API Key** - Enkripsi otomatis dengan kunci spesifik mesin

### 🛠️ Persyaratan

- **Python 3.8+** 
- **FFmpeg** (harus ada di PATH sistem)
- **CUDA Toolkit & cuDNN** (opsional, untuk akselerasi GPU)
- **API Key** dari provider pilihan Anda

### 📦 Instalasi

```bash
# Clone repository
git clone https://github.com/Fapzarz/FilmTranslatorGenerator.git
cd FilmTranslatorGenerator

# Buat virtual environment (Windows)
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 🚀 Penggunaan

```bash
python main.py
```

1. **Tambah Video** - Klik "Add Video(s)" untuk memilih file
2. **Pilih Provider** - Pilih provider terjemahan (Gemini, OpenAI, dll)
3. **Masukkan API Key** - Input API key untuk provider yang dipilih
4. **Atur Bahasa** - Pilih bahasa target terjemahan
5. **Konfig Whisper** - Pilih model, device, dan compute type
6. **Generate** - Klik "Generate Subtitles"

### 🏗️ Struktur Proyek

```
FilmTranslatorGenerator/
├── backend/        # Logic pemrosesan inti
├── dialogs/        # Komponen dialog UI
├── managers/       # Manager fitur
├── utils/          # Utilitas dan helper
├── docs/           # Dokumentasi HTML
├── main.py         # Entry point aplikasi
└── qt_app.py       # Aplikasi Qt utama
```

### 📚 Dokumentasi

Dokumentasi lengkap tersedia dalam folder `docs/`:
- **Panduan Pengguna** - Instruksi penggunaan lengkap
- **Konfigurasi API** - Setup untuk semua provider
- **Fitur Lanjutan** - Fitur untuk power user
- **Troubleshooting** - Solusi masalah umum

### 📝 Lisensi

Proyek ini dilisensikan di bawah **GNU Affero General Public License v3 (AGPLv3)**.

</details>
