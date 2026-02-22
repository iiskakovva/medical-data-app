import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
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
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Отсутствует обязательное поле: {field}")
    
    if not isinstance(data['patient_id'], str) or not data['patient_id'].strip():
        raise ValidationError("ID пациента должен быть непустой строкой")
    
    if not isinstance(data['patient_name'], str) or not data['patient_name'].strip():
        raise ValidationError("Имя пациента должно быть непустой строкой")
    
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

def export_to_xml(health_data):
    """
    Экспорт данных в XML формат
    """
    root = ET.Element('health_data')
    
    ET.SubElement(root, 'patient_id').text = health_data.patient_id
    ET.SubElement(root, 'patient_name').text = health_data.patient_name
    ET.SubElement(root, 'age').text = str(health_data.age)
    ET.SubElement(root, 'height').text = str(health_data.height)
    ET.SubElement(root, 'weight').text = str(health_data.weight)
    ET.SubElement(root, 'blood_pressure_systolic').text = str(health_data.blood_pressure_systolic)
    ET.SubElement(root, 'blood_pressure_diastolic').text = str(health_data.blood_pressure_diastolic)
    ET.SubElement(root, 'heart_rate').text = str(health_data.heart_rate)
    ET.SubElement(root, 'cholesterol').text = str(health_data.cholesterol)
    ET.SubElement(root, 'bmi').text = str(health_data.bmi)
    ET.SubElement(root, 'bmi_category').text = health_data.get_bmi_category()
    ET.SubElement(root, 'created_at').text = health_data.created_at.isoformat()
    
    rough_string = ET.tostring(root, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

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

def import_from_xml(file_path):
    """
    Импорт данных из XML файла
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        data = {}
        for child in root:
            data[child.tag] = child.text
        
        numeric_fields = ['age', 'height', 'weight', 'blood_pressure_systolic', 
                         'blood_pressure_diastolic', 'heart_rate', 'cholesterol']
        
        for field in numeric_fields:
            if field in data:
                try:
                    if field in ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate']:
                        data[field] = int(data[field])
                    else:
                        data[field] = float(data[field])
                except (ValueError, TypeError):
                    raise ValidationError(f"Некорректное числовое значение для поля {field}")
        
        validate_health_data(data)
        return data
    except ET.ParseError as e:
        raise ValidationError(f"Ошибка парсинга XML: {str(e)}")
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
    name, ext = os.path.splitext(filename)
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name).strip().lower()
    name = name[:100]
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
        if filename.endswith(('.json', '.xml')):
            file_path = os.path.join(upload_dir, filename)
            try:
                files.append({
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'type': 'JSON' if filename.endswith('.json') else 'XML',
                    'modified': os.path.getmtime(file_path)
                })
            except OSError:
                continue
    
    files.sort(key=lambda x: x['modified'], reverse=True)
    return files

def save_health_data_from_dict(data):
    """
    Сохранение данных в базу с проверкой на дубликаты
    """
    if HealthData.objects.filter(patient_id=data['patient_id']).exists():
        raise ValidationError(f"Пациент с ID {data['patient_id']} уже существует в базе данных")
    
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