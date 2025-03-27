import json
import ollama
from app.schemas import JobResume, JobVacancy, MatchResult

def compare_text_with_ai(job_data: JobResume, job_vacancy: JobVacancy) -> MatchResult:
    job_data_dict = job_data.model_dump()

    job_vacancy_dict = job_vacancy.model_dump()

    prompt = f"""
    Вакансия:
    {json.dumps(job_vacancy_dict, ensure_ascii=False, indent=2)}
    
    Резюме:
    {json.dumps(job_data_dict, ensure_ascii=False, indent=2)}
    
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
