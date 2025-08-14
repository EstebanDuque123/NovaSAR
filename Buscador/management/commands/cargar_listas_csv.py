import csv
from django.core.management.base import BaseCommand
from Buscador.models import Lista, PersonaLista
from datetime import datetime

class Command(BaseCommand):
    help = 'Carga masiva de personas desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str, help='Ruta al archivo CSV a cargar')

    def handle(self, *args, **kwargs):
        archivo_csv = kwargs['archivo_csv']

        # Usa la codificación 'utf-8-sig' para eliminar el BOM
        with open(archivo_csv, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')  # Usamos el delimitador de punto y coma
            
            # Imprime los nombres de las columnas (encabezados) para ver si son correctos
            print("Encabezados:", reader.fieldnames)

            total = 0
            for row in reader:
                # Imprime cada fila para depuración
                print(row)
                
                try:
                    nombre_lista = row['lista']
                    tipo_lista = row['tipo_lista']
                    fuente = row['fuente']
                except KeyError as e:
                    print(f"Error en la clave: {e}")
                    continue

                lista_obj, _ = Lista.objects.get_or_create(
                    nombre=nombre_lista,
                    defaults={
                        'tipo': tipo_lista,
                        'fuente': fuente,
                    }
                )

                fecha_ingreso = datetime.strptime(row['fecha_ingreso'], '%d/%m/%Y').date()

                PersonaLista.objects.create(
                    nombre=row['nombre'],
                    identificacion=row.get('identificacion', ''),
                    lista=lista_obj,
                    fecha_ingreso=fecha_ingreso
                )
                total += 1

        self.stdout.write(self.style.SUCCESS(f'Se cargaron {total} registros desde {archivo_csv}'))
