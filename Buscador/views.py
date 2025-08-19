from django.shortcuts import render
from .models import PersonaLista, Consulta
from django.contrib.auth.decorators import login_required  # Importar
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import PersonaLista
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from usuarios.models import PerfilUsuario 
import requests

@login_required
def buscador(request):
    resultados = []
    termino = ""
    perfil = PerfilUsuario.objects.get(user=request.user)
    es_administrador = request.user.groups.filter(name='Administradores').exists()

    if request.method == "POST":
        if perfil.busquedas_realizadas >= perfil.limite_busquedas:
            return render(request, "busqueda.html", {
                "error": "Has alcanzado tu límite de búsquedas.",
                "perfil": perfil,
                "termino": termino,
                "resultados": [],
                "es_administrador": es_administrador,
            })

        termino = request.POST.get("termino")
        resultados = PersonaLista.objects.filter(nombre__icontains=termino)
        
        # Registrar búsqueda solo si hay resultados
        if resultados:
            perfil.busquedas_realizadas += 1
            perfil.save()

        Consulta.objects.create(termino=termino, resultado=f"{len(resultados)} resultados")

    return render(request, "busqueda.html", {
        "resultados": resultados,
        "termino": termino,
        "perfil": perfil,
        "es_administrador": es_administrador,
    })


def generar_pdf(request):
    perfil = PerfilUsuario.objects.get(user=request.user)

    if perfil.reportes_generados >= perfil.limite_reportes:
        return HttpResponse("Has alcanzado tu límite de generación de reportes.", status=403)
    
    if request.method == "POST":
        ids = request.POST.getlist('personas')
        personas = PersonaLista.objects.filter(id__in=ids)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        title = Paragraph("Reporte NovaSAR", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))

        data = [[
            "Nombre", "Identificación", "Lista", "Tipo", "Fecha Ingreso"
        ]]

        for persona in personas:
            row = [
                Paragraph(str(persona.nombre), styles["Normal"]),
                Paragraph(str(persona.identificacion), styles["Normal"]),
                Paragraph(str(persona.lista.nombre), styles["Normal"]),
                Paragraph(str(persona.lista.tipo), styles["Normal"]),
                Paragraph(str(persona.fecha_ingreso), styles["Normal"]),
            ]
            data.append(row)

        table = Table(data, colWidths=[90, 80, 100, 80, 80])  # Ajusta los anchos según necesidad

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        perfil.reportes_generados += 1
        perfil.save()
        
        return HttpResponse(buffer, content_type='application/pdf')
    

def generar_pdf_ia(request):
    perfil = PerfilUsuario.objects.get(user=request.user)

    if perfil.reportes_generados >= perfil.limite_reportes:
        return HttpResponse("Has alcanzado tu límite de generación de reportes.", status=403)
    
    if request.method == "POST":
        ids = request.POST.getlist('personas')
        personas = PersonaLista.objects.filter(id__in=ids)

        # Generar texto plano de las personas para la IA
        texto = ""
        for persona in personas:
            texto += f"Nombre: {persona.nombre}, Identificación: {persona.identificacion}, Lista: {persona.lista.nombre}, Tipo: {persona.lista.tipo}, Fecha Ingreso: {persona.fecha_ingreso}\n"

        # Llamar a Ollama Gemma2 para resumir
        try:
            response = requests.post(
                "http://localhost:11434/v1/completions",
                json={
                    "model": "gemma:2b",
                    "prompt": f"Genera un reporte analítico SARLAFT en texto plano, sin símbolos, sin asteriscos ni Markdown. Presenta la información de manera clara y profesional, con encabezados y párrafos, listo para un PDF. Información de personas:\n{texto}",
                    "stream": False
                }
            )
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                resumen = data["choices"][0]["text"]
            else:
                resumen = "No se pudo generar el resumen con IA."
        except Exception as e:
            resumen = f"No se pudo generar el resumen con IA. Error: {str(e)}"

        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        title = Paragraph("Reporte NovaSAR con Resumen IA", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Agregar resumen al PDF
        elements.append(Paragraph("Resumen generado por IA:", styles["Heading2"]))
        elements.append(Paragraph(resumen, styles["Normal"]))
        elements.append(Spacer(1, 12))

        # Crear tabla con los datos
        data_table = [[
            "Nombre", "Identificación", "Lista", "Tipo", "Fecha Ingreso"
        ]]
        for persona in personas:
            row = [
                Paragraph(str(persona.nombre), styles["Normal"]),
                Paragraph(str(persona.identificacion), styles["Normal"]),
                Paragraph(str(persona.lista.nombre), styles["Normal"]),
                Paragraph(str(persona.lista.tipo), styles["Normal"]),
                Paragraph(str(persona.fecha_ingreso), styles["Normal"]),
            ]
            data_table.append(row)

        table = Table(data_table, colWidths=[90, 80, 100, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        perfil.reportes_generados += 1
        perfil.save()

        return HttpResponse(buffer, content_type='application/pdf')

    # Si no es POST, también debes retornar algo
    return HttpResponse("Método no permitido", status=405)
