# Prepared Texts Management Guide

## Overview

PocketMusec automatically saves the exact text content that gets sent to the embedding API during the embedding generation process. These "prepared texts" are stored in dedicated folders and can be inspected, analyzed, and used to debug extraction quality issues.

## File Structure

```
data/prepared_texts/
├── standards/          # Prepared text for standards (combined content)
│   ├── 2.CN.1.txt
│   ├── 2.CN.2.txt
│   └── ...
└── objectives/         # Prepared text for individual objectives
    ├── 2.CN.1.1.txt
    ├── 2.CN.1.2.txt
    └── ...
```

## What's in the Prepared Texts?

### Standards (`standards/` folder)
Each standard file contains the combined text that was sent to the embedding API:

```
Grade Level: 2
Strand: Connect (CN)
Standard: 2.CN.1 United States, including various indigenous and cultural groups. uses.
Objectives: 2.CN.1.1 Describe how American music reflects heritage, customs, and traditions of people in 2.CN.1.2 Identify cross-curricular connections between music and other content areas. 2.CN.1.3 Describe how music exists in national traditions, celebrations, entertainment, or other
```

### Objectives (`objectives/` folder)
Each objective file contains the raw objective text:

```
2.CN.1.1 Describe how American music reflects heritage, customs, and traditions of people in
```

## CLI Commands for Managing Prepared Texts

### List All Prepared Texts
```bash
pocketmusec embeddings texts
```

Shows:
- Count of standard and objective prepared texts
- List of IDs with prepared texts
- File location information

### View Specific Prepared Text
```bash
# View a standard's prepared text
pocketmusec embeddings show-text 2.CN.1 --type standard

# View an objective's prepared text
pocketmusec embeddings show-text 2.CN.1.1 --type objective
```

### Clear All Prepared Texts
```bash
pocketmusec embeddings clear-texts
```

**Note:** This only removes text files, not embeddings from the database.

## Use Cases

### 1. Debugging Extraction Quality

If you notice poor search results or unexpected embeddings, inspect the prepared texts:

```bash
# Check what text was actually embedded
pocketmusec embeddings show-text 2.CN.1 --type standard
```

Look for:
- Truncated text
- Missing objectives
- Formatting issues
- Encoding problems

### 2. Understanding Embedding Context

See exactly how standards and objectives are combined for embedding:

```bash
# Compare standard vs individual objective texts
pocketmusec embeddings show-text 2.CN.1 --type standard
pocketmusec embeddings show-text 2.CN.1.1 --type objective
pocketmusec embeddings show-text 2.CN.1.2 --type objective
```

### 3. Tweaking Extraction Results

If you need to modify how text is prepared for embedding:

1. **Identify Issues**: Use `show-text` to examine problematic content
2. **Modify Parser**: Update the text preparation logic in `backend/llm/embeddings.py`
3. **Regenerate**: Clear embeddings and regenerate with `--force`

```bash
# Clear and regenerate after fixes
pocketmusec embeddings clear
pocketmusec embeddings clear-texts
pocketmusec embeddings generate --force
```

### 4. Quality Assurance

Systematically review prepared texts before production use:

```bash
# Get overview
pocketmusec embeddings texts

# Sample check specific standards
for id in 2.CN.1 2.PR.1 2.RE.1; do
    echo "=== Standard $id ==="
    pocketmusec embeddings show-text $id --type standard
    echo ""
done
```

## Technical Details

### Text Preparation Process

1. **Standards**: The `_prepare_standard_text()` method combines:
   - Grade level
   - Strand name and code
   - Standard text
   - All associated objectives (concatenated)

2. **Objectives**: The `generate_objective_embedding()` method uses:
   - Raw objective text only

### File Naming Convention

- **Standards**: `{standard_id}.txt` (e.g., `2.CN.1.txt`)
- **Objectives**: `{objective_id}.txt` (e.g., `2.CN.1.1.txt`)

### Encoding

All files are saved using UTF-8 encoding to preserve special characters and formatting.

## Integration with Development Workflow

### Before Code Changes

1. **Baseline**: Generate and review current prepared texts
2. **Identify**: Note specific issues or improvements needed
3. **Document**: Record expected changes

### After Code Changes

1. **Clear**: Remove old prepared texts and embeddings
2. **Regenerate**: Create new prepared texts with updated logic
3. **Compare**: Verify changes match expectations
4. **Test**: Run full embedding generation and search tests

### Automated Quality Checks

Create scripts to validate prepared text quality:

```bash
#!/bin/bash
# Check for common issues
echo "Checking prepared text quality..."

# Check for empty files
find data/prepared_texts -name "*.txt" -size 0 -echo "Empty file: {}"

# Check for truncation indicators
grep -l "\.\.\.$" data/prepared_texts/standards/*.txt

# Check encoding issues
file data/prepared_texts/*/*.txt | grep -v "UTF-8"

echo "Quality check complete."
```

## Troubleshooting

### Common Issues

**1. Missing Prepared Texts**
```bash
# If no prepared texts exist
pocketmusec embeddings texts
# Expected: 0 standards, 0 objectives

# Solution: Generate embeddings
pocketmusec embeddings generate
```

**2. Corrupted Text Files**
```bash
# Check file integrity
head data/prepared_texts/standards/*.txt | head -5

# Solution: Clear and regenerate
pocketmusec embeddings clear-texts
pocketmusec embeddings generate --force
```

**3. Permission Issues**
```bash
# Check directory permissions
ls -la data/prepared_texts/

# Solution: Fix permissions
chmod 755 data/prepared_texts
chmod 644 data/prepared_texts/*/*
```

### Debug Mode

Enable verbose logging to see text preparation in real-time:

```bash
export LOG_LEVEL=DEBUG
pocketmusec embeddings generate --verbose
```

This will show:
- Text being prepared for each standard
- File save operations
- Any errors during text preparation

## Best Practices

1. **Regular Review**: Periodically check prepared texts for quality
2. **Version Control**: Track changes to text preparation logic
3. **Documentation**: Document any custom text formatting rules
4. **Testing**: Include prepared text validation in test suites
5. **Backup**: Keep copies of prepared texts for major releases

## Integration with Other Tools

### Text Editors
Open prepared texts directly in your editor:

```bash
# Open all standard texts
code data/prepared_texts/standards/

# Open specific text
code data/prepared_texts/standards/2.CN.1.txt
```

### Text Analysis Tools
Use external tools for analysis:

```bash
# Word frequency analysis
wordfreq data/prepared_texts/standards/*.txt

# Text length statistics
wc -l data/prepared_texts/*/*.txt

# Search for patterns
grep -r "truncated" data/prepared_texts/
```

### Version Control
Track changes to prepared texts:

```bash
# Add to git (optional)
git add data/prepared_texts/
git commit -m "Add prepared texts for debugging"
```

---

This guide helps you effectively use PocketMusec's prepared text feature for debugging, quality assurance, and extraction result optimization.