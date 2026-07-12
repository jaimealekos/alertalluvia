# Changelog

## [0.2] - 2026-07-13

### Corregido

- wunderground.com dejó de incluir la tabla de datos en el HTML de sus páginas
  (ahora se rellena con JavaScript), lo que dejó de funcionar el scraping de la
  versión 0.1. Los datos se obtienen ahora de la misma API JSON que utiliza la
  propia web, usando su clave pública, que se extrae automáticamente de la
  página de la estación.
- La conversión de pulgadas a milímetros de la versión 0.1 truncaba un decimal
  de cada valor. Ya no es necesaria: la API devuelve los valores directamente
  en milímetros.

### Añadido

- Interfaz de línea de comandos con `argparse`: ayuda (`--help`), versión
  (`--version`) y umbrales de alerta configurables (`--umbral-hora`,
  `--umbral-rate`, `--umbral-total`) sin tener que editar el código.
- Manejo de errores: tiempo de espera y errores de red, estación inexistente
  o sin datos, y registros sin datos de precipitación.
- Compatibilidad con los colores ANSI en la consola clásica de Windows.
- `README.md`, `LICENSE` (MIT), `requirements.txt`, `CHANGELOG.md` y
  `.gitignore`.

### Cambiado

- Código reorganizado según PEP 8: constantes en mayúsculas, funciones con
  docstrings, punto de entrada `main()` y correcciones menores de estilo.
- El umbral de alerta por hora por defecto pasa de 300 a 90 mm.

## [0.1] - 2024-11-27

- Versión inicial.
