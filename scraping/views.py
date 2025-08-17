import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.core.management import call_command
from django.contrib import messages
import subprocess
import pandas as pd
from django.http import HttpResponse
from Buscador.models import Lista, PersonaLista
from datetime import datetime

def cargar_listas(request):
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo = request.FILES["archivo"]

        # ✅ Validar nombre exacto
        if archivo.name != "Listas.csv":
            messages.error(request, "❌ Solo se permite subir el archivo con el nombre exacto 'Listas.csv'")
            return redirect("cargar_listas")

        # Carpeta destino
        ruta_listas = os.path.join(settings.BASE_DIR, "scraping", "listas")
        os.makedirs(ruta_listas, exist_ok=True)

        # Guardar archivo
        ruta_archivo = os.path.join(ruta_listas, archivo.name)
        with open(ruta_archivo, "wb+") as destino:
            for chunk in archivo.chunks():
                destino.write(chunk)

        try:
            # Ejecutar comando con ese archivo
            call_command("cargar_listas_csv", ruta_archivo)
            messages.success(request, "✅ Listas cargadas correctamente desde Listas.csv")
        except Exception as e:
            messages.error(request, f"❌ Error al cargar las listas: {e}")

        return redirect("scraping:cargar_listas")

    return render(request, "scraping/cargar_listas.html")


from django.contrib import messages
from django.shortcuts import redirect
import subprocess

def scrape_argentina(request):
    if request.method == "POST":
        try:
            # Aquí llamas a tu script de scraping (ajusta la ruta)
            subprocess.run(["python", "scraping/scrape_argentina.py"], check=True)

            messages.success(request, "✅ Scraping de Argentina ejecutado correctamente.")
        except Exception as e:
            messages.error(request, f"❌ Error al ejecutar el scraping: {str(e)}")

    # Redirige de nuevo al mismo template (cargar_listas.html o scraping.html)
    return redirect("scraping:cargar_listas")


def actualizar_lista(request):
    """
    Lee el CSV generado por el scraping y sincroniza la base de datos con su contenido:
    - Agrega nuevos registros
    - Mantiene los existentes
    - Elimina los que ya no aparecen en el CSV
    """
    csv_path = os.path.join(
        settings.BASE_DIR, 
        "scraping", "resultado_scraping", 
        "ARGENTINA_PROFUGOS_DE_LA_JUSTICIA.csv"
    )

    if not os.path.exists(csv_path):
        messages.error(request, "❌ No se encuentra el archivo del scraping. Ejecute primero el scraping.")
        return redirect("scraping:cargar_listas")

    df = pd.read_csv(csv_path)

    if df.empty:
        messages.warning(request, "⚠️ El archivo CSV está vacío.")
        return redirect("scraping:cargar_listas")

    # Conjunto de registros únicos del CSV
    registros_csv = set()
    for _, row in df.iterrows():
        registros_csv.add((
            row["nombre"],
            str(row.get("identificacion", "")),
            row["lista"]
        ))

    total_agregados = 0
    total_eliminados = 0

    # Procesar cada lista del CSV
    listas = df["lista"].unique()
    for lista_nombre in listas:
        subset = df[df["lista"] == lista_nombre]

        lista_obj, _ = Lista.objects.get_or_create(
            nombre=lista_nombre,
            defaults={
                "tipo": subset.iloc[0]["tipo_lista"],
                "fuente": subset.iloc[0]["fuente"],
            }
        )

        # --- AGREGAR / ACTUALIZAR ---
        for _, row in subset.iterrows():
            try:
                fecha_ingreso = datetime.strptime(row["fecha_ingreso"], "%d/%m/%Y").date()
            except Exception:
                fecha_ingreso = None

            _, created = PersonaLista.objects.update_or_create(
                nombre=row["nombre"],
                identificacion=row.get("identificacion", ""),
                lista=lista_obj,
                defaults={"fecha_ingreso": fecha_ingreso}
            )
            if created:
                total_agregados += 1

        # --- ELIMINAR LOS QUE YA NO ESTÁN ---
        registros_csv_lista = set(
            (r["nombre"], str(r.get("identificacion", "")))
            for _, r in subset.iterrows()
        )

        registros_db = PersonaLista.objects.filter(lista=lista_obj)
        for persona in registros_db:
            if (persona.nombre, str(persona.identificacion)) not in registros_csv_lista:
                persona.delete()
                total_eliminados += 1

    messages.success(
        request,
        f"✅ Lista sincronizada. Se agregaron {total_agregados} nuevos registros y se eliminaron {total_eliminados} que ya no estaban en el scraping."
    )
    return redirect("scraping:cargar_listas")
