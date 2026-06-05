from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='list'),
    path('new/', views.ticket_create, name='create'),
    path('mine/', views.my_tickets, name='my_tickets'),
    path('sla-config/', views.sla_config_view, name='sla_config'),
    path('api/subcategories/', views.subcategories_ajax, name='subcategories_ajax'),
    path('<str:number>/', views.TicketDetailView.as_view(), name='detail'),
    path('<str:number>/edit/', views.ticket_edit, name='edit'),
    path('<str:number>/status/', views.ticket_change_status, name='change_status'),
    path('<str:number>/assign/', views.ticket_assign, name='assign'),
    path('<str:number>/request-info/', views.ticket_request_info, name='request_info'),
    path('<str:number>/priority/', views.ticket_change_priority, name='change_priority'),
    path('<str:number>/comment/', views.add_comment, name='add_comment'),
    path('<str:number>/attach/', views.add_attachment, name='add_attachment'),
]
