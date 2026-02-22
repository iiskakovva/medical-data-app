from django.urls import path
from . import views

app_name = 'health_info'

urlpatterns = [
    path('', views.home, name='home'),
    path('input/', views.input_data, name='input_data'),
    path('upload/', views.upload_file, name='upload_file'),
    path('data/', views.data_list, name='data_list'),
    path('ajax-search/', views.ajax_search, name='ajax_search'),
    path('edit/<int:record_id>/', views.edit_record, name='edit_record'),
    path('delete/<int:record_id>/', views.delete_record, name='delete_record'),
    path('analyze/', views.analyze_data, name='analyze_data'),
]