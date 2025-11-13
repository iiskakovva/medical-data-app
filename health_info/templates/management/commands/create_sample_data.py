from django.core.management.base import BaseCommand
from health_info.models import HealthData
import random

class Command(BaseCommand):
    help = 'Create sample medical data for demonstration'

    def handle(self, *args, **options):
        sample_patients = [
            {
                'patient_id': 'P001',
                'patient_name': 'Иванов Иван Иванович',
                'age': 45,
                'height': 175.5,
                'weight': 80.2,
                'blood_pressure_systolic': 130,
                'blood_pressure_diastolic': 85,
                'heart_rate': 72,
                'cholesterol': 5.2
            },
            {
                'patient_id': 'P002', 
                'patient_name': 'Петрова Мария Сергеевна',
                'age': 35,
                'height': 165.0,
                'weight': 62.5,
                'blood_pressure_systolic': 120,
                'blood_pressure_diastolic': 75,
                'heart_rate': 68,
                'cholesterol': 4.8
            },
            # Добавьте больше тестовых данных...
        ]

        for patient_data in sample_patients:
            HealthData.objects.create(**patient_data)

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample medical data')
        )