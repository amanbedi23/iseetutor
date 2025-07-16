# ISEE Tutor - AI Educational Companion

An AI-powered educational companion device designed for children, featuring ISEE test preparation and general knowledge companion modes. Built to run locally on NVIDIA Jetson hardware for privacy and offline operation.

## Features

- **Dual Mode Operation**:
  - **Tutor Mode**: Focused ISEE test preparation with adaptive learning
  - **Companion Mode**: General knowledge AI friend for casual learning
- **Voice Interaction**: Natural conversation with speech recognition and synthesis
- **Privacy-First**: All processing happens locally, no cloud dependency
- **Child-Safe**: Content filtering and age-appropriate responses
- **Hardware Integration**: LED feedback, button controls, touchscreen support
- **Kiosk Mode**: Boots directly to app like Alexa devices (no desktop visible)

## Quick Start

1. **Initial Setup**:
   ```bash
   cd setup
   sudo bash initial-setup.sh
   ```

2. **Quick Installation**:
   ```bash
   python3 quick_setup.py
   ```

3. **Start the System**:
   ```bash
   python3 start_api.py
   ```

## Documentation

- [Setup Guide](docs/setup/SETUP_GUIDE.md) - Complete installation instructions
- [Hardware Setup](docs/hardware/hardware-setup-guide.md) - Physical device assembly
- [Kiosk Mode Setup](docs/kiosk-mode-setup.md) - Configure boot-to-app experience
- [System Architecture](docs/system-architecture.md) - Technical overview
- [Development Guide](docs/development/project-structure.md) - For contributors
- [Migration Guide](MIGRATION_GUIDE.md) - Migrating between Jetson devices
- [Quick Migration Steps](QUICK_MIGRATION_STEPS.md) - Quick reference for hardware migration

## Project Structure

```
iseetutor/
├── src/              # Source code
│   ├── api/         # FastAPI backend
│   ├── core/        # Core functionality
│   └── models/      # AI model interfaces
├── web/             # Web interface
├── data/            # Knowledge bases and content
├── scripts/         # Utility scripts
├── tests/           # Test files
├── docs/            # Documentation
├── setup/           # Setup and installation
└── config/          # Configuration files
```

## Requirements

- NVIDIA Jetson Orin Nano (8GB RAM)
- 1TB NVMe SSD
- USB microphone and speaker
- Python 3.10+
- 7-8GB storage for models and knowledge bases

## License

[License information to be added]