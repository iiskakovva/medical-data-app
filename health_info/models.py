from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

class HealthData(models.Model):
    patient_id = models.CharField(
        max_length=50, 
        verbose_name="ID пациента",
        unique=True,
        error_messages={'unique': 'Пациент с таким ID уже существует'}
    )
    patient_name = models.CharField(
        max_length=100, 
        verbose_name="Имя пациента"
    )
    age = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        verbose_name="Возраст"
    )
    height = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name="Рост (см)"
    )
    weight = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name="Вес (кг)"
    )
    blood_pressure_systolic = models.IntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(250)],
        verbose_name="Систолическое давление"
    )
    blood_pressure_diastolic = models.IntegerField(
        validators=[MinValueValidator(30), MaxValueValidator(150)],
        verbose_name="Диастолическое давление"
    )
    heart_rate = models.IntegerField(
        validators=[MinValueValidator(30), MaxValueValidator(200)],
        verbose_name="Частота сердечных сокращений"
    )
    cholesterol = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name="Уровень холестерина"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.CharField(
        max_length=10,
        choices=[('db', 'База данных'), ('file', 'Файл')],
        default='db',
        verbose_name="Источник данных"
    )
    
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
    
    def get_absolute_url(self):
        return reverse('health_info:edit_data', kwargs={'pk': self.pk})
    
    def __str__(self):
        return f"{self.patient_name} ({self.patient_id})"
    
    class Meta:
        verbose_name = "Медицинские данные"
        verbose_name_plural = "Медицинские данные"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['patient_name']),
            models.Index(fields=['created_at']),
        ]