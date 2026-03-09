import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

DB_PATH = "maintenance_os.db"
UNITS = ["SGT800", "SGT5-4000F / SGT6-5000F", "GT11NM"]
SPECIALTIES = ["Mecánica", "Eléctrica", "Instrumentación"]
PRIORITIES = ["Alta", "Media", "Baja"]
CRITICALITIES = ["Crítica", "Alta", "Media", "Baja"]
STATUS_GENERIC = ["Abierto", "En curso", "Bloqueado", "Cerrado"]


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    with closing(get_conn()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS critical_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date TEXT NOT NULL,
                unit TEXT NOT NULL,
                event_type TEXT NOT NULL,
                criticality TEXT NOT NULL,
                description TEXT NOT NULL,
                operational_impact TEXT,
                preliminary_cause TEXT,
                status TEXT NOT NULL,
                owner TEXT,
                immediate_actions TEXT,
                closure_actions TEXT,
                lessons_learned TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS backlog_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                description TEXT NOT NULL,
                specialty TEXT NOT NULL,
                unit TEXT NOT NULL,
                priority TEXT NOT NULL,
                detection_date TEXT NOT NULL,
                target_date TEXT NOT NULL,
                status TEXT NOT NULL,
                owner TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS weekly_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS weekly_plan_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                backlog_item_id INTEGER,
                custom_task TEXT,
                assigned_to TEXT NOT NULL,
                scheduled_date TEXT NOT NULL,
                restrictions TEXT,
                materials_ready INTEGER NOT NULL DEFAULT 0,
                permits_ready INTEGER NOT NULL DEFAULT 0,
                conditions_ready INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Programado',
                FOREIGN KEY(plan_id) REFERENCES weekly_plans(id),
                FOREIGN KEY(backlog_item_id) REFERENCES backlog_items(id)
            );

            CREATE TABLE IF NOT EXISTS followup_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                origin TEXT NOT NULL,
                related_id INTEGER,
                owner TEXT NOT NULL,
                commitment_date TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()


def read_df(query, params=()):
    with closing(get_conn()) as conn:
        return pd.read_sql_query(query, conn, params=params)


def execute(query, params=()):
    with closing(get_conn()) as conn:
        conn.execute(query, params)
        conn.commit()


def export_csv(df: pd.DataFrame, filename: str):
    return st.download_button(
        label=f"Exportar CSV: {filename}",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def semaforo(target_date: str, status: str):
    if status == "Cerrado":
        return "✅ Cerrado"
    today = date.today()
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    if target < today:
        return "🔴 Vencido"
    if target <= today + timedelta(days=7):
        return "🟡 Próximo a vencer"
    return "🟢 En plazo"


def render_dashboard():
    st.header("Dashboard de Mantenimiento")

    open_events = read_df("SELECT * FROM critical_events WHERE status != 'Cerrado'")
    backlog = read_df("SELECT * FROM backlog_items")
    pending_actions = read_df("SELECT * FROM followup_actions WHERE status != 'Cerrado'")
    weekly = read_df(
        """
        SELECT wpi.*, wp.week_start
        FROM weekly_plan_items wpi
        JOIN weekly_plans wp ON wp.id = wpi.plan_id
        WHERE date(wpi.scheduled_date) >= date('now') AND date(wpi.scheduled_date) <= date('now','+6 days')
        """
    )

    overdue = backlog[(backlog["status"] != "Cerrado") & (pd.to_datetime(backlog["target_date"]).dt.date < date.today())] if not backlog.empty else pd.DataFrame()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Eventos críticos abiertos", len(open_events))
    c2.metric("Trabajos vencidos", len(overdue))
    c3.metric("Acciones pendientes", len(pending_actions))
    c4.metric("Trabajos de esta semana", len(weekly))

    st.subheader("Backlog por prioridad")
    if backlog.empty:
        st.info("Sin datos de backlog todavía.")
    else:
        chart = backlog[backlog["status"] != "Cerrado"].groupby("priority").size().reindex(PRIORITIES, fill_value=0)
        st.bar_chart(chart)

    st.subheader("Resumen por unidad")
    if backlog.empty and open_events.empty:
        st.info("No hay registros para mostrar por unidad.")
    else:
        rows = []
        for unit in UNITS:
            rows.append(
                {
                    "Unidad": unit,
                    "Eventos abiertos": int(len(open_events[open_events["unit"] == unit])),
                    "Backlog abierto": int(len(backlog[(backlog["unit"] == unit) & (backlog["status"] != "Cerrado")])),
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_events():
    st.header("Eventos Críticos")
    with st.form("new_event", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        event_date = c1.date_input("Fecha", value=date.today())
        unit = c2.selectbox("Unidad", UNITS)
        criticality = c3.selectbox("Criticidad", CRITICALITIES)
        event_type = st.text_input("Tipo de evento", placeholder="Disparo, vibración, fuga, etc.")
        description = st.text_area("Descripción")
        operational_impact = st.text_area("Impacto operativo")
        preliminary_cause = st.text_area("Causa preliminar")
        status = st.selectbox("Estado", STATUS_GENERIC)
        owner = st.text_input("Responsable")
        immediate_actions = st.text_area("Acciones inmediatas")
        closure_actions = st.text_area("Acciones de cierre")
        lessons = st.text_area("Lecciones aprendidas")

        if st.form_submit_button("Registrar evento", use_container_width=True):
            if not event_type.strip() or not description.strip():
                st.error("Tipo de evento y descripción son obligatorios.")
            else:
                execute(
                    """
                    INSERT INTO critical_events
                    (event_date, unit, event_type, criticality, description, operational_impact, preliminary_cause,
                    status, owner, immediate_actions, closure_actions, lessons_learned)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_date.isoformat(),
                        unit,
                        event_type.strip(),
                        criticality,
                        description.strip(),
                        operational_impact.strip(),
                        preliminary_cause.strip(),
                        status,
                        owner.strip(),
                        immediate_actions.strip(),
                        closure_actions.strip(),
                        lessons.strip(),
                    ),
                )
                st.success("Evento crítico creado.")

    events = read_df("SELECT * FROM critical_events ORDER BY event_date DESC")
    if events.empty:
        st.info("No hay eventos cargados.")
        return

    st.subheader("Filtros")
    f1, f2, f3, f4 = st.columns(4)
    f_unit = f1.selectbox("Unidad", ["Todas"] + UNITS)
    f_crit = f2.selectbox("Criticidad", ["Todas"] + CRITICALITIES)
    f_status = f3.selectbox("Estado", ["Todos"] + STATUS_GENERIC)
    f_date = f4.date_input("Desde", value=date.today() - timedelta(days=30))

    filtered = events.copy()
    filtered = filtered[pd.to_datetime(filtered["event_date"]).dt.date >= f_date]
    if f_unit != "Todas":
        filtered = filtered[filtered["unit"] == f_unit]
    if f_crit != "Todas":
        filtered = filtered[filtered["criticality"] == f_crit]
    if f_status != "Todos":
        filtered = filtered[filtered["status"] == f_status]

    st.dataframe(filtered[["id", "event_date", "unit", "event_type", "criticality", "status", "owner", "description"]], use_container_width=True, hide_index=True)
    export_csv(filtered, "eventos_criticos.csv")

    st.subheader("Actualizar estado / eliminar")
    row = st.selectbox("Selecciona ID de evento", filtered["id"].tolist())
    ev = filtered[filtered["id"] == row].iloc[0]
    c1, c2 = st.columns(2)
    new_status = c1.selectbox("Nuevo estado", STATUS_GENERIC, index=STATUS_GENERIC.index(ev["status"]))
    if c1.button("Guardar estado", use_container_width=True):
        execute("UPDATE critical_events SET status = ? WHERE id = ?", (new_status, int(row)))
        st.success("Estado actualizado.")
    if c2.button("Eliminar evento", use_container_width=True):
        execute("DELETE FROM critical_events WHERE id = ?", (int(row),))
        st.warning("Evento eliminado.")


def render_backlog():
    st.header("Backlog de Mantenimiento")
    with st.form("new_backlog", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        code = c1.text_input("Código")
        specialty = c2.selectbox("Especialidad", SPECIALTIES)
        unit = c3.selectbox("Unidad", UNITS)
        description = st.text_area("Descripción")
        c4, c5, c6 = st.columns(3)
        priority = c4.selectbox("Prioridad", PRIORITIES)
        detection_date = c5.date_input("Fecha de detección", value=date.today())
        target_date = c6.date_input("Fecha objetivo", value=date.today() + timedelta(days=14))
        status = st.selectbox("Estado", STATUS_GENERIC)
        owner = st.text_input("Responsable")
        notes = st.text_area("Observaciones")

        if st.form_submit_button("Agregar al backlog", use_container_width=True):
            if not code.strip() or not description.strip():
                st.error("Código y descripción son obligatorios.")
            else:
                execute(
                    """
                    INSERT INTO backlog_items
                    (code, description, specialty, unit, priority, detection_date, target_date, status, owner, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        code.strip(),
                        description.strip(),
                        specialty,
                        unit,
                        priority,
                        detection_date.isoformat(),
                        target_date.isoformat(),
                        status,
                        owner.strip(),
                        notes.strip(),
                    ),
                )
                st.success("Trabajo agregado al backlog.")

    backlog = read_df("SELECT * FROM backlog_items ORDER BY target_date ASC")
    if backlog.empty:
        st.info("No hay backlog registrado.")
        return

    backlog["Semáforo"] = backlog.apply(lambda x: semaforo(x["target_date"], x["status"]), axis=1)
    st.dataframe(
        backlog[["id", "code", "description", "specialty", "unit", "priority", "target_date", "status", "owner", "Semáforo"]],
        use_container_width=True,
        hide_index=True,
    )
    export_csv(backlog, "backlog_mantenimiento.csv")

    selected = st.selectbox("Selecciona ID de backlog", backlog["id"].tolist())
    item = backlog[backlog["id"] == selected].iloc[0]
    c1, c2 = st.columns(2)
    new_status = c1.selectbox("Actualizar estado", STATUS_GENERIC, index=STATUS_GENERIC.index(item["status"]))
    if c1.button("Guardar cambio", use_container_width=True):
        execute("UPDATE backlog_items SET status = ? WHERE id = ?", (new_status, int(selected)))
        st.success("Estado actualizado")
    if c2.button("Eliminar trabajo", use_container_width=True):
        execute("DELETE FROM backlog_items WHERE id = ?", (int(selected),))
        st.warning("Trabajo eliminado")


def render_weekly_plan():
    st.header("Planificación Semanal")

    with st.form("create_week", clear_on_submit=True):
        week_start = st.date_input("Inicio de semana", value=date.today() - timedelta(days=date.today().weekday()))
        notes = st.text_area("Notas de la semana")
        if st.form_submit_button("Crear semana", use_container_width=True):
            execute("INSERT INTO weekly_plans (week_start, notes) VALUES (?, ?)", (week_start.isoformat(), notes.strip()))
            st.success("Semana creada")

    plans = read_df("SELECT * FROM weekly_plans ORDER BY week_start DESC")
    if plans.empty:
        st.info("Crea una semana para empezar a programar trabajos.")
        return

    current_plan = st.selectbox(
        "Semana activa",
        plans["id"].tolist(),
        format_func=lambda x: f"Plan #{x} - {plans[plans['id'] == x].iloc[0]['week_start']}",
    )

    backlog_open = read_df("SELECT * FROM backlog_items WHERE status != 'Cerrado' ORDER BY priority, target_date")
    with st.form("add_to_week", clear_on_submit=True):
        task_mode = st.radio("Origen", ["Desde backlog", "Trabajo manual"], horizontal=True)
        backlog_id = None
        custom_task = ""
        if task_mode == "Desde backlog" and not backlog_open.empty:
            backlog_id = st.selectbox(
                "Trabajo backlog",
                backlog_open["id"].tolist(),
                format_func=lambda x: f"{backlog_open[backlog_open['id'] == x].iloc[0]['code']} | {backlog_open[backlog_open['id'] == x].iloc[0]['description'][:60]}",
            )
        elif task_mode == "Trabajo manual":
            custom_task = st.text_input("Trabajo manual")
        else:
            st.warning("No hay trabajos abiertos en backlog; usa trabajo manual.")
            task_mode = "Trabajo manual"
            custom_task = st.text_input("Trabajo manual")

        c1, c2 = st.columns(2)
        assigned = c1.text_input("Responsable")
        scheduled = c2.date_input("Fecha programada", value=date.today())
        restrictions = st.text_input("Restricciones")
        m1, m2, m3 = st.columns(3)
        mat = m1.checkbox("Materiales listos")
        per = m2.checkbox("Permisos listos")
        cond = m3.checkbox("Condiciones listas")

        if st.form_submit_button("Agregar al plan", use_container_width=True):
            if not assigned.strip():
                st.error("Responsable obligatorio")
            elif task_mode == "Trabajo manual" and not custom_task.strip():
                st.error("Describe el trabajo manual")
            else:
                execute(
                    """
                    INSERT INTO weekly_plan_items
                    (plan_id, backlog_item_id, custom_task, assigned_to, scheduled_date, restrictions, materials_ready, permits_ready, conditions_ready)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(current_plan),
                        int(backlog_id) if backlog_id else None,
                        custom_task.strip() if custom_task else None,
                        assigned.strip(),
                        scheduled.isoformat(),
                        restrictions.strip(),
                        int(mat),
                        int(per),
                        int(cond),
                    ),
                )
                st.success("Trabajo agregado al plan semanal")

    items = read_df(
        """
        SELECT wpi.id, wpi.scheduled_date, wpi.assigned_to, wpi.restrictions,
               wpi.materials_ready, wpi.permits_ready, wpi.conditions_ready, wpi.status,
               COALESCE(b.code || ' - ' || b.description, wpi.custom_task) AS task
        FROM weekly_plan_items wpi
        LEFT JOIN backlog_items b ON b.id = wpi.backlog_item_id
        WHERE wpi.plan_id = ?
        ORDER BY wpi.scheduled_date ASC
        """,
        (int(current_plan),),
    )

    if items.empty:
        st.info("No hay trabajos programados en esta semana.")
    else:
        st.dataframe(items, use_container_width=True, hide_index=True)
        export_csv(items, "plan_semanal.csv")


def render_actions():
    st.header("Acciones de Seguimiento")
    origins = ["Falla", "Reunión", "Inspección", "Observación"]

    with st.form("new_action", clear_on_submit=True):
        description = st.text_area("Descripción")
        c1, c2, c3 = st.columns(3)
        origin = c1.selectbox("Origen", origins)
        owner = c2.text_input("Responsable")
        commitment = c3.date_input("Fecha compromiso", value=date.today() + timedelta(days=7))
        c4, c5 = st.columns(2)
        status = c4.selectbox("Estado", STATUS_GENERIC)
        priority = c5.selectbox("Prioridad", PRIORITIES)

        if st.form_submit_button("Crear acción", use_container_width=True):
            if not description.strip() or not owner.strip():
                st.error("Descripción y responsable son obligatorios")
            else:
                execute(
                    "INSERT INTO followup_actions (description, origin, owner, commitment_date, status, priority) VALUES (?, ?, ?, ?, ?, ?)",
                    (description.strip(), origin, owner.strip(), commitment.isoformat(), status, priority),
                )
                st.success("Acción registrada")

    actions = read_df("SELECT * FROM followup_actions ORDER BY commitment_date ASC")
    if actions.empty:
        st.info("Sin acciones registradas.")
        return

    st.dataframe(actions[["id", "description", "origin", "owner", "commitment_date", "status", "priority"]], use_container_width=True, hide_index=True)
    export_csv(actions, "acciones_seguimiento.csv")


def render_reports():
    st.header("Reportes")
    reports = {
        "Eventos abiertos": "SELECT * FROM critical_events WHERE status != 'Cerrado'",
        "Backlog por unidad": "SELECT unit, COUNT(*) as total FROM backlog_items WHERE status != 'Cerrado' GROUP BY unit",
        "Backlog por especialidad": "SELECT specialty, COUNT(*) as total FROM backlog_items WHERE status != 'Cerrado' GROUP BY specialty",
        "Trabajos vencidos": "SELECT * FROM backlog_items WHERE status != 'Cerrado' AND date(target_date) < date('now')",
        "Plan semanal actual": """
            SELECT wp.week_start, wpi.scheduled_date, wpi.assigned_to,
                   COALESCE(b.code || ' - ' || b.description, wpi.custom_task) AS task,
                   wpi.status
            FROM weekly_plan_items wpi
            JOIN weekly_plans wp ON wp.id = wpi.plan_id
            LEFT JOIN backlog_items b ON b.id = wpi.backlog_item_id
            WHERE date(wpi.scheduled_date) >= date('now','-3 days')
            ORDER BY wpi.scheduled_date ASC
        """,
        "Acciones pendientes": "SELECT * FROM followup_actions WHERE status != 'Cerrado' ORDER BY commitment_date ASC",
    }

    selected = st.selectbox("Selecciona reporte", list(reports.keys()))
    df = read_df(reports[selected])
    if df.empty:
        st.info("El reporte no tiene datos por ahora.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        export_csv(df, f"{selected.lower().replace(' ', '_')}.csv")


def main():
    st.set_page_config(page_title="Mantenimiento OS", page_icon="🛠️", layout="wide")
    init_db()

    st.title("🛠️ Sistema Operativo Personal de Mantenimiento")
    st.caption("Central térmica | foco en ejecución diaria, prioridades y seguimiento")

    module = st.sidebar.radio(
        "Módulos",
        [
            "Dashboard",
            "Eventos críticos",
            "Backlog",
            "Planificación semanal",
            "Acciones de seguimiento",
            "Reportes",
        ],
    )

    if module == "Dashboard":
        render_dashboard()
    elif module == "Eventos críticos":
        render_events()
    elif module == "Backlog":
        render_backlog()
    elif module == "Planificación semanal":
        render_weekly_plan()
    elif module == "Acciones de seguimiento":
        render_actions()
    elif module == "Reportes":
        render_reports()


if __name__ == "__main__":
    main()
