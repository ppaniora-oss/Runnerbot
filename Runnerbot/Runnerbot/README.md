# Runnerbot

Run AI models locally from your storage (SSD, HDD, USB). No internet required once models are downloaded.

## Features

- Upload and manage GGUF model files
- Chat with local AI models
- Works offline after model download
- Adjustable settings (temperature, max tokens, top_p)
- Cross-platform (Linux & Windows)

## Requirements

- Python 3.10 or higher
- 4GB+ RAM recommended
- Storage space for model files (500MB - 8GB depending on model)

## Quick Start

### Linux

```bash
# Make scripts executable
chmod +x install_linux.sh run_linux.sh

# Install
./install_linux.sh

# Run
./run_linux.sh
```

### Windows

```cmd
# Install (double-click or run in terminal)
install_windows.bat

# Run (double-click or run in terminal)
run_windows.bat
```

Then open http://localhost:5000 in your browser.

## Getting Models

Download GGUF models from HuggingFace:

### Recommended Small Models (Fast, Low Memory)

| Model | Size | Good For |
|-------|------|----------|
| TinyLlama-1.1B-Chat | ~700MB | Basic chat, fast responses |
| Phi-2 | ~1.6GB | General tasks, reasoning |
| Qwen2-1.5B | ~1GB | Multilingual, coding |

### How to Download

1. Go to [HuggingFace](https://huggingface.co)
2. Search for model name + "GGUF" (e.g., "TinyLlama GGUF")
3. Look for TheBloke's quantized versions
4. Download `.gguf` file (Q4_K_M recommended)
5. Upload to Runnerbot or place in `models/` folder

## Usage

1. Start the application
2. Upload a `.gguf` model file (drag & drop or browse)
3. Click "Load" on your model
4. Start chatting!

## Manual Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

## Project Structure

```
local-llm-runner/
├── app.py              # Flask backend server
├── index.html          # Web interface
├── models/             # Your model files go here
├── requirements.txt    # Python dependencies
├── install_linux.sh    # Linux installer
├── install_windows.bat # Windows installer
├── run_linux.sh        # Linux launcher
└── run_windows.bat     # Windows launcher
```

## Troubleshooting

**Model won't load:**
- Ensure you have enough RAM (model size + 1GB overhead)
- Try a smaller quantized model (Q4_K_M instead of Q8)

**Slow responses:**
- Use smaller models (TinyLlama, Phi-2)
- Reduce max tokens in settings

**Installation fails:**
- Ensure Python 3.10+ is installed
- On Windows, run as Administrator if needed
- Check internet connection for pip downloads

## License

MIT License - Free for personal and commercial use.
