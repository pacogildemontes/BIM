# BIM
Repositorio con documentación y recursos para la definición del apartado de benchmark de equipos Beam.

## Documentación disponible
- [Benchmark Beam para Equipos de Visualización BIM](docs/benchmark-beam.md): guía detallada sobre métricas, sistema de puntuación, presentación del informe y recomendaciones de mejora.

## Benchmark automatizado

El directorio `beam_benchmark` incluye un script en Python que ejecuta pruebas sintéticas de CPU, memoria, almacenamiento, GPU (detección) y red para generar un informe resumido. Requisitos:

```bash
pip install -r requirements.txt
# Opcional para pruebas de red: instalar speedtest-cli (según plataforma)
# sudo apt install speedtest-cli
```

Ejemplo de ejecución mostrando la salida en Markdown:

```bash
python -m beam_benchmark --format markdown --skip-network --skip-gpu
```

Parámetros útiles:

- `--skip-network` y `--skip-gpu` para omitir pruebas que puedan necesitar permisos adicionales.
- `--cpu-duration` ajusta la duración (en segundos) de las pruebas de CPU.
- `--cpu-workers` limita el número máximo de procesos en el test multinúcleo.
- `--disk-size` define el tamaño del archivo temporal usado en el test de almacenamiento.
- `--format json` genera un JSON fácil de integrar en la web.
- `--output informe.md` guarda el resultado en un archivo.
