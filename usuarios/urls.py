from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path("listar/", views.lista_usuarios, name="lista_usuarios"),
    path("crear/", views.crear_usuario, name="crear_usuario"),
    path("listar/", views.lista_usuarios, name="lista_usuarios"),
    path("crear/", views.crear_usuario, name="crear_usuario"),
    path("editar/<int:user_id>/", views.editar_usuario, name="editar_usuario"),
    path("eliminar/<int:user_id>/", views.eliminar_usuario, name="eliminar_usuario"),
]