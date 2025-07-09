# ISEE Tutor Project Structure

## Directory Layout

```
isee-tutor/
├── src/                    # Source code
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── audio.py       # Audio input/output handling
│   │   ├── speech.py      # Speech recognition/synthesis
│   │   ├── llm.py         # Language model interface
│   │   └── hardware.py    # Hardware control (button, LED, etc.)
│   │
│   ├── education/         # Educational modules
│   │   ├── __init__.py
│   │   ├── content.py     # Content management
│   │   ├── quiz.py        # Quiz/test generation
│   │   ├── progress.py    # Progress tracking
│   │   └── subjects/      # Subject-specific modules
│   │       ├── math.py
│   │       ├── verbal.py
│   │       └── reading.py
│   │
│   ├── ui/                # User interface
│   │   ├── __init__.py
│   │   ├── web/           # Web-based UI
│   │   │   ├── app.py
│   │   │   ├── static/
│   │   │   └── templates/
│   │   └── touch/         # Touchscreen UI (when ready)
│   │
│   ├── utils/             # Utilities
│   │   ├── __init__.py
│   │   ├── config.py      # Configuration management
│   │   ├── logger.py      # Logging setup
│   │   └── database.py    # Database operations
│   │
│   └── main.py            # Main application entry point
│
├── data/                  # Data storage
│   ├── content/          # Educational content
│   ├── models/           # AI models
│   ├── audio/            # Audio files
│   └── users/            # User data
│
├── tests/                # Test files
│   ├── unit/
│   ├── integration/
│   └── hardware/
│
├── config/               # Configuration files
│   ├── default.yaml
│   ├── development.yaml
│   └── production.yaml
│
├── scripts/              # Utility scripts
│   ├── setup.sh         # Initial setup script
│   ├── test_hardware.py # Hardware testing
│   └── install_deps.sh  # Dependency installation
│
├── docs/                # Documentation
│   ├── API.md
│   ├── HARDWARE.md
│   └── DEPLOYMENT.md
│
├── web/                 # Web interface (development)
│   ├── package.json
│   ├── src/
│   └── public/
│
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore
├── README.md
└── docker-compose.yml  # For development services
```

## Setup Commands

```bash
# On your Jetson (or through VS Code remote)
cd ~
mkdir -p isee-tutor
cd isee-tutor

# Create directory structure
mkdir -p src/{core,education/subjects,ui/{web/{static,templates},touch},utils}
mkdir -p data/{content,models,audio,users}
mkdir -p tests/{unit,integration,hardware}
mkdir -p config scripts docs web/{src,public}

# Initialize Python packages
touch src/__init__.py
touch src/core/__init__.py
touch src/education/__init__.py
touch src/education/subjects/__init__.py
touch src/ui/__init__.py
touch src/ui/web/__init__.py
touch src/utils/__init__.py

# Create main files
touch src/main.py
touch requirements.txt
touch .env.example
touch README.md
```