#!/bin/bash

# Script de entrada para el contenedor Django
# Este script se ejecuta cada vez que el contenedor se inicia

set -e

echo "================================="
echo "Iniciando Sistema de boletas..."
echo "================================="

# Esperando a que PostgreSQL esté completamente listo
echo "ESPERANDO A POSTGRESQL..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  echo "PostgreSQL no está listo --esperando..."
  sleep 2
done

echo "PostgreSQL está listo"

# Ejecutar migraciones 
echo "Aplicando migraciones de bases de datos..."
python src/manage.py migrate --noinput

# Recolectar archivos estáticos
echo "Recolectando archivos estáticos..."
python src/manage.py collectstatic --noinput --clear

# Verificar si existe un superusuario (opcional)
# Si quieres crear uno automáticamente, descomenta estas líneas
# echo "Verificando superusuario..."
# python manage.py shell << END
# from django.contrib.auth import get_user_model
# User = get_user_model()
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
#     print('Superusuario creado: admin/admin123')
# END

echo "=============================="
echo "Sistema listo para iniciar"
echo "=============================="

# Ejecutar el comando pasado al contenedor (por defecto: runserver)
exec "$@"