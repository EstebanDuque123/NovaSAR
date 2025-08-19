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
from django.contrib.auth.models import Group
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

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


# Obtener todas las listas
listas = Lista.objects.all()

# Filtrar por fuente
dian = Lista.objects.filter(fuente="DIAN")

# Exportar a PDF (ejemplo rápido)
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO



def exportar_pdf(request):
    data = [["ID", "Nombre", "Fuente", "Tipo", "Fecha Actualización"]]
    
    # Estilos para que el texto se ajuste
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]

    for lista in Lista.objects.all():
        # Cada valor se convierte en Paragraph para que haga wrap si es largo
        data.append([
            Paragraph(str(lista.id), style_normal),
            Paragraph(lista.nombre, style_normal),
            Paragraph(lista.fuente, style_normal),
            Paragraph(lista.tipo, style_normal),
            Paragraph(str(lista.fecha_actualizacion), style_normal),
        ])

    pdf_path = "listas.pdf"
    pdf = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=30, rightMargin=30)
    
    # Ajustar ancho de columnas proporcional
    num_columnas = len(data[0])
    ancho_total = A4[0] - pdf.leftMargin - pdf.rightMargin
    ancho_columnas = [ancho_total / num_columnas] * num_columnas
    
    table = Table(data, colWidths=ancho_columnas)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("ALIGN", (0,1), (-1,-1), "LEFT"),  # contenido alineado a la izquierda
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("VALIGN", (0,0), (-1,-1), "TOP"),  # evita que el texto se superponga verticalmente
        ("FONTSIZE", (0,0), (-1,-1), 9),    # reduce tamaño de texto
    ]))

    pdf.build([table])
    
    # Retornar PDF como descarga
    with open(pdf_path, "rb") as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="listas.pdf"'
        return response