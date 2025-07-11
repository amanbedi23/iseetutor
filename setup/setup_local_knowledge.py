#!/usr/bin/env python3
"""
Set up local knowledge bases in the project directory
Works without sudo or /mnt/storage access
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

class LocalKnowledgeSetup:
    def __init__(self):
        # Use local directory instead of /mnt/storage
        self.base_dir = Path("./data/knowledge")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_all(self):
        """Set up all knowledge bases locally"""
        print("=== ISEE Tutor Local Knowledge Base Setup ===\n")
        print(f"Setting up knowledge bases in: {self.base_dir.absolute()}\n")
        
        # Create directory structure
        self.create_directories()
        
        # Set up different knowledge bases
        self.setup_isee_content()
        self.setup_general_knowledge()
        self.setup_science_facts()
        self.setup_math_resources()
        self.create_sample_content()
        
        print("\n✅ Local knowledge base setup complete!")
        print(f"📁 Location: {self.base_dir.absolute()}")
        
    def create_directories(self):
        """Create knowledge base directory structure"""
        dirs = [
            "isee_content/verbal",
            "isee_content/quantitative", 
            "isee_content/reading",
            "isee_content/mathematics",
            "general_knowledge/science",
            "general_knowledge/history",
            "general_knowledge/geography",
            "fun_facts",
            "stories",
            "databases"
        ]
        
        for dir_path in dirs:
            (self.base_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        print("✅ Created directory structure")
        
    def setup_isee_content(self):
        """Set up ISEE-specific content database"""
        print("\n📚 Setting up ISEE content database...")
        
        db_path = self.base_dir / "databases" / "isee_content.db"
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Create tables
        c.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                grade_level TEXT NOT NULL,
                difficulty INTEGER,
                description TEXT
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                topic_id INTEGER,
                question_type TEXT NOT NULL,
                question TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                difficulty INTEGER,
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS study_tips (
                id INTEGER PRIMARY KEY,
                subject TEXT NOT NULL,
                tip TEXT NOT NULL,
                example TEXT
            )
        ''')
        
        # Insert sample ISEE topics
        isee_topics = [
            # Verbal Reasoning
            ("verbal_reasoning", "synonyms", "all", 3, "Understanding word meanings and relationships"),
            ("verbal_reasoning", "sentence_completion", "all", 4, "Filling in blanks with appropriate words"),
            ("verbal_reasoning", "analogies", "middle/upper", 5, "Identifying relationships between word pairs"),
            
            # Quantitative Reasoning  
            ("quantitative_reasoning", "number_concepts", "all", 3, "Understanding numbers and operations"),
            ("quantitative_reasoning", "algebraic_concepts", "middle/upper", 4, "Basic algebra and patterns"),
            ("quantitative_reasoning", "geometry", "all", 4, "Shapes, angles, and spatial reasoning"),
            ("quantitative_reasoning", "measurement", "all", 3, "Units, conversions, and estimation"),
            ("quantitative_reasoning", "data_analysis", "all", 4, "Charts, graphs, and probability"),
            
            # Reading Comprehension
            ("reading_comprehension", "main_idea", "all", 3, "Identifying the central theme"),
            ("reading_comprehension", "supporting_details", "all", 3, "Finding specific information"),
            ("reading_comprehension", "inference", "all", 4, "Drawing conclusions from text"),
            ("reading_comprehension", "vocabulary_in_context", "all", 4, "Understanding words from context"),
            ("reading_comprehension", "tone_and_mood", "middle/upper", 5, "Identifying author's attitude"),
            
            # Mathematics Achievement
            ("mathematics", "arithmetic", "all", 3, "Basic operations and number properties"),
            ("mathematics", "fractions_decimals", "all", 4, "Operations with fractions and decimals"),
            ("mathematics", "algebra", "middle/upper", 5, "Equations and expressions"),
            ("mathematics", "geometry", "all", 4, "Geometric concepts and calculations"),
            ("mathematics", "word_problems", "all", 5, "Applying math to real situations")
        ]
        
        c.executemany(
            'INSERT OR REPLACE INTO topics (subject, topic, grade_level, difficulty, description) VALUES (?, ?, ?, ?, ?)',
            isee_topics
        )
        
        # Insert sample questions
        sample_questions = [
            (1, "multiple_choice", "Which word means the same as 'happy'?", 
             json.dumps(["sad", "joyful", "angry", "tired"]), "joyful",
             "Joyful means feeling or expressing great happiness, which is synonymous with happy.", 3),
             
            (2, "fill_blank", "The student was _____ to learn that she had won the science fair.",
             json.dumps(["disappointed", "elated", "confused", "indifferent"]), "elated",
             "Elated means very happy and excited, which fits the context of winning.", 4),
             
            (14, "multiple_choice", "What is 3/4 + 1/2?",
             json.dumps(["5/6", "4/6", "5/4", "7/8"]), "5/4",
             "To add fractions, find common denominator: 3/4 + 2/4 = 5/4 = 1 1/4", 4),
             
            (6, "multiple_choice", "If a square has a perimeter of 20 cm, what is its area?",
             json.dumps(["25 cm²", "20 cm²", "16 cm²", "100 cm²"]), "25 cm²",
             "Perimeter = 4 × side, so side = 20÷4 = 5 cm. Area = side² = 5² = 25 cm²", 4),
             
            (3, "analogy", "Bird is to Nest as Bee is to _____",
             json.dumps(["Honey", "Hive", "Flower", "Wing"]), "Hive",
             "A bird lives in a nest, just as a bee lives in a hive. This is a 'home' relationship.", 3)
        ]
        
        c.executemany(
            'INSERT OR REPLACE INTO questions (topic_id, question_type, question, options, correct_answer, explanation, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?)',
            sample_questions
        )
        
        # Insert study tips
        study_tips = [
            ("verbal_reasoning", "For synonyms, create word families and group similar words together", 
             "Happy family: joyful, elated, cheerful, delighted"),
            ("quantitative_reasoning", "Draw diagrams for geometry problems to visualize the solution",
             "For area problems, sketch the shape and label all measurements"),
            ("reading_comprehension", "Read the questions first, then scan the passage for answers",
             "This helps you focus on relevant information while reading"),
            ("mathematics", "Show all your work, even for mental calculations",
             "This helps catch errors and can earn partial credit"),
            ("general", "Practice timing yourself to build speed and confidence",
             "ISEE tests are timed, so practice under similar conditions")
        ]
        
        c.executemany(
            'INSERT OR REPLACE INTO study_tips (subject, tip, example) VALUES (?, ?, ?)',
            study_tips
        )
        
        conn.commit()
        conn.close()
        print("✅ ISEE content database created with sample questions")
        
    def setup_general_knowledge(self):
        """Set up general knowledge for friend mode"""
        print("\n🌍 Setting up general knowledge database...")
        
        db_path = self.base_dir / "databases" / "general_knowledge.db"
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY,
                category TEXT NOT NULL,
                subcategory TEXT,
                fact TEXT NOT NULL,
                explanation TEXT,
                age_group TEXT,
                fun_level INTEGER
            )
        ''')
        
        # Extended facts for friend mode
        facts = [
            # Animals
            ("animals", "ocean", "Octopuses have three hearts!", 
             "Two pump blood to the gills, one pumps to the body. They also have blue blood!", "all", 5),
            ("animals", "pets", "Cats spend 70% of their lives sleeping!",
             "That's 13-16 hours a day. No wonder they're so energetic when awake!", "all", 4),
            ("animals", "wild", "A group of flamingos is called a 'flamboyance'!",
             "These pink birds get their color from the shrimp they eat.", "all", 5),
            
            # Space
            ("space", "planets", "A day on Venus is longer than its year!",
             "Venus rotates so slowly that it takes 243 Earth days to spin once, but only 225 days to orbit the Sun.", "all", 5),
            ("space", "moon", "You can fit all the planets between Earth and the Moon!",
             "The average distance is about 238,855 miles - just enough space!", "middle", 5),
            ("space", "stars", "The Sun is actually white, not yellow!",
             "It appears yellow because of Earth's atmosphere scattering blue light.", "middle", 4),
            
            # Science
            ("science", "human_body", "Your body has 206 bones, but babies are born with 300!",
             "Many bones fuse together as we grow up.", "all", 4),
            ("science", "physics", "Hot water can freeze faster than cold water!",
             "This is called the Mpemba effect, and scientists still debate why it happens.", "middle", 5),
            ("science", "chemistry", "Honey never goes bad!",
             "Archaeologists have found 3000-year-old honey in Egyptian tombs that was still good!", "all", 4),
            
            # History
            ("history", "inventions", "The first computer bug was an actual bug!",
             "In 1947, a moth got trapped in a computer at Harvard, causing errors.", "middle", 4),
            ("history", "ancient", "The Great Wall of China isn't visible from space!",
             "This is a common myth - it's too narrow to see without magnification.", "all", 3),
            
            # Geography
            ("geography", "records", "The deepest part of the ocean is deeper than Mount Everest is tall!",
             "The Mariana Trench is about 36,000 feet deep, while Everest is 29,000 feet tall.", "all", 5),
            ("geography", "countries", "There's a country that's only 2.1 km² big!",
             "Monaco is smaller than New York's Central Park!", "middle", 4)
        ]
        
        c.executemany(
            'INSERT OR REPLACE INTO facts (category, subcategory, fact, explanation, age_group, fun_level) VALUES (?, ?, ?, ?, ?, ?)',
            facts
        )
        
        conn.commit()
        conn.close()
        print("✅ General knowledge database created with fun facts")
        
    def setup_science_facts(self):
        """Create science facts for educational chat"""
        print("\n🔬 Setting up science experiments...")
        
        db_path = self.base_dir / "databases" / "science_facts.db"
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                materials TEXT NOT NULL,
                instructions TEXT NOT NULL,
                explanation TEXT,
                safety_notes TEXT,
                age_group TEXT
            )
        ''')
        
        experiments = [
            ("Volcano Eruption", 
             "Baking soda, vinegar, dish soap, food coloring, container",
             "1. Put 3 tbsp baking soda in container\n2. Add drops of dish soap and food coloring\n3. Pour 1/2 cup vinegar and watch eruption!",
             "The acid (vinegar) reacts with the base (baking soda) to create CO2 gas, which makes bubbles.",
             "Do this outside or in a sink. Wear safety goggles.",
             "elementary"),
            
            ("Invisible Ink",
             "Lemon juice, water, cotton swab, white paper, lamp",
             "1. Mix equal parts lemon juice and water\n2. Use cotton swab to write a message\n3. Let it dry completely\n4. Hold paper near lamp bulb to reveal!",
             "The acid in lemon juice weakens the paper, which browns faster when heated.",
             "Adult supervision required for heat source. Don't touch the hot bulb!",
             "all"),
             
            ("Dancing Raisins",
             "Clear soda (like Sprite), raisins, clear glass",
             "1. Fill glass with soda\n2. Drop in 5-6 raisins\n3. Watch them dance up and down!",
             "CO2 bubbles stick to the raisins, making them float. At the top, bubbles pop and raisins sink.",
             "No safety concerns - you can even eat the raisins after!",
             "elementary"),
             
            ("Rainbow in a Glass",
             "Honey, dish soap, milk, water, food coloring, tall glass",
             "1. Pour honey slowly\n2. Add dish soap gently\n3. Mix milk with one color, pour slowly\n4. Mix water with another color, pour last",
             "Different liquids have different densities, so they layer instead of mixing.",
             "Pour slowly over a spoon to prevent mixing.",
             "all")
        ]
        
        c.executemany(
            'INSERT OR REPLACE INTO experiments (name, materials, instructions, explanation, safety_notes, age_group) VALUES (?, ?, ?, ?, ?, ?)',
            experiments
        )
        
        conn.commit()
        conn.close()
        print("✅ Science experiments database created")
        
    def setup_math_resources(self):
        """Create math practice resources"""
        print("\n➕ Setting up math tricks...")
        
        db_path = self.base_dir / "databases" / "math_resources.db"
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS math_tricks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                trick TEXT NOT NULL,
                example TEXT,
                practice_problems TEXT
            )
        ''')
        
        tricks = [
            ("9s Finger Trick", "multiplication",
             "Hold up 10 fingers. For 9×n, fold down the nth finger. Fingers on left = tens, fingers on right = ones.",
             "For 9×7: Fold 7th finger. 6 fingers left, 3 right = 63",
             "Try: 9×3, 9×5, 9×8"),
            
            ("Fraction Pizza", "fractions",
             "Think of fractions as pizza slices. The bottom number is total slices, top is how many you have.",
             "3/8 means pizza cut into 8 slices, you have 3",
             "Which is bigger: 3/8 or 2/5 of a pizza?"),
             
            ("Multiply by 11", "multiplication",
             "For 2-digit numbers: Add the digits and put the sum in the middle.",
             "23 × 11: 2+3=5, so answer is 253",
             "Try: 42×11, 35×11, 61×11"),
             
            ("Percentage Trick", "percentages",
             "To find 10%, move decimal left. For 5%, find 10% and halve it.",
             "10% of 80 = 8.0, so 5% of 80 = 4.0",
             "Find: 10% of 250, 5% of 60, 20% of 45")
        ]
        
        c.executemany(
            'INSERT OR REPLACE INTO math_tricks (name, category, trick, example, practice_problems) VALUES (?, ?, ?, ?, ?)',
            tricks
        )
        
        conn.commit()
        conn.close()
        print("✅ Math tricks database created")
        
    def create_sample_content(self):
        """Create sample content files"""
        print("\n📄 Creating sample content files...")
        
        # Sample ISEE vocabulary list
        vocab_file = self.base_dir / "isee_content" / "verbal" / "vocabulary_list.json"
        vocab_data = {
            "elementary_level": [
                {"word": "abundant", "definition": "plentiful; more than enough", "example": "The garden had abundant flowers.", "synonyms": ["plentiful", "ample", "copious"]},
                {"word": "ancient", "definition": "very old; from long ago", "example": "We studied ancient civilizations.", "synonyms": ["old", "antique", "prehistoric"]},
                {"word": "brilliant", "definition": "very bright or smart", "example": "The brilliant student solved the puzzle.", "synonyms": ["bright", "intelligent", "dazzling"]},
                {"word": "cautious", "definition": "careful to avoid danger", "example": "Be cautious when crossing the street.", "synonyms": ["careful", "wary", "prudent"]},
                {"word": "delicate", "definition": "easily broken; fragile", "example": "The delicate vase needs careful handling.", "synonyms": ["fragile", "dainty", "tender"]}
            ],
            "middle_level": [
                {"word": "adversary", "definition": "opponent; enemy", "example": "The chess players were adversaries.", "synonyms": ["opponent", "rival", "foe"]},
                {"word": "benevolent", "definition": "kind and generous", "example": "The benevolent donor helped the school.", "synonyms": ["kind", "charitable", "generous"]},
                {"word": "candid", "definition": "honest and direct", "example": "She gave a candid opinion.", "synonyms": ["frank", "honest", "straightforward"]},
                {"word": "diligent", "definition": "hardworking and careful", "example": "The diligent student always completes homework.", "synonyms": ["industrious", "assiduous", "conscientious"]},
                {"word": "eloquent", "definition": "fluent and persuasive in speaking", "example": "The eloquent speaker captivated the audience.", "synonyms": ["articulate", "expressive", "fluent"]}
            ]
        }
        
        with open(vocab_file, 'w') as f:
            json.dump(vocab_data, f, indent=2)
        
        # Create index file
        index_file = self.base_dir / "index.json"
        index_data = {
            "created": datetime.now().isoformat(),
            "databases": [
                "databases/isee_content.db",
                "databases/general_knowledge.db",
                "databases/science_facts.db",
                "databases/math_resources.db"
            ],
            "content_files": [
                "isee_content/verbal/vocabulary_list.json"
            ],
            "stats": {
                "isee_topics": 18,
                "sample_questions": 5,
                "fun_facts": 13,
                "experiments": 4,
                "math_tricks": 4
            }
        }
        
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        print("✅ Sample content files and index created")
        
        # Create a summary file
        summary_file = self.base_dir / "README.md"
        with open(summary_file, 'w') as f:
            f.write("""# ISEE Tutor Knowledge Base

This directory contains the local knowledge bases for the ISEE Tutor system.

## Contents

### ISEE Content (`isee_content.db`)
- 18 topics across all ISEE subjects
- Sample questions with explanations
- Study tips and strategies
- Vocabulary lists with synonyms

### General Knowledge (`general_knowledge.db`)
- 13+ fun facts about animals, space, science, history, and geography
- Age-appropriate content for elementary and middle school
- Explanations to encourage curiosity

### Science Experiments (`science_facts.db`)
- 4 safe, fun experiments kids can do at home
- Clear instructions and materials lists
- Scientific explanations
- Safety notes for each experiment

### Math Resources (`math_resources.db`)
- Mental math tricks
- Visual learning techniques
- Practice problems
- Tips for common ISEE math topics

## Usage

These databases are used by:
- **Tutor Mode**: ISEE content, questions, and study tips
- **Friend Mode**: Fun facts, experiments, and general knowledge
- **Both Modes**: Math tricks and educational content

The system automatically selects appropriate content based on the current mode and user's grade level.
""")
        
        print("✅ Knowledge base documentation created")

def main():
    """Main setup function"""
    setup = LocalKnowledgeSetup()
    
    try:
        setup.setup_all()
        
        print("\n=== Local Knowledge Base Setup Complete ===")
        print(f"\nLocation: {setup.base_dir.absolute()}")
        print("\nDatabases created:")
        print("  ✅ ISEE content (topics, questions, study tips)")
        print("  ✅ General knowledge (facts for friend mode)")
        print("  ✅ Science facts and experiments")
        print("  ✅ Math tricks and resources")
        print("\nThe ISEE Tutor now has local knowledge bases for both")
        print("tutoring mode and friend mode conversations!")
        print("\nNote: When you have sudo access, you can move these to /mnt/storage")
        print("by running: sudo mv data/knowledge /mnt/storage/")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()