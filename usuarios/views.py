from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User

from .models import PerfilUsuario
from .forms import UsuarioForm, PerfilUsuarioForm


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            
            # Crear el perfil si no existe
            if not hasattr(user, 'perfilusuario'):
                PerfilUsuario.objects.create(user=user)

            return redirect('buscador')  # Redirigir a la página del buscador (o a donde prefieras)
        else:
            messages.error(request, 'Usuario o contraseña inválidos')
            
    return render(request, 'usuarios/login.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')  # Redirige a la página de login después de cerrar sesión
    else:
        return HttpResponseForbidden("Método no permitido")  # Si no es POST, regresa un error 403
    
def es_superusuario(user):
    return user.is_superuser

def es_administrador(user):
    return user.groups.filter(name="Administradores").exists()

@user_passes_test(es_administrador)
def lista_usuarios(request):
    usuarios = User.objects.filter(is_superuser=False)
    return render(request, "usuarios/lista_usuarios.html", {"usuarios": usuarios})

@user_passes_test(es_administrador)
def crear_usuario(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        perfil_form = PerfilUsuarioForm(request.POST)
        if form.is_valid() and perfil_form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            perfil = perfil_form.save(commit=False)
            perfil.user = user
            perfil.save()
            return redirect("lista_usuarios")
    else:
        form = UsuarioForm()
        perfil_form = PerfilUsuarioForm()
    return render(request, "usuarios/crear_usuario.html", {"form": form, "perfil_form": perfil_form})

@user_passes_test(es_administrador)
def editar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    perfil = get_object_or_404(PerfilUsuario, user=user)

    if request.method == "POST":
        form = UsuarioForm(request.POST, instance=user)
        perfil_form = PerfilUsuarioForm(request.POST, instance=perfil)
        if form.is_valid() and perfil_form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data["password"]:
                user.set_password(form.cleaned_data["password"])
            user.save()
            perfil_form.save()
            return redirect("lista_usuarios")
    else:
        form = UsuarioForm(instance=user)
        form.fields["password"].required = False  # No obligar a cambiarla
        perfil_form = PerfilUsuarioForm(instance=perfil)

    return render(request, "usuarios/editar_usuario.html", {"form": form, "perfil_form": perfil_form, "usuario": user})

@user_passes_test(es_administrador)
def eliminar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        user.delete()
        return redirect("lista_usuarios")
    
    return render(request, "usuarios/eliminar_usuario.html", {"usuario": user})

