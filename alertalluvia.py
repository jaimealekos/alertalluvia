#  ▄▄▄      ██▓   ▓█████ ██▀███ ▄▄▄█████▓▄▄▄      ██▓    ██▓    █    ██ ██▒   █▓██▓▄▄▄      
# ▒████▄   ▓██▒   ▓█   ▀▓██ ▒ ██▓  ██▒ ▓▒████▄   ▓██▒   ▓██▒    ██  ▓██▓██░   █▓██▒████▄    
# ▒██  ▀█▄ ▒██░   ▒███  ▓██ ░▄█ ▒ ▓██░ ▒▒██  ▀█▄ ▒██░   ▒██░   ▓██  ▒██░▓██  █▒▒██▒██  ▀█▄  
# ░██▄▄▄▄██▒██░   ▒▓█  ▄▒██▀▀█▄ ░ ▓██▓ ░░██▄▄▄▄██▒██░   ▒██░   ▓▓█  ░██░ ▒██ █░░██░██▄▄▄▄██ 
#  ▓█   ▓██░██████░▒████░██▓ ▒██▒ ▒██▒ ░ ▓█   ▓██░██████░██████▒▒█████▓   ▒▀█░ ░██░▓█   ▓██▒
#  ▒▒   ▓▒█░ ▒░▓  ░░ ▒░ ░ ▒▓ ░▒▓░ ▒ ░░   ▒▒   ▓▒█░ ▒░▓  ░ ▒░▓  ░▒▓▒ ▒ ▒   ░ ▐░ ░▓  ▒▒   ▓▒█░
#   ▒   ▒▒ ░ ░ ▒  ░░ ░  ░ ░▒ ░ ▒░   ░     ▒   ▒▒ ░ ░ ▒  ░ ░ ▒  ░░▒░ ░ ░   ░ ░░  ▒ ░ ▒   ▒▒ ░
#   ░   ▒    ░ ░     ░    ░░   ░  ░       ░   ▒    ░ ░    ░ ░   ░░░ ░ ░     ░░  ▒ ░ ░   ▒   
#       ░  ░   ░  ░  ░  ░  ░                  ░  ░   ░  ░   ░  ░  ░          ░  ░       ░  ░
#                                                                           ░               
#
# alertalluvia 0.1 por Jaime Alekos - 27/Nov/2024 - http://www.jaimealekos.com - contacto [arroba] jaimealekos [punto] com
#
# Extrae los valores 'Time', 'Precip. Rate' y 'Precip. Accum.' de las últimas 24h de una estación meteorológica de wunderground.com
# Para cada fila de datos, genera una cuarta columna, 'Precip. Accum. / última hora'
# Si el valor de 'Precip. Accum. / última hora' supera un umbral definido por el usuario, muestra una alerta roja
# También marca en rojo 'Precip. Rate' y 'Precip. Accum.' cuando superan un umbral definido por el usuario
#
# Lista de estaciones meteorológicas de wunderground.com: https://www.wunderground.com/wundermap
#
# Uso: alertalluvia <ID de estación>
# Ejemplo: alertalluvia ICHIVA39
#

import re
import sys
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Configuración alertas - Agua en mm
umbral_lluvia_acumulada_por_hora = 300 
umbral_lluvia_ahora = 60
umbral_lluvia_acumulada_total = 250

# Convierte una hora en sistema horario de 12 horas a formato militar
def convertir_hora(fecha_hora_str):
    return datetime.strptime(fecha_hora_str, "%Y-%m-%d %I:%M %p")

# Extrae la fecha de los datos de la url de una estación meteorológica de wunderground.com
def extraer_fecha(texto):
    patron = r'\b(\d{4}-\d{2}-\d{2})\b'
    coincidencia = re.search(patron, texto)
    if coincidencia:
        return coincidencia.group(1)
    return None

# Extrae la tabla de datos de un día entero de la web de una estación meteorológica de wunderground.com
def extraer_estacion_wunderground(estacion, dia):
    url_tabla="https://www.wunderground.com/dashboard/pws/"+estacion+"/table/"+dia+"/"+dia+"/daily"
    respuesta = requests.get(url_tabla)

    if respuesta.status_code == 200:
        html = respuesta.text

        sopa = BeautifulSoup(html, 'html.parser')
        tablas = sopa.find_all('table', class_='history-table')

        # La tabla HTML que contiene los datos es la segunda
        if len(tablas) >= 2:
            tabla = tablas[1]
            filas = []
            fecha = extraer_fecha(url_tabla)

            for tr in tabla.find_all('tr')[1:]:            
                td_elements = tr.find_all('td')

                if td_elements:
                    fila = [td.text.strip() for td in td_elements]
                    fila[0] = f"{fecha} {fila[0]}"
                    filas.append(fila)
            return filas

def extraer_lluvia(filas):
    #Extrae 'HORA', 'PRECIP.RATE' y 'PRECIP. ACUM' de la tabla completa de datos

    lluvia = []

    for fila in filas:
        fecha_hora = str(fila[0])
        precip = round(float(str(fila[8])[:-4]) * 25.4, 2)
        precip_accum = round(float(str(fila[9])[:-4]) * 25.4, 2)

        nueva_fila = [fecha_hora, precip, precip_accum]
        lluvia.append(nueva_fila)    

    ultima_hora = []
    tabla_con_acumulado_hora = []   

    # Añade la columna 'P. ACUM/HORA' al final

    for fila in lluvia:
        fecha_hora_str, lluvia_rate, lluvia_acum = fila  # Desempaquetar fila

        # Convierte la hora
        fecha_hora = convertir_hora(fecha_hora_str)

        # Eliminar registros fuera de la última hora
        ultima_hora = [(h, l) for h, l in ultima_hora if h > fecha_hora - timedelta(hours=1)]

        # Añadir el nuevo registro
        ultima_hora.append((fecha_hora, lluvia_rate))

        # Calcular agua acumulada
        acumulado_hora = sum(l for _, l in ultima_hora)

        # Añadir la nueva fila con el acumulado
        tabla_con_acumulado_hora.append([fecha_hora_str, lluvia_rate, lluvia_acum, round(acumulado_hora, 2)])     

    return tabla_con_acumulado_hora

def mostrar_lluvia_con_formato(tabla):
    NEGRITA = "\033[1m"
    RESET = "\033[0m"
    VERDE = "\033[32m"
    ROHO = "\033[31m"

    # Calcular el límite de tiempo (últimas 24 horas)
    ahora = datetime.now()
    hace_24_horas = ahora - timedelta(hours=24)

    # Anchos de columna
    ancho_columnas = [27, 15, 15, 15]

    # Imprimir encabezados
    encabezados = ["HORA", "PRECIP. RATE", "P. ACUM", "P. ACUM/HORA"]
    encabezado_formateado = "".join(f"{enc[:w]:<{w}}" for enc, w in zip(encabezados, ancho_columnas))
    print(NEGRITA + encabezado_formateado + RESET)

    # Procesar y mostrar cada fila
    for fila in tabla:
        # Convertir la hora de la primera columna al formato datetime
        fecha_hora_str = fila[0]
        dt_obj = datetime.strptime(fecha_hora_str, "%Y-%m-%d %I:%M %p")
        
        # Filtrar solo filas dentro de las últimas 24 horas
        if dt_obj >= hace_24_horas:
            salida_fila = ""

            # Convertir la hora al formato militar
            hora_militar = dt_obj.strftime("%Y-%m-%d %H:%M")
            salida_fila += f"{NEGRITA}{hora_militar:<{ancho_columnas[0]}}{RESET}"

            # Segunda columna: float con color según valor
            color = VERDE if fila[1] < umbral_lluvia_ahora else ROHO
            salida_fila += f"{color}{fila[1]:<{ancho_columnas[1]}.2f}{RESET}"

            # Tercera columna: float con color según valor
            color = VERDE if fila[2] < umbral_lluvia_acumulada_total else ROHO
            salida_fila += f"{color}{fila[2]:<{ancho_columnas[2]}.2f}{RESET}"

            # Cuarta columna: float con color y formato según valor
            if fila[3] < umbral_lluvia_acumulada_por_hora:
                color = VERDE
                salida_fila += f"{color}{fila[3]:<{ancho_columnas[3]}.2f}{RESET}"
            else:
                color = f"{ROHO}{NEGRITA}"
                salida_fila += f"{color}{fila[3]:<15.2f} ALERTA > "+str(umbral_lluvia_acumulada_por_hora)+f"mm/hora{RESET}"

            print(salida_fila)

if __name__ == "__main__":    
    if len(sys.argv) > 1:
        hoy = datetime.now().strftime('%Y-%m-%d')
        ayer = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        datos_hoy = extraer_estacion_wunderground(sys.argv[1], hoy)
        datos_ayer = extraer_estacion_wunderground(sys.argv[1], ayer)

        tabla_lluvia =  extraer_lluvia(datos_ayer + datos_hoy)

        mostrar_lluvia_con_formato(tabla_lluvia)

    else:
        print("\nNo se proporcionó ningún argumento\n\nUso: alertalluvia <ID de estación>\n")
