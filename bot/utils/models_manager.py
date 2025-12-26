from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import re
from utils.utils import models_map
from config import config


class ChatBotModel:
    def __init__(self, models_dir=None):
        self.models_dir = models_dir or config.models_dir
        self.tokenizer = None
        self.model = None
        self.current_model_name = None
        self._init_tokenizer()
    
    def _init_tokenizer(self):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                "ai-forever/rugpt3small_based_on_gpt2"
            )
            # Устанавливаем pad token как eos token, если его нет
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
        except Exception as e:
            print(f"Ошибка при загрузке токенизатора: {e}")
            raise
    
    def load_model(self, name=config.default_model):
        try:
            if name not in models_map:
                print(f"Модель '{name}' не найдена в models_map")
                return False
            
            model_filename = os.path.basename(models_map[name])
            model_path = os.path.join(self.models_dir, model_filename)
            
            if not os.path.exists(model_path):
                print(f"Файл модели не найден: {model_path}")
                return False
            
            # Загружаем модель
            self.model = torch.load(model_path, 
                                  map_location=torch.device('cpu'), 
                                  weights_only=False)
            self.model.eval()  # Переводим в режим оценки
            self.current_model_name = name
            
            print(f"Модель '{name}' успешно загружена")
            return True
            
        except Exception as e:
            print(f"Ошибка при загрузке модели: {e}")
            self.model = None
            self.current_model_name = None
            return False
    
    def generate_response(self, history, max_length=1000, temperature=0.9, 
                         top_k=50, top_p=0.95, no_repeat_ngram_size=2,
                         repetition_penalty=1.1, min_length=10):
        if self.model is None:
            return "Модель не загружена. Пожалуйста, загрузите модель с помощью load_model()."
        
        try:
            prompt = f"Контекст 1: {history[0].strip()}\nКонтекст 2: {history[1].strip()}\nАссистент:"

            tokenized = self.tokenizer(
                prompt, 
                return_tensors="pt",
                truncation=True,
                padding=True
            )
            
            # Генерация ответа
            with torch.no_grad():
                output = self.model.generate(
                    input_ids=tokenized.input_ids,
                    attention_mask=tokenized.attention_mask,
                    num_return_sequences=1,
                    max_length=max_length,
                    min_length=min_length,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    no_repeat_ngram_size=no_repeat_ngram_size,
                    do_sample=True,
                    early_stopping=True,
                )
            
            # Декодирование ответа
            response = self.tokenizer.decode(
                output[0], 
                skip_special_tokens=True
            )
            
            # Очистка ответа
            # response = self._clean_response(response, text)
            response = self._extract_assistant_response(response, prompt)
            
            return response.strip()
            
        except Exception as e:
            print(f"Ошибка при генерации ответа: {e}")
            return ""
    
    def _extract_assistant_response(self, full_response, prompt):
        """Извлекает только ответ ассистента из полного текста"""
        # Удаляем промпт из начала
        if full_response.startswith(prompt):
            response = full_response[len(prompt):]
        else:
            response = full_response
        
        # Удаляем лишние пробелы и переносы строк
        response = response.strip()

        print(f"SEND_MSG: {response}")

        
        # Удаляем все специальные токены
        response = re.sub(r'<\|.*?\|>', '', response)
        
        return response

    def _clean_response(self, response, original_text=""):
        if original_text and response.startswith(original_text):
            response = response[len(original_text):]
        return response
    
    def unload_model(self):
        """Выгрузка модели из памяти"""
        self.model = None
        self.current_model_name = None
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        print("Модель выгружена из памяти")

    def get_model_info(self):
        return self.current_model_name
    


chatbot_model = ChatBotModel()
