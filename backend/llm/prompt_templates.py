"""Prompt templates for lesson generation using Qwen models"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json

from backend.repositories.models import Standard, Objective


@dataclass
class LessonPromptContext:
    """Context for lesson generation prompts"""
    grade_level: str
    strand_code: str
    strand_name: str
    strand_description: str
    standard_id: str
    standard_text: str
    objectives: List[str]
    additional_context: Optional[str] = None
    lesson_duration: Optional[str] = None
    class_size: Optional[int] = None
    available_resources: Optional[List[str]] = None


class LessonPromptTemplates:
    """Prompt templates optimized for Qwen models"""
    
    @staticmethod
    def get_system_prompt() -> str:
        """
        System prompt for Qwen models following best practices.
        Uses XML tags and clear role definition as recommended in Qwen docs.
        """
        return """<role>
You are an expert music education curriculum specialist with deep knowledge of:
- North Carolina music education standards and frameworks
- Age-appropriate pedagogical approaches for K-12 music education
- Lesson planning and instructional design for music classrooms
- Assessment strategies and student engagement techniques
- Differentiated instruction for diverse learning needs
</role>

<expertise>
- 15+ years of experience in music education curriculum development
- Certified music educator with extensive classroom teaching experience
- Expert in aligning lessons with state and national music standards
- Skilled in creating engaging, standards-based music activities
- Proficient in assessment design and student evaluation methods
</expertise>

<instructions>
1. Always align lessons with the provided NC music standards
2. Design age-appropriate activities for the specified grade level
3. Include clear learning objectives and assessment strategies
4. Provide detailed, step-by-step instructional procedures
5. Incorporate diverse teaching methods and student engagement strategies
6. Ensure all content is pedagogically sound and classroom-ready
7. Use professional music education terminology appropriately
8. Structure responses with clear headings and organized sections
</instructions>

<output_format>
- Use markdown formatting with clear headings (##, ###)
- Include time estimates for each activity
- Provide specific materials and resources needed
- Include assessment methods and success criteria
- Add differentiation strategies for diverse learners
- End with reflection questions and extension activities
</output_format>"""

    @staticmethod
    def generate_lesson_plan_prompt(context: LessonPromptContext) -> str:
        """
        Generate a comprehensive lesson plan prompt using Qwen best practices.
        Uses XML tags and structured format as recommended for Qwen3.
        """
        objectives_text = "\n".join([f"- {obj}" for obj in context.objectives])
        resources_text = ", ".join(context.available_resources or ["standard classroom instruments"])
        
        return f"""<task>
Generate a comprehensive, standards-based music lesson plan for {context.grade_level} students.
</task>

<context>
<grade_level>{context.grade_level}</grade_level>
<strand>
<code>{context.strand_code}</code>
<name>{context.strand_name}</name>
<description>{context.strand_description}</description>
</strand>

<standard>
<id>{context.standard_id}</id>
<text>{context.standard_text}</text>
</standard>

<learning_objectives>
{objectives_text}
</learning_objectives>

<lesson_parameters>
<duration>{context.lesson_duration or "45 minutes"}</duration>
<class_size>{context.class_size or "25 students"}</class_size>
<available_resources>{resources_text}</available_resources>
</lesson_parameters>

{f'<additional_context>{context.additional_context}</additional_context>' if context.additional_context else ''}
</context>

<requirements>
1. Create a detailed lesson plan that directly addresses the standard and objectives
2. Include engaging, age-appropriate musical activities
3. Provide clear assessment strategies and success criteria
4. Incorporate differentiation for diverse learning needs
5. Ensure all activities are feasible within the time constraints
6. Include specific materials and setup requirements
7. Add reflection and extension opportunities
</requirements>

<structure>
## Lesson Overview
- Grade level, duration, and focus area
- Primary standard and learning objectives

## Learning Objectives
- Clear, measurable objectives aligned with the standard

## Materials and Resources
- Detailed list of all materials needed
- Setup requirements and preparation notes

## Lesson Procedure
### Introduction/Hook (5-10 minutes)
- Engaging opening activity
- Connection to prior learning

### Main Activities (25-35 minutes)
- Step-by-step instructional procedures
- Modeling and guided practice
- Independent or collaborative work
- Specific time allocations for each activity

### Closure/Reflection (5-10 minutes)
- Summary of key learning
- Student reflection opportunities
- Connection to future learning

## Assessment Strategies
- Formative assessment methods
- Success criteria and rubrics
- Observation guidelines

## Differentiation
- Strategies for diverse learners
- Extension activities for advanced students
- Support strategies for struggling students

## Reflection and Extension
- Student reflection questions
- Homework or extension activities
- Cross-curricular connections
</structure>

<quality_criteria>
- Activities are engaging and developmentally appropriate
- Clear alignment between objectives, activities, and assessment
- Practical implementation in real classroom settings
- Inclusive and culturally responsive teaching approaches
- Opportunities for student creativity and expression
</quality_criteria>"""

    @staticmethod
    def generate_activity_ideas_prompt(context: LessonPromptContext) -> str:
        """
        Generate specific activity ideas for a music standard.
        Uses structured format with clear examples.
        """
        objectives_text = "\n".join([f"- {obj}" for obj in context.objectives])
        return f"""<task>
Generate 5-7 creative, engaging music activities for {context.grade_level} students that address the following standard.
</task>

<standard>
<strand>{context.strand_name} ({context.strand_code})</strand>
<text>{context.standard_text}</text>
<objectives>
{objectives_text}
</objectives>
</standard>

<activity_requirements>
Each activity should include:
1. Clear title and brief description
2. Estimated time required
3. Specific materials needed
4. Step-by-step procedure
5. Assessment method
6. Differentiation strategies
7. Student engagement elements
</activity_requirements>

<examples>
Provide a mix of activity types:
- Performance-based activities
- Listening and analysis activities
- Creative composition activities
- Movement and kinesthetic activities
- Technology-integrated activities
- Collaborative group activities
- Individual reflection activities
</examples>

<format>
For each activity, use this structure:

### Activity Title
**Time:** X minutes  
**Materials:** List of required materials  
**Procedure:** Step-by-step instructions  
**Assessment:** How to measure learning  
**Differentiation:** Support and extension strategies  
**Engagement:** Elements that make it engaging for students
</format>"""

    @staticmethod
    def generate_assessment_prompt(context: LessonPromptContext) -> str:
        """
        Generate assessment strategies for a music standard.
        """
        objectives_text = "\n".join([f"- {obj}" for obj in context.objectives])
        return f"""<task>
Create comprehensive assessment strategies for the following music standard and objectives.
</task>

<standard>
<grade>{context.grade_level}</grade>
<strand>{context.strand_name}</strand>
<text>{context.standard_text}</text>
</standard>

<objectives>
{objectives_text}
</objectives>

<assessment_types>
Create assessments for:
1. Formative Assessment (during instruction)
2. Summative Assessment (end of unit/lesson)
3. Performance Assessment (musical demonstration)
4. Written Assessment (knowledge and understanding)
5. Self/Peer Assessment (student reflection)
</assessment_types>

<requirements>
For each assessment type, include:
- Clear description of the assessment
- Rubric or scoring criteria
- Implementation instructions
- Time requirements
- Materials needed
- Differentiation strategies
</requirements>

<quality_indicators>
Ensure assessments measure:
- Musical skills and techniques
- Knowledge and understanding
- Creative expression
- Collaboration and participation
- Critical thinking and reflection
</quality_indicators>"""

    @staticmethod
    def generate_differentiation_prompt(context: LessonPromptContext) -> str:
        """
        Generate differentiation strategies for diverse learners.
        """
        return f"""<task>
Develop comprehensive differentiation strategies for the following music lesson to support all learners.
</task>

<lesson_context>
<grade>{context.grade_level}</grade>
<standard>{context.standard_text}</standard>
<class_size>{context.class_size or "25 students"}</class_size>
</lesson_context>

<learner_groups>
Consider needs of:
1. Students with diverse learning styles (visual, auditory, kinesthetic)
2. English language learners
3. Students with special needs (physical, cognitive, emotional)
4. Advanced learners needing enrichment
5. Students needing additional support
6. Students with varying musical backgrounds and experiences
</learner_groups>

<strategy_types>
Provide strategies for:
- Content differentiation (what students learn)
- Process differentiation (how students learn)
- Product differentiation (how students demonstrate learning)
- Environment differentiation (learning environment setup)
</strategy_types>

<format>
For each strategy, include:
- Specific learner need addressed
- Description of the strategy
- Implementation steps
- Required resources
- Assessment considerations
</format>"""

    @staticmethod
    def generate_cross_curricular_prompt(context: LessonPromptContext) -> str:
        """
        Generate cross-curricular connections for music education.
        """
        return f"""<task>
Create meaningful cross-curricular connections that enhance the music lesson while reinforcing learning in other subject areas.
</task>

<music_context>
<grade>{context.grade_level}</grade>
<strand>{context.strand_name}</strand>
<standard>{context.standard_text}</standard>
</music_context>

<subject_areas>
Connect with:
- Mathematics (patterns, fractions, counting)
- Language Arts (lyrics, poetry, storytelling)
- Social Studies (history, culture, geography)
- Science (sound waves, physics of music)
- Physical Education (movement, dance)
- Visual Arts (composition, color, form)
- Technology (digital music, recording)
</subject_areas>

<connection_requirements>
For each connection:
1. Clear relationship between music and the subject
2. Specific activity or lesson integration
3. Learning objectives for both subject areas
4. Implementation strategies
5. Assessment methods
6. Resources and materials needed
</connection_requirements>

<quality_criteria>
Ensure connections are:
- Authentic and meaningful, not forced
- Age-appropriate for {context.grade_level}
- Enhance musical learning without diluting it
- Support learning in both subject areas
- Engaging and relevant to students
</quality_criteria>"""

    @staticmethod
    def generate_reflection_prompt(context: LessonPromptContext) -> str:
        """
        Generate reflection questions and metacognitive activities.
        """
        objectives_text = "\n".join([f"- {obj}" for obj in context.objectives])
        return f"""<task>
Create thoughtful reflection questions and metacognitive activities to deepen student learning and self-awareness.
</task>

<lesson_context>
<grade>{context.grade_level}</grade>
<standard>{context.standard_text}</standard>
<objectives>{objectives_text}</objectives>
</lesson_context>

<reflection_types>
Develop questions for:
1. Artistic Reflection (musical experiences and growth)
2. Cognitive Reflection (thinking and learning processes)
3. Affective Reflection (feelings and attitudes)
4. Social Reflection (collaboration and community)
5. Metacognitive Reflection (learning about learning)
</reflection_types>

<question_guidelines>
- Age-appropriate language for {context.grade_level}
- Open-ended questions that encourage deep thinking
- Specific connections to the lesson objectives
- Opportunities for both written and verbal responses
- Questions that promote self-assessment and goal-setting
</question_guidelines>

<activity_formats>
Include:
- Individual reflection prompts
- Think-pair-share questions
- Group discussion starters
- Journal writing prompts
- Exit ticket questions
- Portfolio reflection guidelines
</activity_formats>"""

    @staticmethod
    def generate_parent_communication_prompt(context: LessonPromptContext) -> str:
        """
        Generate parent communication templates.
        """
        return f"""<task>
Create effective parent communication materials to support music education at home.
</task>

<lesson_info>
<grade>{context.grade_level}</grade>
<strand>{context.strand_name}</strand>
<standard>{context.standard_text}</standard>
</lesson_info>

<communication_types>
Create:
1. Newsletter article about the current unit
2. At-home practice suggestions
3. Family activity ideas
4. Progress update template
5. Questions parents can ask their child
6. Resources for further exploration
</communication_types>

<guidelines>
- Use accessible, jargon-free language
- Provide specific, actionable suggestions
- Include cultural relevance and diversity
- Offer options for families with varying resources
- Emphasize the value of music education
- Include translation suggestions for ELL families
</guidelines>"""

    @staticmethod
    def generate_technology_integration_prompt(context: LessonPromptContext) -> str:
        """
        Generate technology integration ideas.
        """
        return f"""<task>
Develop meaningful technology integration strategies that enhance musical learning without replacing essential musical experiences.
</task>

<lesson_context>
<grade>{context.grade_level}</grade>
<standard>{context.standard_text}</standard>
<resources>{context.available_resources or []}</resources>
</lesson_context>

<technology_categories>
Consider:
- Digital audio tools (recording, editing, composition)
- Music education apps and software
- Interactive whiteboards and displays
- Online resources and databases
- Video creation and analysis tools
- Presentation and collaboration tools
- Assistive technology for diverse learners
</technology_categories>

<integration_principles>
Ensure technology:
- Enhances rather than replaces musical experiences
- Is age-appropriate and accessible
- Supports the learning objectives
- Provides opportunities for creativity
- Includes proper digital citizenship education
- Has backup plans for technical issues
</integration_principles>

<format>
For each technology integration:
- Tool or resource description
- Learning purpose and objectives
- Implementation steps
- Assessment considerations
- Technical requirements and setup
- Troubleshooting tips
</format>"""

    @staticmethod
    def generate_culturally_responsive_prompt(context: LessonPromptContext) -> str:
        """
        Generate culturally responsive teaching strategies.
        """
        return f"""<task>
Develop culturally responsive teaching strategies that honor diverse musical traditions and student backgrounds.
</task>

<lesson_context>
<grade>{context.grade_level}</grade>
<strand>{context.strand_name}</strand>
<standard>{context.standard_text}</standard>
</lesson_context>

<cultural_responsiveness_elements>
Include:
- Diverse musical examples and traditions
- Student cultural backgrounds and experiences
- Multiple perspectives in musical analysis
- Inclusive language and materials
- Community connections and resources
- Social justice and equity considerations
</cultural_responsiveness_elements>

<strategy_types>
Develop strategies for:
- Curriculum diversification
- Inclusive classroom environment
- Family and community engagement
- Culturally relevant assessment
- Student voice and choice
- Anti-bias education in music
</strategy_types>

<implementation_guidelines>
- Ensure authenticity and respect for all cultures
- Avoid stereotypes and tokenism
- Provide historical and cultural context
- Include student and family input
- Adapt for local community context
- Align with anti-bias education principles
</implementation_guidelines>"""

    @classmethod
    def get_all_templates(cls) -> Dict[str, Callable]:
        """Get all available prompt templates"""
        return {
            "lesson_plan": cls.generate_lesson_plan_prompt,
            "activity_ideas": cls.generate_activity_ideas_prompt,
            "assessment": cls.generate_assessment_prompt,
            "differentiation": cls.generate_differentiation_prompt,
            "cross_curricular": cls.generate_cross_curricular_prompt,
            "reflection": cls.generate_reflection_prompt,
            "parent_communication": cls.generate_parent_communication_prompt,
            "technology_integration": cls.generate_technology_integration_prompt,
            "culturally_responsive": cls.generate_culturally_responsive_prompt,
        }

    @classmethod
    def generate_prompt(cls, template_type: str, context: LessonPromptContext) -> str:
        """
        Generate a specific type of prompt using the template.
        
        Args:
            template_type: Type of prompt template to use
            context: Lesson context for the prompt
            
        Returns:
            Formatted prompt string
        """
        templates = cls.get_all_templates()
        
        if template_type not in templates:
            available = ", ".join(templates.keys())
            raise ValueError(f"Unknown template type: {template_type}. Available: {available}")
        
        return templates[template_type](context)

    @classmethod
    def create_comprehensive_lesson_prompt(cls, context: LessonPromptContext) -> str:
        """
        Create a comprehensive prompt that includes all major lesson components.
        """
        return f"""<task>
Generate a comprehensive, standards-based music lesson plan for {context.grade_level} students that includes all essential components for effective music instruction.
</task>

{cls.generate_lesson_plan_prompt(context)}

<additional_requirements>
In addition to the lesson plan structure, ensure your response includes:
1. Multiple activity options for different learning styles
2. Comprehensive assessment strategies with rubrics
3. Detailed differentiation for all learner types
4. Cross-curricular connections to at least 2 other subjects
5. Technology integration where appropriate
6. Culturally responsive teaching strategies
7. Parent communication suggestions
8. Student reflection questions and activities
</additional_requirements>

<quality_standards>
The lesson plan should demonstrate:
- Deep understanding of music pedagogy
- Alignment with NC music standards
- Age-appropriate content and activities
- Inclusive and culturally responsive approaches
- Practical classroom implementation
- Opportunities for student creativity and expression
- Effective assessment and feedback strategies
</quality_standards>"""