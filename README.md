# Control Remoto de Apagado vía SSH

Este proyecto permite apagar equipos Linux y Windows de forma remota a través de SSH. Proporciona una interfaz web construida con Streamlit, que ofrece opciones tanto de apagado inmediato como programado.

## Tabla de Contenidos
- [Control Remoto de Apagado vía SSH](#control-remoto-de-apagado-vía-ssh)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [Introducción](#introducción)
  - [Requisitos Funcionales](#requisitos-funcionales)
  - [Requisitos No Funcionales](#requisitos-no-funcionales)
  - [Prerrequisitos](#prerrequisitos)
  - [Instalación](#instalación)
  - [Herramientas y Utilidades Adicionales](#herramientas-y-utilidades-adicionales)
  - [Mantenimiento y Actualizaciones](#mantenimiento-y-actualizaciones)
  - [Soporte](#soporte)

---

## Introducción
En entornos de TI, puede resultar esencial gestionar remotamente el apagado de servidores o estaciones de trabajo. Este proyecto está diseñado para simplificar esa tarea, ofreciendo una aplicación que se conecta vía SSH a los equipos y permite apagarlos, ya sea de inmediato o en una fecha y hora programadas.

---

## Requisitos Funcionales
1. **Autenticación con Contraseña Maestra**: El sistema debe solicitar al usuario una contraseña maestra para acceder a la interfaz.
2. **Gestión de Equipos**: El usuario debe poder agregar, editar y eliminar equipos, especificando sus datos (IP, sistema operativo, descripción) y credenciales SSH.
3. **Configuración SSH**: El sistema debe permitir configurar credenciales SSH globales que se apliquen a todos los equipos que no tengan credenciales específicas.
4. **Apagado Inmediato**: Se debe habilitar el envío de un comando de apagado inmediato a un equipo seleccionado.
5. **Apagado Programado**: Se debe habilitar la programación de un apagado en una fecha y hora específica, ya sea para un equipo o para varios.
6. **Registro de Actividad (Logs)**: El sistema debe registrar cada intento de apagado, indicando fecha, hora, equipo, éxito o error.
7. **Herramientas de Conectividad**: El usuario debe poder comprobar la accesibilidad de un equipo (por ejemplo, mediante ping) antes de proceder con el apagado.

---

## Requisitos No Funcionales
1. **Usabilidad**: La interfaz de usuario debe ser clara, intuitiva y amigable.
2. **Rendimiento**: La aplicación debe responder de manera ágil a las interacciones del usuario.
3. **Seguridad**: La contraseña maestra y las credenciales SSH deben manejarse de forma segura, sin exponer datos sensibles en texto claro.
4. **Compatibilidad**: El sistema debe ejecutarse en Python 3.8 o superior y funcionar tanto en entornos Windows como Linux.
5. **Mantenibilidad**: El código debe estar organizado en módulos, siguiendo buenas prácticas de desarrollo para facilitar su mantenimiento y evolución.

---

## Prerrequisitos
1. **Python 3.8 o superior**.
2. **Servidor OpenSSH** activo en las máquinas remotas (Linux o Windows).
3. **Usuario con privilegios sudo** en Linux, si se requiere un apagado sin solicitar contraseña.
4. **Windows** con OpenSSH Server habilitado.
5. **Librerías de Python** necesarias (por ejemplo, `streamlit`, `paramiko`, etc.).

---

## Instalación

1. **Clonar el Repositorio**
2. **Crear y Activar un Entorno Virtual (Opcional pero Recomendado)**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```
3. **Instalar las Dependencias**:
   ```bash
    pip install -r requirements.txt
    ```

---

## Configuración

### Configuración de SSH en los Equipos Remotos

#### Linux
1. Instalar y habilitar el servidor OpenSSH:
    ```bash
    sudo apt-get update && sudo apt-get install openssh-server
    sudo systemctl enable ssh
    sudo systemctl start ssh
    ```
2. (Opcional) Para omitir la contraseña al ejecutar `shutdown`, editar el archivo `sudoers` con `visudo`:
    ```bash
    tu_usuario ALL=(ALL) NOPASSWD: /sbin/shutdown
    ```
3. Verificar que el puerto 22 (o el que corresponda) esté abierto en el firewall.

#### Windows
1. Ir a **Panel de Control** > **Programas** > **Activar o desactivar las características de Windows**.
2. Activar **OpenSSH Server**.
3. Iniciar el servicio OpenSSH desde la sección de **Servicios** si no está activo.

### Configuración de la Aplicación
1. **Contraseña Maestra**: Define la contraseña maestra en los secretos de Streamlit (`.streamlit/secrets.toml`) o en una variable de entorno:
    ```toml
    [secret]
    MASTER_PASSWORD="MI_CONTRASEÑA_MAESTRA"
    ```
2. **Credenciales SSH Globales**: Configura un usuario y contraseña globales dentro de la aplicación, en la sección de configuración SSH. Estas credenciales se aplican a todos los equipos que no tengan credenciales específicas asignadas.
3. **Credenciales Específicas por Equipo**: En la sección "Gestionar Equipos" se pueden agregar o sobrescribir las credenciales para cada equipo en particular.
4. **Puertos SSH**: Por defecto, el sistema intenta conectar al puerto 22. Si tus equipos usan otro puerto, deberás ajustarlo manualmente en el código que establece la conexión (generalmente en `paramiko.connect()`).

---

## Uso

1. **Ejecutar la Aplicación**:
   ```bash
    streamlit run src/main.py
    ```
2. **Iniciar Sesión**: Ingresa la contraseña maestra en el panel lateral.
3. **Panel de Control**:
   - **Apagado Inmediato**: Selecciona un equipo y haz clic en "Apagar Ahora".
   - **Apagado Programado**: Indica una fecha y hora futura, elige uno o varios equipos y presiona "Programar Apagado".
4. **Gestionar Equipos**: Añade, edita o elimina equipos. Cada uno puede tener credenciales SSH propias.
5. **Configuración SSH**: Ajusta las credenciales SSH predeterminadas que se aplicarán a los equipos sin configuraciones individuales.
6. **Registro de Actividad**: Revisa el historial de apagados realizados, con detalles sobre éxito o error.
7. **Herramientas**: Encuentra utilidades como la verificación de conectividad (ping) y scripts de configuración para equipos Linux.

---

## Estructura del Proyecto
```
proyecto_lumbreras/
│   requirements.txt          # Dependencias
│   README.md                 # Documentación
│   setup-remote.sh           # (Opcional) Script de configuración para Linux
└── src/
    ├── main.py               # Punto de entrada de la aplicación Streamlit
    ├── utils.py              # Funciones utilitarias generales
    ├── ssh_manager.py        # Lógica de conexión y apagado vía SSH
    ├── computer_manager.py   # Gestión de la lista de equipos
    ├── pages/
    │   ├── dashboard.py      # Panel de control principal (apagado inmediato y programado)
    │   ├── computers.py      # Gestión de equipos
    │   ├── ssh_config.py     # Configuración SSH global
    │   ├── logs.py           # Registro de actividad
    │   └── tools.py          # Herramientas adicionales (ping, etc.)
```

---

## Herramientas y Utilidades Adicionales
- **Prueba de Conexión (Ping)**: Permite verificar si un host remoto está accesible.
- **Script de Configuración para Linux** (`setup-remote.sh`): Automatiza la instalación de OpenSSH y la configuración de privilegios sudo.

---

## Mantenimiento y Actualizaciones
- **Actualizar Dependencias**:
    ```bash
    pip install --upgrade -r requirements.txt
    ```
- **Obtener Últimos Cambios**:
    ```bash
    git pull origin main
    ```
- **Buenas Prácticas**:
  - Mantén tu código modular y documentado.
  - Revisa periódicamente los registros de actividad (Logs) para detectar problemas de conexión.
  - Asegura que las contraseñas y credenciales se guarden de forma segura.

---

## Soporte
Si encuentras algún problema, abre un incidente (issue) en el repositorio de GitHub o contacta al responsable del proyecto. Proporciona la mayor cantidad de detalles posible, incluyendo el registro de errores y mensajes de la aplicación.
