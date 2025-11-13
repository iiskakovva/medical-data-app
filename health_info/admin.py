from django.contrib import admin
from .models import HealthData

@admin.register(HealthData)
class HealthDataAdmin(admin.ModelAdmin):
    list_display = [
        'patient_id', 
        'patient_name', 
        'age', 
        'bmi', 
        'blood_pressure_systolic', 
        'blood_pressure_diastolic',
        'created_at'
    ]
    list_filter = ['created_at', 'age']
    search_fields = ['patient_id', 'patient_name']
    readonly_fields = ['bmi', 'created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('patient_id', 'patient_name', 'age')
        }),
        ('Антропометрические данные', {
            'fields': ('height', 'weight', 'bmi')
        }),
        ('Медицинские показатели', {
            'fields': (
                'blood_pressure_systolic', 
                'blood_pressure_diastolic',
                'heart_rate', 
                'cholesterol'
            )
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )