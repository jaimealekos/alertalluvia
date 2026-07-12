#!/usr/bin/env python3
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
"""alertalluvia — Alerta de lluvia intensa en estaciones de Weather Underground.

Extrae la hora, la intensidad de lluvia ('Precip. Rate') y el agua acumulada
('Precip. Accum.') de las últimas 24 horas de una estación meteorológica de
wunderground.com y, para cada registro, calcula una cuarta columna: el agua
acumulada durante la última hora.

Si el agua acumulada en una hora supera el umbral configurado, muestra una
alerta roja. También marca en rojo 'Precip. Rate' y 'Precip. Accum.' cuando
superan sus propios umbrales.

Lista de estaciones meteorológicas: https://www.wunderground.com/wundermap

Uso:
    alertalluvia.py <ID de estación> [opciones]

Ejemplo:
    alertalluvia.py ICHIVA39

Autor: Jaime Alekos - http://www.jaimealekos.com - contacto [arroba] jaimealekos [punto] com
"""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta

import requests

__version__ = "0.2"

# Umbrales de alerta por defecto (agua en mm)
UMBRAL_LLUVIA_ACUMULADA_POR_HORA = 90
UMBRAL_LLUVIA_AHORA = 60
UMBRAL_LLUVIA_ACUMULADA_TOTAL = 250

# wunderground.com ya no incluye la tabla de datos en el HTML de la página
# (se rellena con JavaScript), así que los datos se piden a la misma API JSON
# que usa la web. La clave pública de la API se extrae de la página de la
# estación; si no se encuentra, se usa esta última clave conocida.
URL_DASHBOARD = "https://www.wunderground.com/dashboard/pws/{estacion}"
URL_API = ("https://api.weather.com/v2/pws/history/all"
           "?stationId={estacion}&format=json&units=m&date={dia}&apiKey={api_key}")
API_KEY_CONOCIDA = "e1f10a1e78da46f5b10a1e78da96f525"

TIMEOUT_SEGUNDOS = 30

# Códigos de escape ANSI para el formato de la salida
NEGRITA = "\033[1m"
RESET = "\033[0m"
VERDE = "\033[32m"
ROJO = "\033[31m"


def convertir_hora(fecha_hora_str):
    """Convierte una cadena 'AAAA-MM-DD HH:MM:SS' en un objeto datetime."""
    return datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M:%S")


def obtener_api_key(estacion):
    """Extrae la clave pública de la API de la página de la estación.

    Si no se puede descargar la página o no contiene ninguna clave, devuelve
    la última clave pública conocida.
    """
    try:
        respuesta = requests.get(URL_DASHBOARD.format(estacion=estacion), timeout=TIMEOUT_SEGUNDOS)
        respuesta.raise_for_status()
    except requests.RequestException:
        return API_KEY_CONOCIDA

    coincidencia = re.search(r"apiKey=([0-9a-f]{32})", respuesta.text)
    if coincidencia:
        return coincidencia.group(1)
    return API_KEY_CONOCIDA


def extraer_estacion_wunderground(estacion, dia, api_key):
    """Descarga las observaciones de un día entero de una estación de wunderground.com.

    Devuelve una lista de filas [fecha y hora, intensidad de lluvia en mm,
    agua acumulada en mm]. Las observaciones sin datos de precipitación se
    descartan.
    """
    url = URL_API.format(estacion=estacion, dia=dia.replace("-", ""), api_key=api_key)

    try:
        respuesta = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
        respuesta.raise_for_status()
    except requests.RequestException as error:
        sys.exit(f"Error al descargar los datos de la estación '{estacion}': {error}")

    # La API devuelve 204 (sin contenido) si la estación no tiene datos ese día
    if respuesta.status_code == 204:
        return []

    observaciones = respuesta.json().get("observations") or []
    filas = []

    for observacion in observaciones:
        fecha_hora = observacion.get("obsTimeLocal")
        metrica = observacion.get("metric") or {}
        lluvia_rate = metrica.get("precipRate")
        lluvia_acum = metrica.get("precipTotal")

        if fecha_hora and lluvia_rate is not None and lluvia_acum is not None:
            filas.append([fecha_hora, round(lluvia_rate, 2), round(lluvia_acum, 2)])

    return filas


def calcular_acumulado_por_hora(filas):
    """Añade a cada fila una cuarta columna con el agua acumulada en la última hora."""
    ultima_hora = []
    tabla_con_acumulado_hora = []

    for fecha_hora_str, lluvia_rate, lluvia_acum in filas:
        fecha_hora = convertir_hora(fecha_hora_str)

        # Descarta los registros anteriores a la última hora
        ultima_hora = [(h, l) for h, l in ultima_hora if h > fecha_hora - timedelta(hours=1)]

        # Añade el nuevo registro y calcula el agua acumulada en la última hora
        ultima_hora.append((fecha_hora, lluvia_rate))
        acumulado_hora = sum(l for _, l in ultima_hora)

        tabla_con_acumulado_hora.append([fecha_hora_str, lluvia_rate, lluvia_acum, round(acumulado_hora, 2)])

    return tabla_con_acumulado_hora


def mostrar_lluvia_con_formato(tabla, umbral_hora, umbral_ahora, umbral_total):
    """Muestra la tabla de lluvia de las últimas 24 horas, coloreando cada valor
    en verde o rojo según los umbrales de alerta."""
    hace_24_horas = datetime.now() - timedelta(hours=24)

    ancho_columnas = [27, 15, 15, 15]

    encabezados = ["HORA", "PRECIP. RATE", "P. ACUM", "P. ACUM/HORA"]
    encabezado_formateado = "".join(f"{enc[:w]:<{w}}" for enc, w in zip(encabezados, ancho_columnas))
    print(NEGRITA + encabezado_formateado + RESET)

    for fecha_hora_str, lluvia_rate, lluvia_acum, acumulado_hora in tabla:
        fecha_hora = convertir_hora(fecha_hora_str)

        # Muestra solo las filas de las últimas 24 horas
        if fecha_hora < hace_24_horas:
            continue

        hora = fecha_hora.strftime("%Y-%m-%d %H:%M")
        salida_fila = f"{NEGRITA}{hora:<{ancho_columnas[0]}}{RESET}"

        color = VERDE if lluvia_rate < umbral_ahora else ROJO
        salida_fila += f"{color}{lluvia_rate:<{ancho_columnas[1]}.2f}{RESET}"

        color = VERDE if lluvia_acum < umbral_total else ROJO
        salida_fila += f"{color}{lluvia_acum:<{ancho_columnas[2]}.2f}{RESET}"

        if acumulado_hora < umbral_hora:
            salida_fila += f"{VERDE}{acumulado_hora:<{ancho_columnas[3]}.2f}{RESET}"
        else:
            salida_fila += f"{ROJO}{NEGRITA}{acumulado_hora:<{ancho_columnas[3]}.2f} ALERTA > {umbral_hora}mm/hora{RESET}"

        print(salida_fila)


def crear_parser():
    """Define los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="alertalluvia",
        description="Alerta de lluvia intensa a partir de los datos de las últimas 24 horas "
                    "de una estación meteorológica de wunderground.com.",
        epilog="Lista de estaciones meteorológicas: https://www.wunderground.com/wundermap",
    )
    parser.add_argument("estacion", metavar="ESTACION",
                        help="ID de la estación meteorológica (ejemplo: ICHIVA39)")
    parser.add_argument("--umbral-hora", type=float, default=UMBRAL_LLUVIA_ACUMULADA_POR_HORA, metavar="MM",
                        help="umbral de alerta para el agua acumulada en una hora, en mm (por defecto: %(default)s)")
    parser.add_argument("--umbral-rate", type=float, default=UMBRAL_LLUVIA_AHORA, metavar="MM",
                        help="umbral de alerta para la intensidad de lluvia, en mm (por defecto: %(default)s)")
    parser.add_argument("--umbral-total", type=float, default=UMBRAL_LLUVIA_ACUMULADA_TOTAL, metavar="MM",
                        help="umbral de alerta para el agua acumulada total, en mm (por defecto: %(default)s)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main():
    argumentos = crear_parser().parse_args()

    # Habilita los códigos de escape ANSI en la consola de Windows
    if os.name == "nt":
        os.system("")

    hoy = datetime.now().strftime("%Y-%m-%d")
    ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    api_key = obtener_api_key(argumentos.estacion)

    filas = (extraer_estacion_wunderground(argumentos.estacion, ayer, api_key)
             + extraer_estacion_wunderground(argumentos.estacion, hoy, api_key))

    if not filas:
        sys.exit(f"La estación '{argumentos.estacion}' no ha devuelto datos. "
                 "Comprueba que el ID es correcto y que la estación está en línea.")

    tabla_lluvia = calcular_acumulado_por_hora(filas)

    mostrar_lluvia_con_formato(tabla_lluvia, argumentos.umbral_hora, argumentos.umbral_rate, argumentos.umbral_total)


if __name__ == "__main__":
    main()
