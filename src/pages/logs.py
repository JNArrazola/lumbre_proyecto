# logs.py
import streamlit as st
from datetime import datetime

def app():
    st.title("Registro de Actividad")
    
    # Controles para filtrar y limpiar registros
    col1, col2 = st.columns([3, 1])
    with col1:
        filter_type = st.selectbox("Filtrar por:", ["Todo", "Exitosos", "Errores"])
    with col2:
        if st.button("🗑️ Limpiar registro"):
            st.session_state.shutdown_results = []
            st.experimental_rerun()
    
    # Mostrar registros filtrados (los más recientes primero)
    if st.session_state.shutdown_results:
        for result in st.session_state.shutdown_results[::-1]:
            try:
                ip = result.get("ip", "Unknown")
                os_type = result.get("os", "Unknown")
                message = result.get("message", "No message")
                time_str = result.get("time", datetime.now().strftime("%H:%M:%S"))
                success = result.get("success", False)
                
                if filter_type == "Exitosos" and not success:
                    continue
                if filter_type == "Errores" and success:
                    continue
                
                with st.container():
                    if success:
                        st.success(f"✅ [{time_str}] {ip} ({os_type}) - {message}")
                    else:
                        st.error(f"❌ [{time_str}] {ip} ({os_type}) - {message}")
            except Exception as e:
                st.warning(f"Error al mostrar entrada de registro: {str(e)}")
    else:
        st.info("No hay registros de actividad")
