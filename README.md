# Documentación Técnica

Esta documentación está pensada para desarrolladores que deseen colaborar o extender el proyecto de apagado remoto vía SSH. Aquí se describe la arquitectura del código, la organización en módulos y las directrices para mantenimiento y nuevas funcionalidades.

---

## Tabla de Contenidos
- [Documentación Técnica](#documentación-técnica)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [Descripción General del Proyecto](#descripción-general-del-proyecto)
  - [Arquitectura de la Aplicación](#arquitectura-de-la-aplicación)
  - [Entorno de Desarrollo](#entorno-de-desarrollo)
  - [Estructura de Archivos](#estructura-de-archivos)
  - [Módulos Principales](#módulos-principales)
    - [1. `ssh_manager.py`](#1-ssh_managerpy)
    - [2. `computer_manager.py`](#2-computer_managerpy)
    - [3. `main.py`](#3-mainpy)
    - [4. `pages/`](#4-pages)
    - [5. `utils.py`](#5-utilspy)
  - [Cómo Agregar Nuevas Páginas](#cómo-agregar-nuevas-páginas)
  - [Configuración y Variables de Entorno](#configuración-y-variables-de-entorno)
  - [Gestión de Dependencias](#gestión-de-dependencias)
  - [Puesta en Marcha y Depuración](#puesta-en-marcha-y-depuración)
  - [Pruebas y Validación](#pruebas-y-validación)
  - [Lineamientos de Estilo](#lineamientos-de-estilo)

---

## Descripción General del Proyecto
Este proyecto permite el control remoto de apagado de equipos (Linux y Windows) utilizando SSH. Está construido sobre la biblioteca **Streamlit**, lo que facilita la creación rápida de interfaces web interactivas. El proyecto implementa:
- Apagado inmediato y programado.
- Manejo de credenciales SSH (globales y por equipo).
- Registro de la actividad de apagado.
- Funciones de utilidad (ping, etc.) para verificación de conectividad.

Los objetivos principales son:
- Proveer una interfaz web unificada para la administración de apagados remotos.
- Evitar al usuario final la complejidad de usar clientes SSH y recordar comandos manualmente.
- Permitir la escalabilidad: manejo de múltiples equipos con credenciales diferentes.

---

## Arquitectura de la Aplicación
1. **Capa de Presentación (Streamlit):** Se compone de diferentes páginas (`dashboard.py`, `computers.py`, etc.) que forman la interfaz web.
2. **Capa de Lógica y Servicios (ssh_manager, computer_manager):** Contiene funciones que encapsulan la lógica de conexión, ejecución de comandos y programaciones de apagado.
3. **Capa de Datos (Session State de Streamlit):** Emplea el session state integrado de Streamlit para mantener los datos en memoria (lista de equipos, credenciales, logs).

---

## Entorno de Desarrollo
Para contribuir o extender este proyecto, se recomienda:
1. **Instalar Python 3.8 o superior**.
2. **Crear un entorno virtual** con `venv` o similar.
3. **Activar el entorno** y luego instalar las dependencias con `pip install -r requirements.txt`.

Opcionalmente, se puede usar **Docker**. Sin embargo, no se incluye un `Dockerfile` por defecto en el repositorio. Si deseas contenedorizarlo, deberás crear tu propio archivo Docker e incluir la instalación de Python y las dependencias.

---

## Estructura de Archivos
```
turnoff-remote-ssh/
│   requirements.txt          # Dependencias
│   README.md                 # Documentación general (usuario)
│   DEVELOPER_DOCS.md         # Documentación técnica (este archivo)
│   setup-remote.sh           # Script opcional para configurar SSH en Linux remoto
└── src/
    ├── main.py               # Punto de entrada de la aplicación Streamlit
    ├── utils.py              # Funciones utilitarias
    ├── ssh_manager.py        # Lógica de conexiones SSH y apagado
    ├── computer_manager.py   # Manejo de la lista de equipos (CRUD en session state)
    └── pages/
        ├── dashboard.py      # Panel de control principal
        ├── computers.py      # Gestión de equipos
        ├── ssh_config.py     # Configuración SSH
        ├── logs.py           # Registro de actividad
        └── tools.py          # Herramientas adicionales (ping, etc.)
```

- **`main.py`**: Arranca la aplicación Streamlit, maneja la autenticación y la navegación.
- **`pages/`**: Cada archivo `.py` dentro de esta carpeta corresponde a una pantalla o sección de la aplicación.
- **`ssh_manager.py`**: Funciones para conectarse vía SSH (usando Paramiko) y ejecutar el apagado inmediato o programado.
- **`computer_manager.py`**: Lógica de negocio para CRUD de equipos en memoria.
- **`utils.py`**: Funciones auxiliares (por ejemplo, formatear fechas, reiniciar la app, etc.).

---

## Módulos Principales

### 1. `ssh_manager.py`
- **Objetivo**: Centralizar la conexión SSH y la ejecución de comandos remotos.
- **Funciones Clave**:
  - `schedule_shutdown(ip, os_type, username, password, sudo_password, shutdown_time, immediate)`: Programa o ejecuta de inmediato el apagado según los parámetros.
  - `handle_immediate_shutdown(ip, os_type, computer)`: Facilita el apagado inmediato usando las credenciales definidas.
- **Tecnología**: Usa `paramiko` para el manejo de la conexión.

### 2. `computer_manager.py`
- **Objetivo**: Gestionar la lista de equipos en el estado de sesión de Streamlit.
- **Funciones Clave**:
  - `get_computers(session_state)`: Devuelve la lista de equipos.
  - `update_computers(session_state, new_list)`: Actualiza la lista de equipos.
- **Notas**: El almacenamiento es transitorio (en memoria). Para persistir datos, habría que integrar una base de datos.

### 3. `main.py`
- **Objetivo**: Punto de entrada de la aplicación Streamlit.
- **Responsabilidades**:
  - Inicializa el `session_state`.
  - Carga o verifica la contraseña maestra (definida en `st.secrets`).
  - Ofrece la barra lateral con la navegación.
  - Redirige a cada página (en `pages/`) según la selección del usuario.

### 4. `pages/`
- **dashboard.py**: Pantalla principal con apagado inmediato y programado.
- **computers.py**: Gestión de la lista de equipos, edición de credenciales individuales.
- **ssh_config.py**: Configuración SSH global (usuario/password predeterminados).
- **logs.py**: Muestra la actividad registrada de apagados (éxitos y errores).
- **tools.py**: Herramientas adicionales (ping, descarga de script `setup-remote.sh`, etc.).

### 5. `utils.py`
- **Objetivo**: Contener funciones de utilidad (por ejemplo, formatear hora, recargar la app, etc.).
- **Ejemplo**:
  - `format_time(dt)`: Retorna un string con el tiempo formateado.
  - `rerun()`: Llama a `st.experimental_rerun()` (o un mecanismo alternativo si la versión de Streamlit no lo soporta).

---

## Cómo Agregar Nuevas Páginas
1. Crea un archivo `.py` en la carpeta `pages/` con el nombre de la nueva funcionalidad.
2. Define una función principal `app()` que use las funciones de Streamlit para construir la interfaz.
3. En `main.py`, agrega la lógica de navegación para que el usuario pueda acceder a la nueva página (por ejemplo, un nuevo botón en la barra lateral).
4. Opcionalmente, si la página requiere lógica nueva, crea un módulo adicional en `src/` para encapsular dicha lógica.

---

## Configuración y Variables de Entorno
- **Contraseña Maestra**: Se espera en `st.secrets["MASTER_PASSWORD"]`. Alternativamente, puedes definirla en una variable de entorno y leerla desde Python.
- **Otros Ajustes**:
  - El puerto SSH por defecto se define en `ssh_manager.py`. Si es distinto de 22, modifica la llamada a `client.connect()`.
  - Para habilitar logs más detallados, puedes usar la librería estándar `logging` de Python.

---

## Gestión de Dependencias
- Las dependencias se enumeran en `requirements.txt`.
- Para instalarlas:
  ```bash
  pip install -r requirements.txt
  ```
- Al agregar nuevas bibliotecas, actualiza `requirements.txt`:
  ```bash
  pip freeze > requirements.txt
  ```

---

## Puesta en Marcha y Depuración
1. **Arranque**:
   ```bash
   streamlit run src/main.py
   ```
2. **Autenticación**: Ingresa la contraseña maestra en la barra lateral.
3. **Visualización de Errores**: Streamlit muestra los errores directamente en la interfaz y en la consola. Si un comando SSH falla, se registrará en la sección de logs o en la salida.
4. **Log de Actividad**: Cada intento de apagado genera una entrada en `st.session_state.shutdown_results`. Puedes revisar la página de logs.

---

## Pruebas y Validación
Actualmente, el proyecto no contiene un conjunto formal de pruebas unitarias. Para validaciones básicas:
1. **SSH en Equipos de Prueba**: Configura un contenedor Linux o una VM Windows con OpenSSH para comprobar las rutas de apagado.
2. **Validación Manual**: Inicia la app, añade equipos de ejemplo y ejecuta apagados inmediatos y programados.
3. **Integración**: Si deseas pruebas más extensas, se recomienda usar `pytest` o un framework de pruebas similar.

---

## Lineamientos de Estilo
- **PEP 8**: Se sugiere seguir la convención de estilo PEP 8 en Python.
- **Nombres de Funciones y Variables**: Usar nombres descriptivos en inglés o español, pero de forma consistente.
- **Modularidad**: Separar la lógica de negocio (por ejemplo, `ssh_manager`) de la capa de presentación (Streamlit).

---