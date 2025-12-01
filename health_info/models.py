from django.db import models

class HealthData(models.Model):
    patient_id = models.CharField(
        max_length=50, 
        verbose_name="ID пациента"
    )
    patient_name = models.CharField(
        max_length=100, 
        verbose_name="Имя пациента"
    )
    age = models.IntegerField(
        verbose_name="Возраст"
    )
    height = models.FloatField(
        verbose_name="Рост (см)"
    )
    weight = models.FloatField(
        verbose_name="Вес (кг)"
    )
    blood_pressure_systolic = models.IntegerField(
        verbose_name="Систолическое давление"
    )
    blood_pressure_diastolic = models.IntegerField(
        verbose_name="Диастолическое давление"
    )
    heart_rate = models.IntegerField(
        verbose_name="Частота сердечных сокращений"
    )
    cholesterol = models.FloatField(
        verbose_name="Уровень холестерина"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def bmi(self):
        """Рассчитать индекс массы тела"""
        if self.height > 0:
            return round(self.weight / ((self.height / 100) ** 2), 2)
        return 0
    
    def get_bmi_category(self):
        """Получить категорию ИМТ"""
        bmi = self.bmi
        if bmi < 18.5:
            return "Недостаточный вес"
        elif 18.5 <= bmi < 25:
            return "Нормальный вес"
        elif 25 <= bmi < 30:
            return "Избыточный вес"
        else:
            return "Ожирение"
    
    def __str__(self):
        return f"{self.patient_name} ({self.patient_id})"
    
    class Meta:
        verbose_name = "Медицинские данные"
        verbose_name_plural = "Медицинские данные"
        ordering = ['-created_at']