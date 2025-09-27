# Benchmark Beam para Equipos de Visualización BIM

Este documento define la estructura funcional del apartado de benchmarking para tu página web dedicado a equipos destinados a trabajar con Beam. Incluye las métricas a analizar, el sistema de puntuación, la manera de presentar los resultados y propuestas de mejora futura.

## 1. Objetivos del benchmark

1. Evaluar la adecuación del hardware del equipo para flujos de trabajo con Beam.
2. Proporcionar métricas comparables y fáciles de interpretar para usuarios finales.
3. Ofrecer recomendaciones accionables de mejora según el tipo de proyecto y los recursos disponibles.

## 2. Flujo general del benchmark

1. **Recolección de datos** mediante pruebas automatizadas y consultas al sistema operativo.
2. **Ejecución de pruebas sintéticas** para CPU, RAM, GPU, almacenamiento y red.
3. **Normalización y puntuación** de cada métrica en una escala de 0 a 100.
4. **Cálculo de un índice global Beam** ponderado por la relevancia de cada componente.
5. **Generación del informe** con clasificación del equipo, recomendaciones rápidas y sugerencias de mejora a medio plazo.

## 3. Métricas y metodología

### 3.1 Procesador (CPU)

| Submétrica | Descripción | Herramienta sugerida | Ponderación |
|------------|-------------|----------------------|-------------|
| Rendimiento mononúcleo | Rendimiento para tareas de modelado geométrico y scripts en un solo hilo. | Cinebench R23, Geekbench Single-Core | 20 % |
| Rendimiento multinúcleo | Eficiencia en tareas paralelas como renderizados locales o cálculos masivos. | Cinebench R23 Multi-Core, Geekbench Multi-Core | 15 % |
| Eficiencia energética | Rendimiento por vatio para escenarios móviles. | Lectura de TDP vs. puntuación obtenida | 5 % |

**Puntuación**: Escalar resultados a una referencia (por ejemplo, 100 = workstation de gama alta actual). Aplicar interpolación lineal entre mínimos y máximos esperados.

### 3.2 Memoria RAM

| Submétrica | Descripción | Herramienta sugerida | Ponderación |
|------------|-------------|----------------------|-------------|
| Capacidad útil | Memoria disponible para modelos complejos (mínimo recomendado 32 GB). | Lectura del sistema | 10 % |
| Ancho de banda | Velocidad efectiva (MHz * canales). | AIDA64, PassMark Memory | 7 % |
| Latencia | Respuesta a acceso aleatorio. | AIDA64, LatencyMon | 3 % |

**Puntuación**: Comparar con objetivos (32 GB, 6000 MT/s, CL baja). Asignar 100 si iguala o supera los valores objetivo, 50 si cumple mínimos (16 GB, 3200 MT/s) y 0 en caso de insuficiencia severa (<8 GB).

### 3.3 Almacenamiento

| Submétrica | Descripción | Herramienta sugerida | Ponderación |
|------------|-------------|----------------------|-------------|
| Capacidad total | Espacio para bibliotecas de proyectos y texturas. | Lectura del sistema | 5 % |
| Velocidad de lectura secuencial | Carga de escenas grandes. | CrystalDiskMark, Blackmagic Disk Speed Test | 7 % |
| Velocidad de escritura secuencial | Exportación de renderizados y backups. | CrystalDiskMark, Blackmagic Disk Speed Test | 5 % |
| IOPS aleatorios | Fluidez en proyectos con muchos archivos pequeños. | CrystalDiskMark 4K | 3 % |

**Puntuación**: Establecer como referencia un SSD NVMe PCIe 4.0 (lecturas > 5000 MB/s). Discos duros mecánicos se ubicarán en el rango inferior (<20 puntos).

### 3.4 Tarjeta gráfica (GPU)

| Submétrica | Descripción | Herramienta sugerida | Ponderación |
|------------|-------------|----------------------|-------------|
| Rendimiento rasterizado | FPS en escenas típicas de Beam. | 3DMark Time Spy, Unigine Superposition | 12 % |
| Rendimiento ray tracing / path tracing | Capacidad para renderizado fotorrealista. | 3DMark Port Royal, OctaneBench | 8 % |
| Memoria de video (VRAM) | Capacidad máxima para texturas y modelos complejos. | Lectura del sistema | 5 % |

**Puntuación**: Normalizar contra una GPU objetivo (p. ej., NVIDIA RTX 4080 = 100). Penalizar si la VRAM es < 8 GB.

### 3.5 Red

| Submétrica | Descripción | Herramienta sugerida | Ponderación |
|------------|-------------|----------------------|-------------|
| Latencia (ping) | Interacción con servicios en la nube y colaboración. | Speedtest CLI | 3 % |
| Velocidad de descarga | Importación de modelos y texturas desde servidores remotos. | Speedtest CLI | 4 % |
| Velocidad de subida | Sincronización de proyectos. | Speedtest CLI | 3 % |
| Estabilidad | Jitter y pérdida de paquetes. | PingPlotter, mtr | 2 % |

**Puntuación**: Basada en estándares de trabajo remoto (ping < 20 ms = 100, > 100 ms = 0; descarga >= 300 Mbps = 100, etc.).

## 4. Cálculo de la puntuación global

1. Multiplicar la puntuación normalizada de cada submétrica por su ponderación.
2. Sumar resultados para cada componente (CPU, RAM, GPU, Almacenamiento, Red).
3. Calcular el índice global Beam: 

   ```
   Índice Beam = 0.40 * CPU + 0.20 * GPU + 0.15 * RAM + 0.15 * Almacenamiento + 0.10 * Red
   ```

   Ajustar pesos según el enfoque del estudio (por ejemplo, aumentar GPU para visualización avanzada).

4. Clasificar el equipo en uno de los rangos:

| Índice Beam | Clasificación | Descripción |
|-------------|---------------|-------------|
| 85 - 100 | **Elite** | Óptimo para proyectos complejos, render en tiempo real y VR. |
| 70 - 84 | **Profesional** | Adecuado para equipos multidisciplinares y proyectos grandes. |
| 55 - 69 | **Productivo** | Cumple con proyectos medios y renderizados ocasionales. |
| 40 - 54 | **Básico** | Recomendado para revisión y tareas ligeras. |
| < 40 | **Limitado** | Necesita actualizaciones significativas para Beam. |

## 5. Informe final

El informe generado debe incluir:

1. **Resumen ejecutivo** con el Índice Beam, clasificación y principales puntos fuertes/débiles.
2. **Detalle por componente**: tablas con puntuaciones y valores medidos, gráficas de barras comparativas respecto a los objetivos.
3. **Compatibilidad con Beam**: escenarios recomendados (modelado, renderizado, colaboración en nube, VR/AR).
4. **Alertas críticas**: cuellos de botella que puedan impedir tareas clave.
5. **Recomendaciones** divididas en:
   - **Impacto inmediato** (mejoras rápidas con coste moderado, p. ej., añadir RAM, migrar a SSD NVMe).
   - **Plan estratégico** (upgrades a medio plazo: nueva GPU, migración a red 10 GbE, etc.).

## 6. Recomendaciones de mejora según tipo de proyecto

| Tipo de proyecto | Prioridades de mejora | Justificación |
|------------------|-----------------------|---------------|
| Modelado arquitectónico colaborativo | RAM (>= 32 GB), Red (baja latencia), CPU mononúcleo | Modelos complejos compartidos en tiempo real. |
| Renderizado fotorrealista | GPU ray tracing, CPU multinúcleo, almacenamiento rápido | Render local y cacheo de texturas pesadas. |
| Coordinación BIM y clash detection | CPU multinúcleo, RAM, SSD NVMe | Revisión de interferencias y cálculos intensivos. |
| Realidad virtual / recorridos en tiempo real | GPU rasterizado, VRAM, red estable | Fluidez y baja latencia en presentaciones inmersivas. |
| Trabajo remoto con nubes de puntos | GPU con VRAM alta, almacenamiento masivo, red de subida | Gestión de archivos pesados y sincronización. |

Cada recomendación debe incluir un **estimado de coste** (bajo, medio, alto) y un **impacto esperado** (incremento porcentual aproximado en el Índice Beam).

## 7. Plan de mejoras futuras para el benchmark

1. **Automatización y API**: Implementar scripts que integren resultados de herramientas externas mediante CLI para alimentar automáticamente la base de datos del sitio web.
2. **Historial de equipos**: Permitir comparar versiones previas del mismo equipo y visualizar la evolución de puntuaciones tras mejoras.
3. **Base de datos de referencia**: Publicar tablas con los equipos más habituales y sus puntuaciones para dar contexto al usuario.
4. **Métricas ambientales**: Incorporar medición de consumo energético y huella de carbono estimada durante las pruebas.
5. **Benchmarks personalizados**: Opción para seleccionar la ponderación según el perfil (arquitecto, visualizador, coordinador BIM).
6. **Integración con Beam**: Generar recomendaciones específicas dentro de la aplicación (por ejemplo, avisos de falta de RAM al abrir proyectos grandes).
7. **Alertas preventivas**: Monitorear temperaturas y ruido para detectar throttling y problemas de confort.

## 8. Consideraciones de implementación en la web

- **Interfaz**: Panel dividido en tarjetas para cada componente, con indicadores de color (verde/amarillo/rojo) y badges de clasificación.
- **Interactividad**: Posibilidad de filtrar por tipo de proyecto y recalcular pesos en tiempo real mediante sliders.
- **Exportación**: Generar PDF/HTML con el informe resumido para compartir con clientes o equipo técnico.
- **Accesibilidad**: Garantizar contraste y etiquetas descriptivas para todos los elementos visuales.
- **Actualización de datos**: Programar actualizaciones periódicas (por ejemplo, cada 6 meses) para recalibrar la escala con hardware nuevo.

## 9. Próximos pasos

1. Validar las ponderaciones con expertos de Beam y usuarios avanzados.
2. Seleccionar y automatizar las herramientas de benchmarking que mejor se integren con el flujo de trabajo.
3. Diseñar el prototipo del apartado web y probarlo con usuarios internos.
4. Integrar el sistema de recomendaciones con la base de datos de productos y servicios ofrecidos.

## 10. Referencia de la herramienta automatizada

El repositorio incorpora un script de referencia en `beam_benchmark/` que ejecuta las pruebas descritas y genera un informe en formato Markdown o JSON. Es ideal para obtener una primera aproximación a la puntuación global y validar los pesos definidos.

```bash
pip install -r requirements.txt
python -m beam_benchmark --format markdown --skip-network
```

Para ejecutar las pruebas de red es necesario contar con `speedtest-cli` o el binario oficial de Speedtest en el sistema. Los parámetros disponibles permiten ajustar la duración de las pruebas, el tamaño del archivo temporal para almacenamiento y omitir GPU o red cuando no se disponga de permisos o hardware dedicado. Los resultados pueden integrarse directamente en la web o almacenarse en una base de datos para análisis histórico.

Parámetros destacados:

- `--cpu-duration` y `--cpu-workers` regulan el esfuerzo de la prueba de CPU.
- `--disk-size` controla el tamaño del archivo temporal (en MB) utilizado para medir lectura/escritura.
- `--skip-gpu` y `--skip-network` permiten omitir componentes específicos.
- `--format json` exporta un resumen estructurado listo para la web.

Este marco te permitirá construir un apartado web funcional, claro y con recomendaciones accionables para tus usuarios centrados en Beam.
