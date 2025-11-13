from django.urls import path
from . import views

app_name = 'health_info'

urlpatterns = [
    path('', views.home, name='home'),
    path('input/', views.input_data, name='input'),
    path('upload/', views.upload_file, name='upload'),
    path('files/', views.file_list, name='files'),
    path('analyze/', views.analyze_data, name='analyze'),
    path('download/<str:filename>/', views.download_file, name='download'),
]