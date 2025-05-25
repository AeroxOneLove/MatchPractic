import json
import re
from datetime import date
from typing import Optional

import numpy as np
import ollama
from fastapi import HTTPException
from sklearn.metrics.pairwise import cosine_similarity
from stop_words import get_stop_words

from app.config import config

ollama_client = ollama.Client(host=config.OLLAMA_HOST)


class MatchService:
    def __init__(self):
        self.EMBEDDING_SIZE = 1000
        self.SKILL_MATCH_THRESHOLD = 0.8
        self.stop_words = get_stop_words("russian")

    def calculate_experience(self, experiences: list[dict]) -> float:
        """Рассчитывает общий опыт работы в годах"""
        total_days = 0
        for exp in experiences:
            try:
                start = exp["start_date"]
                end = exp["end_date"] if exp["end_date"] else date.today()
                total_days += (end - start).days
            except Exception:
                continue

        return round(total_days / 365, 1)

    def extract_skills_from_text(self, text: str) -> list[str]:
        """Извлечение навыков из текста вакансии"""
        explicit_skills = []
        skill_keywords = ["знание", "владение", "опыт работы с", "умение работать с", "навыки работы с"]

        for keyword in skill_keywords:
            matches = re.finditer(rf"{keyword}\s+([\w\s/]+)", text, re.IGNORECASE)
            for match in matches:
                skills = match.group(1).split("/")
                explicit_skills.extend([s.strip() for s in skills if s.strip()])

        if explicit_skills:
            return list(set(explicit_skills))

        PROMPT = """Извлеки ТОЛЬКО технические навыки из текста вакансии на русском языке.
    Текст: {text}
    Верни ОДИН JSON-объект строго в формате: {{"skills": ["навык1", "навык2"]}}
    Не добавляй никаких комментариев!"""

        try:
            response = ollama_client.chat(
                model="llama3.2:3b", messages=[{"role": "user", "content": PROMPT.format(text=text)}]
            )
            content = response["message"]["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            result = json.loads(json_str)
            return result.get("skills", [])
        except Exception as e:
            print(f"Ошибка при извлечении навыков: {e}")
            return []

    def extract_experience_from_text(self, text: str) -> int:
        """Извлекает требуемый опыт работы из текста"""
        patterns = [
            r"опыт\s*(?:работы)?\s*(?:от)?\s*(\d+)\s*(\+)?\s*(?:года|лет|год)",
            r"(\d+)\s*[-+]\s*(?:года|лет|год)",
            r"не\s*менее\s*(\d+)\s*(?:года|лет|год)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        PROMPT = """Определи требуемый опыт работы из текста на русском. Ответь только числом:
    Текст: {text}
    Примеры ответов: 3, 5, 0 (если опыт не указан)"""

        try:
            response = ollama_client.chat(
                model="llama3.2:3b", messages=[{"role": "user", "content": PROMPT.format(text=text)}]
            )
            return int(response["message"]["content"].strip())
        except Exception:
            return 0

    def preprocess_text(self, text: str) -> str:
        """Предобработка текста для эмбеддингов"""
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        text = " ".join(word for word in text.split() if word not in self.stop_words)
        return text

    def get_embedding_ollama(self, text: str) -> np.ndarray:
        """Получение эмбеддинга через Ollama"""
        try:
            response = ollama_client.embed(model="nomic-embed-text", input=text)
            if hasattr(response, "embeddings") and len(response.embeddings) > 0:
                return np.array(response.embeddings[0])
            return np.zeros(self.EMBEDDING_SIZE)
        except Exception:
            return np.zeros(self.EMBEDDING_SIZE)

    def extract_years_from_skill(self, skill: str) -> Optional[int]:
        """Извлекает количество лет из описания навыка"""
        match = re.search(r"(\d+)\s*год[ау]?", skill.lower())
        return int(match.group(1)) if match else None

    def analyze_data(self, data: dict) -> dict:
        """Анализирует резюме или вакансию"""
        result = {"position": "", "key_skills": [], "work_experience": 0}

        if not data:
            return result

        try:
            if "resume" in data:
                resume = data["resume"]
                result["position"] = resume.get("position", "")
                result["key_skills"] = resume.get("skills", [])
                result["work_experience"] = self.calculate_experience(resume.get("experiences", []))
            elif "job" in data:
                job = data["job"]
                result["position"] = job.get("title", "")
                result["key_skills"] = self.extract_skills_from_text(job.get("requirements", ""))
                result["work_experience"] = self.extract_experience_from_text(job.get("requirements", ""))
        except Exception as e:
            print(f"Ошибка при анализе данных: {e}")

        return result

    def compare_skills(self, resume_skills: list[str], job_skills: list[str]) -> dict:
        """Сравнивает навыки с учетом порога сходства"""
        result = {"missing_skills": [], "matched_skills": 0, "total_skills": len(job_skills)}

        skill_embeddings = {
            skill: self.get_embedding_ollama(self.preprocess_text(skill)) for skill in set(resume_skills + job_skills)
        }

        for job_skill in job_skills:
            job_skill_lower = job_skill.lower()
            years_required = self.extract_years_from_skill(job_skill_lower)

            if years_required:
                base_skill = re.sub(r"от\s*\d+\s*год[ау]?", "", job_skill_lower).strip()
                found = False
                for resume_skill in resume_skills:
                    resume_skill_lower = resume_skill.lower()
                    if base_skill in resume_skill_lower:
                        resume_years = self.extract_years_from_skill(resume_skill_lower) or 0
                        if resume_years >= years_required:
                            result["matched_skills"] += 1
                            found = True
                            break
                if not found:
                    result["missing_skills"].append(job_skill)
                continue

            max_similarity = 0.0
            for resume_skill in resume_skills:
                similarity = cosine_similarity([skill_embeddings[job_skill]], [skill_embeddings[resume_skill]])[0][0]
                if similarity > max_similarity:
                    max_similarity = similarity

            if max_similarity >= self.SKILL_MATCH_THRESHOLD:
                result["matched_skills"] += 1
            else:
                job_parts = re.split(r"\s+и\s+|\s*,\s*", job_skill_lower)
                matched_parts = 0
                for part in job_parts:
                    for resume_skill in resume_skills:
                        if part in resume_skill.lower():
                            matched_parts += 1
                            break
                if matched_parts / len(job_parts) >= 0.5:
                    result["matched_skills"] += 0.5
                else:
                    result["missing_skills"].append(job_skill)

        return result

    def compare_position(self, resume_pos: str, job_pos: str) -> bool:
        """Сравнивает позиции через эмбеддинги, возвращает True, если similarity > порог"""
        resume_emb = self.get_embedding_ollama(self.preprocess_text(resume_pos))
        job_emb = self.get_embedding_ollama(self.preprocess_text(job_pos))

        if np.any(resume_emb) and np.any(job_emb):
            similarity = cosine_similarity([resume_emb], [job_emb])[0][0]
            return similarity >= 0.5
        else:
            resume_words = set(self.preprocess_text(resume_pos).split())
            job_words = set(self.preprocess_text(job_pos).split())
            common_words = resume_words & job_words
            return len(common_words) >= 1

    def compare_experience(self, resume_exp: float, job_exp: float) -> bool:
        """Сравнение опыта работы"""
        return resume_exp >= job_exp * 0.8

    def calculate_match(self, resume: dict, job: dict) -> dict:
        """Сравнивает резюме и вакансию"""
        result = {"match": 0, "didnt_match": []}

        position_match = self.compare_position(resume["position"], job["position"])
        if not position_match:
            result["didnt_match"].append(
                f"Позиция '{resume['position']}' может не полностью соответствовать '{job['position']}'"
            )
        position_score = 20 if position_match else 10

        experience_match = self.compare_experience(resume["work_experience"], job["work_experience"])
        if not experience_match:
            exp_diff = job["work_experience"] - resume["work_experience"]
            result["didnt_match"].append(
                f"Опыт работы: {resume['work_experience']} лет (требуется {job['work_experience']}+,\
не хватает {exp_diff:.1f} лет)"
            )
        experience_score = (
            20
            if experience_match
            else max(0, 20 * (1 - (job["work_experience"] - resume["work_experience"]) / job["work_experience"]))
        )

        # Проверка навыков (50%)
        skills_result = self.compare_skills(resume["key_skills"], job["key_skills"])
        if skills_result["missing_skills"]:
            result["didnt_match"].append(f"Не хватает навыков: {', '.join(skills_result['missing_skills'])}")
        skills_score = (
            50 * (skills_result["matched_skills"] / skills_result["total_skills"])
            if skills_result["total_skills"] > 0
            else 0
        )

        # Общий счет
        total_score = position_score + experience_score + skills_score

        # Корректировка с учетом эмбеддингов
        resume_text = f"{resume['position']} {' '.join(resume['key_skills'])} {resume['work_experience']}"
        job_text = f"{job['position']} {' '.join(job['key_skills'])} {job['work_experience']}"
        resume_embedding = self.get_embedding_ollama(self.preprocess_text(resume_text))
        job_embedding = self.get_embedding_ollama(self.preprocess_text(job_text))

        if np.any(resume_embedding) and np.any(job_embedding):
            embedding_similarity = cosine_similarity([resume_embedding], [job_embedding])[0][0]
            total_score = (total_score * 0.7) + (embedding_similarity * 100 * 0.3)

        result["match"] = min(100, int(round(total_score)))
        return result

    async def compare_resume_vacancy(self, resume_data: dict, vacancy_data: dict) -> dict:
        """Сравнивает резюме и вакансию"""
        try:
            resume_analyzed = self.analyze_data({"resume": resume_data})
            job_analyzed = self.analyze_data({"job": vacancy_data})
            return self.calculate_match(resume_analyzed, job_analyzed)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing comparison: {str(e)}")
