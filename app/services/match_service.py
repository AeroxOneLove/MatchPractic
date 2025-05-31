import re
import ollama
import numpy as np
from datetime import datetime, date
from sklearn.metrics.pairwise import cosine_similarity
from stop_words import get_stop_words
from typing import Dict, List, Optional
from fastapi import HTTPException
import spacy

from app.config import config

ollama_client = ollama.Client(host=config.OLLAMA_HOST)

try:
    MODEL_PATH = "lfs/model_skills"
    import os

    if not os.path.exists(MODEL_PATH):
        print(f"Директория модели {MODEL_PATH} не существует")
    else:
        print(f"Директория модели {MODEL_PATH} найдена, содержимое: {os.listdir(MODEL_PATH)}")
    nlp = spacy.load(MODEL_PATH)
    print(f"Модель успешно загружена из {MODEL_PATH}")
except Exception as e:
    print(f"Ошибка загрузки модели: {e}")
    import traceback

    traceback.print_exc()
    nlp = None


class MatchService:
    def __init__(self):
        self.EMBEDDING_SIZE = 1000
        self.SKILL_MATCH_THRESHOLD = 0.8
        self.stop_words = get_stop_words("russian")

    def calculate_experience(self, experiences: List[Dict]) -> float:
        total_days = 0
        for exp in experiences:
            try:
                start_date = exp.get("start_date")
                if isinstance(start_date, str):
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                elif isinstance(start_date, date):
                    start = datetime.combine(start_date, datetime.min.time())
                else:
                    continue

                end_date = exp.get("end_date")
                if end_date:
                    if isinstance(end_date, str):
                        end = datetime.strptime(end_date, "%Y-%m-%d")
                    elif isinstance(end_date, date):
                        end = datetime.combine(end_date, datetime.min.time())
                    else:
                        continue
                else:
                    end = datetime.now()

                if start > end:
                    continue

                days = (end - start).days
                total_days += days
            except Exception:
                continue
        years = round(total_days / 365, 1)
        return years

    def extract_skills_from_text(self, text: str) -> List[str]:
        """
        Извлекает технические навыки из текста с использованием модели spacy.
        Если модель не загружена, возвращает пустой список.
        """
        if nlp is None:
            print("Модель spacy не загружена! Навыки не могут быть извлечены.")
            return []

        try:
            doc = nlp(text)
            skills = [ent.text.strip() for ent in doc.ents if ent.label_ == "SKILL"]
            return list(set(skills))  # Удаляем дубликаты
        except Exception as e:
            print(f"Ошибка при извлечении навыков с помощью spacy: {e}")
            return []

    def extract_experience_from_text(self, text: str) -> int:
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
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        text = " ".join(word for word in text.split() if word not in self.stop_words)
        return text

    def get_embedding_ollama(self, text: str) -> np.ndarray:
        try:
            response = ollama_client.embed(model="nomic-embed-text", input=text)
            if hasattr(response, "embeddings") and len(response.embeddings) > 0:
                return np.array(response.embeddings[0])
            return np.zeros(self.EMBEDDING_SIZE)
        except Exception:
            return np.zeros(self.EMBEDDING_SIZE)

    def extract_years_from_skill(self, skill: str) -> Optional[int]:
        match = re.search(r"(\d+)\s*год[ау]?", skill.lower())
        return int(match.group(1)) if match else None

    def analyze_data(self, data: Dict) -> Dict:
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

    def compare_skills(self, resume_skills: List[str], job_skills: List[str]) -> Dict:
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
        resume_words = set(self.preprocess_text(resume_pos).split())
        job_words = set(self.preprocess_text(job_pos).split())
        common_words = resume_words & job_words
        return len(common_words) >= max(1, min(len(resume_words), len(job_words)) / 2)

    def compare_experience(self, resume_exp: float, job_exp: float) -> bool:
        return resume_exp >= job_exp * 0.8

    def calculate_match(self, resume: Dict, job: Dict) -> Dict:
        result = {"match": 0, "didnt_match": []}

        position_match = self.compare_position(resume["position"], job["position"])
        if not position_match:
            result["didnt_match"].append(f"Позиция: '{resume['position']}' не соответствует '{job['position']}'")
        position_score = 30 if position_match else 0

        experience_match = self.compare_experience(resume["work_experience"], job["work_experience"])
        if not experience_match:
            exp_diff = job["work_experience"] - resume["work_experience"]
            result["didnt_match"].append(
                f"Опыт работы: {resume['work_experience']} лет (требуется {job['work_experience']}+,\
не хватает {exp_diff:.1f} лет)"
            )

        if job["work_experience"] == 0 or experience_match:
            experience_score = 20  # Полный балл, если опыт достаточен или не требуется
        elif exp_diff < 1.0:
            experience_score = 10  # Нехватка менее 1 года
        elif exp_diff <= 2.0:
            experience_score = 5  # Нехватка от 1 до 2 лет
        else:
            experience_score = 0  # Нехватка более 2 лет

        skills_result = self.compare_skills(resume["key_skills"], job["key_skills"])
        if skills_result["missing_skills"]:
            result["didnt_match"].append(f"Не хватает навыков: {', '.join(skills_result['missing_skills'])}")
        skills_score = (
            50 * (skills_result["matched_skills"] / skills_result["total_skills"])
            if skills_result["total_skills"] > 0
            else 0
        )

        total_score = position_score + experience_score + skills_score

        result["match"] = min(100, int(round(total_score)))
        return result

    async def compare_resume_vacancy(self, resume_data: Dict, vacancy_data: Dict) -> Dict:
        try:
            resume_analyzed = self.analyze_data({"resume": resume_data})
            job_analyzed = self.analyze_data({"job": vacancy_data})
            return self.calculate_match(resume_analyzed, job_analyzed)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing comparison: {str(e)}")
