# ssh_manager.py
import paramiko
import time
from datetime import datetime

def schedule_shutdown(ip, os_type, username, password, sudo_password=None, shutdown_time=None, immediate=False):
    """
    Programa o ejecuta el apagado inmediato en la máquina remota.
    
    Para apagado programado en Linux, se calcula el delay (en segundos)
    entre el momento actual y la hora indicada, y se ejecuta:
    
        sleep {delay_seconds}; shutdown now
    """
    try:
        # Validación de parámetros obligatorios
        if not ip or not os_type or not username or not password:
            return False, "Missing required parameters"
            
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Conexión vía SSH usando autenticación por contraseña
            client.connect(
                hostname=ip,
                username=username,
                password=password,
                timeout=10
            )
        except Exception as e:
            return False, f"SSH connection error: {str(e)}"
            
        # Se obtiene la contraseña sudo; si no se provee, se usa la contraseña SSH
        sudo_pwd = sudo_password if sudo_password else password
        
        # Verificar conexión básica (por ejemplo, obtener el usuario actual)
        try:
            stdin, stdout, stderr = client.exec_command("whoami")
            connected_user = stdout.read().decode().strip()
            # Se puede registrar la conexión exitosa si se desea
        except Exception as e:
            return False, f"Error ejecutando comando básico: {str(e)}"
        
        # Lógica para sistemas Linux
        if os_type == "Linux":
            if immediate:
                # Apagado inmediato: se prueban dos comandos
                commands = [
                    f'echo "{sudo_pwd}" | sudo -S shutdown now',
                    f'echo "{sudo_pwd}" | sudo -S bash -c "shutdown now"'
                ]
                for i, cmd in enumerate(commands):
                    try:
                        client.exec_command(cmd)
                        # Se espera un poco, ya que el equipo puede desconectar rápidamente
                        time.sleep(2)
                        return True, "Comando de apagado enviado con éxito"
                    except Exception as e:
                        if i == len(commands) - 1:
                            return False, f"Fallaron todos los intentos de apagado: {str(e)}"
                        continue
            else:
                # Apagado programado: se usa un delay (sleep) antes de ejecutar shutdown now
                if not shutdown_time:
                    return False, "No shutdown time provided for scheduled shutdown"
                    
                now = datetime.now()
                time_diff = shutdown_time - now
                delay_seconds = max(1, int(time_diff.total_seconds()))  # Al menos 1 segundo
                
                # El comando se compone de: esperar 'delay_seconds' y luego ejecutar shutdown now
                command = f'echo "{sudo_pwd}" | sudo -S bash -c "sleep {delay_seconds}; shutdown now"'
                
                try:
                    stdin, stdout, stderr = client.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()
                    error = stderr.read().decode().strip()
                    
                    if exit_status != 0 or error:
                        return False, f"Error programando apagado: {error}"
                        
                    return True, f"Apagado programado para {shutdown_time.strftime('%H:%M')}"
                except Exception as e:
                    return False, f"Error programando apagado: {str(e)}"
        
        # Lógica para sistemas Windows
        elif os_type == "Windows":
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
            except Exception:
                pass  # Ignorar errores al cerrar la conexión

def handle_immediate_shutdown(ip, os_type, computer=None):
    """
    Maneja el apagado inmediato usando credenciales específicas para el equipo,
    o utiliza las globales almacenadas en session_state.
    """
    # Se obtienen las credenciales específicas del equipo (o se usan valores globales)
    username = computer.get('ssh_user', "admin") if computer else "admin"
    password = computer.get('ssh_password', "")
    sudo_pass = computer.get('sudo_pass', "")
    
    if not password:
        return
    
    ip = ip.strip()
    
    if not ip:
        return
        
    success, message = schedule_shutdown(
        ip=ip, 
        os_type=os_type, 
        username=username, 
        password=password,
        sudo_password=sudo_pass,
        immediate=True
    )
    
    return success, message
