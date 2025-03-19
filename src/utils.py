# utils.py
from datetime import datetime

def init_session_state(st):
    """Inicializa las variables del session_state si no existen."""
    defaults = {
        "shutdown_results": [],
        "ssh_user": "admin",
        "ssh_password": "",
        "sudo_pass": "",
        "page": "dashboard",
        "computers": [
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

import streamlit as st
def rerun():
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        # Alternativamente, podrías simplemente detener la ejecución
        st.stop()


def format_time(dt):
    return dt.strftime("%H:%M:%S")
