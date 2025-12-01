from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
import os
import uuid

from .forms import HealthDataForm, FileUploadForm
from .models import HealthData
from .utils import (
    export_to_json, import_from_json,
    get_upload_directory, sanitize_filename, get_uploaded_files,
    save_health_data_from_dict
)

def home(request):
    """
    Главная страница
    """
    context = {
        'total_patients': HealthData.objects.count(),
        'total_files': len(get_uploaded_files())
    }
    return render(request, 'health_info/home.html', context)

def input_data(request):
    """
    Ввод данных через форму
    """
    if request.method == 'POST':
        form = HealthDataForm(request.POST)
        
        if form.is_valid():
            try:
                # Сохраняем данные в базу
                health_data = form.save()
                
                # Экспортируем в JSON файл
                upload_dir = get_upload_directory()
                content = export_to_json(health_data)
                filename = f"health_data_{health_data.patient_id}_{uuid.uuid4().hex[:8]}.json"
                
                # Санитайзинг имени файла
                safe_filename = sanitize_filename(filename)
                file_path = os.path.join(upload_dir, safe_filename)
                
                # Сохраняем файл
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                messages.success(
                    request, 
                    f'Данные пациента {health_data.patient_name} успешно сохранены и экспортированы в JSON!'
                )
                return redirect('health_info:file_list')
                
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении данных: {str(e)}')
        else:
            # Показываем конкретные ошибки
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        error_messages.append(str(error))
                    else:
                        field_label = form.fields[field].label
                        error_messages.append(f"{field_label}: {error}")
            
            for error_msg in error_messages:
                messages.error(request, error_msg)
    else:
        form = HealthDataForm()
    
    return render(request, 'health_info/input_data.html', {'form': form})

def upload_file(request):
    """
    Загрузка файла на сервер
    """
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            
            # Проверяем расширение файла
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            if file_extension != '.json':
                messages.error(request, 'Файл должен иметь расширение .json')
                return render(request, 'health_info/upload_file.html', {'form': form})
            
            # Санитайзинг имени файла
            safe_filename = sanitize_filename(uploaded_file.name)
            upload_dir = get_upload_directory()
            file_path = os.path.join(upload_dir, safe_filename)
            
            try:
                # Сохраняем файл
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                
                # Валидация и импорт данных
                data = import_from_json(file_path)
                
                # Сохраняем в базу данных
                health_data = save_health_data_from_dict(data)
                
                messages.success(
                    request, 
                    f'Файл успешно загружен! Данные пациента {health_data.patient_name} импортированы.'
                )
                return redirect('health_info:file_list')
                
            except Exception as e:
                # Удаляем невалидный файл
                if os.path.exists(file_path):
                    os.remove(file_path)
                messages.error(request, f'Ошибка при обработке файла: {str(e)}')
    else:
        form = FileUploadForm()
    
    return render(request, 'health_info/upload_file.html', {'form': form})

def file_list(request):
    """
    Список всех файлов и их содержимое
    """
    files = get_uploaded_files()
    file_contents = []
    
    for file_info in files:
        try:
            content = import_from_json(file_info['path'])
            
            file_contents.append({
                'file_info': file_info,
                'content': content
            })
        except Exception as e:
            file_contents.append({
                'file_info': file_info,
                'error': str(e)
            })
    
    context = {
        'file_contents': file_contents,
        'files_exist': len(files) > 0,
        'total_files': len(files)
    }
    
    return render(request, 'health_info/file_list.html', context)

def analyze_data(request):
    """
    Анализ данных
    """
    all_data = HealthData.objects.all()
    
    if not all_data.exists():
        messages.info(request, 'Нет данных для анализа. Добавьте данные через форму или загрузите файлы.')
        return redirect('health_info:home')
    
    # Базовая статистика
    total_patients = all_data.count()
    avg_age = sum([data.age for data in all_data]) / total_patients
    avg_bmi = sum([data.bmi for data in all_data]) / total_patients
    avg_heart_rate = sum([data.heart_rate for data in all_data]) / total_patients
    avg_cholesterol = sum([data.cholesterol for data in all_data]) / total_patients
    
    # Категории ИМТ - вычисляем вручную, так как bmi - это property
    bmi_categories = {
        'underweight': 0,
        'normal': 0,
        'overweight': 0,
        'obese': 0
    }
    
    for data in all_data:
        bmi = data.bmi
        if bmi < 18.5:
            bmi_categories['underweight'] += 1
        elif 18.5 <= bmi < 25:
            bmi_categories['normal'] += 1
        elif 25 <= bmi < 30:
            bmi_categories['overweight'] += 1
        else:
            bmi_categories['obese'] += 1
    
    # Анализ давления - тоже вычисляем вручную
    bp_categories = {
        'normal': 0,
        'elevated': 0,
        'stage1': 0,
        'stage2': 0
    }
    
    for data in all_data:
        systolic = data.blood_pressure_systolic
        diastolic = data.blood_pressure_diastolic
        
        if systolic < 120 and diastolic < 80:
            bp_categories['normal'] += 1
        elif 120 <= systolic <= 129 and diastolic < 80:
            bp_categories['elevated'] += 1
        elif 130 <= systolic <= 139 or 80 <= diastolic <= 89:
            bp_categories['stage1'] += 1
        elif systolic >= 140 or diastolic >= 90:
            bp_categories['stage2'] += 1
    
    context = {
        'total_patients': total_patients,
        'avg_age': round(avg_age, 1),
        'avg_bmi': round(avg_bmi, 1),
        'avg_heart_rate': round(avg_heart_rate, 1),
        'avg_cholesterol': round(avg_cholesterol, 1),
        'bmi_categories': bmi_categories,
        'bp_categories': bp_categories,
        'all_data': all_data
    }
    
    return render(request, 'health_info/analyze.html', context)

def download_file(request, filename):
    """
    Скачивание файла
    """
    upload_dir = get_upload_directory()
    file_path = os.path.join(upload_dir, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    else:
        messages.error(request, 'Файл не найден')
        return redirect('health_info:file_list')