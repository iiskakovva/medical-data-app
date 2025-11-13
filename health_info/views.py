from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import re

from .models import HealthData

# Простые утилиты прямо в views.py (временно)
def validate_health_data(data):
    required_fields = ['patient_id', 'patient_name', 'age', 'height', 'weight', 
                      'blood_pressure_systolic', 'blood_pressure_diastolic', 
                      'heart_rate', 'cholesterol']
    
    for field in required_fields:
        if field not in data:
            raise Exception(f"Отсутствует поле: {field}")

def export_to_json(health_data):
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
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

def export_to_xml(health_data):
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
    
    rough_string = ET.tostring(root, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def get_upload_directory():
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'health_data')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def sanitize_filename(filename):
    name, ext = os.path.splitext(filename)
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name).strip().lower()
    return f"{name}_{uuid.uuid4().hex[:8]}{ext}"

def home(request):
    context = {
        'total_patients': HealthData.objects.count(),
        'total_files': len(os.listdir(get_upload_directory())) if os.path.exists(get_upload_directory()) else 0
    }
    return render(request, 'health_info/home.html', context)

def input_data(request):
    if request.method == 'POST':
        try:
            # Создаем объект HealthData из POST данных
            health_data = HealthData(
                patient_id=request.POST.get('patient_id'),
                patient_name=request.POST.get('patient_name'),
                age=int(request.POST.get('age', 0)),
                height=float(request.POST.get('height', 0)),
                weight=float(request.POST.get('weight', 0)),
                blood_pressure_systolic=int(request.POST.get('blood_pressure_systolic', 0)),
                blood_pressure_diastolic=int(request.POST.get('blood_pressure_diastolic', 0)),
                heart_rate=int(request.POST.get('heart_rate', 0)),
                cholesterol=float(request.POST.get('cholesterol', 0)),
            )
            
            # Сохраняем в базу
            health_data.save()
            
            # Экспортируем в файл
            file_type = request.POST.get('file_type', 'json')
            upload_dir = get_upload_directory()
            
            if file_type == 'json':
                content = export_to_json(health_data)
                filename = f"health_data_{health_data.patient_id}.json"
            else:
                content = export_to_xml(health_data)
                filename = f"health_data_{health_data.patient_id}.xml"
            
            safe_filename = sanitize_filename(filename)
            file_path = os.path.join(upload_dir, safe_filename)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            messages.success(request, f'Данные сохранены и экспортированы в {file_type.upper()}!')
            return redirect('health_info:files')
            
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    return render(request, 'health_info/input_data.html')

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_type = request.POST.get('file_type', 'json')
        
        try:
            # Сохраняем файл
            safe_filename = sanitize_filename(uploaded_file.name)
            upload_dir = get_upload_directory()
            file_path = os.path.join(upload_dir, safe_filename)
            
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Читаем и парсим файл
            if file_type == 'json':
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
            else:
                tree = ET.parse(file_path)
                root = tree.getroot()
                data = {}
                for child in root:
                    data[child.tag] = child.text
                
                # Конвертируем числа
                numeric_fields = ['age', 'height', 'weight', 'blood_pressure_systolic', 
                                'blood_pressure_diastolic', 'heart_rate', 'cholesterol']
                for field in numeric_fields:
                    if field in data:
                        if field in ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate']:
                            data[field] = int(data[field])
                        else:
                            data[field] = float(data[field])
            
            validate_health_data(data)
            
            # Сохраняем в базу
            health_data = HealthData(
                patient_id=data['patient_id'],
                patient_name=data['patient_name'],
                age=data['age'],
                height=data['height'],
                weight=data['weight'],
                blood_pressure_systolic=data['blood_pressure_systolic'],
                blood_pressure_diastolic=data['blood_pressure_diastolic'],
                heart_rate=data['heart_rate'],
                cholesterol=data['cholesterol'],
            )
            health_data.save()
            
            messages.success(request, 'Файл успешно загружен и данные импортированы!')
            return redirect('health_info:files')
            
        except Exception as e:
            # Удаляем невалидный файл
            if os.path.exists(file_path):
                os.remove(file_path)
            messages.error(request, f'Ошибка: {str(e)}')
    
    return render(request, 'health_info/upload_file.html')

def file_list(request):
    upload_dir = get_upload_directory()
    files = []
    
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            if filename.endswith(('.json', '.xml')):
                file_path = os.path.join(upload_dir, filename)
                try:
                    file_info = {
                        'name': filename,
                        'type': 'JSON' if filename.endswith('.json') else 'XML',
                        'size': os.path.getsize(file_path),
                    }
                    
                    # Читаем содержимое файла
                    if filename.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = json.load(file)
                    else:
                        tree = ET.parse(file_path)
                        root = tree.getroot()
                        content = {}
                        for child in root:
                            content[child.tag] = child.text
                    
                    files.append({
                        'file_info': file_info,
                        'content': content
                    })
                except Exception as e:
                    files.append({
                        'file_info': file_info,
                        'error': str(e)
                    })
    
    context = {
        'file_contents': files,
        'files_exist': len(files) > 0,
        'total_files': len(files)
    }
    return render(request, 'health_info/file_list.html', context)

def analyze_data(request):
    all_data = HealthData.objects.all()
    
    if not all_data.exists():
        messages.info(request, 'Нет данных для анализа.')
        return redirect('health_info:home')
    
    # Статистика
    total_patients = all_data.count()
    avg_age = sum([data.age for data in all_data]) / total_patients
    avg_bmi = sum([data.bmi for data in all_data]) / total_patients
    avg_heart_rate = sum([data.heart_rate for data in all_data]) / total_patients
    
    # Категории ИМТ
    bmi_categories = {
        'underweight': all_data.filter(bmi__lt=18.5).count(),
        'normal': all_data.filter(bmi__gte=18.5, bmi__lt=25).count(),
        'overweight': all_data.filter(bmi__gte=25, bmi__lt=30).count(),
        'obese': all_data.filter(bmi__gte=30).count()
    }
    
    context = {
        'total_patients': total_patients,
        'avg_age': round(avg_age, 1),
        'avg_bmi': round(avg_bmi, 1),
        'avg_heart_rate': round(avg_heart_rate, 1),
        'bmi_categories': bmi_categories,
        'all_data': all_data
    }
    
    return render(request, 'health_info/analyze.html', context)

def download_file(request, filename):
    upload_dir = get_upload_directory()
    file_path = os.path.join(upload_dir, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    
    messages.error(request, 'Файл не найден')
    return redirect('health_info:files')