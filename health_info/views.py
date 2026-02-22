from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
import os
import uuid

from .forms import HealthDataForm, FileUploadForm, SaveLocationForm, DataSourceForm
from .models import HealthData
from .utils import (
    export_to_json, export_to_xml, import_from_json, import_from_xml,
    get_upload_directory, sanitize_filename, get_uploaded_files,
    save_health_data_from_dict
)

def home(request):
    """Главная страница"""
    context = {
        'total_patients': HealthData.objects.count(),
        'total_files': len(get_uploaded_files())
    }
    return render(request, 'health_info/home.html', context)

def input_data(request):
    """Ввод данных через форму с выбором места сохранения"""
    if request.method == 'POST':
        form = HealthDataForm(request.POST)
        save_form = SaveLocationForm(request.POST)
        
        if form.is_valid() and save_form.is_valid():
            try:
                location = save_form.cleaned_data['location']
                
                if location == 'db':
                    # Сохраняем в базу данных с проверкой на дубликаты
                    patient_id = form.cleaned_data['patient_id']
                    
                    if HealthData.objects.filter(patient_id=patient_id).exists():
                        messages.warning(
                            request, 
                            f'Пациент с ID {patient_id} уже существует в базе данных. Данные не добавлены.'
                        )
                    else:
                        health_data = form.save()
                        messages.success(
                            request, 
                            f'Данные пациента {health_data.patient_name} успешно сохранены в базу данных!'
                        )
                
                else:  # Сохраняем в файл
                    health_data = form.save(commit=False)
                    health_data.save()
                    
                    # Экспортируем в файл
                    upload_dir = get_upload_directory()
                    content = export_to_json(health_data)
                    filename = f"health_data_{health_data.patient_id}_{uuid.uuid4().hex[:8]}.json"
                    
                    safe_filename = sanitize_filename(filename)
                    file_path = os.path.join(upload_dir, safe_filename)
                    
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    
                    messages.success(
                        request, 
                        f'Данные пациента {health_data.patient_name} успешно сохранены в файл!'
                    )
                
                return redirect('health_info:data_list')
                
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении данных: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = HealthDataForm()
        save_form = SaveLocationForm(initial={'location': 'db'})
    
    return render(request, 'health_info/input_data.html', {
        'form': form,
        'save_form': save_form
    })

def upload_file(request):
    """Загрузка файла на сервер"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_type = form.cleaned_data['file_type']
            
            # Проверяем расширение файла
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            expected_ext = f'.{file_type}'
            
            if file_extension != expected_ext:
                messages.error(request, f'Файл должен иметь расширение {expected_ext}')
                return render(request, 'health_info/upload_file.html', {'form': form})
            
            safe_filename = sanitize_filename(uploaded_file.name)
            upload_dir = get_upload_directory()
            file_path = os.path.join(upload_dir, safe_filename)
            
            try:
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                
                # Валидация и импорт данных
                if file_type == 'json':
                    data = import_from_json(file_path)
                else:
                    data = import_from_xml(file_path)
                
                # Сохраняем в базу данных с проверкой дубликатов
                try:
                    health_data = save_health_data_from_dict(data)
                    messages.success(
                        request, 
                        f'Файл успешно загружен! Данные пациента {health_data.patient_name} импортированы в базу данных.'
                    )
                except Exception as e:
                    messages.warning(request, f'Файл загружен, но данные не импортированы: {str(e)}')
                
                return redirect('health_info:data_list')
                
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                messages.error(request, f'Ошибка при обработке файла: {str(e)}')
    else:
        form = FileUploadForm()
    
    return render(request, 'health_info/upload_file.html', {'form': form})

def data_list(request):
    """Список данных с выбором источника"""
    source_form = DataSourceForm(request.GET or None)
    
    if source_form.is_valid():
        source = source_form.cleaned_data['source']
    else:
        source = 'db'
    
    context = {
        'source_form': source_form,
        'source': source,
        'files_exist': len(get_uploaded_files()) > 0,
        'db_records_exist': HealthData.objects.exists()
    }
    
    if source == 'file':
        files = get_uploaded_files()
        file_contents = []
        
        for file_info in files:
            try:
                if file_info['type'] == 'JSON':
                    content = import_from_json(file_info['path'])
                else:
                    content = import_from_xml(file_info['path'])
                
                file_contents.append({
                    'file_info': file_info,
                    'content': content
                })
            except Exception as e:
                file_contents.append({
                    'file_info': file_info,
                    'error': str(e)
                })
        
        context.update({
            'file_contents': file_contents,
            'total_files': len(files)
        })
        
        return render(request, 'health_info/file_list.html', context)
    
    else:  # source == 'db'
        search_query = request.GET.get('q', '')
        records = HealthData.objects.all().order_by('-created_at')
        
        if search_query:
            records = records.filter(
                Q(patient_id__icontains=search_query) |
                Q(patient_name__icontains=search_query)
            )
        
        context.update({
            'records': records,
            'search_query': search_query,
            'total_records': records.count()
        })
        
        return render(request, 'health_info/db_list.html', context)

def ajax_search(request):
    """AJAX поиск по базе данных"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('q', '')
        
        if query:
            results = HealthData.objects.filter(
                Q(patient_id__icontains=query) |
                Q(patient_name__icontains=query)
            ).order_by('-created_at')[:10]
            
            data = []
            for record in results:
                data.append({
                    'id': record.id,
                    'patient_id': record.patient_id,
                    'patient_name': record.patient_name,
                    'age': record.age,
                    'height': record.height,
                    'weight': record.weight,
                    'bmi': record.bmi,
                    'blood_pressure': f"{record.blood_pressure_systolic}/{record.blood_pressure_diastolic}",
                    'heart_rate': record.heart_rate,
                    'cholesterol': record.cholesterol,
                    'created_at': record.created_at.strftime('%d.%m.%Y %H:%M'),
                    'edit_url': f"/edit/{record.id}/",
                    'delete_url': f"/delete/{record.id}/"
                })
            
            return JsonResponse({'results': data})
    
    return JsonResponse({'results': []})

def edit_record(request, record_id):
    """Редактирование записи в базе данных"""
    record = get_object_or_404(HealthData, id=record_id)
    
    if request.method == 'POST':
        form = HealthDataForm(request.POST, instance=record)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Запись успешно обновлена!')
                return redirect('health_info:data_list')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении записи: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = HealthDataForm(instance=record)
    
    return render(request, 'health_info/edit_record.html', {
        'form': form,
        'record': record
    })

def delete_record(request, record_id):
    """Удаление записи из базы данных"""
    record = get_object_or_404(HealthData, id=record_id)
    
    if request.method == 'POST':
        patient_name = record.patient_name
        record.delete()
        messages.success(request, f'Запись пациента {patient_name} успешно удалена!')
        return redirect('health_info:data_list')
    
    return render(request, 'health_info/delete_confirm.html', {
        'record': record
    })

def analyze_data(request):
    """
    Анализ медицинских данных
    """
    from django.shortcuts import render
    from .models import HealthData
    
    all_data = HealthData.objects.all()
    
    if not all_data.exists():
        from django.contrib import messages
        messages.info(request, 'Нет данных для анализа. Добавьте данные через форму или загрузите файлы.')
        from django.shortcuts import redirect
        return redirect('health_info:home')
    
    # Базовая статистика
    total_patients = all_data.count()
    avg_age = sum([data.age for data in all_data]) / total_patients
    avg_bmi = sum([data.bmi for data in all_data]) / total_patients
    avg_heart_rate = sum([data.heart_rate for data in all_data]) / total_patients
    avg_cholesterol = sum([data.cholesterol for data in all_data]) / total_patients
    
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
        'avg_cholesterol': round(avg_cholesterol, 1),
        'bmi_categories': bmi_categories,
        'all_data': all_data
    }
    
    return render(request, 'health_info/analyze.html', context)