from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('agregar/', views.agregar_usuario, name='agregar_usuario'),
    path('editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('eliminar/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('toggle-status/<int:usuario_id>/', views.toggle_usuario_status, name='toggle_usuario_status'),
]