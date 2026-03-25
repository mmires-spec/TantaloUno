"""
Simulación de Flujograma PMS — Planificación Semanal de Mantenimiento
Central térmica (SGT800 / SGT5-4000F / GT11NM)
"""

import streamlit as st

st.set_page_config(
    page_title="Flujograma PMS Semanal",
    page_icon="🔁",
    layout="wide",
)

st.title("🔁 Flujograma — Proceso de Planificación Semanal de Mantenimiento (PMS)")
st.caption("Simulación del ciclo semanal: desde la detección de trabajos hasta el cierre y registro.")

# ── Selector de etapa para destacar ────────────────────────────────────────────
ETAPAS = [
    "Completo (todas las etapas)",
    "1. Revisión de backlog y eventos",
    "2. Verificación de prerrequisitos",
    "3. Programación semanal",
    "4. Reunión de arranque semanal",
    "5. Ejecución de trabajos",
    "6. Seguimiento diario",
    "7. Cierre y registro",
]

etapa = st.sidebar.selectbox("Resaltar etapa", ETAPAS)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
**Leyenda de colores**
- 🟦 Inicio / Fin
- 🟨 Proceso / Actividad
- 🔶 Decisión
- 🟩 Resultado positivo
- 🟥 Resultado negativo / reprogramar
"""
)

# ── Construcción del grafo Graphviz ─────────────────────────────────────────────

def color_nodo(nombre: str, etapa_activa: str, color_default: str) -> str:
    """Resalta un nodo si la etapa activa coincide con su grupo."""
    if etapa_activa == "Completo (todas las etapas)":
        return color_default
    return "#ff9900" if nombre in etapa_activa else color_default


DOT = """
digraph PMS {{
    graph [rankdir=TB fontname="Helvetica" splines=ortho nodesep=0.6 ranksep=0.7]
    node  [fontname="Helvetica" fontsize=12 style=filled penwidth=1.5]
    edge  [fontname="Helvetica" fontsize=10]

    // ── INICIO ──────────────────────────────────────────────────────────────
    INICIO [label="INICIO\\n(Lunes AM)" shape=oval fillcolor="{c_inicio}" fontcolor=white]

    // ── ETAPA 1: Revisión ────────────────────────────────────────────────────
    E1_REV   [label="1. Revisar backlog\\ny eventos críticos" shape=box fillcolor="{c1}"]
    E1_PRIO  [label="1b. Priorizar por\\ncriticidad / fecha\\nvencimiento" shape=box fillcolor="{c1}"]

    // ── ETAPA 2: Prerrequisitos ──────────────────────────────────────────────
    E2_CHK   [label="2. Verificar\\nprerequisitos" shape=diamond fillcolor="{c2}" fontcolor=black]
    E2_OK    [label="Materiales\\nPermisos\\nCondiciones\\n✅ OK" shape=box fillcolor="#2ecc71" fontcolor=white]
    E2_NOK   [label="Falta algún\\nrequisito" shape=box fillcolor="#e74c3c" fontcolor=white]
    E2_GEST  [label="Gestionar\\npendiente\\n(materiales / permisos)" shape=box fillcolor="{c2}"]

    // ── ETAPA 3: Programación ────────────────────────────────────────────────
    E3_PROG  [label="3. Programar trabajos\\nen la semana\\n(día + responsable)" shape=box fillcolor="{c3}"]
    E3_CAP   [label="3b. ¿Capacidad\\ndisponible?" shape=diamond fillcolor="{c3}" fontcolor=black]
    E3_PASA  [label="Pasar exceso al\\nbacklog siguiente" shape=box fillcolor="#e74c3c" fontcolor=white]

    // ── ETAPA 4: Reunión arranque ────────────────────────────────────────────
    E4_MTG   [label="4. Reunión de arranque\\nde semana (15 min)" shape=box fillcolor="{c4}"]
    E4_ACU   [label="Comunicar plan\\ny responsables" shape=box fillcolor="{c4}"]

    // ── ETAPA 5: Ejecución ───────────────────────────────────────────────────
    E5_EXEC  [label="5. Ejecución\\nde trabajos" shape=box fillcolor="{c5}"]
    E5_INC   [label="¿Incidencia\\ndurante ejecución?" shape=diamond fillcolor="{c5}" fontcolor=black]
    E5_EVC   [label="Registrar evento\\ncrítico" shape=box fillcolor="#e74c3c" fontcolor=white]

    // ── ETAPA 6: Seguimiento diario ──────────────────────────────────────────
    E6_FOLL  [label="6. Seguimiento\\ndiario (stand-up)" shape=box fillcolor="{c6}"]
    E6_COMP  [label="¿Trabajo completado\\neste día?" shape=diamond fillcolor="{c6}" fontcolor=black]
    E6_RESCH [label="Reprogramar o\\nagregar restricción" shape=box fillcolor="#e74c3c" fontcolor=white]

    // ── ETAPA 7: Cierre ──────────────────────────────────────────────────────
    E7_CLOSE [label="7. Cierre semanal\\n(Viernes PM)" shape=box fillcolor="{c7}"]
    E7_DOC   [label="Documentar lecciones\\naprendidas" shape=box fillcolor="{c7}"]
    E7_KPI   [label="Actualizar KPIs\\n(cumplimiento / vencidos)" shape=box fillcolor="{c7}"]

    // ── FIN ──────────────────────────────────────────────────────────────────
    FIN [label="FIN\\n(ciclo siguiente)" shape=oval fillcolor="{c_inicio}" fontcolor=white]

    // ── FLUJO PRINCIPAL ──────────────────────────────────────────────────────
    INICIO  -> E1_REV
    E1_REV  -> E1_PRIO
    E1_PRIO -> E2_CHK

    E2_CHK  -> E2_OK   [label="Sí"]
    E2_CHK  -> E2_NOK  [label="No"]
    E2_NOK  -> E2_GEST
    E2_GEST -> E2_CHK  [style=dashed label="reintentar"]
    E2_OK   -> E3_PROG

    E3_PROG -> E3_CAP
    E3_CAP  -> E4_MTG  [label="Sí, hay\\ncapacidad"]
    E3_CAP  -> E3_PASA [label="No"]
    E3_PASA -> E3_PROG [style=dashed label="ajustar"]

    E4_MTG  -> E4_ACU
    E4_ACU  -> E5_EXEC

    E5_EXEC -> E5_INC
    E5_INC  -> E6_FOLL [label="No"]
    E5_INC  -> E5_EVC  [label="Sí"]
    E5_EVC  -> E6_FOLL [style=dashed]

    E6_FOLL -> E6_COMP
    E6_COMP -> E5_EXEC  [label="No (sigue\\nel día)" style=dashed]
    E6_COMP -> E7_CLOSE [label="Sí (fin\\nde semana)"]
    E6_COMP -> E6_RESCH [label="Bloqueado"]
    E6_RESCH -> E6_FOLL [style=dashed]

    E7_CLOSE -> E7_DOC
    E7_DOC   -> E7_KPI
    E7_KPI   -> FIN
    FIN      -> INICIO  [style=dashed label="semana\\nsiguiente" color=gray]
}}
""".format(
    c_inicio="#2c3e50",
    c1=color_nodo("1", etapa, "#3498db"),
    c2=color_nodo("2", etapa, "#f39c12"),
    c3=color_nodo("3", etapa, "#9b59b6"),
    c4=color_nodo("4", etapa, "#1abc9c"),
    c5=color_nodo("5", etapa, "#e67e22"),
    c6=color_nodo("6", etapa, "#2980b9"),
    c7=color_nodo("7", etapa, "#27ae60"),
)

st.graphviz_chart(DOT, use_container_width=True)

# ── Descripción detallada de cada etapa ────────────────────────────────────────
st.markdown("---")
st.subheader("Descripción de cada etapa")

etapas_detalle = {
    "1. Revisión de backlog y eventos": {
        "cuando": "Lunes AM",
        "responsable": "Planificador / Supervisor",
        "descripcion": (
            "Se revisa el backlog abierto priorizando por criticidad y fecha de vencimiento. "
            "Se identifican eventos críticos pendientes de cierre y acciones de seguimiento vencidas."
        ),
        "entradas": ["Backlog de mantenimiento", "Eventos críticos abiertos", "Acciones de seguimiento"],
        "salidas": ["Lista priorizada de trabajos candidatos a la semana"],
    },
    "2. Verificación de prerrequisitos": {
        "cuando": "Lunes AM – antes de programar",
        "responsable": "Planificador",
        "descripcion": (
            "Para cada trabajo candidato se verifica: materiales disponibles, permisos de trabajo listos "
            "y condiciones operativas (equipo disponible para intervención). Solo se programa lo que tiene "
            "prerrequisitos satisfechos; lo demás se gestiona para semanas futuras."
        ),
        "entradas": ["Lista priorizada", "Almacén / SAP", "Operaciones"],
        "salidas": ["Trabajos listos para programar", "Trabajos bloqueados con acción de gestión"],
    },
    "3. Programación semanal": {
        "cuando": "Lunes AM",
        "responsable": "Planificador",
        "descripcion": (
            "Se asigna cada trabajo a un día de la semana y a un responsable, respetando la "
            "capacidad disponible (horas-hombre). Si la demanda supera la capacidad, el exceso "
            "regresa al backlog con nueva prioridad."
        ),
        "entradas": ["Trabajos con prerrequisitos OK", "Calendario de disponibilidad del equipo"],
        "salidas": ["Plan semanal con día, responsable y restricciones"],
    },
    "4. Reunión de arranque semanal": {
        "cuando": "Lunes AM (≤ 15 min)",
        "responsable": "Supervisor / Equipo",
        "descripcion": (
            "Reunión corta para comunicar el plan: quién hace qué y cuándo. "
            "Se resuelven dudas rápidas y se confirman compromisos."
        ),
        "entradas": ["Plan semanal"],
        "salidas": ["Equipo alineado con compromisos del día"],
    },
    "5. Ejecución de trabajos": {
        "cuando": "Lunes – Viernes",
        "responsable": "Técnicos / Especialistas",
        "descripcion": (
            "Ejecución del trabajo de campo según el plan. Si ocurre una incidencia "
            "(falla no esperada, disparo, anomalía) se registra como Evento Crítico."
        ),
        "entradas": ["Plan semanal", "Permisos de trabajo"],
        "salidas": ["Trabajos ejecutados", "Eventos críticos (si aplica)"],
    },
    "6. Seguimiento diario": {
        "cuando": "Cada día (stand-up ~ 10 min)",
        "responsable": "Supervisor",
        "descripcion": (
            "Revisión rápida del avance: ¿se completó lo programado? "
            "Si hay bloqueos se reprograma o se registra restricción. "
            "Se actualiza el estado en el sistema."
        ),
        "entradas": ["Plan del día", "Reporte de técnicos"],
        "salidas": ["Estado actualizado", "Reprogramaciones si aplica"],
    },
    "7. Cierre y registro": {
        "cuando": "Viernes PM",
        "responsable": "Planificador / Supervisor",
        "descripcion": (
            "Se cierra la semana: se documentan lecciones aprendidas, se actualizan KPIs "
            "(% cumplimiento del plan, trabajos vencidos, eventos críticos cerrados). "
            "El backlog se depura para arrancar el nuevo ciclo."
        ),
        "entradas": ["Plan ejecutado", "Eventos y acciones de la semana"],
        "salidas": ["KPIs actualizados", "Backlog depurado", "Informe semanal"],
    },
}

for titulo, info in etapas_detalle.items():
    with st.expander(titulo):
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"**Cuándo:** {info['cuando']}")
            st.markdown(f"**Responsable:** {info['responsable']}")
            st.markdown("**Entradas:**")
            for e in info["entradas"]:
                st.markdown(f"- {e}")
            st.markdown("**Salidas:**")
            for s in info["salidas"]:
                st.markdown(f"- {s}")
        with c2:
            st.info(info["descripcion"])

st.markdown("---")
st.caption("Flujograma generado con Graphviz • Proyecto TantaloUno")
