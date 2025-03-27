import json
import ollama
from app.schemas import JobResume, JobVacancy, MatchResult

PROMPT_TEMPLATE = """ 
Вакансия:
{job_vacancy}

Резюме:
{job_data}

Представь, что ты ищешь сотрудника для этой вакансии. Важные параметры для сравнения указаны в вакансии. 
Сравни вакансию с резюме и дай мне ответ в формате JSON:

{{
    "match_percentage": int,
    "matched": list[str],
    "didnt_match": list[str]
}}

Важно: если в вакансии не упоминаются параметры, которые есть в резюме, их не учитывай.

Ответ строго в JSON без лишнего текста.
"""

def compare_text_with_ai(job_data: JobResume, job_vacancy: JobVacancy) -> MatchResult:
    job_data_dict = json.dumps(job_data.model_dump(), ensure_ascii=False, indent=2)
    job_vacancy_dict = json.dumps(job_vacancy.model_dump(), ensure_ascii=False, indent=2)

    prompt = PROMPT_TEMPLATE.format(job_data=job_data_dict, job_vacancy=job_vacancy_dict)

    response = ollama.chat(model="mistral:latest", messages=[{"role": "user", "content": prompt}])

    match_results_store: list[MatchResult] = []

    try:
        result = json.loads(response['message']['content'])

        match_result = MatchResult(
            match_percentage=result["match_percentage"],
            matched=result["matched"],
            didnt_match=result["didnt_match"]
        )

        match_results_store.append(match_result)

        return match_result
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Ошибка обработки AI-ответа: {e}")
