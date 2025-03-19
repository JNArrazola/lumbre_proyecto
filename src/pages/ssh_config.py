# ssh_config.py
import streamlit as st
import paramiko
from datetime import datetime

def app():
    st.title("Configuración SSH Global")
    
    st.info(
        """
        **Configuración de acceso SSH predeterminada:**
        
        Estas credenciales se utilizarán como valores predeterminados para:
        1. Equipos nuevos que se agreguen al sistema.
        2. Equipos existentes que no tengan credenciales específicas configuradas.
        
        Para configurar credenciales específicas por equipo, vaya a "Gestionar Equipos" > "Configurar Credenciales".
        """
    )
    
    with st.form("ssh_config_form"):
        st.subheader("Credenciales SSH")
        ssh_user = st.text_input("Usuario SSH:", value=st.session_state.ssh_user)
        ssh_password = st.text_input("Contraseña SSH:", type="password", value=st.session_state.ssh_password)
        sudo_pass = st.text_input(
            "Contraseña sudo (Linux):",
            type="password",
            value=st.session_state.sudo_pass,
            help="Solo necesaria si es diferente de la contraseña SSH"
        )
        apply_to_all = st.checkbox(
            "Aplicar a todos los equipos (sobrescribir credenciales individuales)",
            help="Marque esta opción para sobrescribir todas las credenciales individuales con estos valores"
        )
        submitted = st.form_submit_button("Guardar Configuración")
        
        if submitted:
            # Actualizar credenciales globales
            st.session_state.ssh_user = ssh_user
            st.session_state.ssh_password = ssh_password
            st.session_state.sudo_pass = sudo_pass
            
            updated_count = 0
            total_count = len(st.session_state.computers)
            
            # Actualiza equipos sin credenciales o todos si se selecciona la opción
            for i, computer in enumerate(st.session_state.computers):
                if apply_to_all or not computer.get('ssh_password'):
                    st.session_state.computers[i]['ssh_user'] = ssh_user
                    st.session_state.computers[i]['ssh_password'] = ssh_password
                    st.session_state.computers[i]['sudo_pass'] = sudo_pass
                    updated_count += 1
            
            if ssh_password:
                if apply_to_all:
                    st.success(f"✅ Configuración SSH actualizada y aplicada a todos los equipos ({updated_count}/{total_count})")
                else:
                    st.success(f"✅ Configuración SSH actualizada y aplicada a equipos sin credenciales ({updated_count}/{total_count})")
            else:
                st.warning("⚠️ Se requiere contraseña SSH")
            
            if updated_count > 0:
                st.info("Los equipos actualizados se marcarán con ✅ en el Panel de Control")
    
    st.subheader("Estado de Credenciales")
    no_creds = [c for c in st.session_state.computers if not c.get('ssh_password')]
    if no_creds:
        st.warning(f"Hay {len(no_creds)} equipos sin credenciales configuradas:")
        for comp in no_creds:
            st.markdown(f"• {comp['IP']} - {comp.get('Description', '')}")
    else:
        st.success("✅ Todos los equipos tienen credenciales configuradas")
                
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
                    
                    cmd = "whoami"
                    stdin, stdout, stderr = client.exec_command(cmd)
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    
                    if error:
                        st.warning(f"Advertencia: {error}")
                    
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
