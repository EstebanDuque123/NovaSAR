import csv
from django.core.management.base import BaseCommand
from Buscador.models import Lista, PersonaLista
from datetime import datetime

class Command(BaseCommand):
    help = 'Sincroniza las personas desde un archivo CSV (agrega, actualiza y elimina)'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str, help='Ruta al archivo CSV a cargar')

    def handle(self, *args, **kwargs):
        archivo_csv = kwargs['archivo_csv']

        # Lee todo el CSV
        with open(archivo_csv, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')

            print("Encabezados:", reader.fieldnames)

            # Guardamos todos los IDs únicos del CSV para comparar luego
            personas_csv = []
            listas_csv = []

            for row in reader:
                try:
                    nombre_lista = row['lista']
                    tipo_lista = row['tipo_lista']
                    fuente = row['fuente']
                    fecha_ingreso = datetime.strptime(row['fecha_ingreso'], '%d/%m/%Y').date()
                    nombre = row['nombre']
                    identificacion = row.get('identificacion', '')
                except KeyError as e:
                    print(f"Error en la clave: {e}")
                    continue

                # --- Listas ---
                lista_obj, _ = Lista.objects.update_or_create(
                    nombre=nombre_lista,
                    defaults={
                        'tipo': tipo_lista,
                        'fuente': fuente,
                    }
                )
                listas_csv.append(lista_obj.id)

                # --- Personas ---
                persona, _ = PersonaLista.objects.update_or_create(
                    identificacion=identificacion,
                    lista=lista_obj,
                    defaults={
                        'nombre': nombre,
                        'fecha_ingreso': fecha_ingreso
                    }
                )
                personas_csv.append(persona.id)

            # --- Eliminar registros que ya no están en el CSV ---
            eliminadas_listas = Lista.objects.exclude(id__in=listas_csv).delete()
            eliminadas_personas = PersonaLista.objects.exclude(id__in=personas_csv).delete()

        self.stdout.write(self.style.SUCCESS(
            f"✅ Sincronización completada.\n"
            f"Listas eliminadas: {eliminadas_listas[0]} | Personas eliminadas: {eliminadas_personas[0]}"
        ))
