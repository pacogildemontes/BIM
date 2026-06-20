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

## Qué incluye hoy

- **Resumen / patrimonio neto**: agrega cuentas + inversiones + viviendas − hipotecas,
  con próximos vencimientos y movimientos recientes.
- **Cuentas**: bancos, tarjetas, cuentas de inversión y efectivo, con su saldo.
- **Movimientos**: alta manual e **importación de extractos CSV** (detecta
  automáticamente columnas de fecha/concepto/importe y formatos español/inglés,
  incluido Debe/Haber).
- **Viviendas**: ficha por inmueble con valor, hipoteca, alquiler e inquilino, sus
  **suministros y gastos independientes** (luz, agua, gas, comunidad, IBI, seguro…)
  y cálculo automático de **resultado anual y rentabilidad bruta/neta**.
- **Inversiones**: cartera de ETFs/fondos que **replica tu plan** (% objetivo,
  importes) y lo **simula**: valor actual, P/L, peso real frente al objetivo
  (desviación para rebalanceo) y **proyección a 1/3/5/10/15/20 años** con aportación
  mensual y rentabilidad esperada. No conecta con el bróker; el precio se actualiza a mano.
- **Calendario de obligaciones**: vencimientos con categoría, importe, recurrencia
  (mensual/bimestral/trimestral/semestral/anual) y avisos de cuánto falta o si están
  vencidos. Al marcar como pagado un recurrente, la fecha avanza al siguiente.
- **Patrimonio**: desglose del neto por bloques y registro de «otros activos»
  (vehículos, criptos…).

## Base de datos: SQLite o PostgreSQL (Supabase)

La app funciona con dos backends, de forma transparente para el código:

- **SQLite** (por defecto): para uso local, fichero `finanzas.db`. No requiere nada.
- **PostgreSQL** (recomendado en producción): se activa **solo** definiendo la variable
  `DATABASE_URL`. Pensado para una base persistente y gratuita como **Supabase**, de
  modo que los datos sobrevivan a los reinicios del hosting.

Ambos caminos están **probados** con la misma suite de pruebas (`tests/test_postgres.py`
se ejecuta si `DATABASE_URL` apunta a Postgres).

## Despliegue gratis: Supabase (datos) + Render (app)

La app está lista para `gunicorn` e incluye `wsgi.py`, `Procfile` y `render.yaml`.
Además, si defines `APP_PASSWORD`, exige **login por contraseña** (imprescindible
antes de exponer datos financieros en internet).

**1) Base de datos en [Supabase](https://supabase.com) (gratis):**

1. Crea un proyecto. En *Project Settings → Database → Connection string* copia la
   cadena en formato **URI** (algo como
   `postgresql://postgres:TU_PASSWORD@db.xxxxx.supabase.co:5432/postgres`).
2. Esa cadena es tu `DATABASE_URL`. La app crea las tablas sola en el primer arranque.

**2) App en [Render](https://render.com) (gratis):**

1. Render → **New → Blueprint** y conecta este repositorio/rama.
2. Render lee `render.yaml`. Cuando lo pida, define:
   - `DATABASE_URL` → la cadena de Supabase.
   - `APP_PASSWORD` → la contraseña de acceso a la app.
3. En 2-3 min tendrás una URL pública (`https://mis-finanzas.onrender.com`) con tus
   datos guardados de verdad en Supabase.

> Seguridad: estas variables se configuran **en los paneles de Render/Supabase**,
> nunca en el repositorio. No incluyas contraseñas ni cadenas de conexión en el código.

Variables de entorno relevantes:

| Variable        | Para qué sirve                                                      |
|-----------------|--------------------------------------------------------------------|
| `DATABASE_URL`  | Cadena Postgres (Supabase). Si no se define, se usa SQLite local.  |
| `APP_PASSWORD`  | Activa el login y define la contraseña de acceso.                  |
| `SECRET_KEY`    | Clave de sesión (Render la genera sola con el blueprint).          |
| `FINANCE_DB`    | Ruta del fichero SQLite (solo backend SQLite).                     |

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
run.py          Punto de entrada local (Flask dev server)
wsgi.py         Punto de entrada de producción (gunicorn)
Procfile        Comando de arranque para PaaS
render.yaml     Blueprint de despliegue en Render
```

## Roadmap (siguientes fases)

- **Conexión bancaria automática (Open Banking / PSD2)** mediante un agregador
  como *GoCardless Bank Account Data* (plan gratuito, cubre banca española).
  Sincronización de saldos y movimientos sin importar CSV. Requiere alta y gestión
  de credenciales; las conexiones caducan ~90 días por normativa.
- **Precios de ETFs automáticos** (API gratuita) para no actualizar a mano.
- **Histórico de patrimonio**: snapshots periódicos para ver la evolución en el tiempo.
- **Avisos**: notificaciones por email/Telegram de vencimientos próximos.
- **Integración con la app de facturación** existente (importar ingresos/gastos
  de autónomo y previsión de IVA/IRPF trimestral).
```
