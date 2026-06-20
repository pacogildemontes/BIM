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

## Despliegue en hosting gratuito (Render)

La app está lista para desplegarse con `gunicorn`. Incluye:

- `wsgi.py` (`gunicorn wsgi:app`), `Procfile` y `render.yaml` (blueprint de Render).
- **Login por contraseña**: si defines la variable `APP_PASSWORD`, la app exige
  iniciar sesión. Imprescindible antes de exponer datos financieros en internet.

Pasos en [Render](https://render.com) (plan gratuito):

1. Entra en Render → **New → Blueprint** y conecta este repositorio/rama.
2. Render lee `render.yaml` y crea el servicio. Define `APP_PASSWORD` cuando lo pida.
3. En 2-3 min tendrás una URL pública (`https://mis-finanzas.onrender.com`).

> Aviso del plan gratuito: no tiene disco persistente, así que la base de datos
> (SQLite en `/tmp`) se reinicia en cada redeploy o tras inactividad. Sirve para
> **probar** la app; para uso real, añade un disco de pago o una base de datos externa.

Variables de entorno relevantes:

| Variable        | Para qué sirve                                             |
|-----------------|------------------------------------------------------------|
| `APP_PASSWORD`  | Activa el login y define la contraseña de acceso.          |
| `SECRET_KEY`    | Clave de sesión (Render la genera sola con el blueprint).  |
| `FINANCE_DB`    | Ruta del fichero SQLite.                                    |

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
