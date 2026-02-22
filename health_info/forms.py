from django import forms
from .models import HealthData

class HealthDataForm(forms.ModelForm):
    class Meta:
        model = HealthData
        fields = '__all__'
        widgets = {
            'patient_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ID пациента'
            }),
            'patient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите полное имя'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '150'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Рост в сантиметрах'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Вес в килограммах'
            }),
            'blood_pressure_systolic': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '50',
                'max': '250',
                'placeholder': 'Верхнее давление'
            }),
            'blood_pressure_diastolic': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '30',
                'max': '150',
                'placeholder': 'Нижнее давление'
            }),
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '30',
                'max': '200',
                'placeholder': 'Ударов в минуту'
            }),
            'cholesterol': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Уровень холестерина'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        systolic = cleaned_data.get('blood_pressure_systolic')
        diastolic = cleaned_data.get('blood_pressure_diastolic')
        
        if systolic and diastolic and systolic <= diastolic:
            raise forms.ValidationError(
                "Систолическое давление должно быть больше диастолического"
            )
        
        return cleaned_data

class FileUploadForm(forms.Form):
    FILE_TYPES = [
        ('json', 'JSON файл'),
        ('xml', 'XML файл'),
    ]
    
    file = forms.FileField(
        label='Выберите файл для загрузки',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json,.xml'
        })
    )
    file_type = forms.ChoiceField(
        choices=FILE_TYPES,
        label='Тип файла',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='json'
    )

class SaveLocationForm(forms.Form):
    LOCATION_CHOICES = [
        ('file', 'Сохранить в JSON/XML файл'),
        ('db', 'Сохранить в базу данных'),
    ]
    
    location = forms.ChoiceField(
        choices=LOCATION_CHOICES,
        label='Куда сохранить данные',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='db'
    )

class DataSourceForm(forms.Form):
    SOURCE_CHOICES = [
        ('db', 'База данных'),
        ('file', 'Файлы (JSON/XML)'),
    ]
    
    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        label='Источник данных',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='db'
    )