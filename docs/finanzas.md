# Hub de finanzas personales

Aplicación web local para tener en un solo sitio tus **cuentas**, **patrimonio**
(propiedades, fondos, inversiones) y un **calendario de obligaciones** (seguros,
IBI, IRPF, IVA trimestral, impuestos, suministros…), con importación de extractos
bancarios en CSV.

Pensada para ejecutarse en tu propio equipo: los datos viven en un fichero SQLite
local (`finanzas.db`), que **no se sube al repositorio** (está en `.gitignore`).

## Puesta en marcha

```bash
pip install -r requirements.txt
python run.py
# Abre http://127.0.0.1:5000
```

Para abrirlo desde el móvil en la misma red wifi:

```bash
python run.py --host 0.0.0.0
# Luego entra a http://IP-DE-TU-PC:5000 desde el móvil
```

La base de datos se crea sola la primera vez. Puedes cambiar su ubicación con la
variable de entorno `FINANCE_DB`:

```bash
FINANCE_DB=/ruta/segura/mis_finanzas.db python run.py
```

## Qué incluye hoy (fase 1)

- **Resumen / patrimonio neto**: cuentas + activos − deudas, próximos vencimientos
  y movimientos recientes.
- **Cuentas**: bancos, tarjetas, cuentas de inversión y efectivo, con su saldo.
- **Movimientos**: alta manual e **importación de extractos CSV** (detecta
  automáticamente columnas de fecha/concepto/importe y formatos español/inglés,
  incluido Debe/Haber).
- **Patrimonio**: propiedades, fondos e inversiones con su valor y deuda asociada
  (p. ej. hipoteca), calculando el neto.
- **Calendario de obligaciones**: vencimientos con categoría, importe, recurrencia
  (mensual/trimestral/semestral/anual) y avisos de cuánto falta o si están vencidos.
  Al marcar como pagado un recurrente, la fecha avanza automáticamente al siguiente.

## Arquitectura

```
finanzas/
  app.py        Rutas Flask y fábrica de la aplicación
  models.py     Acceso a datos (cuentas, movimientos, activos, obligaciones)
  importer.py   Parseo de extractos CSV
  utils.py      Parseo/formato de importes y fechas (formato español)
  db.py         Conexión e inicialización de SQLite
  schema.sql    Esquema de la base de datos
  templates/    Plantillas Jinja2 (Bootstrap 5)
  static/       Estilos
run.py          Punto de entrada
```

## Roadmap (siguientes fases)

- **Fase 2 — Conexión bancaria automática (Open Banking / PSD2)** mediante un
  agregador como *GoCardless Bank Account Data* (plan gratuito, cubre banca
  española). Sincronización de saldos y movimientos sin importar CSV. Requiere
  alta y gestión de credenciales; las conexiones caducan ~90 días por normativa.
- **Histórico de patrimonio**: snapshots periódicos para ver la evolución en el tiempo.
- **Avisos**: notificaciones por email/Telegram de vencimientos próximos.
- **Categorización automática** de movimientos y cuadros de gasto por categoría.
- **Integración con la app de facturación** existente (importar ingresos/gastos
  de autónomo y previsión de IVA/IRPF trimestral).
```
