#!/usr/bin/env python3
"""
Set up local knowledge bases for ISEE Tutor
Downloads and processes educational content for offline use
"""

import os
import sys
import json
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
import subprocess
from tqdm import tqdm

class KnowledgeBaseSetup:
    def __init__(self):
        self.base_dir = Path("/mnt/storage/knowledge")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_all(self):
        """Set up all knowledge bases"""
        print("=== ISEE Tutor Knowledge Base Setup ===\n")
        
        # Create directory structure
        self.create_directories()
        
        # Set up different knowledge bases
        self.setup_isee_content()
        self.setup_general_knowledge()
        self.setup_science_facts()
        self.setup_math_resources()
        self.create_sample_content()
        
        print("\n✅ Knowledge base setup complete!")
        
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
            'INSERT INTO topics (subject, topic, grade_level, difficulty, description) VALUES (?, ?, ?, ?, ?)',
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
             "To add fractions, find common denominator: 3/4 + 2/4 = 5/4 = 1 1/4", 4)
        ]
        
        c.executemany(
            'INSERT INTO questions (topic_id, question_type, question, options, correct_answer, explanation, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?)',
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
             "This helps catch errors and can earn partial credit")
        ]
        
        c.executemany(
            'INSERT INTO study_tips (subject, tip, example) VALUES (?, ?, ?)',
            study_tips
        )
        
        conn.commit()
        conn.close()
        print("✅ ISEE content database created")
        
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
        
        # Sample facts for friend mode
        facts = [
            ("animals", "ocean", "Octopuses have three hearts!", 
             "Two pump blood to the gills, one pumps to the body.", "all", 5),
            ("space", "planets", "A day on Venus is longer than its year!",
             "Venus rotates so slowly that it takes 243 Earth days to spin once, but only 225 days to orbit the Sun.", "all", 5),
            ("science", "human_body", "Your body has 206 bones, but babies are born with 300!",
             "Many bones fuse together as we grow up.", "all", 4),
            ("history", "inventions", "The first computer bug was an actual bug!",
             "In 1947, a moth got trapped in a computer at Harvard, causing errors.", "middle", 4),
            ("geography", "records", "The deepest part of the ocean is deeper than Mount Everest is tall!",
             "The Mariana Trench is about 36,000 feet deep.", "all", 5)
        ]
        
        c.executemany(
            'INSERT INTO facts (category, subcategory, fact, explanation, age_group, fun_level) VALUES (?, ?, ?, ?, ?, ?)',
            facts
        )
        
        conn.commit()
        conn.close()
        print("✅ General knowledge database created")
        
    def setup_science_facts(self):
        """Create science facts for educational chat"""
        print("\n🔬 Setting up science facts...")
        
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
             "1. Put baking soda in container\n2. Add drops of dish soap and food coloring\n3. Pour vinegar and watch eruption!",
             "The acid (vinegar) reacts with the base (baking soda) to create CO2 gas.",
             "Do this outside or in a sink. Wear safety goggles.",
             "elementary"),
            
            ("Invisible Ink",
             "Lemon juice, water, paper, lamp or hair dryer",
             "1. Mix lemon juice with a little water\n2. Write message with cotton swab\n3. Let dry\n4. Hold near heat to reveal!",
             "The acid in lemon juice weakens the paper, which browns faster when heated.",
             "Adult supervision required for heat source.",
             "all")
        ]
        
        c.executemany(
            'INSERT INTO experiments (name, materials, instructions, explanation, safety_notes, age_group) VALUES (?, ?, ?, ?, ?, ?)',
            experiments
        )
        
        conn.commit()
        conn.close()
        print("✅ Science facts database created")
        
    def setup_math_resources(self):
        """Create math practice resources"""
        print("\n➕ Setting up math resources...")
        
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
             "Which is bigger: 3/8 or 2/5 of a pizza?")
        ]
        
        c.executemany(
            'INSERT INTO math_tricks (name, category, trick, example, practice_problems) VALUES (?, ?, ?, ?, ?)',
            tricks
        )
        
        conn.commit()
        conn.close()
        print("✅ Math resources database created")
        
    def create_sample_content(self):
        """Create sample content files"""
        print("\n📄 Creating sample content files...")
        
        # Sample ISEE vocabulary list
        vocab_file = self.base_dir / "isee_content" / "verbal" / "vocabulary_list.json"
        vocab_data = {
            "elementary_level": [
                {"word": "abundant", "definition": "plentiful; more than enough", "example": "The garden had abundant flowers."},
                {"word": "ancient", "definition": "very old; from long ago", "example": "We studied ancient civilizations."},
                {"word": "brilliant", "definition": "very bright or smart", "example": "The brilliant student solved the puzzle."}
            ],
            "middle_level": [
                {"word": "adversary", "definition": "opponent; enemy", "example": "The chess players were adversaries."},
                {"word": "benevolent", "definition": "kind and generous", "example": "The benevolent donor helped the school."},
                {"word": "candid", "definition": "honest and direct", "example": "She gave a candid opinion."}
            ]
        }
        
        with open(vocab_file, 'w') as f:
            json.dump(vocab_data, f, indent=2)
        
        # Sample reading passage
        passage_file = self.base_dir / "isee_content" / "reading" / "sample_passage.txt"
        with open(passage_file, 'w') as f:
            f.write("""The Life Cycle of Butterflies

Butterflies undergo a remarkable transformation called metamorphosis. This process has four distinct stages: egg, larva (caterpillar), pupa (chrysalis), and adult butterfly.

The cycle begins when a female butterfly lays tiny eggs on a host plant. These eggs are often no bigger than a pinhead. After a few days, a tiny caterpillar emerges. The caterpillar's main job is to eat and grow. It munches on leaves constantly, growing so quickly that it must shed its skin several times.

When the caterpillar has grown enough, it forms a chrysalis. Inside this protective casing, an amazing transformation occurs. The caterpillar's body completely reorganizes itself into a butterfly. This process, called metamorphosis, takes about two weeks.

Finally, a beautiful butterfly emerges. Its wings are soft and crumpled at first, but they soon expand and harden. The adult butterfly will feed on nectar from flowers and eventually lay eggs to begin the cycle again.

Questions:
1. What are the four stages of butterfly metamorphosis?
2. What is the main purpose of the caterpillar stage?
3. How long does the transformation in the chrysalis typically take?
4. What do adult butterflies eat?""")
        
        print("✅ Sample content files created")
        
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
                "isee_content/verbal/vocabulary_list.json",
                "isee_content/reading/sample_passage.txt"
            ],
            "total_size_mb": 50  # Placeholder
        }
        
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        print("✅ Knowledge base index created")

def main():
    """Main setup function"""
    setup = KnowledgeBaseSetup()
    
    try:
        setup.setup_all()
        
        print("\n=== Knowledge Base Setup Complete ===")
        print(f"\nLocation: /mnt/storage/knowledge")
        print("\nDatabases created:")
        print("  - ISEE content (topics, questions, study tips)")
        print("  - General knowledge (facts for friend mode)")
        print("  - Science facts and experiments")
        print("  - Math tricks and resources")
        print("\nThe ISEE Tutor now has offline knowledge bases for both")
        print("tutoring mode and friend mode conversations!")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        print("Please check permissions and try again.")

if __name__ == "__main__":
    main()