import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class SummarizationService:
    def __init__(self):
        self.model_path = "lfs/summarization_model"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path).to(self.device)
        self.max_input_length = 512

    def generate_summary(self, text: str) -> str:
        self.model.eval()
        inputs = self.tokenizer.encode(text, return_tensors="pt", max_length=self.max_input_length, truncation=True).to(
            self.device
        )
        outputs = self.model.generate(
            inputs,
            max_length=120,  # короче итоговый текст
            min_length=50,  # минимальная длина
            num_beams=5,
            early_stopping=True,
            no_repeat_ngram_size=3,
            length_penalty=1.2,
            repetition_penalty=2.0,
        )
        summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)

        # Обрезаем текст по последней точке, чтобы не было обрывов
        last_period_pos = summary.rfind(".")
        if last_period_pos != -1:
            summary = summary[: last_period_pos + 1]

        return summary.strip()
