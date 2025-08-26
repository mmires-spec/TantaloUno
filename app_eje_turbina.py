import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Monitor de Flecha Térmica - SGT-800", layout="centered")

# Título
st.title("🛡️ Monitor de Deformación del Eje – SGT-800")
st.markdown("Simulación de flecha térmica durante enfriamiento con/sin giro lento.")

# Subida de archivo
uploaded_file = st.file_uploader("📤 Sube tu archivo CSV de simulación", type=["csv"])

if uploaded_file is not None:
    # Leer datos
    data = pd.read_csv(uploaded_file)

    # Validar columnas necesarias
    required_cols = ['Tiempo_h', 'Flecha_con_giro_mm', 'Flecha_sin_giro_mm']
    if not all(col in data.columns for col in required_cols):
        st.error("❌ El archivo debe contener las columnas: 'Tiempo_h', 'Flecha_con_giro_mm', 'Flecha_sin_giro_mm'")
    else:
        st.success("✅ Datos cargados correctamente")
        
        # Selector de escenario
        opcion = st.radio(
            "Selecciona el escenario a visualizar:",
            ["Con giro lento", "Sin giro lento", "Comparación"]
        )

        # Gráfico
        fig, ax = plt.subplots(figsize=(10, 5))
        
        tiempo = data['Tiempo_h']
        limite = 0.005  # 5 micrones

        if opcion == "Con giro lento":
            ax.plot(tiempo, data['Flecha_con_giro_mm'], color='green', linewidth=2, label='Con giro lento')
            min_time = data[data['Flecha_con_giro_mm'] <= limite]['Tiempo_h'].min()
        elif opcion == "Sin giro lento":
            ax.plot(tiempo, data['Flecha_sin_giro_mm'], color='red', linewidth=2, label='Sin giro lento')
            min_time = data[data['Flecha_sin_giro_mm'] <= limite]['Tiempo_h'].min()
        else:  # Comparación
            ax.plot(tiempo, data['Flecha_con_giro_mm'], color='green', linewidth=2, label='Con giro lento')
            ax.plot(tiempo, data['Flecha_sin_giro_mm'], color='red', linewidth=2, label='Sin giro lento')
            min_time_con = data[data['Flecha_con_giro_mm'] <= limite]['Tiempo_h'].min()
            min_time_sin = data[data['Flecha_sin_giro_mm'] <= limite]['Tiempo_h'].min()
            min_time = min_time_con  # Para recomendación

        # Línea de seguridad
        ax.axhline(y=limite, color='blue', linestyle='--', label='Límite seguro (5 μm)')
        ax.set_xlabel("Tiempo (horas)")
        ax.set_ylabel("Flecha del eje (mm)")
        ax.set_title("Flecha térmica durante enfriamiento")
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_ylim(0, data[['Flecha_con_giro_mm', 'Flecha_sin_giro_mm']].max().max() * 1.1)

        st.pyplot(fig)

        # Tiempo mínimo seguro
        if pd.notna(min_time) and min_time > 0:
            st.success(f"✅ El eje estará listo para arranque seguro después de **{min_time:.2f} horas**.")
        else:
            st.warning("⚠️ El eje no alcanza el límite seguro en el tiempo simulado. ¡No arrancar!")

        # Recomendaciones
        st.subheader("💡 Recomendaciones Operativas")
        if opcion == "Sin giro lento":
            st.error("🔴 **No se recomienda arrancar sin giro lento.** Riesgo alto de contacto rotor-estator.")
        else:
            st.info("""
            - Verifica presión de **aceite de levitación (jacking oil)**.
            - Monitorea vibraciones al reinicio.
            - No saltes el ciclo de giro lento, incluso en emergencias.
            """)

else:
    st.info("Por favor, sube un archivo CSV para comenzar.")
    st.markdown("""
    > 📝 **Formato esperado del CSV**:
    > ```
    > Tiempo_h,Flecha_con_giro_mm,Flecha_sin_giro_mm
    > 0.00,0.1000,0.1000
    > 0.06,0.0951,0.1239
    > ...
    > ```
    """)

# Footer
st.markdown("---")
st.markdown("🛠️ Aplicación desarrollada para monitoreo de turbinas SGT-800 | Basado en modelo térmico de flecha")