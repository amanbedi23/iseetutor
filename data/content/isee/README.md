# ISEE Content Directory Structure

## Where to Place Your PDFs

Place your ISEE practice PDFs in the appropriate directories:

### By Level (Recommended)
- `raw/lower/` - Lower Level ISEE (grades 4-5 applying to 5-6)
- `raw/middle/` - Middle Level ISEE (grades 6-7 applying to 7-8)  
- `raw/upper/` - Upper Level ISEE (grades 8-11 applying to 9-12)

### By Subject (Alternative)
- `raw/verbal/` - Verbal Reasoning materials
- `raw/quantitative/` - Quantitative Reasoning materials
- `raw/reading/` - Reading Comprehension materials
- `raw/math/` - Mathematics Achievement materials
- `raw/writing/` - Essay/Writing materials

## Naming Convention (Optional but Helpful)

For best results, name your PDFs descriptively:
- `ISEE_Upper_Verbal_Practice_Test_1.pdf`
- `ISEE_Middle_Math_Chapter_3_Fractions.pdf`
- `ISEE_Lower_Reading_Passages_Set_2.pdf`

## What Happens Next

1. Place your PDFs in the appropriate `raw/` subdirectories
2. Run the import script: `python3 scripts/import_isee_content.py`
3. The script will:
   - Extract text and questions from PDFs
   - Classify content by subject and difficulty
   - Store in the database
   - Save processed files to `processed/` directories
   - Index content for the AI tutor

## Supported Formats

- PDF files (primary format)
- The import script will be expanded to support:
  - Word documents (.docx)
  - Text files (.txt)
  - JSON question banks (.json)
  - CSV question lists (.csv)