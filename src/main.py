# main.py
import streamlit as st
from utils import init_session_state
from pages import dashboard, computers, ssh_config, logs, tools

# Inicializar session state
init_session_state(st)

# Panel lateral para autenticación y navegación
with st.sidebar:
    st.title("Autenticación de Don Iker Ozuna")
    admin_pass = st.text_input("Contraseña maestra:", type="password")
    if admin_pass == st.secrets["MASTER_PASSWORD"]:
        st.session_state.authenticated = True
        st.success("✅ Autenticado")
    else:
        st.session_state.authenticated = False
        if admin_pass:
            st.error("❌ Contraseña incorrecta")
    
    if st.session_state.get("authenticated"):
        st.subheader("Navegación")
        opcion = st.radio("Ir a:", ["Panel de Control", "Gestionar Equipos"])
        st.session_state.page = opcion

if st.session_state.get("authenticated"):
    if st.session_state.page == "Panel de Control":
        dashboard.app()
    elif st.session_state.page == "Gestionar Equipos":
        computers.app()
    elif st.session_state.page == "Configuración SSH":
        # ssh_config.app()
        pass 
    elif st.session_state.page == "Registro de Actividad":
        # logs.app()
        pass
    elif st.session_state.page == "Herramientas":
        # tools.app()
        pass
else:
    st.title("Aplicación de Don Iker Ozuna")
    st.markdown("### Ingrese la contraseña")
    st.info("Por favor, ingrese la contraseña maestra para comenzar.")
    st.image("https://cdn-icons-png.flaticon.com/512/25/25235.png", width=150)
