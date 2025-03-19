# tools.py
import streamlit as st
import os

def app():
    st.title("Herramientas")
    
    st.header("Script de Configuración para Equipos Remotos")
    st.info(
        """
        **Configuración de equipos remotos:**
        
        Para que un equipo Linux pueda ser controlado remotamente, debe tener:
        - OpenSSH Server instalado y en ejecución.
        - Un usuario con permisos sudo.
        - Configuración adecuada para permitir el comando de apagado.
        
        El siguiente script automatiza esta configuración. Descárguelo y ejecútelo en cada equipo Linux que desee controlar remotamente.
        """
    )
    
    try:
        with open("setup-remote.sh", "r") as file:
            script_content = file.read()
        st.download_button(
            "📥 Descargar Script de Configuración",
            script_content,
            file_name="setup-remote.sh",
            mime="text/plain",
            help="Descargue este script y ejecútelo en los equipos remotos"
        )
        
        st.subheader("Instrucciones")
        st.markdown(
            """
            1. Descargue el script en el equipo remoto.
            2. Abra una terminal en ese equipo.
            3. Ejecute los siguientes comandos:
            ```bash
            chmod +x setup-remote.sh
            sudo ./setup-remote.sh
            ```
            4. Siga las instrucciones en pantalla.
            5. Una vez completado, el equipo estará listo para ser controlado remotamente.
            """
        )
        
        st.subheader("Conexión manual por SSH")
        st.code("ssh usuario@ip 'sudo shutdown now'")
        
        with st.expander("Ver contenido del script"):
            st.code(script_content, language="bash")
    except FileNotFoundError:
        st.error("⚠️ El script de configuración no está disponible. Contacte al administrador.")
    
    st.header("Otras Herramientas")
    st.subheader("Verificar conectividad (ping)")
    ping_ip = st.text_input("Dirección IP:", placeholder="192.168.1.100", key="ping_ip")
    if st.button("Verificar conectividad"):
        if ping_ip:
            with st.spinner(f"Verificando conectividad con {ping_ip}..."):
                import subprocess
                try:
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
