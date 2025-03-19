# computer_manager.py
def get_computers(session_state):
    """Obtiene la lista de computadoras del session_state o una lista por defecto."""
    if 'computers' not in session_state:
        session_state.computers = [
            {
                "IP": "192.168.1.100",
                "OS": "Linux",
                "Description": "Prueba",
                "ssh_user": "test",
                "ssh_password": "test",
                "sudo_pass": "test"
            },
        ]
    return session_state.computers

def update_computers(session_state, new_list):
    """Actualiza la lista de computadoras en el session_state."""
    session_state.computers = new_list
