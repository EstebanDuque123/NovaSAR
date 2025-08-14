from django.contrib.auth.models import User
from django.db import models

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    limite_busquedas = models.IntegerField(default=10)
    limite_reportes = models.IntegerField(default=5)
    busquedas_realizadas = models.IntegerField(default=0)
    reportes_generados = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username