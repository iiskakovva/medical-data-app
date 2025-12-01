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
    file = forms.FileField(
        label='Выберите JSON файл для загрузки',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json'
        })
    )