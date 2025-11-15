from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import re

from .models import HealthData
from .forms import HealthDataForm, HealthDataEditForm, FileUploadForm, DataSourceForm

# Утилиты для работы с файлами
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
        form = HealthDataForm(request.POST)
        if form.is_valid():
            try:
                storage_type = form.cleaned_data['storage_type']
                patient_data = form.cleaned_data
                
                if storage_type == 'db':
                    # Сохраняем в базу данных
                    try:
                        health_data = HealthData.objects.create(
                            patient_id=patient_data['patient_id'],
                            patient_name=patient_data['patient_name'],
                            age=patient_data['age'],
                            height=patient_data['height'],
                            weight=patient_data['weight'],
                            blood_pressure_systolic=patient_data['blood_pressure_systolic'],
                            blood_pressure_diastolic=patient_data['blood_pressure_diastolic'],
                            heart_rate=patient_data['heart_rate'],
                            cholesterol=patient_data['cholesterol'],
                            source='db'
                        )
                        messages.success(request, f'Данные пациента {health_data.patient_name} успешно сохранены в базу данных!')
                        return redirect('health_info:view_data')
                        
                    except Exception as e:
                        if 'unique' in str(e).lower():
                            messages.error(request, f'Пациент с ID {patient_data["patient_id"]} уже существует в базе данных!')
                        else:
                            messages.error(request, f'Ошибка при сохранении в базу: {str(e)}')
                
                else:
                    # Экспортируем в файл
                    health_data = HealthData(
                        patient_id=patient_data['patient_id'],
                        patient_name=patient_data['patient_name'],
                        age=patient_data['age'],
                        height=patient_data['height'],
                        weight=patient_data['weight'],
                        blood_pressure_systolic=patient_data['blood_pressure_systolic'],
                        blood_pressure_diastolic=patient_data['blood_pressure_diastolic'],
                        heart_rate=patient_data['heart_rate'],
                        cholesterol=patient_data['cholesterol'],
                        source='file'
                    )
                    
                    upload_dir = get_upload_directory()
                    
                    if storage_type == 'json':
                        content = export_to_json(health_data)
                        filename = f"health_data_{health_data.patient_id}.json"
                    else:
                        content = export_to_xml(health_data)
                        filename = f"health_data_{health_data.patient_id}.xml"
                    
                    safe_filename = sanitize_filename(filename)
                    file_path = os.path.join(upload_dir, safe_filename)
                    
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    
                    messages.success(request, f'Данные успешно экспортированы в {storage_type.upper()} файл!')
                    return redirect('health_info:view_data')
                    
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
    else:
        form = HealthDataForm()
    
    return render(request, 'health_info/input_data.html', {'form': form})

def view_data(request):
    source_form = DataSourceForm(request.GET or None)
    source = request.GET.get('source', 'db')
    
    context = {
        'source_form': source_form,
        'selected_source': source,
    }
    
    if source == 'db':
        # Данные из базы
        health_data = HealthData.objects.all().order_by('-created_at')
        context['db_data'] = health_data
        context['total_records'] = health_data.count()
    else:
        # Данные из файлов
        upload_dir = get_upload_directory()
        files_data = []
        
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
                        
                        if filename.endswith('.json'):
                            with open(file_path, 'r', encoding='utf-8') as file:
                                content = json.load(file)
                        else:
                            tree = ET.parse(file_path)
                            root = tree.getroot()
                            content = {}
                            for child in root:
                                content[child.tag] = child.text
                        
                        files_data.append({
                            'file_info': file_info,
                            'content': content
                        })
                    except Exception as e:
                        files_data.append({
                            'file_info': file_info,
                            'error': str(e)
                        })
        
        context['files_data'] = files_data
        context['total_records'] = len(files_data)
    
    return render(request, 'health_info/view_data.html', context)

@csrf_exempt
def search_data(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'error': 'Слишком короткий запрос'}, status=400)
        
        results = HealthData.objects.filter(
            models.Q(patient_id__icontains=query) |
            models.Q(patient_name__icontains=query)
        ).values(
            'id', 'patient_id', 'patient_name', 'age', 'height', 'weight',
            'blood_pressure_systolic', 'blood_pressure_diastolic', 
            'heart_rate', 'cholesterol', 'bmi', 'created_at'
        )[:50]  # Ограничиваем результаты
        
        data = list(results)
        for item in data:
            item['created_at'] = item['created_at'].strftime('%d.%m.%Y %H:%M')
            item['bmi_category'] = HealthData(
                bmi=item['bmi']
            ).get_bmi_category()
        
        return JsonResponse({'results': data, 'count': len(data)})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def edit_data(request, pk):
    health_data = get_object_or_404(HealthData, pk=pk)
    
    if request.method == 'POST':
        form = HealthDataEditForm(request.POST, instance=health_data)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Данные пациента {health_data.patient_name} успешно обновлены!')
                return redirect('health_info:view_data')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении: {str(e)}')
    else:
        form = HealthDataEditForm(instance=health_data)
    
    return render(request, 'health_info/edit_data.html', {
        'form': form,
        'health_data': health_data
    })

@require_http_methods(["POST"])
def delete_data(request, pk):
    health_data = get_object_or_404(HealthData, pk=pk)
    patient_name = health_data.patient_name
    
    try:
        health_data.delete()
        messages.success(request, f'Данные пациента {patient_name} успешно удалены!')
    except Exception as e:
        messages.error(request, f'Ошибка при удалении: {str(e)}')
    
    return redirect('health_info:view_data')

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_type = request.POST.get('file_type', 'json')
        
        try:
            safe_filename = sanitize_filename(uploaded_file.name)
            upload_dir = get_upload_directory()
            file_path = os.path.join(upload_dir, safe_filename)
            
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            if file_type == 'json':
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
            else:
                tree = ET.parse(file_path)
                root = tree.getroot()
                data = {}
                for child in root:
                    data[child.tag] = child.text
                
                numeric_fields = ['age', 'height', 'weight', 'blood_pressure_systolic', 
                                'blood_pressure_diastolic', 'heart_rate', 'cholesterol']
                for field in numeric_fields:
                    if field in data:
                        if field in ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate']:
                            data[field] = int(data[field])
                        else:
                            data[field] = float(data[field])
            
            validate_health_data(data)
            
            # Проверяем дубликаты перед сохранением в БД
            if HealthData.objects.filter(patient_id=data['patient_id']).exists():
                messages.warning(request, f'Пациент с ID {data["patient_id"]} уже существует в базе данных. Файл загружен, но данные не импортированы.')
            else:
                health_data = HealthData.objects.create(
                    patient_id=data['patient_id'],
                    patient_name=data['patient_name'],
                    age=data['age'],
                    height=data['height'],
                    weight=data['weight'],
                    blood_pressure_systolic=data['blood_pressure_systolic'],
                    blood_pressure_diastolic=data['blood_pressure_diastolic'],
                    heart_rate=data['heart_rate'],
                    cholesterol=data['cholesterol'],
                    source='file'
                )
                messages.success(request, f'Файл успешно загружен и данные пациента {health_data.patient_name} импортированы в базу!')
            
            return redirect('health_info:view_data')
            
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            messages.error(request, f'Ошибка: {str(e)}')
    
    return render(request, 'health_info/upload_file.html')

def analyze_data(request):
    all_data = HealthData.objects.all()
    
    if not all_data.exists():
        messages.info(request, 'Нет данных для анализа.')
        return redirect('health_info:home')
    
    total_patients = all_data.count()
    avg_age = sum([data.age for data in all_data]) / total_patients
    avg_bmi = sum([data.bmi for data in all_data]) / total_patients
    avg_heart_rate = sum([data.heart_rate for data in all_data]) / total_patients
    
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