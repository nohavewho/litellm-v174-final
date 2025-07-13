#!/usr/bin/env python3
"""
Gemini Duplicates Filter Patch for LiteLLM v1.70.0
Применяет фикс для фильтрации дублирующих моделей gemini-pro-2.5, gemini-flash-2.5
"""

import os
import sys
import re
from typing import List

def apply_gemini_filter_patch():
    """Применяет патч для фильтрации дублирующих Gemini моделей"""
    
    print("🚀 Starting Gemini filter patch...")
    
    # Проверяем переменную окружения
    if not os.getenv("LITELLM_FILTER_GEMINI_DUPLICATES"):
        print("❌ LITELLM_FILTER_GEMINI_DUPLICATES не установлена, патч не применяется")
        return False
    
    try:
        # Найти путь к установленному LiteLLM в site-packages
        import site
        import litellm
        
        # Получаем путь к установленному пакету
        litellm_path = os.path.dirname(litellm.__file__)
        proxy_server_path = os.path.join(litellm_path, "proxy", "proxy_server.py")
        
        print(f"📂 Найден LiteLLM в: {litellm_path}")
        print(f"📄 Применяю патч к: {proxy_server_path}")
        
        if not os.path.exists(proxy_server_path):
            print(f"❌ Файл не найден: {proxy_server_path}")
            return False
        
        # Читаем файл
        with open(proxy_server_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Функция фильтрации для вставки
        filter_function = '''

def _filter_gemini_duplicates(all_models: List[dict]) -> List[dict]:
    """
    Filter out duplicate Gemini models that have:
    - deployment_id: null
    - db_model: null  
    - Model names: gemini-pro-2.5, gemini-flash-2.5
    
    These are automatically created duplicates that interfere with load balancing.
    """
    models_to_filter = ["gemini-pro-2.5", "gemini-flash-2.5"]
    filtered_models = []
    filtered_count = 0
    
    for model in all_models:
        model_name = model.get("model_name", "")
        deployment_id = model.get("deployment_id")
        db_model = model.get("db_model")
        
        # Filter out problematic duplicate models
        if (model_name in models_to_filter and 
            deployment_id is None and 
            db_model is None):
            filtered_count += 1
            continue
            
        filtered_models.append(model)
    
    if filtered_count > 0:
        verbose_proxy_logger.info(f"Filtered {filtered_count} duplicate Gemini models from /model/info")
    
    return filtered_models
'''
        
        # Проверяем есть ли уже функция
        if '_filter_gemini_duplicates' in content:
            print("⚠️  Функция _filter_gemini_duplicates уже существует, пропускаем добавление")
        else:
            # Ищем место для вставки функции - перед model_info_v1
            # Используем регулярное выражение для поиска
            pattern = r'(@router\.get\(\s*"/model/info".*?\)\s*async def model_info_v1\()'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                # Вставляем функцию перед декоратором
                insert_position = match.start()
                content = content[:insert_position] + filter_function + '\n\n' + content[insert_position:]
                print("✅ Добавлена функция _filter_gemini_duplicates")
            else:
                # Альтернативный поиск
                insert_position = content.find('async def model_info_v1(')
                if insert_position != -1:
                    # Найти начало строки с декоратором
                    line_start = content.rfind('@router.get', 0, insert_position)
                    if line_start != -1:
                        content = content[:line_start] + filter_function + '\n\n' + content[line_start:]
                        print("✅ Добавлена функция _filter_gemini_duplicates (альтернативный метод)")
                    else:
                        print("❌ Не найден декоратор для model_info_v1")
                        return False
                else:
                    print("❌ Не найдена функция model_info_v1")
                    return False
        
        # Добавляем вызов фильтра в model_info_v1
        # Ищем return {"data": all_models} в функции model_info_v1
        
        # Сначала найдем начало функции model_info_v1
        func_start = content.find('async def model_info_v1(')
        if func_start == -1:
            print("❌ Не найдена функция model_info_v1 для добавления вызова")
            return False
        
        # Найдем конец функции (следующую функцию или конец файла)
        next_func = content.find('\nasync def ', func_start + 1)
        next_def = content.find('\ndef ', func_start + 1)
        func_end = min(x for x in [next_func, next_def, len(content)] if x > func_start)
        
        # Извлекаем тело функции
        func_body = content[func_start:func_end]
        
        # Ищем return {"data": all_models} в теле функции
        return_pattern = r'return\s+\{\s*"data"\s*:\s*all_models\s*\}'
        
        if re.search(return_pattern, func_body):
            # Проверяем, не добавлен ли уже вызов
            if 'all_models = _filter_gemini_duplicates(all_models)' not in func_body:
                # Заменяем в исходном content
                new_return = '''# Filter out duplicate Gemini models
    all_models = _filter_gemini_duplicates(all_models)
    
    return {"data": all_models}'''
                
                content = content[:func_start] + re.sub(
                    return_pattern,
                    new_return,
                    content[func_start:func_end]
                ) + content[func_end:]
                
                print("✅ Добавлен вызов _filter_gemini_duplicates в model_info_v1")
            else:
                print("⚠️  Вызов _filter_gemini_duplicates уже добавлен")
        else:
            print("❌ Не найден паттерн return {'data': all_models} в model_info_v1")
            # Попробуем альтернативный поиск
            if 'return {' in func_body and '"data"' in func_body and 'all_models' in func_body:
                print("⚠️  Найден альтернативный return, но не можем безопасно модифицировать")
        
        # Записываем обратно
        with open(proxy_server_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("🎉 Gemini фильтр патч успешно применен!")
        print("✨ Дублирующие модели gemini-pro-2.5 и gemini-flash-2.5 будут отфильтрованы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения патча: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_gemini_filter_patch()
    sys.exit(0 if success else 1) 