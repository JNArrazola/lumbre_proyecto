#!/bin/bash

# Script para configurar un equipo Linux para permitir apagado remoto vía SSH
# Autor: Richy
# Fecha: 2023

echo "==================================================================="
echo "    Configurador de apagado remoto SSH para sistemas Linux"
echo "==================================================================="
echo ""

# Verificar que se ejecuta con privilegios de root
if [ "$(id -u)" -ne 0 ]; then
   echo "⚠️  Este script debe ejecutarse como root" 
   echo "   Ejecute: sudo bash $0"
   exit 1
fi

# Función para comprobar paquetes instalados
check_package() {
    if command -v $1 &>/dev/null; then
        echo "✅ $1 ya está instalado"
        return 0
    else
        echo "❌ $1 no está instalado"
        return 1
    fi
}

# Detectar gestor de paquetes
if command -v apt &>/dev/null; then
    PKG_MANAGER="apt"
elif command -v yum &>/dev/null; then
    PKG_MANAGER="yum"
elif command -v dnf &>/dev/null; then
    PKG_MANAGER="dnf"
else
    echo "❌ No se pudo detectar un gestor de paquetes compatible (apt, yum, dnf)"
    exit 1
fi

echo "📦 Usando gestor de paquetes: $PKG_MANAGER"
echo ""

# Actualizar repositorios
echo "🔄 Actualizando listas de repositorios..."
if [ "$PKG_MANAGER" = "apt" ]; then
    apt update -qq
elif [ "$PKG_MANAGER" = "yum" ]; then
    yum check-update -q
elif [ "$PKG_MANAGER" = "dnf" ]; then
    dnf check-update -q
fi

# Crear usuario "richy" con contraseña "hola123"
echo ""
echo "👤 Creando usuario richy..."

# Verificar si el usuario ya existe
if id "richy" &>/dev/null; then
    echo "✅ El usuario richy ya existe"
else
    # Crear usuario con contraseña y directorio home
    useradd -m -s /bin/bash richy
    echo "✅ Usuario richy creado"
    
    # Definir contraseña
    echo "richy:hola123" | chpasswd
    echo "✅ Contraseña establecida para el usuario richy"
    
    # Agregar al grupo sudo
    if [ "$PKG_MANAGER" = "apt" ]; then
        usermod -aG sudo richy
        echo "✅ Usuario richy añadido al grupo sudo"
    else
        usermod -aG wheel richy
        echo "✅ Usuario richy añadido al grupo wheel"
    fi
    
    echo "✅ Configuración de usuario richy completada"
fi

# Instalar o verificar OpenSSH server
echo ""
echo "🔒 Verificando OpenSSH server..."
if ! check_package "sshd"; then
    echo "📥 Instalando OpenSSH server..."
    if [ "$PKG_MANAGER" = "apt" ]; then
        apt install -y openssh-server
    elif [ "$PKG_MANAGER" = "yum" ]; then
        yum install -y openssh-server
    elif [ "$PKG_MANAGER" = "dnf" ]; then
        dnf install -y openssh-server
    fi
fi

# Configurar y iniciar SSH
echo ""
echo "🔧 Configurando servicio SSH..."
systemctl enable sshd
systemctl start sshd

# Verificar estado de SSH
if systemctl is-active --quiet sshd; then
    echo "✅ Servicio SSH activo y funcionando"
else
    echo "❌ Error: El servicio SSH no está ejecutándose"
    exit 1
fi

# Configurar sudo
echo ""
echo "🔑 Configurando permisos sudo..."
if ! check_package "sudo"; then
    echo "📥 Instalando sudo..."
    if [ "$PKG_MANAGER" = "apt" ]; then
        apt install -y sudo
    elif [ "$PKG_MANAGER" = "yum" ]; then
        yum install -y sudo
    elif [ "$PKG_MANAGER" = "dnf" ]; then
        dnf install -y sudo
    fi
fi

# Mostrar usuarios en /home
echo ""
echo "👥 Usuarios disponibles en el sistema:"
users=$(ls /home)
for user in $users
do
    if id "$user" &>/dev/null; then
        groups=$(groups "$user" | cut -d : -f 2)
        if [[ $groups == *"sudo"* ]] || [[ $groups == *"wheel"* ]]; then
            echo "   - $user (✅ Ya tiene permisos sudo)"
            HAS_SUDO_USER=1
        else
            echo "   - $user"
        fi
    fi
done

# Configurar un usuario para sudo si es necesario
if [ -z "$HAS_SUDO_USER" ] && [ ! $(id -u richy &>/dev/null; echo $?) -eq 0 ]; then
    echo ""
    echo "❗ No se encontró ningún usuario con permisos sudo"
    echo "Para que el apagado remoto funcione, necesita un usuario con permisos sudo."
    echo ""
    read -p "Ingrese el nombre de un usuario existente para añadirlo al grupo sudo: " selected_user
    
    if id "$selected_user" &>/dev/null; then
        if [ "$PKG_MANAGER" = "apt" ]; then
            usermod -aG sudo $selected_user
            echo "✅ Usuario $selected_user añadido al grupo sudo"
        else
            usermod -aG wheel $selected_user
            echo "✅ Usuario $selected_user añadido al grupo wheel"
        fi
    else
        echo "❌ El usuario $selected_user no existe"
        exit 1
    fi
fi

# Configurar NOPASSWD para el comando shutdown
echo ""
echo "🔧 Configurando sudo sin contraseña para el comando shutdown..."

if [ "$PKG_MANAGER" = "apt" ]; then
    SUDO_FILE="/etc/sudoers.d/shutdown-nopasswd"
else
    SUDO_FILE="/etc/sudoers.d/shutdown-nopasswd"
fi

cat > "$SUDO_FILE" <<EOF
# Permitir que los usuarios con sudo ejecuten shutdown sin contraseña
%sudo   ALL=(ALL) NOPASSWD: /sbin/shutdown, /usr/sbin/shutdown
%wheel  ALL=(ALL) NOPASSWD: /sbin/shutdown, /usr/sbin/shutdown
EOF

chmod 440 "$SUDO_FILE"
echo "✅ Configuración NOPASSWD para shutdown completada"

# Obtener la dirección IP
echo ""
echo "🌐 Información de red:"

# Listar todas las interfaces y sus IPs
interfaces=$(ip -o -4 addr show | awk '!/^[0-9]*: ?lo|link\/ether/ {print $2}')
for interface in $interfaces
do
    ip_addr=$(ip -o -4 addr show $interface | awk '{print $4}' | cut -d/ -f1)
    echo "   - Interface: $interface - IP: $ip_addr"
done

# Configurar el firewall si está presente
echo ""
echo "🔥 Configurando firewall para permitir SSH (puerto 22)..."

if command -v ufw &>/dev/null; then
    # Ubuntu/Debian firewall
    ufw allow ssh
    echo "✅ UFW: Puerto SSH habilitado"
elif command -v firewall-cmd &>/dev/null; then
    # CentOS/RHEL/Fedora firewall
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --reload
    echo "✅ FirewallD: Puerto SSH habilitado"
else
    echo "⚠️  No se detectó firewall. Asegúrese de que el puerto 22 esté abierto."
fi

# Instrucciones finales
echo ""
echo "==================================================================="
echo "✅ ¡Configuración completada con éxito!"
echo "==================================================================="
echo ""
echo "Ahora puede conectarse remotamente y apagar este equipo usando:"
echo ""
echo "1. Dirección IP: Una de las mostradas arriba"
echo "2. Usuario SSH: richy (contraseña: hola123) o cualquier usuario con permisos sudo"
echo "3. Para otros usuarios: Contraseña del usuario seleccionado"
echo ""
echo "Para probar el apagado, intente ejecutar:"
echo "   ssh richy@[ip] 'sudo shutdown now'"
echo ""
echo "==================================================================="
