import json
import os
import re
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import HealthData

def validate_health_data(data):
    """
    Валидация медицинских данных
    """
    required_fields = [
        'patient_id', 'patient_name', 'age', 'height', 'weight',
        'blood_pressure_systolic', 'blood_pressure_diastolic', 
        'heart_rate', 'cholesterol'
    ]
    
    # Проверка наличия всех обязательных полей
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Отсутствует обязательное поле: {field}")
    
    # Проверка типов данных
    if not isinstance(data['patient_id'], str) or not data['patient_id'].strip():
        raise ValidationError("ID пациента должен быть непустой строкой")
    
    if not isinstance(data['patient_name'], str) or not data['patient_name'].strip():
        raise ValidationError("Имя пациента должно быть непустой строкой")
    
    # Проверка числовых значений
    try:
        age = int(data['age'])
        if age < 0 or age > 150:
            raise ValidationError("Возраст должен быть между 0 и 150")
    except (ValueError, TypeError):
        raise ValidationError("Возраст должен быть целым числом")
    
    try:
        height = float(data['height'])
        if height <= 0:
            raise ValidationError("Рост должен быть положительным числом")
    except (ValueError, TypeError):
        raise ValidationError("Рост должен быть числом")
    
    try:
        weight = float(data['weight'])
        if weight <= 0:
            raise ValidationError("Вес должен быть положительным числом")
    except (ValueError, TypeError):
        raise ValidationError("Вес должен быть числом")

def export_to_json(health_data):
    """
    Экспорт данных в JSON формат
    """
    data = {
        'patient_id': health_data.patient_id,
        'patient_name': health_data.patient_name,
        'age': health_data.age,
        'height': health_data.height,
        'weight': health_data.weight,
        'blood_pressure_systolic': health_data.blood_pressure_systolic,
        'blood_pressure_diastolic': health_data.blood_pressure_diastolic,
        'heart_rate': health_data.heart_rate,
        'cholesterol': health_data.cholesterol,
        'bmi': health_data.bmi,
        'bmi_category': health_data.get_bmi_category(),
        'created_at': health_data.created_at.isoformat()
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

def import_from_json(file_path):
    """
    Импорт данных из JSON файла
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        validate_health_data(data)
        return data
    except json.JSONDecodeError as e:
        raise ValidationError(f"Ошибка декодирования JSON: {str(e)}")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Ошибка чтения файла: {str(e)}")

def get_upload_directory():
    """
    Получить директорию для загрузки файлов
    """
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'health_data')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def sanitize_filename(filename):
    """
    Санитайзинг имени файла
    """
    # Разделяем имя и расширение
    name, ext = os.path.splitext(filename)
    
    # Удаляем небезопасные символы
    name = re.sub(r'[^\w\s-]', '', name)
    
    # Заменяем пробелы и множественные дефисы
    name = re.sub(r'[-\s]+', '-', name).strip().lower()
    
    # Ограничиваем длину имени
    name = name[:100]
    
    # Добавляем UUID для уникальности
    unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    
    return unique_name

def get_uploaded_files():
    """
    Получить список загруженных файлов
    """
    upload_dir = get_upload_directory()
    
    if not os.path.exists(upload_dir):
        return []
    
    files = []
    for filename in os.listdir(upload_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(upload_dir, filename)
            try:
                files.append({
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'type': 'JSON',
                    'modified': os.path.getmtime(file_path)
                })
            except OSError:
                continue
    
    # Сортируем по дате изменения (новые сначала)
    files.sort(key=lambda x: x['modified'], reverse=True)
    return files

def save_health_data_from_dict(data):
    """
    Сохранение данных в базу
    """
    health_data = HealthData(
        patient_id=data['patient_id'],
        patient_name=data['patient_name'],
        age=data['age'],
        height=data['height'],
        weight=data['weight'],
        blood_pressure_systolic=data['blood_pressure_systolic'],
        blood_pressure_diastolic=data['blood_pressure_diastolic'],
        heart_rate=data['heart_rate'],
        cholesterol=data['cholesterol']
    )
    
    health_data.full_clean()
    health_data.save()
    
    return health_data