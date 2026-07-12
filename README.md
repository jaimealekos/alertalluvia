# alertalluvia

Monitor de lluvia intensa para estaciones meteorológicas personales de [Weather Underground](https://www.wunderground.com/).

Extrae la hora, la intensidad de lluvia (*Precip. Rate*) y el agua acumulada (*Precip. Accum.*) de las últimas 24 horas de una estación de wunderground.com y, para cada registro, calcula el **agua acumulada durante la última hora**. Si ese valor supera el umbral configurado, muestra una **alerta roja**. También marca en rojo la intensidad y el acumulado total cuando superan sus propios umbrales.

Todos los valores se muestran en milímetros.

```text
HORA                       PRECIP. RATE   P. ACUM        P. ACUM/HORA
2026-07-12 07:24           0.76           6.35           4.56
2026-07-12 07:29           0.76           6.35           5.32            ALERTA > 5.0mm/hora
2026-07-12 07:34           0.76           6.35           6.08            ALERTA > 5.0mm/hora
```

## Requisitos

- Python 3.8 o superior
- [requests](https://pypi.org/project/requests/)

## Instalación

```bash
git clone https://github.com/jaimealekos/alertalluvia.git
cd alertalluvia
pip install -r requirements.txt
```

## Uso

```bash
python alertalluvia.py <ID de estación> [opciones]
```

Ejemplo:

```bash
python alertalluvia.py ICHIVA39
```

El ID de cualquier estación meteorológica puede consultarse en el [Wundermap](https://www.wunderground.com/wundermap).

### Opciones

| Opción | Descripción | Por defecto |
|---|---|---|
| `--umbral-hora MM` | Umbral de alerta para el agua acumulada en una hora (mm) | 90 |
| `--umbral-rate MM` | Umbral de alerta para la intensidad de lluvia (mm) | 60 |
| `--umbral-total MM` | Umbral de alerta para el agua acumulada total (mm) | 250 |
| `--version` | Muestra la versión | |
| `-h`, `--help` | Muestra la ayuda | |

Ejemplo con umbrales personalizados:

```bash
python alertalluvia.py ICHIVA39 --umbral-hora 60 --umbral-total 150
```

## Cómo funciona

Desde 2025, wunderground.com ya no incluye la tabla de datos en el HTML de sus páginas (se rellena con JavaScript), por lo que el programa obtiene las observaciones de la misma API JSON que utiliza la propia web, usando su clave pública, que se extrae automáticamente de la página de la estación.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## Autor

**Jaime Alekos** — [jaimealekos.com](http://www.jaimealekos.com) — contacto [arroba] jaimealekos [punto] com
