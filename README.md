# 🏦 Sistema de Boletas Bancarias

Sistema automatizado para la gestión y control de boletas bancarias mediante correo electrónico.

## 📋 Características

- ✅ Recepción automática de boletas por correo electrónico (IMAP)
- ✅ Validación de seguridad de imágenes y remitentes
- ✅ Procesamiento automático de pagos
- ✅ Generación de recibos
- ✅ Envío automático de confirmaciones (SMTP)
- ✅ Gestión de múltiples locales comerciales
- ✅ Reportes y historial de transacciones

## 🚀 Requisitos Previos

- Docker Desktop instalado ([Descargar](https://www.docker.com/products/docker-desktop))
- 8 GB RAM mínimo
- 10 GB espacio en disco

## ⚙️ Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/joferiste/tickets.git
cd sistema-boletas
```

### 2. Configurar variables de entorno
```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
# En Windows: notepad .env
# En Linux/Mac: nano .env
```

**Configuraciones importantes en .env:**
- `POSTGRES_PASSWORD`: Password seguro para la base de datos
- `SECRET_KEY`: Generar una nueva (ver instrucciones en .env.example)
- `EMAIL_USERNAME` y `EMAIL_PASSWORD`: Credenciales de Gmail con App Password

### 3. Construir y levantar los contenedores
```bash
docker compose up -d
```

La primera vez tomará algunos minutos mientras descarga las imágenes.

### 4. Crear superusuario
```bash
docker compose exec django python src/manage.py createsuperuser
```

### 5. Acceder al sistema

Abrir navegador en: [http://localhost:8000](http://localhost:8000)

## 🛠️ Comandos Útiles
```bash
# Ver logs
docker compose logs -f

# Detener sistema
docker compose down

# Reiniciar servicios
docker compose restart

# Entrar al shell de Django
docker compose exec django python src/manage.py shell

# Ejecutar migraciones
docker compose exec django python src/manage.py migrate

# Crear respaldo de base de datos
docker compose exec postgres pg_dump -U postgres tickets > backup.sql
```

## 📁 Estructura del Proyecto
```
tickets/
├── Dockerfile              # Configuración de imagen Docker
├── docker-compose.yml      # Orquestación de servicios
├── entrypoint.sh          # Script de inicialización
├── .env.example           # Template de configuración
└── sistema_boleta/        # Código Django
    ├── manage.py
    ├── requirements.txt
    └── ...
```

## 🔒 Seguridad

- ⚠️ Nunca subas el archivo `.env` a GitHub
- ⚠️ Genera una nueva `SECRET_KEY` para cada instalación
- ⚠️ Usa contraseñas seguras en producción
- ⚠️ Para Gmail, usa App Passwords, no tu contraseña normal

## 📝 Licencia

Este código es propiedad del autor y no puede ser copiado, distribuido ni modificado sin autorización expresa.  
Todos los derechos reservados.

## 👥 Autor

[Jorge Riscajché/freelancer developer]

## 🐛 Reportar Problemas

Para reportar bugs o solicitar features, abre un issue en GitHub.