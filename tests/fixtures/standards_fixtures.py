"""Test fixtures for standards data based on real NC music standards"""

from typing import List, Dict, Any
import json
from pathlib import Path

# Real NC Music Standards structure based on actual documents
NC_STANDARDS_FIXTURES = {
    "kindergarten_cn": {
        "grade_level": "Kindergarten",
        "strand_code": "CN", 
        "strand_name": "Connect",
        "standards": [
            {
                "standard_id": "K.CN.1.1",
                "standard_text": "Execute rhythmic patterns, including quarter notes and eighth notes, using body percussion, instruments, or voice.",
                "objectives": [
                    "Students will clap quarter note patterns accurately",
                    "Students will perform eighth note patterns with proper timing",
                    "Students will identify rhythmic patterns in familiar songs",
                    "Students will create simple rhythmic patterns using classroom instruments"
                ]
            },
            {
                "standard_id": "K.CN.1.2", 
                "standard_text": "Execute simple melodic patterns using voice or instruments.",
                "objectives": [
                    "Students will sing simple melodic patterns on pitch",
                    "Students will play melodic patterns on classroom instruments",
                    "Students will identify melodic direction (up/down)",
                    "Students will improvise simple melodic responses"
                ]
            }
        ]
    },
    "first_grade_cr": {
        "grade_level": "1st Grade",
        "strand_code": "CR",
        "strand_name": "Create and Respond", 
        "standards": [
            {
                "standard_id": "1.CR.1.1",
                "standard_text": "Create musical compositions using a variety of sound sources.",
                "objectives": [
                    "Students will compose original rhythmic patterns",
                    "Students will create melodies using classroom instruments",
                    "Students will organize sounds into musical form",
                    "Students will notate original compositions using pictures or symbols"
                ]
            },
            {
                "standard_id": "1.CR.1.2",
                "standard_text": "Evaluate musical performances using appropriate terminology.",
                "objectives": [
                    "Students will identify strengths in peer performances",
                    "Students will use musical vocabulary to describe performances",
                    "Students will suggest improvements for musical performances",
                    "Students will demonstrate respectful audience behavior"
                ]
            }
        ]
    },
    "second_grade_pr": {
        "grade_level": "2nd Grade",
        "strand_code": "PR",
        "strand_name": "Perform",
        "standards": [
            {
                "standard_id": "2.PR.1.1", 
                "standard_text": "Execute musical performances with appropriate technique and expression.",
                "objectives": [
                    "Students will demonstrate proper instrument technique",
                    "Students will perform with dynamic contrast",
                    "Students will maintain steady tempo during performances",
                    "Students will express musical ideas through performance"
                ]
            },
            {
                "standard_id": "2.PR.1.2",
                "standard_text": "Read and perform musical notation.",
                "objectives": [
                    "Students will identify basic musical symbols",
                    "Students will perform simple rhythmic notation",
                    "Students will read melodic patterns on staff",
                    "Students will follow musical form during performance"
                ]
            }
        ]
    },
    "third_grade_re": {
        "grade_level": "3rd Grade", 
        "strand_code": "RE",
        "strand_name": "Respond",
        "standards": [
            {
                "standard_id": "3.RE.1.1",
                "standard_text": "Analyze musical elements using appropriate terminology.",
                "objectives": [
                    "Students will identify tempo, dynamics, and timbre in music",
                    "Students will describe musical form using appropriate terms",
                    "Students will compare musical examples from different cultures",
                    "Students will explain how musical elements create emotional effects"
                ]
            },
            {
                "standard_id": "3.RE.1.2",
                "standard_text": "Interpret meaning in musical works.",
                "objectives": [
                    "Students will identify the mood or emotion of musical pieces",
                    "Students will explain the story or meaning behind program music",
                    "Students will connect music to personal experiences",
                    "Students will describe how music reflects cultural contexts"
                ]
            }
        ]
    }
}

# Sample lesson content for testing
LESSON_CONTENT_FIXTURES = {
    "rhythm_lesson": """# Music Lesson: Rhythm Patterns

## Grade Level
Kindergarten

## Strand
Connect (CN)

## Standard
K.CN.1.1 - Execute rhythmic patterns, including quarter notes and eighth notes, using body percussion, instruments, or voice.

## Learning Objectives
1. Students will clap quarter note patterns accurately
2. Students will perform eighth note patterns with proper timing  
3. Students will identify rhythmic patterns in familiar songs
4. Students will create simple rhythmic patterns using classroom instruments

## Lesson Materials
- Rhythm sticks
- Hand drums
- Triangle
- Rhythm notation cards
- Music recordings with clear rhythmic patterns

## Lesson Activities

### Warm-up (5 minutes)
- Call and response clapping patterns
- Body percussion exploration (clap, pat, stomp)

### Introduction (10 minutes)
- Introduce quarter note and eighth note notation
- Demonstrate patterns using voice and body percussion
- Show rhythm notation cards

### Practice (15 minutes)
- Echo rhythmic patterns using instruments
- Read and perform rhythm patterns from notation cards
- Partner rhythm practice

### Creation (10 minutes)
- Students create their own 4-beat rhythmic patterns
- Share patterns with classmates
- Combine patterns to create class composition

### Performance (5 minutes)
- Perform class composition
- Individual performances of original patterns

## Assessment
- Observation of participation and engagement
- Accuracy of rhythm pattern performance
- Originality of student-created patterns
- Ability to read and perform notation

## Differentiation
- **Advanced**: Create 8-beat patterns, add syncopation
- **Support**: Focus on quarter notes only, use visual aids
- **ELL**: Use non-verbal demonstrations, visual cues

## Integration
- **Math**: Counting beats, fractions (quarter/half)
- **Language Arts**: Pattern recognition, following directions
- **Physical Education**: Motor skills, coordination
""",
    
    "composition_lesson": """# Music Lesson: Musical Storytelling

## Grade Level  
1st Grade

## Strand
Create and Respond (CR)

## Standard
1.CR.1.1 - Create musical compositions using a variety of sound sources.

## Learning Objectives
1. Students will compose original rhythmic patterns
2. Students will create melodies using classroom instruments  
3. Students will organize sounds into musical form
4. Students will notate original compositions using pictures or symbols

## Lesson Materials
- Classroom percussion instruments
- Xylophones or glockenspiels
- Drawing paper and crayons
- Story books for inspiration
- Recording device (optional)

## Lesson Activities

### Introduction (10 minutes)
- Read a short story or poem
- Discuss how music can tell stories
- Listen to examples of programmatic music

### Exploration (15 minutes)
- Experiment with different instrument sounds
- Match sounds to story characters or events
- Create sound effects for story elements

### Composition (20 minutes)
- Students work in small groups to create musical story
- Use graphic notation to plan composition
- Practice performing musical story

### Performance (10 minutes)
- Groups perform their musical stories
- Class members identify story elements in performances
- Discuss how music conveyed the story

### Reflection (5 minutes)
- Students describe their composition process
- Discuss challenges and successes
- Share favorite parts of compositions

## Assessment
- Originality and creativity of compositions
- Ability to match music to story elements
- Use of graphic notation for planning
- Collaboration and participation in group work

## Differentiation
- **Advanced**: Add more complex musical elements, longer forms
- **Support**: Use familiar stories, teacher-guided composition
- **ELL**: Focus on non-verbal storytelling, visual notation
"""
}

# Sample generated lessons for regression testing
GENERATED_LESSON_FIXTURES = {
    "minimal_lesson": """# Music Lesson

## Grade Level
Kindergarten

## Standard
K.CN.1.1

## Objectives
1. Clap quarter note patterns
2. Identify rhythmic patterns

## Activities
1. Warm-up clapping exercises
2. Rhythm reading practice
3. Instrument exploration

## Assessment
- Observation of participation
- Rhythm performance accuracy
""",
    
    "detailed_lesson": """# Comprehensive Music Lesson: Musical Elements Exploration

## Grade Level
3rd Grade

## Strand  
Respond (RE)

## Standard
3.RE.1.1 - Analyze musical elements using appropriate terminology.

## Learning Objectives
1. Students will identify tempo, dynamics, and timbre in music examples
2. Students will describe musical form using appropriate musical terminology
3. Students will compare musical examples from different cultural traditions
4. Students will explain how musical elements create emotional effects in listeners
5. Students will demonstrate understanding of musical vocabulary through discussion and writing

## Cross-Curricular Connections
- **Language Arts**: Descriptive writing, vocabulary development, comparative analysis
- **Social Studies**: Cultural awareness, global perspectives, historical context
- **Science**: Sound waves, acoustics, scientific observation and classification

## Materials and Resources
- Audio recordings from diverse musical traditions
- Musical instruments for demonstration (piano, drums, wind instruments)
- Graphic organizers for musical analysis
- Vocabulary cards with musical terms
- Listening journals for student responses
- Interactive whiteboard or chart paper
- Music listening maps

## Lesson Procedure

### Anticipatory Set (10 minutes)
- Play two contrasting musical examples
- Ask students to describe differences using their own words
- Introduce key vocabulary: tempo, dynamics, timbre, form
- Create a word web with student contributions

### Direct Instruction (15 minutes)
- Model musical analysis using a familiar piece
- Demonstrate how to identify musical elements systematically
- Introduce musical analysis framework:
  1. Tempo (fast/slow, changes)
  2. Dynamics (loud/soft, gradual changes)
  3. Timbre (instrument sounds, vocal qualities)
  4. Form (structure, patterns, repetition)

### Guided Practice (20 minutes)
- Analyze a musical example as a class
- Students work in pairs with guided analysis worksheet
- Circulate and provide support for vocabulary usage
- Share findings and discuss different interpretations

### Independent Practice (25 minutes)
- Students choose from 3 different musical examples
- Complete detailed musical analysis using graphic organizer
- Write a paragraph describing how elements create emotional effects
- Compare their chosen piece with another student's selection

### Closure and Reflection (10 minutes)
- Share key findings from independent analyses
- Discuss how musical analysis deepens appreciation
- Introduce upcoming composition project using analyzed elements

## Assessment Strategies

### Formative Assessment
- Observe student participation in discussions
- Check completion of guided practice worksheets
- Monitor appropriate vocabulary usage in partner work

### Summative Assessment  
- Musical analysis graphic organizer (completed independently)
- Written paragraph describing emotional effects of musical elements
- Comparative analysis of two musical examples

### Performance Assessment
- Student-led musical analysis presentation
- Use of musical terminology in context
- Ability to support opinions with musical evidence

## Differentiation Strategies

### For Advanced Learners
- Analyze more complex musical examples
- Include additional elements: harmony, texture, style
- Research cultural context of chosen pieces
- Create original musical analysis presentation

### For Struggling Learners
- Provide sentence frames for written responses
- Use visual aids for vocabulary (tempo pictures, dynamic symbols)
- Offer simplified musical examples with clear elements
- Work in teacher-led small group for analysis

### For English Language Learners
- Provide bilingual vocabulary cards
- Use non-verbal demonstrations of musical concepts
- Emphasize listening and speaking before writing
- Pair with supportive peer for collaborative work

## Extension Activities
- Create original compositions incorporating analyzed elements
- Research composers from different cultural backgrounds
- Design listening maps for favorite musical pieces
- Interview family members about musical preferences and cultural traditions

## Homework
- Listen to a piece of music at home and complete analysis worksheet
- Teach family members about one musical element learned in class
- Find and bring in an example of music from another culture

## Standards Alignment
- **Music Standards**: 3.RE.1.1, 3.RE.1.2
- **Language Arts**: CCSS.ELA-LITERACY.SL.3.1, CCSS.ELA-LITERACY.W.3.2
- **Social Studies**: Cultural studies standards
- **Science**: Sound and energy standards
"""
}

def get_standards_fixture(grade_strand: str) -> Dict[str, Any]:
    """Get a standards fixture by grade and strand combination"""
    return NC_STANDARDS_FIXTURES.get(grade_strand, {})

def get_lesson_fixture(lesson_type: str) -> str:
    """Get a lesson content fixture by type"""
    return LESSON_CONTENT_FIXTURES.get(lesson_type, "")

def get_generated_lesson_fixture(lesson_type: str) -> str:
    """Get a generated lesson fixture for regression testing"""
    return GENERATED_LESSON_FIXTURES.get(lesson_type, "")

def save_fixtures_to_json(output_dir: Path):
    """Save all fixtures to JSON files for testing"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save standards fixtures
    with open(output_dir / "standards_fixtures.json", "w") as f:
        json.dump(NC_STANDARDS_FIXTURES, f, indent=2)
    
    # Save lesson content fixtures
    with open(output_dir / "lesson_content_fixtures.json", "w") as f:
        json.dump(LESSON_CONTENT_FIXTURES, f, indent=2)
    
    # Save generated lesson fixtures
    with open(output_dir / "generated_lesson_fixtures.json", "w") as f:
        json.dump(GENERATED_LESSON_FIXTURES, f, indent=2)

if __name__ == "__main__":
    # Save fixtures to tests/fixtures directory
    fixtures_dir = Path(__file__).parent
    save_fixtures_to_json(fixtures_dir)
    print(f"✅ Test fixtures saved to {fixtures_dir}")