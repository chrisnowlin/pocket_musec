# Embeddings Source Data Location

## 📂 **Primary Source Data Location**

### **Data Directory - JSON Data**
```
📁 data/
├── 📁 json_data/
│   ├── 📄 nc_arts_education_standards_framework_2024.json    (309 lines)
│   ├── 📄 nc_arts_education_standards_drilling_down_2024.json (195 lines)
│   └── 📄 nc_music_standards_expanded_2024.json               (2,660 lines) ⭐ PRIMARY SOURCE
├── 📁 prepared_texts/
├── 📁 temp/
└── 📄 pocket_musec.db
```

### **Original NC Music Standards and Resources Directory**
```
📁 NC Music Standards and Resources/
├── 📄 [20+ PDF supporting documents]
└── 📄 Various unpacking guides by grade level
```

## 🎯 **Primary Embeddings Source**

### **`nc_music_standards_expanded_2024.json`**
- **File Size**: 2,660 lines of structured JSON
- **Source**: Final Music NCSCOS - Google Docs.pdf
- **Organization**: North Carolina Department of Public Instruction
- **Revision Date**: May 16, 2024
- **Purpose**: Complete K-12 Music standards with objectives

### **Data Structure**
```json
{
  "document": {
    "title": "2024 North Carolina Standard Course of Study - K-12 Music (Expanded)",
    "revision_date": "May 16, 2024",
    "source": "Final Music NCSCOS - Google Docs.pdf",
    "organization": "North Carolina Department of Public Instruction"
  },
  "general_music": {
    "grade_levels": {
      "kindergarten": {
        "grade": "Kindergarten",
        "code": "K",
        "strands": {
          "connect": {
            "strand_code": "CN",
            "strand_name": "Connect",
            "standards": [
              {
                "code": "K.CN.1",
                "text": "Relate musical ideas and works with personal...",
                "objectives": [
                  {
                    "code": "K.CN.1.1",
                    "text": "Identify the similarities and differences..."
                  }
                ]
              }
            ]
          }
        }
      }
    }
  }
}
```

## 🗄️ **Database Storage**

### **Source Data in Database**
The JSON data is ingested into normalized database tables:

```sql
-- Documents (source files)
documents:
  - id: 2
  - title: "2024 North Carolina Standard Course of Study - K-12 Music (Expanded)"
  - revision_date: "May 16, 2024"
  - source: "Final Music NCSCOS - Google Docs.pdf"

-- Standards (112 records from JSON)
standards:
  - id, code, text, category
  - Links to strands, disciplines, levels, documents

-- Supporting lookup tables
strands: CONNECT, CREATE, PRESENT, RESPOND
disciplines: music, dance, theatre, visual_arts
levels: K, 1, 2, 3, 4, 5, 6, 7, 8, N, D, I, AC, AD
```

### **RAG-Ready View**
```sql
-- standards_full VIEW used for embeddings
CREATE VIEW standards_full AS
SELECT 
    s.id AS standard_id,
    s.code AS standard_code,
    s.text AS standard_text,
    str.name AS strand_name,
    l.name AS level_name,
    doc.title AS document_title,
    doc.revision_date
FROM standards s
JOIN strands str ON s.strand_id = str.id
JOIN disciplines d ON s.discipline_id = d.id
JOIN levels l ON s.level_id = l.id
JOIN documents doc ON s.document_id = doc.id
WHERE s.is_variant = 0;
```

## 🔄 **Data Flow for Embeddings**

### **1. Source → Database**
```
data/json_data/nc_music_standards_expanded_2024.json
    ↓ (migrate_standards_database.py)
SQLite tables (standards, strands, levels, etc.)
    ↓ (standards_full VIEW)
112 standardized records
```

### **2. Database → Embeddings**
```
standards_full VIEW
    ↓ (embeddings generation)
standard_embeddings TABLE
    ↓ (RAG system)
Semantic search capability
```

### **3. Text Preparation for Embeddings**
For each standard, the system prepares text like:
```
Grade Level: First Grade
Strand: Create (CR)
Standard: Create original musical ideas and works, independently and collaboratively.
Objectives: Generate musical ideas, Organize and develop musical ideas, 
           Refine and complete musical works
```

## 📋 **Supporting Documents**

### **Additional Reference Materials**
- **Framework Document**: `data/json_data/nc_arts_education_standards_framework_2024.json`
- **Grade-Specific PDFs**: Kindergarten through Advanced unpacking guides (in NC Music Standards and Resources/)
- **Implementation Guides**: VIM and general music implementation (in NC Music Standards and Resources/)
- **Alignment Documents**: Horizontal and vertical alignment guides (in NC Music Standards and Resources/)

### **Original PDF Sources**
- `Final Music NCSCOS - Google Docs.pdf` (primary source)
- `Final NCSCOS Arts Education Framework - Google Docs.pdf`
- Grade-level unpacking documents
- Implementation and alignment guides

## 🔍 **Verification Commands**

### **Check Source Data**
```bash
# View primary source structure
jq ".document" "data/json_data/nc_music_standards_expanded_2024.json"

# Count standards in source
jq ".general_music.grade_levels | to_entries | map(.value.strands | to_entries | map(.value.stands | length)) | flatten | add" "data/json_data/nc_music_standards_expanded_2024.json"
```

### **Check Database Ingestion**
```bash
# Verify database source
sqlite3 data/pocket_musec.db "SELECT title, source FROM documents;"

# Check standards count
sqlite3 data/pocket_musec.db "SELECT COUNT(*) FROM standards_full;"
```

## ✅ **Summary**

**Primary Source**: `data/json_data/nc_music_standards_expanded_2024.json`

This 2,660-line JSON file contains the complete NC music education standards that were:
1. **Ingested** into the SQLite database via migration script
2. **Structured** into normalized tables with proper relationships  
3. **Embedded** into 4096-dimensional vectors for RAG functionality
4. **Stored** in `standard_embeddings` table for semantic search

The original JSON source remains unchanged and serves as the authoritative reference for all 112 standards now available through the RAG system.