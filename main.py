import streamlit as st
import paramiko
from datetime import datetime, timedelta
import time
import os
import uuid

# Create a session state for tracking shutdown attempts if it doesn't exist
if 'shutdown_results' not in st.session_state:
    st.session_state.shutdown_results = []
if 'ssh_user' not in st.session_state:
    st.session_state.ssh_user = "admin"  # Default user (legacy)
if 'ssh_password' not in st.session_state:
    st.session_state.ssh_password = ""   # Default password (legacy)
if 'sudo_pass' not in st.session_state:
    st.session_state.sudo_pass = ""      # Default sudo password (legacy)
if 'page' not in st.session_state:
    st.session_state.page = "dashboard"

def schedule_shutdown(ip, os_type, username, password, sudo_password=None, shutdown_time=None, immediate=False):
    """Schedule or execute immediate shutdown on remote machine"""
    try:
        # Input validation
        if not ip or not os_type or not username or not password:
            return False, "Missing required parameters"
            
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Use password authentication instead of key-based
            client.connect(
                hostname=ip,
                username=username,
                password=password,
                timeout=10
            )
        except Exception as e:
            return False, f"SSH connection error: {str(e)}"
            
        # Get sudo password if provided, otherwise use SSH password
        sudo_pwd = sudo_password if sudo_password else password
        
        # First verify if SSH connection is working properly
        try:
            stdin, stdout, stderr = client.exec_command("whoami")
            connected_user = stdout.read().decode().strip()
            st.session_state.shutdown_results.append({
                "success": True,
                "ip": ip,
                "os": os_type,
                "message": f"Conectado como usuario: {connected_user}",
                "time": datetime.now().strftime("%H:%M:%S")
            })
        except Exception as e:
            return False, f"Error ejecutando comando básico: {str(e)}"

        # Para Linux, intentamos diferentes enfoques para el apagado
        if os_type == "Linux":
            # Try multiple approaches for shutdown to increase success chance
            if immediate:
                # Opción 1: Usar approach directo
                command1 = f'echo "{sudo_pwd}" | sudo -S shutdown now'
                
                # Opción 2: Usar expect con script
                shutdown_script = f'''
                spawn sudo shutdown now
                expect "password"
                send "{sudo_pwd}\\r"
                expect eof
                '''
                command2 = f'echo "{shutdown_script}" > /tmp/shutdown_script.exp && chmod +x /tmp/shutdown_script.exp && expect -f /tmp/shutdown_script.exp'
                
                # Opción 3: Usar approach bash -c
                command3 = f'echo "{sudo_pwd}" | sudo -S bash -c "shutdown now"'
                
                # Intentar cada enfoque
                commands = [command1, command3]  # Omitimos command2 si no hay expect instalado
                
                for i, cmd in enumerate(commands):
                    try:
                        stdin, stdout, stderr = client.exec_command(cmd)
                        # Corto tiempo de espera ya que el apagado puede desconectar rápidamente
                        time.sleep(2)
                        # Si llegamos aquí sin error, probablemente funcionó
                        return True, "Comando de apagado enviado con éxito"
                    except Exception as e:
                        if i == len(commands) - 1:  # Si es el último intento
                            return False, f"Fallaron todos los intentos de apagado: {str(e)}"
                        # Si no es el último intento, seguimos probando
                        continue
            else:
                # Scheduled shutdown
                if not shutdown_time:
                    return False, "No shutdown time provided for scheduled shutdown"
                    
                now = datetime.now()
                time_diff = shutdown_time - now
                minutes = max(1, int(time_diff.total_seconds() // 60))  # Al menos 1 minuto
                
                # Usar el mismo enfoque múltiple para apagado programado
                command = f'echo "{sudo_pwd}" | sudo -S shutdown -h +{minutes}'
                
                try:
                    stdin, stdout, stderr = client.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()
                    error = stderr.read().decode().strip()
                    
                    # Ignorar mensajes comunes de sudo que no son errores
                    if error and ("password for" in error.lower() or "sudo" in error.lower()):
                        error = ""
                        
                    if exit_status != 0 or error:
                        return False, f"Error programando apagado: {error}"
                        
                    return True, f"Apagado programado para {shutdown_time.strftime('%H:%M')}"
                except Exception as e:
                    return False, f"Error programando apagado: {str(e)}"
        
        elif os_type == "Windows":
            # Windows shutdown
            if immediate:
                command = 'shutdown /s /f /t 0'
            else:
                if not shutdown_time:
                    return False, "No shutdown time provided for scheduled shutdown"
                now = datetime.now()
                time_diff = shutdown_time - now
                seconds = int(time_diff.total_seconds())
                if seconds <= 0:
                    return False, "Scheduled time must be in the future"
                command = f'shutdown /s /f /t {seconds}'
                
            stdin, stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            error = stderr.read().decode().strip()
            
            if exit_status != 0 or error:
                return False, f"Command failed: {error}"
            
            return True, "Shutdown command executed successfully"
        else:
            return False, f"Unsupported OS type: {os_type}"

    except Exception as e:
        return False, f"Error general: {str(e)}"
    finally:
        if 'client' in locals() and client:
            try:
                client.close()
            except:
                pass  # Ignorar errores al cerrar conexión

# Define immediate shutdown handler function with per-computer credentials
def handle_immediate_shutdown(ip, os_type, computer=None):
    # Use computer-specific credentials if available, otherwise fall back to global
    username = computer.get('ssh_user', st.session_state.ssh_user) if computer else st.session_state.ssh_user
    password = computer.get('ssh_password', st.session_state.ssh_password) if computer else st.session_state.ssh_password
    sudo_pass = computer.get('sudo_pass', st.session_state.sudo_pass) if computer else st.session_state.sudo_pass
    
    if not password:
        st.session_state.shutdown_results.append({
            "success": False, 
            "ip": ip, 
            "os": os_type, 
            "message": "No hay contraseña SSH configurada para este equipo"
        })
        return
        
    ip = ip.strip()
    
    if not ip:
        st.session_state.shutdown_results.append({
            "success": False,
            "ip": "Unknown",
            "os": os_type,
            "message": "IP address is required"
        })
        return
        
    success, message = schedule_shutdown(
        ip=ip, 
        os_type=os_type, 
        username=username, 
        password=password,
        sudo_password=sudo_pass,
        immediate=True
    )
    
    # Record the result
    st.session_state.shutdown_results.append({
        "success": success,
        "ip": ip,
        "os": os_type,
        "message": message,
        "time": datetime.now().strftime("%H:%M:%S")
    })

# Initialize default computer list with credential fields
if 'computers' not in st.session_state:
    st.session_state.computers = [
        {
            "IP": "192.168.1.100", 
            "OS": "Linux", 
            "Description": "Server 1",
            "ssh_user": "admin",
            "ssh_password": "",
            "sudo_pass": ""
        },
        {
            "IP": "192.168.1.101", 
            "OS": "Linux", 
            "Description": "Server 2",
            "ssh_user": "admin",
            "ssh_password": "",
            "sudo_pass": ""
        }
    ]

# Interfaz web
st.set_page_config(page_title="Control de Apagado Remoto", page_icon="⏰", layout="wide")

# Sidebar for navigation and configuration
with st.sidebar:
    st.title("⏰ Control Remoto")
    
    # Authentication section in sidebar
    with st.expander("🔐 Autenticación", expanded=True):
        admin_pass = st.text_input("Contraseña maestra:", type="password")
        correct_pass = st.secrets["MASTER_PASSWORD"]
        authenticated = admin_pass == correct_pass
        
        if authenticated:
            st.success("✅ Autenticado")
        elif admin_pass:
            st.error("❌ Contraseña incorrecta")
    
    # Only show navigation when authenticated
    if authenticated:
        st.subheader("Navegación")
        
        # Navigation buttons
        if st.button("📊 Panel de Control", use_container_width=True):
            st.session_state.page = "dashboard"
        if st.button("🖥️ Gestionar Equipos", use_container_width=True):
            st.session_state.page = "computers"
        if st.button("⚙️ Configuración SSH", use_container_width=True):
            st.session_state.page = "ssh"
        if st.button("📝 Registro de Actividad", use_container_width=True):
            st.session_state.page = "logs"
        if st.button("🛠️ Herramientas", use_container_width=True):
            st.session_state.page = "tools"
        
        # Show SSH configuration status
        st.subheader("Estado")
        
        if st.session_state.ssh_password:
            st.success("✅ Credenciales SSH configuradas")
        else:
            st.warning("⚠️ Faltan credenciales SSH")
            
        status_text = f"Usuario SSH: {st.session_state.ssh_user}"
        if st.session_state.sudo_pass:
            status_text += "\n✅ Contraseña sudo configurada"
        st.info(status_text)

# Main content area
if authenticated:
    # Dashboard page - Main control panel
    if st.session_state.page == "dashboard":
        st.title("Panel de Control")
        
        # Quick stats at the top
        col1, col2 = st.columns(2)
        with col1:
            computers = st.session_state.get('computers', [
                {"IP": "192.168.1.100", "OS": "Linux", "Description": "Server 1"},
                {"IP": "192.168.1.101", "OS": "Linux", "Description": "Server 2"}
            ])
            st.metric("Total de Equipos", len(computers))
        
        with col2:
            if st.session_state.ssh_password:
                st.success("Sistema listo para controlar equipos")
            else:
                st.warning("Configure las credenciales SSH para continuar")
        
        # Show computers status and controls
        if computers:
            st.subheader("Equipos disponibles")
            
            # Two tabs for immediate and scheduled shutdown
            tab1, tab2 = st.tabs(["🔴 Apagado Inmediato", "⏱️ Apagado Programado"])
            
            with tab1:
                st.info("Seleccione los equipos que desea apagar inmediatamente")
                
                # Display computers in a nice grid with action buttons
                for i in range(0, len(computers), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        idx = i + j
                        if idx < len(computers):
                            with cols[j]:
                                computer = computers[idx]
                                ip = computer["IP"]
                                os_type = computer["OS"]
                                description = computer.get("Description", "")
                                has_credentials = bool(computer.get('ssh_password', ''))
                                
                                # Create a card-like container for each computer
                                with st.container():
                                    st.subheader(f"{ip}")
                                    st.caption(f"{description} ({os_type})")
                                    
                                    # Show credential status
                                    if has_credentials:
                                        st.caption("✅ Credenciales configuradas")
                                    else:
                                        st.caption("⚠️ Sin credenciales específicas")
                                    
                                    if st.button("🔴 Apagar Ahora", key=f"shutdown_now_{ip}", use_container_width=True):
                                        # Use computer-specific credentials when available
                                        handle_immediate_shutdown(ip, os_type, computer)
                                        st.rerun()
            
            with tab2:
                st.subheader("Programar apagado")
                
                # Store the selected date and time in session state to prevent reset
                if 'selected_shutdown_date' not in st.session_state:
                    st.session_state.selected_shutdown_date = datetime.now().date()
                if 'selected_shutdown_time' not in st.session_state:
                    st.session_state.selected_shutdown_time = (datetime.now() + timedelta(minutes=5)).time()
                
                col1, col2 = st.columns(2)
                with col1:
                    selected_date = st.date_input(
                        "Fecha:", 
                        value=st.session_state.selected_shutdown_date,
                        min_value=datetime.now().date(),
                        key="shutdown_date"
                    )
                    st.session_state.selected_shutdown_date = selected_date
                    
                with col2:
                    selected_time = st.time_input(
                        "Hora:", 
                        value=st.session_state.selected_shutdown_time,
                        key="shutdown_time"
                    )
                    st.session_state.selected_shutdown_time = selected_time
                
                # Combine date and time for shutdown
                shutdown_time = datetime.combine(selected_date, selected_time)
                
                # Check if the selected time is valid (in the future)
                current_time = datetime.now()
                time_difference = shutdown_time - current_time
                minutes_difference = time_difference.total_seconds() / 60
                
                # Show scheduled time in user-friendly format with validation
                if minutes_difference <= 0:
                    st.error(f"⚠️ La hora seleccionada ({shutdown_time.strftime('%d/%m/%Y a las %H:%M')}) está en el pasado. Seleccione una hora futura.")
                    valid_time = False
                else:
                    st.info(f"📅 Hora programada: {shutdown_time.strftime('%d/%m/%Y a las %H:%M')} (en {int(minutes_difference)} minutos)")
                    valid_time = True
                
                # Select computers to schedule
                st.subheader("Seleccionar equipos")
                selected_computers = []
                
                for idx, computer in enumerate(computers):
                    has_credentials = bool(computer.get('ssh_password', ''))
                    credential_status = "✅" if has_credentials else "⚠️"
                    
                    selected = st.checkbox(
                        f"{computer['IP']} - {computer.get('Description', '')} ({credential_status})", 
                        key=f"select_computer_{idx}"
                    )
                    if selected:
                        selected_computers.append(computer)
                
                if len(selected_computers) > 0:
                    shutdown_button = st.button(
                        f"⏱️ Programar apagado para {len(selected_computers)} equipos", 
                        use_container_width=True,
                        disabled=not valid_time
                    )
                    
                    if shutdown_button:
                        if all(not pc.get('ssh_password', '') for pc in selected_computers):
                            st.error("⚠️ Ninguno de los equipos seleccionados tiene credenciales configuradas")
                        else:
                            success_count = 0
                            for pc in selected_computers:
                                ip = pc["IP"].strip()
                                os_type = pc["OS"]
                                
                                # Use computer-specific credentials
                                username = pc.get('ssh_user', st.session_state.ssh_user)
                                password = pc.get('ssh_password', st.session_state.ssh_password)
                                sudo_pass = pc.get('sudo_pass', st.session_state.sudo_pass)
                                
                                # Skip computers without credentials
                                if not password:
                                    st.session_state.shutdown_results.append({
                                        "success": False,
                                        "ip": ip,
                                        "os": os_type,
                                        "message": "No hay credenciales configuradas para este equipo",
                                        "time": datetime.now().strftime("%H:%M:%S")
                                    })
                                    continue
                                
                                if ip:
                                    success, message = schedule_shutdown(
                                        ip=ip,
                                        os_type=os_type,
                                        username=username,
                                        password=password,
                                        sudo_password=sudo_pass,
                                        shutdown_time=shutdown_time
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
                            
                            st.metric("Equipos programados", f"{success_count}/{len(selected_computers)}")
                            
                            # Show recent results
                            if success_count > 0:
                                st.success(f"✅ {success_count} equipos programados exitosamente")
                            if success_count < len(selected_computers):
                                st.error(f"❌ {len(selected_computers) - success_count} equipos fallaron")
                                st.info("Consulte el registro de actividad para más detalles")
                else:
                    st.warning("Seleccione al menos un equipo para programar")
    
    # Computer management page
    elif st.session_state.page == "computers":
        st.title("Gestión de Equipos")
        
        # Instructions
        st.info("Añada, edite o elimine equipos de la lista. Para cada equipo, puede configurar credenciales SSH específicas.")
        
        # Need to split the interface to allow credential editing
        tabs = st.tabs(["🖥️ Listado de Equipos", "🔑 Configurar Credenciales"])
        
        with tabs[0]:
            # Editable table of computers (basic info)
            computers_basic = st.data_editor(
                [{
                    "IP": c["IP"],
                    "OS": c["OS"],
                    "Description": c.get("Description", "")
                } for c in st.session_state.computers],
                column_config={
                    "IP": st.column_config.TextColumn("Dirección IP", required=True, width="medium"),
                    "OS": st.column_config.SelectboxColumn(
                        "Sistema Operativo",
                        options=["Linux", "Windows"],
                        required=True,
                        width="small"
                    ),
                    "Description": st.column_config.TextColumn("Descripción", width="large")
                },
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="computers_basic_editor"
            )
            
            # Update session state with basic info but preserve credentials
            updated_computers = []
            for idx, basic in enumerate(computers_basic):
                # Get existing credentials if any
                existing = st.session_state.computers[idx] if idx < len(st.session_state.computers) else {}
                updated_computer = {
                    "IP": basic["IP"],
                    "OS": basic["OS"],
                    "Description": basic.get("Description", ""),
                    "ssh_user": existing.get("ssh_user", st.session_state.ssh_user),
                    "ssh_password": existing.get("ssh_password", ""),
                    "sudo_pass": existing.get("sudo_pass", "")
                }
                updated_computers.append(updated_computer)
            
            # Add any new computers
            if len(computers_basic) > len(st.session_state.computers):
                for i in range(len(st.session_state.computers), len(computers_basic)):
                    updated_computers[i] = {
                        "IP": computers_basic[i]["IP"],
                        "OS": computers_basic[i]["OS"],
                        "Description": computers_basic[i].get("Description", ""),
                        "ssh_user": st.session_state.ssh_user,
                        "ssh_password": "",
                        "sudo_pass": ""
                    }
            
            st.session_state.computers = updated_computers

        with tabs[1]:
            st.subheader("Credenciales de acceso SSH")
            st.info("Configure las credenciales SSH específicas para cada equipo. Estos datos se utilizarán para la conexión remota.")
            
            # Show credential editor for each computer
            for idx, computer in enumerate(st.session_state.computers):
                with st.expander(f"{computer['IP']} - {computer.get('Description', '')}"):
                    # Create a form for each computer's credentials
                    with st.form(key=f"credentials_form_{idx}"):
                        cols = st.columns(3)
                        with cols[0]:
                            ssh_user = st.text_input(
                                "Usuario SSH:", 
                                value=computer.get("ssh_user", st.session_state.ssh_user),
                                key=f"ssh_user_{idx}"
                            )
                        with cols[1]:
                            ssh_password = st.text_input(
                                "Contraseña SSH:", 
                                type="password",
                                value=computer.get("ssh_password", ""),
                                key=f"ssh_password_{idx}"
                            )
                        with cols[2]:
                            sudo_pass = st.text_input(
                                "Contraseña sudo:", 
                                type="password",
                                value=computer.get("sudo_pass", ""),
                                help="Solo para Linux, si es diferente de la SSH",
                                key=f"sudo_pass_{idx}"
                            )
                            
                        if st.form_submit_button("Guardar credenciales"):
                            st.session_state.computers[idx]["ssh_user"] = ssh_user
                            st.session_state.computers[idx]["ssh_password"] = ssh_password
                            st.session_state.computers[idx]["sudo_pass"] = sudo_pass
                            st.success("✅ Credenciales actualizadas")
                        
        # Add option to import/export computer list
        st.subheader("Importar/Exportar")
        col1, col2 = st.columns(2)
        
        with col1:
            # Export only basic info (no passwords)
            st.download_button(
                "📥 Exportar lista de equipos (sin credenciales)",
                "\n".join([f"{c['IP']},{c['OS']},{c.get('Description', '')}" for c in st.session_state.computers]),
                file_name="computers_list.csv",
                mime="text/csv"
            )
        
        with col2:
            csv_file = st.file_uploader("Importar lista de equipos (CSV)", type="csv")
            if csv_file:
                try:
                    imported_computers = []
                    content = csv_file.getvalue().decode("utf-8")
                    for line in content.strip().split("\n"):
                        parts = line.split(",", 2)
                        if len(parts) >= 2:
                            imported_computers.append({
                                "IP": parts[0].strip(),
                                "OS": parts[1].strip(),
                                "Description": parts[2].strip() if len(parts) > 2 else "",
                                "ssh_user": st.session_state.ssh_user,
                                "ssh_password": "",
                                "sudo_pass": ""
                            })
                    
                    if imported_computers:
                        st.session_state.computers = imported_computers
                        st.success(f"✅ Importados {len(imported_computers)} equipos")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al importar: {str(e)}")
    
    # SSH Configuration page
    elif st.session_state.page == "ssh":
        st.title("Configuración SSH Global")
        
        st.info("""
        **Configuración de acceso SSH predeterminada:**
        
        Estas credenciales se utilizarán como valores predeterminados para equipos que no tengan credenciales específicas configuradas.
        Para configurar credenciales por equipo, vaya a "Gestionar Equipos" > "Configurar Credenciales".
        """)
        
        with st.form("ssh_config_form"):
            st.subheader("Credenciales SSH")
            
            ssh_user = st.text_input("Usuario SSH:", value=st.session_state.ssh_user)
            ssh_password = st.text_input("Contraseña SSH:", type="password", value=st.session_state.ssh_password)
            sudo_pass = st.text_input("Contraseña sudo (Linux):", type="password", value=st.session_state.sudo_pass, 
                                     help="Solo necesaria si es diferente de la contraseña SSH")
            
            submitted = st.form_submit_button("Guardar Configuración")
            
            if submitted:
                st.session_state.ssh_user = ssh_user
                st.session_state.ssh_password = ssh_password
                st.session_state.sudo_pass = sudo_pass
                
                if ssh_password:
                    st.success("✅ Configuración SSH actualizada")
                else:
                    st.warning("⚠️ Se requiere contraseña SSH")
        
        # SSH testing section
        st.subheader("Probar conexión SSH")
        
        test_ip = st.text_input("Dirección IP para probar:", placeholder="192.168.1.100")
        test_os = st.selectbox("Sistema operativo:", ["Linux", "Windows"])
        
        if st.button("🔄 Probar conexión"):
            if not test_ip:
                st.error("Ingrese una dirección IP")
            elif not st.session_state.ssh_password:
                st.error("Debe configurar una contraseña SSH primero")
            else:
                with st.spinner("Probando conexión..."):
                    try:
                        client = paramiko.SSHClient()
                        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        
                        st.info(f"Conectando a {test_ip} como {st.session_state.ssh_user}...")
                        
                        client.connect(
                            hostname=test_ip,
                            username=st.session_state.ssh_user,
                            password=st.session_state.ssh_password,
                            timeout=5
                        )
                        
                        # Test a simple command
                        cmd = "whoami" if test_os == "Linux" else "whoami"
                        stdin, stdout, stderr = client.exec_command(cmd)
                        output = stdout.read().decode().strip()
                        error = stderr.read().decode().strip()
                        
                        if error:
                            st.warning(f"Advertencia: {error}")
                        
                        # Probar que podamos obtener privilegios sudo (solo Linux)
                        if test_os == "Linux":
                            sudo_pwd = st.session_state.sudo_pass if st.session_state.sudo_pass else st.session_state.ssh_password
                            cmd = f'echo "{sudo_pwd}" | sudo -S id'
                            stdin, stdout, stderr = client.exec_command(cmd)
                            sudo_output = stdout.read().decode().strip()
                            sudo_error = stderr.read().decode().strip()
                            
                            if "uid=0" in sudo_output:
                                st.success("✅ Acceso sudo verificado")
                            else:
                                st.warning(f"⚠️ Posible problema con acceso sudo: {sudo_error}")
                        
                        st.success(f"✅ Conexión exitosa a {test_ip}")
                        st.code(f"Usuario: {output}")
                        
                        client.close()
                    except Exception as e:
                        st.error(f"❌ Error de conexión: {str(e)}")
                        st.info("Revise que los datos sean correctos y el equipo esté encendido y accesible.")

    # Logs page
    elif st.session_state.page == "logs":
        st.title("Registro de Actividad")
        
        # Controls to filter/clear logs
        col1, col2 = st.columns([3, 1])
        with col1:
            filter_type = st.selectbox("Filtrar por:", ["Todo", "Exitosos", "Errores"])
        with col2:
            if st.button("🗑️ Limpiar registro"):
                st.session_state.shutdown_results = []
                st.rerun()
        
        # Display filtered logs
        if st.session_state.shutdown_results:
            for result in st.session_state.shutdown_results[::-1]:  # Show newest first
                try:
                    ip = result.get("ip", "Unknown")
                    os_type = result.get("os", "Unknown")
                    message = result.get("message", "No message")
                    time_str = result.get("time", datetime.now().strftime("%H:%M:%S"))
                    success = result.get("success", False)
                    
                    # Apply filter
                    if filter_type == "Exitosos" and not success:
                        continue
                    if filter_type == "Errores" and success:
                        continue
                    
                    # Create a card-like display for each log entry
                    with st.container():
                        if success:
                            st.success(f"✅ [{time_str}] {ip} ({os_type}) - {message}")
                        else:
                            st.error(f"❌ [{time_str}] {ip} ({os_type}) - {message}")
                except Exception as e:
                    st.warning(f"Error al mostrar entrada de registro: {str(e)}")
        else:
            st.info("No hay registros de actividad")

    # Tools page - Additional utilities
    elif st.session_state.page == "tools":
        st.title("Herramientas")
        
        st.header("Script de Configuración para Equipos Remotos")
        
        st.info("""
        **Configuración de equipos remotos:**
        
        Para que un equipo Linux pueda ser controlado remotamente, debe tener:
        - OpenSSH Server instalado y en ejecución
        - Un usuario con permisos sudo
        - Configuración adecuada para permitir el comando de apagado
        
        El siguiente script automatiza esta configuración. Descárguelo y ejecútelo
        en cada equipo Linux que desee controlar remotamente.
        """)
        
        # Leer el contenido del script
        try:
            with open("setup-remote.sh", "r") as file:
                script_content = file.read()
                
            # Botón para descargar el script
            st.download_button(
                "📥 Descargar Script de Configuración",
                script_content,
                file_name="setup-remote.sh",
                mime="text/plain",
                help="Descargue este script y ejecútelo en los equipos remotos"
            )
            
            # Mostrar instrucciones
            st.subheader("Instrucciones")
            st.markdown("""
            1. Descargue el script en el equipo remoto
            2. Abra una terminal en ese equipo
            3. Ejecute los siguientes comandos:
            ```bash
            chmod +x setup-remote.sh
            sudo ./setup-remote.sh
            ```
            4. Siga las instrucciones en pantalla
            5. Una vez completado, el equipo estará listo para ser controlado remotamente
            """)
            
            # Mostrar ejemplo de uso manual por SSH
            st.subheader("Conexión manual por SSH")
            st.code("ssh usuario@ip 'sudo shutdown now'")
            
            # Mostrar el contenido del script para referencia
            with st.expander("Ver contenido del script"):
                st.code(script_content, language="bash")
                
        except FileNotFoundError:
            st.error("⚠️ El script de configuración no está disponible. Contacte al administrador.")
            
        # Otras herramientas útiles
        st.header("Otras Herramientas")
        
        # Herramienta de ping
        st.subheader("Verificar conectividad (ping)")
        
        ping_ip = st.text_input("Dirección IP:", placeholder="192.168.1.100", key="ping_ip")
        if st.button("Verificar conectividad"):
            if ping_ip:
                with st.spinner(f"Verificando conectividad con {ping_ip}..."):
                    import subprocess
                    try:
                        # Intentar hacer ping (diferente comando según sistema operativo)
                        param = '-n' if os.name == 'nt' else '-c'
                        command = ['ping', param, '4', ping_ip]
                        result = subprocess.run(command, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            st.success(f"✅ {ping_ip} está accesible")
                            st.code(result.stdout)
                        else:
                            st.error(f"❌ {ping_ip} no responde")
                            st.code(result.stderr)
                    except Exception as e:
                        st.error(f"Error al verificar conectividad: {str(e)}")
            else:
                st.warning("Ingrese una dirección IP para verificar")

else:
    # Show login screen when not authenticated
    st.title("⏰ Programador de Apagado Remoto")
    st.markdown("### Sistema para equipos Windows y Linux")
    
    st.info("Por favor, ingrese la contraseña maestra en el panel lateral para comenzar.")
    
    # Show a nice illustration or logo
    st.image("https://cdn-icons-png.flaticon.com/512/25/25235.png", width=150)
