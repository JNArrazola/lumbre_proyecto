# computer_manager.py
def get_computers(session_state):
    """Obtiene la lista de computadoras del session_state o una lista por defecto."""
    if 'computers' not in session_state:
        session_state.computers = [
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
    return session_state.computers

def update_computers(session_state, new_list):
    """Actualiza la lista de computadoras en el session_state."""
    session_state.computers = new_list
