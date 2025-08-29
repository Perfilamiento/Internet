import csv
import pyproj
import folium
import webbrowser
import os
import glob

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
            nodo = row.get('Nodo', '').strip()
            distrito = row.get('Distrito', '').strip()
            caja = row.get('Caja', '').strip()
            
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
    # --- Encontrar el archivo de resumen más reciente ---
    lista_archivos = sorted(glob.glob('resumen_cajas_*.csv'))
    if not lista_archivos:
        print("Error: No se encontraron archivos con el patrón 'resumen_cajas_*.csv'")
        exit()
    
    archivo_resumen = lista_archivos[-1]
    print(f"Usando el archivo de resumen más reciente: {archivo_resumen}")

    # --- Cargar datos del resumen ---
    datos_resumen = []
    try:
        with open(archivo_resumen, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            datos_resumen = list(reader)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {archivo_resumen}")
    except Exception as e:
        print(f"Error al leer {archivo_resumen}: {e}")

    # --- Crear mapa ---
    if datos_resumen:
        crear_mapa_osm(datos_resumen)