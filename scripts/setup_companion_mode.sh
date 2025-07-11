#!/bin/bash
# Setup script for ISEE Tutor Companion Mode
# This script downloads models and sets up knowledge bases

set -e

echo "=== ISEE Tutor Companion Mode Setup ==="
echo "This will download models and knowledge bases (~150GB total)"
echo ""

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "Warning: This doesn't appear to be a Jetson device"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create directory structure
echo "Creating directory structure..."
sudo mkdir -p /mnt/storage/{models,knowledge,content}
sudo chown -R $USER:$USER /mnt/storage

# Function to download with progress
download_with_progress() {
    local url=$1
    local output=$2
    echo "Downloading $(basename $output)..."
    wget --progress=bar:force -O "$output" "$url" 2>&1 | tail -f -n +6
}

# 1. Download Llama 3.2 8B Quantized Model
echo ""
echo "=== Downloading Llama 3.2 8B (Q4_K_M quantization) ==="
echo "This is the main model for both tutoring and companion mode"

MODEL_DIR="/mnt/storage/models"
mkdir -p $MODEL_DIR

# Download from Hugging Face (you'll need to accept license)
echo "Please visit https://huggingface.co/meta-llama/Llama-3.2-8B"
echo "Accept the license agreement, then run:"
echo ""
echo "huggingface-cli download meta-llama/Llama-3.2-8B-Instruct-GGUF llama-3.2-8b-instruct.Q4_K_M.gguf --local-dir $MODEL_DIR"
echo ""
read -p "Press enter once you've downloaded the model..."

# 2. Download Whisper for Speech Recognition
echo ""
echo "=== Setting up Whisper for Speech Recognition ==="
python3 -c "
import os
os.makedirs('/mnt/storage/models/whisper', exist_ok=True)

# Download Whisper base model
import urllib.request
print('Downloading Whisper base model...')
urllib.request.urlretrieve(
    'https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/base.pt',
    '/mnt/storage/models/whisper/base.pt'
)
print('Whisper model downloaded!')
"

# 3. Set up Wikipedia for Kids (Simplified Wikipedia)
echo ""
echo "=== Setting up Knowledge Bases ==="
echo "Downloading kid-friendly Wikipedia subset..."

KNOWLEDGE_DIR="/mnt/storage/knowledge"
mkdir -p $KNOWLEDGE_DIR/{wikipedia,science,stories}

# Download Simple Wikipedia dump (smaller, kid-friendly)
echo "Downloading Simple Wikipedia..."
wget -P $KNOWLEDGE_DIR/wikipedia https://dumps.wikimedia.org/simplewiki/latest/simplewiki-latest-pages-articles.xml.bz2

# 4. Create Python setup script for processing
cat > $KNOWLEDGE_DIR/process_knowledge.py << 'EOF'
"""
Process knowledge bases for ISEE Tutor
"""
import os
import bz2
import json
import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET
from tqdm import tqdm

def process_simple_wikipedia(xml_path, output_db):
    """Process Simple Wikipedia dump into SQLite database"""
    print("Processing Simple Wikipedia...")
    
    # Create database
    conn = sqlite3.connect(output_db)
    c = conn.cursor()
    
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            categories TEXT,
            is_safe_for_kids INTEGER DEFAULT 1
        )
    ''')
    
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_title ON articles(title);
    ''')
    
    # Parse XML (this is simplified - real implementation would be more robust)
    with bz2.open(xml_path, 'rt', encoding='utf-8') as f:
        # Process the XML file
        article_count = 0
        for event, elem in ET.iterparse(f, events=['end']):
            if elem.tag.endswith('page'):
                title = elem.find('.//{http://www.mediawiki.org/xml/export-0.10/}title').text
                text_elem = elem.find('.//{http://www.mediawiki.org/xml/export-0.10/}text')
                
                if text_elem is not None and text_elem.text:
                    content = text_elem.text[:5000]  # Limit content length
                    
                    # Basic safety filter
                    if is_safe_for_kids(title, content):
                        c.execute(
                            'INSERT INTO articles (title, content) VALUES (?, ?)',
                            (title, content)
                        )
                        article_count += 1
                        
                        if article_count % 1000 == 0:
                            print(f"Processed {article_count} articles...")
                            conn.commit()
                
                elem.clear()
    
    conn.commit()
    conn.close()
    print(f"Processed {article_count} kid-safe articles!")

def is_safe_for_kids(title, content):
    """Basic safety filter for kid-appropriate content"""
    # Add your safety logic here
    unsafe_keywords = ['violence', 'death', 'adult', 'explicit']
    text = (title + ' ' + content).lower()
    return not any(keyword in text for keyword in unsafe_keywords)

def create_science_facts_db():
    """Create a database of science facts for kids"""
    conn = sqlite3.connect('/mnt/storage/knowledge/science/science_facts.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY,
            category TEXT NOT NULL,
            fact TEXT NOT NULL,
            explanation TEXT,
            age_group TEXT,
            difficulty INTEGER
        )
    ''')
    
    # Add some starter facts
    starter_facts = [
        ('space', 'The Sun is a star!', 'Our Sun is just one of billions of stars in the galaxy.', 'elementary', 1),
        ('animals', 'Octopuses have three hearts!', 'Two pump blood to the gills, one pumps blood to the body.', 'elementary', 2),
        ('physics', 'Light travels faster than sound.', 'That\'s why you see lightning before hearing thunder!', 'middle', 2),
    ]
    
    c.executemany(
        'INSERT INTO facts (category, fact, explanation, age_group, difficulty) VALUES (?, ?, ?, ?, ?)',
        starter_facts
    )
    
    conn.commit()
    conn.close()
    print("Created science facts database!")

if __name__ == "__main__":
    # Process Wikipedia
    wiki_xml = '/mnt/storage/knowledge/wikipedia/simplewiki-latest-pages-articles.xml.bz2'
    wiki_db = '/mnt/storage/knowledge/wikipedia/wikipedia_kids.db'
    
    if os.path.exists(wiki_xml):
        process_simple_wikipedia(wiki_xml, wiki_db)
    else:
        print("Wikipedia dump not found. Please download it first.")
    
    # Create science facts database
    create_science_facts_db()
EOF

# 5. Create the mode switching UI component
mkdir -p /home/tutor/iseetutor/web/src/components/ModeSelector

cat > /home/tutor/iseetutor/web/src/components/ModeSelector/ModeSelector.tsx << 'EOF'
import React, { useState } from 'react';
import { 
  Box, 
  ToggleButton, 
  ToggleButtonGroup,
  Typography,
  Card,
  CardContent,
  Fade
} from '@mui/material';
import { School, EmojiPeople, AutoAwesome } from '@mui/icons-material';

interface ModeSelectorProps {
  currentMode: 'tutor' | 'friend' | 'hybrid';
  onModeChange: (mode: 'tutor' | 'friend' | 'hybrid') => void;
}

const ModeSelector: React.FC<ModeSelectorProps> = ({ currentMode, onModeChange }) => {
  const [showDescription, setShowDescription] = useState(false);

  const modeDescriptions = {
    tutor: {
      title: 'Tutor Mode',
      description: 'Focused ISEE test preparation with practice questions and explanations',
      icon: <School />,
      color: '#1976d2'
    },
    friend: {
      title: 'Friend Mode',
      description: 'Chat about anything! Ask questions, hear stories, and explore the world',
      icon: <EmojiPeople />,
      color: '#2e7d32'
    },
    hybrid: {
      title: 'Hybrid Mode',
      description: 'Mix of learning and fun - switch naturally between studying and chatting',
      icon: <AutoAwesome />,
      color: '#9c27b0'
    }
  };

  const handleModeChange = (event: React.MouseEvent<HTMLElement>, newMode: string | null) => {
    if (newMode !== null) {
      onModeChange(newMode as 'tutor' | 'friend' | 'hybrid');
      setShowDescription(true);
      setTimeout(() => setShowDescription(false), 3000);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Choose Your Mode
      </Typography>
      
      <ToggleButtonGroup
        value={currentMode}
        exclusive
        onChange={handleModeChange}
        aria-label="tutor mode"
        sx={{ mb: 2 }}
      >
        <ToggleButton value="tutor" aria-label="tutor mode">
          <School sx={{ mr: 1 }} />
          Tutor
        </ToggleButton>
        <ToggleButton value="friend" aria-label="friend mode">
          <EmojiPeople sx={{ mr: 1 }} />
          Friend
        </ToggleButton>
        <ToggleButton value="hybrid" aria-label="hybrid mode">
          <AutoAwesome sx={{ mr: 1 }} />
          Hybrid
        </ToggleButton>
      </ToggleButtonGroup>

      <Fade in={showDescription}>
        <Card sx={{ 
          bgcolor: modeDescriptions[currentMode].color,
          color: 'white'
        }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {modeDescriptions[currentMode].title}
            </Typography>
            <Typography variant="body2">
              {modeDescriptions[currentMode].description}
            </Typography>
          </CardContent>
        </Card>
      </Fade>
    </Box>
  );
};

export default ModeSelector;
EOF

# 6. Create FastAPI endpoint for mode switching
cat > /home/tutor/iseetutor/src/api/routes/companion.py << 'EOF'
"""
API routes for companion mode functionality
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
from ...models.companion_llm import CompanionLLM, ISEEContentManager
from ...core.companion.mode_manager import TutorMode

router = APIRouter()

# Initialize companion
companion = CompanionLLM()
content_manager = ISEEContentManager()

class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = None
    user_context: Dict = {}

class ModeChangeRequest(BaseModel):
    new_mode: str
    reason: Optional[str] = None

@router.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat messages in current mode"""
    
    # Classify the query
    category, topic = content_manager.classify_query(request.message)
    
    # Add classification to context
    request.user_context['query_category'] = category
    request.user_context['query_topic'] = topic
    
    # Get response from companion
    force_mode = TutorMode(request.mode) if request.mode else None
    response, metadata = await companion.get_response(
        request.message,
        request.user_context,
        force_mode
    )
    
    return {
        "response": response,
        "metadata": metadata,
        "category": category,
        "topic": topic
    }

@router.post("/switch-mode")
async def switch_mode(request: ModeChangeRequest):
    """Explicitly switch between modes"""
    
    try:
        new_mode = TutorMode(request.new_mode)
        message = await companion.mode_manager.switch_mode(new_mode, request.reason)
        
        return {
            "success": True,
            "message": message,
            "new_mode": new_mode.value
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mode")

@router.get("/current-mode")
async def get_current_mode():
    """Get current mode and configuration"""
    
    return {
        "mode": companion.mode_manager.current_mode.value,
        "config": companion.mode_manager.get_mode_config()
    }

@router.get("/session-stats")
async def get_session_stats():
    """Get session statistics"""
    
    mode_history = companion.mode_manager.mode_history
    
    return {
        "mode_switches": len(mode_history),
        "current_mode": companion.mode_manager.current_mode.value,
        "mode_history": mode_history[-5:] if mode_history else []  # Last 5 switches
    }
EOF

echo ""
echo "=== Setup Script Created ==="
echo ""
echo "Next steps:"
echo "1. Run: python3 $KNOWLEDGE_DIR/process_knowledge.py"
echo "2. The system will process Wikipedia into a kid-safe knowledge base"
echo "3. Start the API server to test companion mode"
echo ""
echo "To test mode switching:"
echo "- 'Switch to friend mode' - Changes to companion mode"
echo "- 'Let's study for the ISEE' - Switches back to tutor mode"
echo "- The system can also suggest mode switches based on context"

chmod +x /home/tutor/iseetutor/scripts/setup_companion_mode.sh