# BIM
codex/create-pc-benchmark-section-for-beam-rfu5ta
Repositorio con documentación y recursos para la definición del apartado de benchmark de equipos Beam.

## Documentación disponible
- [Benchmark Beam para Equipos de Visualización BIM](docs/benchmark-beam.md): guía detallada sobre métricas, sistema de puntuación, presentación del informe y recomendaciones de mejora.
- [Hub de finanzas personales](docs/finanzas.md): app web local para centralizar cuentas, patrimonio y calendario de obligaciones (seguros, IBI, impuestos…).

## Hub de finanzas personales

App web (Flask + SQLite) para tener en un solo sitio cuentas bancarias y de inversión,
**viviendas** (ficha por inmueble con sus suministros, gastos y rentabilidad de alquiler),
una **cartera de inversión** que replica y simula tu plan de ETFs/fondos, y un
**calendario de vencimientos** (seguros, IBI, IRPF, IVA trimestral…), con importación
de extractos en CSV. Los datos se guardan en un fichero local `finanzas.db` (no se sube
al repositorio). Lista para desplegar gratis en Render (ver [docs/finanzas.md](docs/finanzas.md)).

```bash
pip install -r requirements.txt
python run.py
# Abre http://127.0.0.1:5000  (usa --host 0.0.0.0 para entrar desde el móvil)
```

Más detalles y roadmap (incluida la conexión bancaria automática vía Open Banking)
en [docs/finanzas.md](docs/finanzas.md).

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


Repositorio con documentación y recursos para la definición del apartado de benchmark de equipos Beam.

## Documentación disponible

- [Benchmark Beam para Equipos de Visualización BIM](docs/benchmark-beam.md): guía detallada sobre métricas, sistema de puntuación, presentación del informe y recomendaciones de mejora.
 main
