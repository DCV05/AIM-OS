#!/bin/bash

# Extraer el nombre y la versión del sistema operativo
name=$(grep '^NAME=' /etc/os-release | cut -d'"' -f2)
version=$(grep '^VERSION=' /etc/os-release | cut -d'"' -f2)

# Imprimir la información en el formato deseado
echo "OS: $name Version $version"

# Imprime el nombre del usuario actual
echo -n "User: "
whoami

# Kernel
echo -n "Kernel: "
uname -r

# Imprime el tiempo desde que el sistema fue encendido
echo -n "Uptime: "
uptime -p

# Información mínima del servidor (CPU y memoria)
echo -n "CPU: "
lscpu | grep "Model name"

echo -n "RAM: "
free -h | grep "Mem:" | awk '{print $4 "/" $2}'