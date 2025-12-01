from django.urls import path
from . import views

app_name = 'health_info'

urlpatterns = [
    path('', views.home, name='home'),
    path('input/', views.input_data, name='input_data'),
    path('upload/', views.upload_file, name='upload_file'),
    path('files/', views.file_list, name='file_list'),
    path('analyze/', views.analyze_data, name='analyze_data'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
]