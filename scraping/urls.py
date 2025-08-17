from django.urls import path
from . import views

app_name = "scraping"

urlpatterns = [
    path("cargar_listas/", views.cargar_listas, name="cargar_listas"),
    path("scrape-argentina/", views.scrape_argentina, name="scrape_argentina"),
    path("actualizar-lista/", views.actualizar_lista, name="actualizar_lista"),

]
