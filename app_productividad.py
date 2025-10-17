import streamlit as st
import pandas as pd
from datetime import datetime, date, time

st.set_page_config(
    page_title="Asistente de Productividad Personal",
    page_icon="✅",
    layout="wide",
)

st.title("🧠 Planificador de Productividad")
st.caption(
    "Añade tareas al instante, programa tu día y recibe sugerencias para trabajar de forma más inteligente."
)

if "tareas" not in st.session_state:
    st.session_state.tareas = []

col_form, col_plan = st.columns([1, 2])

with col_form:
    st.subheader("➕ Nueva tarea")
    with st.form("form_tarea", clear_on_submit=True):
        titulo = st.text_input("Título", placeholder="Ej. Llamar a proveedor")
        descripcion = st.text_area(
            "Detalles",
            placeholder="Notas rápidas, entregables o contexto",
            height=80,
        )
        prioridad = st.select_slider("Prioridad", options=["Baja", "Media", "Alta"], value="Media")
        energia = st.selectbox(
            "Energía requerida",
            ["Alta", "Media", "Baja"],
            index=1,
            help="Úsalo para organizar tu día según tu nivel de concentración",
        )
        duracion = st.number_input(
            "Duración estimada (horas)",
            min_value=0.25,
            max_value=8.0,
            value=1.0,
            step=0.25,
        )
        fecha = st.date_input("Fecha objetivo", value=date.today())
        hora = st.time_input("Hora objetivo", value=time(hour=9, minute=0))
        st.write("")
        submitted = st.form_submit_button("Guardar tarea", use_container_width=True)

        if submitted:
            if titulo.strip():
                st.session_state.tareas.append(
                    {
                        "titulo": titulo.strip(),
                        "descripcion": descripcion.strip(),
                        "prioridad": prioridad,
                        "energia": energia,
                        "duracion": float(duracion),
                        "fecha": fecha.isoformat(),
                        "hora": hora.strftime("%H:%M"),
                        "fecha_hora": datetime.combine(fecha, hora),
                        "completada": False,
                        "creada": datetime.now(),
                    }
                )
                st.success("Tarea registrada")
            else:
                st.error("Necesitas al menos un título para la tarea")

with col_plan:
    st.subheader("🗓️ Agenda inteligente")
    tareas = st.session_state.tareas

    if tareas:
        df = pd.DataFrame(tareas)
        df.sort_values(by=["completada", "fecha_hora", "prioridad"], inplace=True)

        prioridad_map = {"Alta": 1, "Media": 2, "Baja": 3}
        df["peso_prioridad"] = df["prioridad"].map(prioridad_map)
        df.sort_values(by=["completada", "peso_prioridad", "fecha_hora"], inplace=True)

        st.metric(
            "Tareas activas",
            f"{(~df['completada']).sum()} pendientes / {len(df)} totales",
        )

        st.dataframe(
            df[
                [
                    "titulo",
                    "prioridad",
                    "energia",
                    "duracion",
                    "fecha",
                    "hora",
                    "completada",
                ]
            ].rename(
                columns={
                    "titulo": "Título",
                    "prioridad": "Prioridad",
                    "energia": "Energía",
                    "duracion": "Horas",
                    "fecha": "Fecha",
                    "hora": "Hora",
                    "completada": "¿Listo?",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

        st.markdown("### ✅ Actualiza tu progreso")
        for idx, tarea in enumerate(tareas):
            with st.expander(
                f"{'✅' if tarea['completada'] else '🔜'} {tarea['titulo']} — {tarea['prioridad']} prioridad"
            ):
                st.write(tarea["descripcion"] or "Sin descripción")
                col1, col2 = st.columns(2)
                with col1:
                    completada = st.checkbox(
                        "Marcar como completada",
                        value=tarea["completada"],
                        key=f"check_{idx}",
                    )
                with col2:
                    eliminar = st.button("Eliminar", key=f"delete_{idx}")

                st.caption(
                    f"⏱️ {tarea['duracion']}h • {tarea['energia']} energía • Objetivo: {tarea['fecha']} {tarea['hora']}"
                )

                if completada != tarea["completada"]:
                    st.session_state.tareas[idx]["completada"] = completada
                if eliminar:
                    st.session_state.tareas.pop(idx)
                    st.experimental_rerun()

        st.markdown("### 🧭 Recomendaciones personalizadas")

        pendientes = df[~df["completada"]]
        if not pendientes.empty:
            pendientes.sort_values(by=["peso_prioridad", "fecha_hora"], inplace=True)

            primera = pendientes.iloc[0]
            siguiente = pendientes.iloc[1:3]

            st.info(
                f"**Enfoque ahora:** {primera['titulo']} ({primera['prioridad']} prioridad, {primera['duracion']}h)."
            )

            if not siguiente.empty:
                recomendacion = " → ".join(
                    [
                        f"{row['titulo']} ({row['duracion']}h)"
                        for _, row in siguiente.iterrows()
                    ]
                )
                st.write(f"Luego continúa con: {recomendacion}")

            horas_total = pendientes["duracion"].sum()
            vencen_hoy = pendientes[pendientes["fecha_hora"].dt.date == date.today()]
            energia_alta = pendientes[pendientes["energia"] == "Alta"]

            st.markdown(
                f"- Te quedan **{horas_total:.1f}h** de trabajo pendiente."
            )
            st.markdown(
                f"- **{len(vencen_hoy)} tareas** vencen hoy. Reserva huecos para ellas."
            )
            st.markdown(
                f"- Programa tareas de alta energía cuando te sientas más alerta: "
                f"{', '.join(energia_alta['titulo']) if not energia_alta.empty else 'no hay pendientes de alta energía'}."
            )

            ventana_mananera = [8, 11]
            necesita_reprogramacion = pendientes[
                pendientes["fecha_hora"].dt.hour < ventana_mananera[0]
            ]
            if not necesita_reprogramacion.empty:
                st.warning(
                    "Hay tareas programadas demasiado temprano. Ajusta tu horario si lo necesitas."
                )
        else:
            st.success("🎉 ¡Todo al día! Dedica un momento a revisar o planificar la semana.")
    else:
        st.empty()
        st.info("Todavía no tienes tareas registradas. Usa el formulario para crear la primera.")

st.markdown("---")
st.markdown(
    "Hecho con Streamlit para ayudarte a mantener tus objetivos claros y accionables."
)
