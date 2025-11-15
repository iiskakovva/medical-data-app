from django.urls import path
from . import views

app_name = 'health_info'

urlpatterns = [
    path('', views.home, name='home'),
    path('input/', views.input_data, name='input'),
    path('upload/', views.upload_file, name='upload'),
    path('data/', views.view_data, name='view_data'),  
    path('search/', views.search_data, name='search_data'),
    path('edit/<int:pk>/', views.edit_data, name='edit_data'),
    path('delete/<int:pk>/', views.delete_data, name='delete_data'),
    path('analyze/', views.analyze_data, name='analyze'),
]