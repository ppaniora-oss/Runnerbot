# Runnerbot

## Overview
A web application for running local Large Language Models (LLMs) from storage. Upload GGUF model files and chat with them directly in the browser.

## Features
- **Chat**: Converse with local AI models
- **Providers**: Connect external AI services (OpenAI, Claude, Grok, Ollama) with persistent token storage
- **Vibe Coding**: Full AI coding suite like Cursor/Replit
  - Generate code from description
  - Explain, debug, refactor, optimize code
  - Add documentation and comments
  - Convert between languages
  - Complete/continue code (like Cursor Tab)
  - Code review with suggestions
  - Generate unit tests
  - Edit code with natural language instructions
- **Library**: Upload documents for searching and AI-assisted learning
- **Memory**: Persistent memory that remembers facts across conversations
- **Skills**: Create reusable AI prompts and execute them with custom input
- **Agents**: Create specialized AI personas with custom personalities
- **Files**: Browse and access local files on your system
- **Network**: Configure localhost, ports, mesh networks (ZeroTier, Tailscale, Nebula, WireGuard), custom URLs, and internet tunneling (ngrok, Pinggy, LocalTunnel)

## Architecture
- **Backend**: Python Flask server (`app.py`)
  - Model upload/management API
  - Inference using `llama-cpp-python`
  - Vibe coding (code generation, explanation, debugging)
  - Library search and AI learning
- **Frontend**: Static HTML/CSS/JS (`index.html`)
  - Tabbed interface (Chat, Vibe Coding, Library)
  - Drag-and-drop file upload
  - Model settings (temperature, tokens)

## Project Structure
```
/
├── app.py                      # Flask backend server
├── index.html                  # Frontend interface
├── models/                     # Directory for uploaded LLM models
├── library/                    # Directory for documents to search/learn
├── data/                       # Persistent data (memory, skills, agents)
├── static/                     # Static assets (icon, etc.)
├── requirements.txt            # Python dependencies
├── install_linux.sh            # Linux installer
├── install_mac.sh              # macOS installer
├── install_windows.bat         # Windows installer
├── install_portable_linux.sh   # Portable Linux installer (USB/HDD/SSD)
├── install_portable_mac.sh     # Portable macOS installer (USB/HDD/SSD)
├── install_portable_windows.bat# Portable Windows installer (USB/HDD/SSD)
├── install_usb_universal.sh    # Universal USB installer (all platforms)
├── create_iso.sh               # Create ISO image
├── create_bootable_usb.sh      # Create bootable USB drive
├── run_linux.sh                # Linux launcher
├── run_mac.sh                  # macOS launcher
├── run_windows.bat             # Windows launcher
├── README.md                   # Full documentation
└── replit.md                   # This file
```

## Cross-Platform Installation (Self-Contained)
The app runs in a self-contained mode - all data stays within its folder.
Safe to run from SSD, HDD, or USB drives.

### Quick Install (Current Location)
- **Linux**: Run `./install_linux.sh` then `./run_linux.sh`
- **macOS**: Run `./install_mac.sh` then `./run_mac.sh`
- **Windows**: Run `install_windows.bat` then `run_windows.bat`

### Portable Install (USB/HDD/SSD)
Install to any external drive or custom location:
- **Linux**: Run `./install_portable_linux.sh` and enter destination path
- **macOS**: Run `./install_portable_mac.sh` and enter destination path
- **Windows**: Run `install_portable_windows.bat` and enter destination path
- **Universal**: Run `./install_usb_universal.sh` for cross-platform USB

Example paths:
- Linux USB: `/media/username/USB_DRIVE/Runnerbot`
- macOS USB: `/Volumes/USB_DRIVE/Runnerbot`
- Windows USB: `E:\Runnerbot`
- External SSD: `/mnt/external/Runnerbot` or `D:\Runnerbot`

### Create ISO Image
Run `./create_iso.sh` to create a Runnerbot.iso file that can be:
- Burned to CD/DVD
- Mounted as a virtual drive
- Written to USB with `dd`

### Create Bootable USB
Run `sudo ./create_bootable_usb.sh` to create a bootable USB drive with Runnerbot.
Warning: This erases all data on the USB drive.

### Portable Usage
1. Use the portable installer to copy Runnerbot to any drive
2. Run the installer once on the target system to set up Python
3. All models, documents, memories, and settings stay within the folder
4. Moving the folder preserves all your data

## API Endpoints
### Models
- `GET /api/models` - List available models
- `POST /api/models/upload` - Upload a model file
- `POST /api/models/load` - Load a model into memory
- `POST /api/models/unload` - Unload current model
- `POST /api/models/delete` - Delete a model file

### Chat
- `POST /api/chat` - Send chat message
- `POST /api/chat/stream` - Streaming chat response
- `POST /api/generate` - Raw text generation

### Vibe Coding
- `POST /api/code/generate` - Generate code from description
- `POST /api/code/explain` - Explain code
- `POST /api/code/debug` - Debug and fix code
- `POST /api/code/refactor` - Refactor code for better structure
- `POST /api/code/optimize` - Optimize code for performance
- `POST /api/code/document` - Add comments and documentation
- `POST /api/code/convert` - Convert code to another language
- `POST /api/code/complete` - Complete/continue code (like Cursor)
- `POST /api/code/review` - Code review with suggestions
- `POST /api/code/tests` - Generate unit tests
- `POST /api/code/edit` - Edit code with natural language instruction

### Library
- `GET /api/library` - List library files
- `POST /api/library/upload` - Upload document
- `POST /api/library/delete` - Delete document
- `POST /api/library/search` - Search in documents
- `POST /api/library/read` - Read document content
- `POST /api/library/learn` - AI-assisted learning from documents
- `POST /api/library/teach` - AI Teacher with voice reading support

### Memory
- `GET /api/memory` - Get stored memories
- `POST /api/memory/add` - Add a fact to memory
- `POST /api/memory/context` - Set context
- `POST /api/memory/delete` - Delete a memory
- `POST /api/memory/clear` - Clear all memories

### Skills
- `GET /api/skills` - List skills
- `POST /api/skills/create` - Create a new skill
- `POST /api/skills/execute` - Execute a skill with input
- `POST /api/skills/delete` - Delete a skill

### Agents
- `GET /api/agents` - List agents
- `POST /api/agents/create` - Create a new agent
- `POST /api/agents/chat` - Chat with an agent
- `POST /api/agents/delete` - Delete an agent

### Files
- `GET /api/files` - Browse directory
- `POST /api/files/read` - Read file content
- `POST /api/files/ai-search` - AI-powered file search using natural language

### Providers
- `GET /api/providers` - List configured providers
- `POST /api/providers/add` - Add a new provider with token
- `POST /api/providers/delete` - Delete a provider
- `POST /api/providers/activate` - Set active provider
- `POST /api/providers/chat` - Chat with active provider

### Network
- `GET /api/network` - Get network configuration
- `POST /api/network/save` - Save network settings
- `GET /api/network/status` - Get current network status
- `POST /api/network/tunnel/start` - Start tunnel (ngrok/pinggy/localtunnel)
- `POST /api/network/tunnel/stop` - Stop tunnel
- `POST /api/network/mesh/save` - Save mesh network settings (ZeroTier/Tailscale/Nebula/WireGuard/Custom)
- `POST /api/network/vpn/save` - Save VPN provider settings
- `POST /api/search` - Web search using DuckDuckGo/Google/Bing/Brave

### Download
- `GET /api/download` - Download entire app as ZIP file

## Usage
1. Upload a GGUF model file (drag & drop or click to browse)
2. Click "Load" on the model to load it into memory
3. Start chatting!

## Getting Models
Download GGUF models from HuggingFace. Recommended:
- TheBloke's quantized models (Q4_K_M or Q5_K_M for balance of quality/size)
- Models under 4GB work best in this environment

## Recent Changes
- 2026-01-31: Added External AI Providers tab with support for OpenAI, Claude, Grok, Ollama with persistent token storage
- 2026-01-31: Added Download button to export entire app as ZIP file
- 2026-01-31: Added Network tab with localhost/port configuration and tunnel support (ngrok, Pinggy, LocalTunnel)
- 2026-01-31: Enhanced Vibe Coding with 12 skills (refactor, optimize, document, convert, complete, review, tests, edit)
- 2026-01-31: Made app fully self-contained for portable use on external drives
- 2026-01-31: Added OpenClaw-like features (Memory, Skills, Agents, File Browser)
- 2026-01-31: Renamed to Runnerbot
- 2026-01-31: Added Vibe Coding feature (generate, explain, debug code)
- 2026-01-31: Added Library feature (search documents, AI-assisted learning)
- 2026-01-31: Added cross-platform installers for Linux and Windows
- 2026-01-31: Initial implementation with Flask backend and llama-cpp-python
