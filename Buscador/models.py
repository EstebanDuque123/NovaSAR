from django.db import models

# Create your models here.
class Lista(models.Model):
    nombre = models.CharField(max_length=100)
    fuente = models.URLField()
    tipo = models.CharField(max_length=50)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class PersonaLista(models.Model):
    nombre = models.CharField(max_length=255)
    identificacion = models.CharField(max_length=100, blank=True, null=True)
    lista = models.ForeignKey(Lista, on_delete=models.CASCADE)
    fecha_ingreso = models.DateField()

    def __str__(self):
        return self.nombre

class Consulta(models.Model):
    termino = models.CharField(max_length=255)
    resultado = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.termino} ({self.fecha})"