import csv
import pyproj
import folium
import webbrowser
import os
import pandas as pd

def crear_mapa_osm(datos_resumen):
    # --- Configuración ---
    archivo_gpon = 'CajasGPON_202508.txt'
    archivo_salida_html = 'index.html'

    # --- Proyección de coordenadas ---
    # UTM zona 17S (EPSG:32717) a WGS84 (lat/lon) (EPSG:4326)
    try:
        transformer = pyproj.Transformer.from_crs("epsg:32717", "epsg:4326", always_xy=True)
    except Exception as e:
        print(f"Error al crear el transformador de coordenadas: {e}")
        print("Asegúrate de que la librería 'pyproj' está instalada (`pip install pyproj`).")
        return

    # 1. Cargar coordenadas del archivo GPON
    coordenadas_gpon = {}
    try:
        with open(archivo_gpon, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tag = row.get('Tag', '').replace('"', '').strip()
                coord_x = row.get('Coord_X')
                coord_y = row.get('Coord_Y')
                if tag and coord_x and coord_y:
                    try:
                        coordenadas_gpon[tag] = (float(coord_x), float(coord_y))
                    except (ValueError, TypeError):
                        # Ignorar si las coordenadas no son números válidos
                        continue
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {archivo_gpon}")
        return
    except Exception as e:
        print(f"Error al leer {archivo_gpon}: {e}")
        return

    # 2. Procesar el resumen, unir datos y preparar los puntos para el mapa
    puntos_mapa = []
    for row in datos_resumen:
        try:
            # Asegurarse de que los valores no sean nulos (NaN) que puede venir de pandas
            nodo = str(row.get('Nodo', '')).strip() if pd.notna(row.get('Nodo')) else ''
            distrito = str(row.get('Distrito', '')).strip() if pd.notna(row.get('Distrito')) else ''
            caja = str(row.get('Caja', '')).strip() if pd.notna(row.get('Caja')) else ''
            
            if not (nodo and distrito and caja):
                continue

            tag_union = f"{nodo},{distrito},{caja},"

            if tag_union in coordenadas_gpon:
                utm_x, utm_y = coordenadas_gpon[tag_union]
                lon, lat = transformer.transform(utm_x, utm_y)
                
                info_html = f"<b>Caja:</b> {caja}<br><b>Nodo:</b> {nodo}<br><b>Distrito:</b> {distrito}"
                puntos_mapa.append({
                    'lat': lat,
                    'lon': lon,
                    'info': info_html
                })
        except Exception:
            # Ignorar errores en filas individuales para no detener todo el proceso
            continue
            
    if not puntos_mapa:
        print("No se encontraron cajas para mostrar en el mapa.")
        return

    # 3. Generar el mapa con Folium
    # Calcular el centro del mapa
    avg_lat = sum(p['lat'] for p in puntos_mapa) / len(puntos_mapa)
    avg_lon = sum(p['lon'] for p in puntos_mapa) / len(puntos_mapa)
    
    # Crear el mapa
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=14)

    # Añadir marcadores
    for punto in puntos_mapa:
        folium.Marker(
            location=[punto['lat'], punto['lon']],
            popup=folium.Popup(punto['info'], max_width=300)
        ).add_to(m)

    try:
        # Guardar el mapa en un archivo HTML
        m.save(archivo_salida_html)
        print(f"Se ha generado el archivo '{archivo_salida_html}' con {len(puntos_mapa)} puntos.")
        
        # Abrir el archivo en el navegador
        webbrowser.open('file://' + os.path.realpath(archivo_salida_html))

    except Exception as e:
        print(f"Error al guardar o abrir el archivo HTML: {e}")

if __name__ == '__main__':
    # URL de OneDrive que apunta al archivo CSV.
    url_onedrive = 'https://1drv.ms/x/c/4049d6b4b6ccf513/IQTnY0C0DDmfQbsFBgH6Dyw6AcG-W7q8cCBMz3EJgc1q8sk'

    print(f"Descargando el archivo de resumen CSV desde OneDrive...")

    datos_resumen = []
    try:
        # Leer el contenido del CSV directamente desde la URL.
        # pandas se encarga de la descarga y lectura del archivo.
        df = pd.read_csv(url_onedrive)

        # Convertir el DataFrame a una lista de diccionarios, 
        # que es el formato que la función crear_mapa_osm espera.
        datos_resumen = df.to_dict('records')
        print("Archivo CSV descargado y procesado correctamente.")

    except Exception as e:
        print(f"Error al descargar o procesar el archivo CSV desde la URL: {e}")
        print("Por favor, asegúrate de que la URL es una URL de descarga directa de un archivo CSV.")
        print("También, asegúrate de tener instalada la librería 'pandas' (`pip install pandas`).")
        exit()

    # --- Crear mapa ---
    if datos_resumen:
        crear_mapa_osm(datos_resumen)
