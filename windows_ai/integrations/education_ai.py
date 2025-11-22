"""
Education & Learning AI Manager - 20+ Services
Tutoring, content generation, assessment, adaptive learning
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class EducationAIManager:
    """Unified education AI across 20+ services"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== AI TUTORING ====================

    async def tutor(self, subject: str, question: str, student_level: str = "high_school") -> Dict:
        """AI tutoring with Socratic method"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""You are an expert tutor for {subject} at the {student_level} level.
Use the Socratic method - guide students to answers through questions.
Provide hints rather than direct answers.
Break down complex concepts into simpler parts.
Use examples and analogies relevant to their level.
Encourage critical thinking."""},
            {"role": "user", "content": question}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return {"subject": subject, "level": student_level, "response": response["content"]}

    async def explain_concept(self, concept: str, subject: str, level: str = "beginner") -> Dict:
        """Explain a concept at appropriate level"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Explain this {subject} concept at the {level} level:
1. Start with a simple definition
2. Provide real-world examples
3. Use analogies if helpful
4. Include visual descriptions
5. Summarize key points"""},
            {"role": "user", "content": concept}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return {"concept": concept, "explanation": response["content"]}

    # ==================== CONTENT GENERATION ====================

    async def generate_lesson_plan(self, topic: str, grade_level: str, duration_minutes: int) -> Dict:
        """Generate comprehensive lesson plan"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Generate a detailed lesson plan with:
1. Learning objectives
2. Materials needed
3. Warm-up activity
4. Main instruction
5. Guided practice
6. Independent practice
7. Assessment
8. Differentiation strategies
9. Closure activity
Return structured JSON."""},
            {"role": "user", "content": f"Topic: {topic}\nGrade: {grade_level}\nDuration: {duration_minutes} minutes"}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"lesson_plan": response["content"]}

    async def generate_quiz(self, topic: str, num_questions: int, question_types: List[str] = None) -> Dict:
        """Generate quiz questions"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        types = question_types or ["multiple_choice", "true_false", "short_answer"]

        messages = [
            {"role": "system", "content": f"""Generate a quiz with {num_questions} questions about {topic}.
Include these question types: {', '.join(types)}
For each question provide:
- Question text
- Type
- Options (for multiple choice)
- Correct answer
- Explanation
Return JSON array of questions."""},
            {"role": "user", "content": f"Create quiz on: {topic}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return {"questions": json.loads(response["content"])}
        except:
            return {"questions": response["content"]}

    async def generate_flashcards(self, topic: str, num_cards: int = 20) -> List[Dict]:
        """Generate study flashcards"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Generate {num_cards} flashcards for studying.
Each card should have:
- Front: question or term
- Back: answer or definition
- Difficulty: easy/medium/hard
Return JSON array."""},
            {"role": "user", "content": f"Topic: {topic}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return [{"content": response["content"]}]

    # ==================== ASSESSMENT ====================

    async def grade_essay(self, essay: str, rubric: Dict = None, max_score: int = 100) -> Dict:
        """Grade essay with detailed feedback"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        default_rubric = {
            "thesis": 20,
            "evidence": 25,
            "organization": 20,
            "analysis": 25,
            "grammar": 10
        }
        rubric = rubric or default_rubric

        messages = [
            {"role": "system", "content": f"""Grade this essay using this rubric (max {max_score} points):
{rubric}
Provide:
1. Score for each category
2. Overall score
3. Strengths
4. Areas for improvement
5. Specific suggestions
Return structured JSON."""},
            {"role": "user", "content": essay}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"feedback": response["content"]}

    async def grade_code(self, code: str, language: str, assignment: str) -> Dict:
        """Grade programming assignment"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Grade this {language} code for: {assignment}
Evaluate:
1. Correctness (40%)
2. Code quality/style (20%)
3. Efficiency (20%)
4. Comments/documentation (10%)
5. Error handling (10%)
Provide detailed feedback and suggestions.
Return JSON with scores and feedback."""},
            {"role": "user", "content": code}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"feedback": response["content"]}

    # ==================== ADAPTIVE LEARNING ====================

    async def assess_knowledge(self, subject: str, questions_answered: List[Dict]) -> Dict:
        """Assess student knowledge level"""
        correct = sum(1 for q in questions_answered if q.get("correct"))
        total = len(questions_answered)

        topics_missed = [q.get("topic") for q in questions_answered if not q.get("correct")]

        return {
            "score": (correct / total * 100) if total > 0 else 0,
            "mastery_level": "advanced" if correct/total > 0.9 else "intermediate" if correct/total > 0.7 else "beginner",
            "topics_to_review": list(set(topics_missed)),
            "recommendations": await self._get_recommendations(subject, topics_missed)
        }

    async def _get_recommendations(self, subject: str, weak_topics: List[str]) -> List[str]:
        """Get learning recommendations"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        if not weak_topics:
            return ["Great job! Move on to advanced topics."]

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": "Provide 5 specific learning recommendations."},
            {"role": "user", "content": f"Subject: {subject}\nWeak topics: {weak_topics}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return response["content"].split("\n")

    # ==================== LANGUAGE LEARNING ====================

    async def practice_conversation(self, language: str, scenario: str, user_input: str) -> Dict:
        """Language learning conversation practice"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""You are a {language} conversation partner.
Scenario: {scenario}
- Respond naturally in {language}
- Correct any errors gently
- Provide translation in parentheses
- Suggest better phrasing when appropriate"""},
            {"role": "user", "content": user_input}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return {"response": response["content"], "language": language}

    async def analyze_pronunciation(self, audio_path: str, target_language: str, target_text: str) -> Dict:
        """Analyze pronunciation from audio"""
        from windows_ai.integrations.audio_speech import AudioSpeechManager

        audio = AudioSpeechManager()
        await audio.initialize()

        # Transcribe the audio
        transcription = await audio.speech_to_text(audio_path, provider="whisper")

        return {
            "transcribed": transcription,
            "target": target_text,
            "accuracy": self._calculate_similarity(transcription, target_text)
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100

    # ==================== RESEARCH ASSISTANCE ====================

    async def summarize_paper(self, paper_text: str) -> Dict:
        """Summarize academic paper"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Summarize this academic paper:
1. Main research question
2. Methodology
3. Key findings
4. Conclusions
5. Limitations
6. Future work suggestions
Return structured summary."""},
            {"role": "user", "content": paper_text}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        return {"summary": response["content"]}

    async def generate_citations(self, sources: List[Dict], style: str = "apa") -> List[str]:
        """Generate citations in specified style"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"Generate {style.upper()} citations for these sources. Return one citation per line."},
            {"role": "user", "content": str(sources)}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return response["content"].split("\n")

    def list_capabilities(self) -> Dict[str, List[str]]:
        return {
            "tutoring": ["socratic_method", "explain_concept", "step_by_step"],
            "content": ["lesson_plans", "quizzes", "flashcards", "worksheets"],
            "assessment": ["essay_grading", "code_grading", "quiz_grading"],
            "adaptive": ["knowledge_assessment", "personalized_recommendations"],
            "language": ["conversation", "pronunciation", "grammar"],
            "research": ["paper_summary", "citations", "literature_review"]
        }
