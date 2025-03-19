# computers.py
import streamlit as st

def app():
    st.title("Gestión de Equipos")
    
    st.info("Añada, edite o elimine equipos de la lista. Para cada equipo, puede configurar credenciales SSH específicas.")
    
    tabs = st.tabs(["🖥️ Listado de Equipos", "🔑 Configurar Credenciales"])
    
    with tabs[0]:
        # Editor para información básica de equipos (sin credenciales)
        computers_basic = st.data_editor(
            [
                {"IP": c["IP"], "OS": c["OS"], "Description": c.get("Description", "")} 
                for c in st.session_state.computers
            ],
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
        
        # Actualiza la lista de equipos sin perder las credenciales ya configuradas
        updated_computers = []
        for idx, basic in enumerate(computers_basic):
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
        
        # Si se agregaron nuevas filas, inicializarlas
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
        
        for idx, computer in enumerate(st.session_state.computers):
            with st.expander(f"{computer['IP']} - {computer.get('Description', '')}"):
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
        
        st.subheader("Importar/Exportar")
        col1, col2 = st.columns(2)
        with col1:
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
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error al importar: {str(e)}")
