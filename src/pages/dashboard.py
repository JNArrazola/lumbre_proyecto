# pages/dashboard.py
import streamlit as st
from datetime import datetime, timedelta
from ssh_manager import handle_immediate_shutdown, schedule_shutdown
from computer_manager import get_computers
from utils import format_time, rerun

def app():
    st.title("Panel de Control")
    
    computers = get_computers(st.session_state)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Equipos", len(computers))
    with col2:
        if st.session_state.ssh_password:
            st.success("Sistema listo para controlar equipos")
        else:
            st.warning("Configure las credenciales SSH para continuar")
    
    if computers:
        st.subheader("Equipos disponibles")
        tab1, tab2 = st.tabs(["🔴 Apagado Inmediato", "⏱️ Apagado Programado"])
        
        with tab1:
            st.info("Seleccione los equipos que desea apagar inmediatamente")
            for computer in computers:
                ip = computer["IP"]
                os_type = computer["OS"]
                description = computer.get("Description", "")
                st.subheader(ip)
                st.caption(f"{description} ({os_type})")
                if st.button("🔴 Apagar Ahora", key=f"shutdown_now_{ip}"):
                    handle_immediate_shutdown(ip, os_type, computer)
                    rerun()
        
        with tab2:
            st.subheader("Programar apagado")
            st.info("Seleccione la fecha, ingrese la hora manualmente (formato HH:MM) y los equipos para programar el apagado")
            
            # Seleccionar fecha (sin preconfigurar la hora)
            selected_date = st.date_input("Fecha:", min_value=datetime.now().date())
            
            # Ingresar manualmente la hora en formato HH:MM
            custom_time_str = st.text_input("Hora (formato HH:MM):", placeholder="Ej. 23:45")
            
            valid_time = False
            if custom_time_str:
                try:
                    selected_time = datetime.strptime(custom_time_str, "%H:%M").time()
                    valid_time = True
                except ValueError:
                    st.error("Formato de hora incorrecto. Use el formato HH:MM")
            else:
                st.error("Ingrese la hora manualmente en formato HH:MM")
            
            if valid_time:
                shutdown_time = datetime.combine(selected_date, selected_time)
                current_time = datetime.now()
                time_diff = shutdown_time - current_time
                
                if time_diff.total_seconds() <= 0:
                    st.error("La hora seleccionada debe ser en el futuro")
                    valid_time = False
                else:
                    st.info(f"Apagado programado para: {shutdown_time.strftime('%d/%m/%Y %H:%M')}")
            
            # Seleccionar equipos para programar apagado
            st.subheader("Seleccionar equipos")
            selected_computers = []
            for idx, computer in enumerate(computers):
                has_credentials = bool(computer.get('ssh_password', ''))
                status = "✅" if has_credentials else "⚠️"
                selected = st.checkbox(
                    f"{computer['IP']} - {computer.get('Description', '')} ({status})", 
                    key=f"select_{idx}"
                )
                if selected:
                    selected_computers.append(computer)
            
            if selected_computers:
                if st.button(
                    f"⏱️ Programar apagado para {len(selected_computers)} equipos", 
                    disabled=not valid_time
                ):
                    success_count = 0
                    for computer in selected_computers:
                        ip = computer["IP"].strip()
                        os_type = computer["OS"]
                        
                        # Obtener credenciales (específicas o globales)
                        username = computer.get('ssh_user', st.session_state.ssh_user)
                        password = computer.get('ssh_password', st.session_state.ssh_password)
                        sudo_pass = computer.get('sudo_pass', st.session_state.sudo_pass)
                        
                        if not password:
                            st.session_state.shutdown_results.append({
                                "success": False,
                                "ip": ip,
                                "os": os_type,
                                "message": "No hay credenciales configuradas para este equipo",
                                "time": datetime.now().strftime("%H:%M:%S")
                            })
                            continue
                        
                        # Ejecutar apagado programado (la función schedule_shutdown calculará el delay y usará sleep)
                        success, message = schedule_shutdown(
                            ip=ip,
                            os_type=os_type,
                            username=username,
                            password=password,
                            sudo_password=sudo_pass,
                            shutdown_time=shutdown_time,
                            immediate=False
                        )
                        
                        if success:
                            success_count += 1
                        
                        st.session_state.shutdown_results.append({
                            "success": success,
                            "ip": ip,
                            "os": os_type,
                            "message": message if not success else f"Apagado programado: {shutdown_time.strftime('%H:%M')}",
                            "time": datetime.now().strftime("%H:%M:%S")
                        })
                    
                    st.success(f"Programados {success_count}/{len(selected_computers)} equipos")
                    rerun()
            else:
                st.warning("Seleccione al menos un equipo para programar")
