# Mantenimiento OS (MVP)

Aplicación web interna para gestión personal de mantenimiento en central térmica.

## Fase 1 — Análisis y alcance

### Problema
El responsable de mantenimiento maneja eventos críticos, backlog, planificación semanal y acciones en herramientas dispersas (SAP, Excel, correo), lo que dificulta priorizar y ejecutar con disciplina semanal.

### Alcance del MVP
- Dashboard operativo diario.
- Registro y seguimiento de eventos críticos.
- Backlog con semáforo de vencimiento.
- Planificación semanal vinculada al backlog.
- Acciones de seguimiento.
- Reportes exportables a CSV.

### Usuario objetivo
- Usuario único principal: responsable de mantenimiento de planta.
- Uso interno/personal, sin autenticación corporativa en MVP.

### Casos de uso clave
- Registrar evento crítico y actualizar su estado.
- Cargar trabajo al backlog y priorizar por fecha/criticidad.
- Armar plan semanal y validar alistamiento (materiales/permisos/condiciones).
- Crear acciones de seguimiento y cerrar pendientes.
- Exportar reportes para reuniones de coordinación.

### Entidades principales
- `critical_events`
- `backlog_items`
- `weekly_plans`
- `weekly_plan_items`
- `followup_actions`

### Flujo general
1. Registrar eventos y backlog durante la semana.
2. Revisar dashboard en sesiones rápidas diarias.
3. Construir plan semanal desde backlog.
4. Gestionar acciones y cierre.
5. Exportar reportes para coordinación.

## Fase 2 — Arquitectura técnica

### Stack elegida (pragmática para app interna)
- **Frontend + Backend:** Streamlit (Python) en una sola app.
- **Persistencia:** SQLite local (`maintenance_os.db`).
- **Transformación/Reportes:** pandas + exportación CSV.

### Justificación
- Implementación muy rápida para MVP usable.
- Bajo costo operativo y mantenimiento simple para uso personal.
- Sin dependencia de infraestructura compleja.
- Evolucionable a FastAPI + React en una fase 2 si crece el equipo.

### Estructura de proyecto
- `app_mantenimiento.py`: aplicación completa por módulos.
- `maintenance_os.db`: base SQLite (autogenerada).
- `README.md`: diseño funcional/técnico y operación.

## Fase 3 — Modelo de datos (resumen)

Relaciones:
- `weekly_plans` 1—N `weekly_plan_items`
- `backlog_items` 1—N `weekly_plan_items` (opcional)

Tablas:
- `critical_events`: eventos críticos y trazabilidad de cierre.
- `backlog_items`: trabajos pendientes con prioridad/fecha objetivo.
- `weekly_plans`: cabecera semanal.
- `weekly_plan_items`: tareas programadas y restricciones.
- `followup_actions`: acciones derivadas de fallas/reuniones/inspecciones.

## Fase 4 — Wireframes funcionales (texto)

### 1) Dashboard
- KPIs superiores: eventos abiertos, vencidos, acciones pendientes, trabajos semana.
- Gráfico backlog por prioridad.
- Tabla resumen por unidad (SGT800 / SGT5-4000F-SGT6-5000F / GT11NM).

### 2) Eventos críticos
- Formulario de alta completo.
- Tabla con filtros por unidad, criticidad, estado, fecha.
- Acciones: actualizar estado / eliminar / exportar CSV.

### 3) Backlog
- Formulario de alta con especialidad, prioridad, fecha objetivo.
- Tabla principal con semáforo (rojo/amarillo/verde).
- Acciones: cambiar estado / eliminar / exportar CSV.

### 4) Planificación semanal
- Crear semana (fecha inicio + notas).
- Agregar ítems desde backlog o manual.
- Campos de alistamiento: materiales, permisos, condiciones.
- Tabla de trabajos programados + exportación CSV.

### 5) Acciones de seguimiento
- Formulario de acción (origen, responsable, compromiso, prioridad).
- Tabla de acciones y exportación CSV.

### 6) Reportes
- Selector de reporte.
- Vista tabular.
- Descarga CSV.

## Fase 5 — Implementación
Implementada en `app_mantenimiento.py` por módulos:
1. estructura base + navegación lateral
2. inicialización automática de base SQLite
3. APIs internas de lectura/escritura SQL
4. UI por módulo con CRUD operativo
5. exportación CSV por módulo y reportes

## Fase 6 — Ejecución local
1. Crear entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar la app:
   ```bash
   streamlit run app_mantenimiento.py
   ```
4. Abrir en navegador `http://localhost:8501`.

## Fase 7 — Mejoras futuras (fuera del MVP)
- Plantillas de planes por tipo de parada (menor/mayor).
- Indicadores MTBF/MTTR y tendencias de causas.
- Carga masiva desde Excel.
- Adjuntos (informes, fotos, OT).
- Control básico de usuarios/roles.
- API para futura integración con SAP/CMMS.
