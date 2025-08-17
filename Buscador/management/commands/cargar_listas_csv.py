import csv
from django.core.management.base import BaseCommand
from Buscador.models import Lista, PersonaLista
from datetime import datetime
from django.db import transaction

class Command(BaseCommand):
    help = 'Sincroniza las personas desde un archivo CSV (agrega, actualiza y elimina)'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str, help='Ruta al archivo CSV a cargar')

    def handle(self, *args, **kwargs):
        archivo_csv = kwargs['archivo_csv']

        with open(archivo_csv, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            print("Encabezados:", reader.fieldnames)

            # Guardaremos las IDs de listas y personas para eliminar lo que no esté en el CSV
            listas_csv = set()
            personas_csv = set()

            # Usamos transacción para consistencia
            with transaction.atomic():
                for row in reader:
                    try:
                        nombre_lista = row['lista']
                        tipo_lista = row['tipo_lista']
                        fuente = row['fuente']
                        fecha_ingreso = datetime.strptime(row['fecha_ingreso'], '%d/%m/%Y').date()
                        nombre = row['nombre']
                        identificacion = row.get('identificacion', '')
                    except KeyError as e:
                        print(f"❌ Error en la clave del CSV: {e}")
                        continue
                    except ValueError as e:
                        print(f"❌ Error en formato de fecha: {e}")
                        continue

                    # --- Listas ---
                    lista_obj, _ = Lista.objects.update_or_create(
                        nombre=nombre_lista,
                        defaults={
                            'tipo': tipo_lista,
                            'fuente': fuente,
                        }
                    )
                    listas_csv.add(lista_obj.id)

                    # --- Personas ---
                    persona = PersonaLista.objects.create(
                        nombre=nombre,
                        identificacion=identificacion,
                        lista=lista_obj,
                        fecha_ingreso=fecha_ingreso
                    )
                    personas_csv.add(persona.id)

                # --- Eliminar personas antiguas que ya no están en el CSV, por lista ---
                # Solo eliminamos personas de las listas presentes en el CSV
                for lista_id in listas_csv:
                    PersonaLista.objects.filter(lista_id=lista_id).exclude(id__in=personas_csv).delete()

        self.stdout.write(self.style.SUCCESS(
            f"✅ Sincronización completada.\n"
            f"Listas procesadas: {len(listas_csv)} | Personas insertadas: {len(personas_csv)}"
        ))
