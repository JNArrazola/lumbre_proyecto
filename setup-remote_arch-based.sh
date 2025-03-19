#!/bin/bash

# Script para configurar un equipo Linux para permitir apagado remoto vía SSH en Arch Linux
# Autor: Richy (Modificado para pacman)
# Fecha: 2025

echo "==================================================================="
echo "    Configurador de apagado remoto SSH para Arch Linux"
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
    if pacman -Qi $1 &>/dev/null; then
        echo "✅ $1 ya está instalado"
        return 0
    else
        echo "❌ $1 no está instalado"
        return 1
    fi
}

# Actualizar repositorios
echo "🔄 Actualizando listas de repositorios..."
pacman -Sy --noconfirm

echo ""
echo "🔒 Verificando OpenSSH server..."
if ! check_package "openssh"; then
    echo "📥 Instalando OpenSSH server..."
    pacman -S --noconfirm openssh
fi

# Configurar y activar SSH
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

echo ""
echo "🔑 Verificando instalación de sudo..."
if ! check_package "sudo"; then
    echo "📥 Instalando sudo..."
    pacman -S --noconfirm sudo
fi

echo ""
echo "👥 Usuarios disponibles en el sistema:"
users=$(ls /home)
for user in $users
do
    if id "$user" &>/dev/null; then
        groups=$(groups "$user" | cut -d : -f 2)
        if [[ $groups == *"wheel"* ]]; then
            echo "   - $user (✅ Ya tiene permisos sudo)"
            HAS_SUDO_USER=1
        else
            echo "   - $user"
        fi
    fi
done

# Configurar un usuario para sudo si es necesario
if [ -z "$HAS_SUDO_USER" ]; then
    echo ""
    echo "❗ No se encontró ningún usuario con permisos sudo"
    echo "Para que el apagado remoto funcione, necesita un usuario con permisos sudo."
    echo ""
    read -p "Ingrese el nombre de un usuario existente para añadirlo al grupo wheel: " selected_user
    
    if id "$selected_user" &>/dev/null; then
        usermod -aG wheel $selected_user
        echo "✅ Usuario $selected_user añadido al grupo wheel"
    else
        echo "❌ El usuario $selected_user no existe"
        exit 1
    fi
fi

echo ""
echo "🔧 Configurando sudo sin contraseña para el comando shutdown..."
SUDO_FILE="/etc/sudoers.d/shutdown-nopasswd"
cat > "$SUDO_FILE" <<EOF
# Permitir que los usuarios con sudo ejecuten shutdown sin contraseña
%wheel  ALL=(ALL) NOPASSWD: /sbin/shutdown, /usr/sbin/shutdown
EOF
chmod 440 "$SUDO_FILE"
echo "✅ Configuración NOPASSWD para shutdown completada"

echo ""
echo "🌐 Información de red:"
interfaces=$(ip -o -4 addr show | awk '!/^[0-9]*: ?lo|link\/ether/ {print $2}')
for interface in $interfaces
do
    ip_addr=$(ip -o -4 addr show $interface | awk '{print $4}' | cut -d/ -f1)
    echo "   - Interface: $interface - IP: $ip_addr"
done

echo ""
echo "🔥 Configurando firewall para permitir SSH (puerto 22)..."
if command -v ufw &>/dev/null; then
    ufw allow ssh
    echo "✅ UFW: Puerto SSH habilitado"
elif command -v firewall-cmd &>/dev/null; then
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --reload
    echo "✅ FirewallD: Puerto SSH habilitado"
else
    echo "⚠️  No se detectó firewall. Asegúrese de que el puerto 22 esté abierto."
fi

echo ""
echo "==================================================================="
echo "✅ ¡Configuración completada con éxito!"
echo "==================================================================="
echo ""
echo "Ahora puede conectarse remotamente y apagar este equipo usando:"
echo ""
echo "1. Dirección IP: Una de las mostradas arriba"
echo "2. Usuario SSH: Un usuario con permisos sudo"
echo "3. Contraseña: La contraseña del usuario seleccionado"
echo ""
echo "Para probar el apagado, intente ejecutar:"
echo "   ssh [usuario]@[ip] 'sudo shutdown now'"
echo ""
echo "==================================================================="
