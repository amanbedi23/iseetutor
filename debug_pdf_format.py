#!/usr/bin/env python3
"""Debug PDF format to understand question structure"""

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

def main():
    # Load the processed JSON
    with open('data/isee_content/ISEE_LowerTest1_processed.json', 'r') as f:
        data = json.load(f)
    
    # Look at a specific page that should have questions
    page_8_text = data['pages'][7]['text']  # Page 8 has VR questions
    
    print("=== PAGE 8 TEXT (First 1000 chars) ===")
    print(page_8_text[:1000])
    print("\n=== Looking for question patterns ===")
    
    # Look for numbered items
    lines = page_8_text.split('\n')
    for i, line in enumerate(lines):
        if line.strip() and any(line.strip().startswith(f"{n}.") for n in range(1, 35)):
            print(f"Line {i}: {line[:100]}")
            # Show next few lines for context
            for j in range(1, 5):
                if i+j < len(lines):
                    print(f"  +{j}: {lines[i+j][:100]}")

if __name__ == "__main__":
    main()