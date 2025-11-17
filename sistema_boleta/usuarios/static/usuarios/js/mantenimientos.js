// ===================================
// SISTEMA DE PESTAÑAS
// ===================================
let tabActual = 'estados';

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar event listeners de pestañas
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            cambiarTab(tabName, this);
        });
    });

    // Restaurar tab despues de redireccion
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');

    if (tabParam) {
        const button = document.querySelector(`[data-tab="${tabParam}"]`);
        if (button) {
            cambiarTab(tabParam, button);
        }
    }
});

function cambiarTab(tabName, button) {
    tabActual = tabName;

    // Ocultar todos los contenidos de tabs
    const allTabContents = document.querySelectorAll('.tab-content');
    allTabContents.forEach(content => {
        content.classList.remove('active');
    });
    
    // Desactivar todos los botones de tabs
    const allTabButtons = document.querySelectorAll('.tab-button');
    allTabButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar el tab seleccionado
    const selectedTab = document.getElementById('tab-' + tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Activar el botón seleccionado
    if (button) {
        button.classList.add('active');
    }
}

// ===================================
// MODAL DE EDICIÓN
// ===================================
function abrirModalEditar(btn, tipo) {
    const row = btn.closest('tr');
    const id = row.getAttribute('data-id');
    const nombre = row.getAttribute('data-nombre');
    
    const modal = document.getElementById('modal-editar');
    const titulo = document.getElementById('titulo-editar');
    
    // Configurar título según el tipo
    if (tipo === 'estado') {
        titulo.textContent = 'Editar Estado Usuario';
    } 
    
    // Llenar los campos del formulario
    document.getElementById('item-id').value = id;
    document.getElementById('tipo-editar').value = tipo;
    document.getElementById('nombre-editar').value = nombre;
    
    // Mostrar modal con animación
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    
    // Focus en el campo de nombre
    setTimeout(() => {
        document.getElementById('nombre-editar').focus();
    }, 100);
}

// Manejar el envio del formulario de edicion con fetch
document.addEventListener('DOMContentLoaded', function() {
    const formEditar = document.getElementById('form-editar');

    if (formEditar) {
        formEditar.addEventListener('submit', function(e) {
            e.preventDefault(); //Prevenir envio normal del formulario

            const nombre = document.getElementById('nombre-editar').value.trim();
            const itemId = document.getElementById('item-id').value;
            const tipo = document.getElementById('tipo-editar').value;

            // validacion del campo vacio
            if (!nombre) {
                mostrarError('Por favor, ingrese un nombre valido');
                document.getElementById('nombre-editar').focus();
                return false;
            }

            // validacion: no permitir numeros
            if (/\d/.test(nombre)) {
                mostrarError('El nombre no puede contener numeros');
                document.getElementById('nombre-editar').focus();
                return false;
            }

            // Mostrar indicador de carga
            const btnSubmit = formEditar.querySelector('button[type="submit"]');
            const btnTextoOriginal = btnSubmit.innerHTML;
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<span> Guardando...</span>';

            // Obtener el token CSRF
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Preparar datos para el formulario
            const formData = new FormData();
            formData.append('item_id', itemId);
            formData.append('tipo', tipo);
            formData.append('nombre', nombre);
            formData.append('csrfmiddlewaretoken', csrfToken);

            // Hacer la peticion AJAX
            fetch(formEditar.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Actualizar la data en la fila sin recargar
                    const row = document.querySelector(`tr[data-id="${itemId}"][data-tipo="${tipo}"]`);
                    if (row) {
                        row.setAttribute('data-nombre', data.data.nombre);
                        row.querySelector('.nombre-column').textContent = data.data.nombre;
                    }

                    // Mostrar mensaje de exito
                    mostrarExito(data.message);

                    // Cerrar modal
                    cerrarModal('editar');
                } else {
                    mostrarError(data.error || 'Error al actualizar el elemento');
                }
            })
            .catch(error => {
                console.error('Error: ', error);
                mostrarError('Error al procesar la solicitud. Por favor, intente nuevamente.')
            })
            .finally(() => {
                // Restaurar boton
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = btnTextoOriginal;
            });
        });
    }
})

// ===================================
// MODAL DE ELIMINACIÓN
// ===================================
function abrirModalEliminar(btn, tipo) {
    const row = btn.closest('tr');
    const id = row.getAttribute('data-id');
    const nombre = row.getAttribute('data-nombre');
    
    const modal = document.getElementById('modal-eliminar');
    const form = document.getElementById('form-eliminar');
    
    // Llenar información del elemento a eliminar
    document.getElementById('eliminar-item-id').value = id;
    document.getElementById('tipo-eliminar').value = tipo;
    document.getElementById('eliminar-item-nombre').textContent = nombre;

    // Modificar la action del formulario para incluir el tab actual
    const currentAction = form.action.split('?')[0];
    form.action = `${currentAction}?tab=${tabActual}`;
    
    // Mostrar modal con animación
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// ===================================
// CERRAR MODALES
// ===================================
function cerrarModal(tipoModal) {
    const modal = document.getElementById('modal-' + tipoModal);
    
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
        
        // Limpiar formulario si es el modal de edición
        if (tipoModal === 'editar') {
            const form = document.getElementById('form-editar');
            if (form) {
                form.reset();
            }
        }
    }
}

// Cerrar modal al hacer clic en el overlay
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        const modal = e.target.closest('.modal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = 'auto';
        }
    }
});

// Cerrar modal con la tecla ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modalAbierto = document.querySelector('.modal.show');
        if (modalAbierto) {
            modalAbierto.classList.remove('show');
            document.body.style.overflow = 'auto';
        }
    }
});

// ===================================
// VALIDACIÓN EN TIEMPO REAL
// ===================================
document.addEventListener('DOMContentLoaded', function() {
    const nombreInput = document.getElementById('nombre-editar');
    
    if (nombreInput) {
        nombreInput.addEventListener('input', function(e) {
            const valor = e.target.value;
            
            // Remover números automáticamente
            if (/\d/.test(valor)) {
                e.target.value = valor.replace(/\d/g, '');
                mostrarAdvertencia('No se permiten números en el nombre');
            }
        });
    }
});


// ===================================
// MENSAJES DE NOTIFICACIÓN
// ===================================
function mostrarExito(mensaje) {
    mostrarNotificacion(mensaje, 'success');
}

function mostrarError(mensaje) {
    mostrarNotificacion(mensaje, 'error');
}

function mostrarAdvertencia(mensaje) {
    mostrarNotificacion(mensaje, 'warning');
}

function mostrarNotificacion(mensaje, tipo = 'success') {
    // Remover notificación existente
    const notifExistente = document.querySelector('.notificacion-toast');
    if (notifExistente) {
        notifExistente.remove();
    }
    
    // Crear nueva notificación
    const notificacion = document.createElement('div');
    notificacion.className = `notificacion-toast notificacion-${tipo}`;
    
    const iconos = {
        success: '✓',
        error: '✕',
        warning: '⚠'
    };
    
    notificacion.innerHTML = `
        <span class="notificacion-icono">${iconos[tipo]}</span>
        <span class="notificacion-mensaje">${mensaje}</span>
    `;
    
    document.body.appendChild(notificacion);
    
    // Animar entrada
    setTimeout(() => {
        notificacion.classList.add('show');
    }, 10);
    
    // Auto-remover después de 4 segundos
    setTimeout(() => {
        notificacion.classList.remove('show');
        setTimeout(() => {
            notificacion.remove();
        }, 300);
    }, 4000);
}

// ===================================
// VALIDACIÓN DE FORMULARIOS
// ===================================
document.addEventListener('DOMContentLoaded', function() {
    const formEditar = document.getElementById('form-editar');
    
    if (formEditar) {
        formEditar.addEventListener('submit', function(e) {
            const nombre = document.getElementById('nombre-editar').value.trim();
            
            if (!nombre) {
                e.preventDefault();
                alert('Por favor, ingrese un nombre válido.');
                document.getElementById('nombre-editar').focus();
                return false;
            }
            
            // Mostrar indicador de carga
            const btnSubmit = formEditar.querySelector('button[type="submit"]');
            if (btnSubmit) {
                btnSubmit.disabled = true;
                btnSubmit.innerHTML = '<span>Guardando...</span>';
            }
        });
    }
    
    const formEliminar = document.getElementById('form-eliminar');
    
    if (formEliminar) {
        formEliminar.addEventListener('submit', function(e) {
            // Mostrar indicador de carga
            const btnSubmit = formEliminar.querySelector('button[type="submit"]');
            if (btnSubmit) {
                btnSubmit.disabled = true;
                btnSubmit.innerHTML = '<span>Eliminando...</span>';
            }
        });
    }
});

// ===================================
// ANIMACIONES DE HOVER EN FILAS
// ===================================
document.addEventListener('DOMContentLoaded', function() {
    const rows = document.querySelectorAll('.tabla-mantenimiento tbody tr');
    
    rows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(4px)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });
});

// ===================================
// UTILIDADES
// ===================================

// Función para mostrar mensajes de confirmación
function mostrarMensaje(mensaje, tipo = 'success') {
    // Esta función puede ser expandida para mostrar notificaciones toast
    console.log(`[${tipo.toUpperCase()}] ${mensaje}`);
}

// Función para validar campos vacíos
function validarCampo(campo) {
    return campo && campo.trim().length > 0;
}

// Función para capitalizar texto
function capitalizar(texto) {
    if (!texto) return '';
    return texto.charAt(0).toUpperCase() + texto.slice(1).toLowerCase();
}