from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    path('', views.report_index, name='index'),
    path('tickets/', views.report_tickets, name='tickets'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/excel/', views.export_excel, name='export_excel'),
]
