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

    // Restaurar tab después de redirección
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
    
    // Limpiar campos opcionales
    const grupoCosto = document.getElementById('grupo-costo');
    const grupoUbicacion = document.getElementById('grupo-ubicacion');
    
    // Configurar título y campos según el tipo
    if (tipo === 'estado') {
        titulo.textContent = 'Editar Estado de Local';
        grupoCosto.style.display = 'none';
        grupoUbicacion.style.display = 'none';
        
    } else if (tipo === 'nivel') {
        titulo.textContent = 'Editar Nivel';
        grupoCosto.style.display = 'block';
        grupoUbicacion.style.display = 'block';
        
        // Obtener datos adicionales para nivel
        const costo = row.getAttribute('data-costo');
        const ubicacionId = row.getAttribute('data-ubicacion-id');
        const ubicacionNombre = row.getAttribute('data-ubicacion-nombre');
        
        // CARGAR VALORES ACTUALES
        document.getElementById('costo-editar').value = parseFloat(costo).toFixed(2);
        document.getElementById('ubicacion-editar').value = ubicacionId;
        
        // Guardar valores originales
        document.getElementById('nombre-original').value = nombre;
        document.getElementById('costo-original').value = costo;
        document.getElementById('ubicacion-original').value = ubicacionId;
        
    } else if (tipo === 'ubicacion') {
        titulo.textContent = 'Editar Ubicación';
        grupoCosto.style.display = 'none';
        grupoUbicacion.style.display = 'none';
    }
    
    // Llenar el campo nombre
    document.getElementById('item-id').value = id;
    document.getElementById('tipo-editar').value = tipo;
    document.getElementById('nombre-editar').value = nombre;
    
    // Guardar nombre original para todos los tipos
    document.getElementById('nombre-original').value = nombre;
    
    // Mostrar modal con animación
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    
    // Focus en el campo de nombre
    setTimeout(() => {
        document.getElementById('nombre-editar').focus();
    }, 100);
}

// Manejar el envío del formulario de edición con fetch
document.addEventListener('DOMContentLoaded', function() {
    const formEditar = document.getElementById('form-editar');

    if (formEditar) {
        formEditar.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevenir envío normal del formulario

            const itemId = document.getElementById('item-id').value;
            const tipo = document.getElementById('tipo-editar').value;
            
            const nombre = document.getElementById('nombre-editar').value.trim();
            const nombreOriginal = document.getElementById('nombre-original').value;

            // Determinar qué campos cambiaron
            let cambios = false;
            const formData = new FormData();
            formData.append('item_id', itemId);
            formData.append('tipo', tipo);

            // Validar y agregar nombre si cambió
            if (nombre !== nombreOriginal) {
                // Validación: no permitir números en nombre
                if (/\d/.test(nombre)) {
                    mostrarError('El nombre no puede contener números');
                    document.getElementById('nombre-editar').focus();
                    return false;
                }
                
                if (!nombre) {
                    mostrarError('El nombre no puede estar vacío');
                    document.getElementById('nombre-editar').focus();
                    return false;
                }
                
                formData.append('nombre', nombre);
                cambios = true;
            } else {
                // Enviar el nombre original para mantenerlo
                formData.append('nombre', nombreOriginal);
            }

            // Si es tipo 'nivel', verificar costo y ubicación
            if (tipo === 'nivel') {
                const costo = document.getElementById('costo-editar').value.trim();
                const costoOriginal = document.getElementById('costo-original').value;
                const ubicacionId = document.getElementById('ubicacion-editar').value;
                const ubicacionOriginal = document.getElementById('ubicacion-original').value;

                // Verificar si el costo cambió
                if (costo !== costoOriginal && costo !== '') {
                    // Validar que el costo sea un número válido
                    if (!/^\d+(\.\d{1,2})?$/.test(costo)) {
                        mostrarError('El costo debe ser un número válido (ej: 150.00)');
                        document.getElementById('costo-editar').focus();
                        return false;
                    }

                    // Validar que el costo sea mayor a 0
                    if (parseFloat(costo) <= 0) {
                        mostrarError('El costo debe ser mayor a 0');
                        document.getElementById('costo-editar').focus();
                        return false;
                    }

                    formData.append('costo', costo);
                    cambios = true;
                } else {
                    // Mantener costo original
                    formData.append('costo', costoOriginal);
                }

                // Verificar si la ubicación cambió
                if (ubicacionId && ubicacionId !== ubicacionOriginal) {
                    formData.append('ubicacion', ubicacionId);
                    cambios = true;
                } else {
                    // Mantener ubicación original
                    formData.append('ubicacion', ubicacionOriginal);
                }
            }

            // Si no hubo cambios, mostrar mensaje
            if (!cambios && tipo !== 'estado' && tipo !== 'ubicacion') {
                mostrarAdvertencia('No se detectaron cambios para guardar');
                return false;
            }

            // Mostrar indicador de carga
            const btnSubmit = formEditar.querySelector('button[type="submit"]');
            const btnTextoOriginal = btnSubmit.innerHTML;
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<span>Guardando...</span>';

            // Obtener el token CSRF
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            formData.append('csrfmiddlewaretoken', csrfToken);

            // Hacer la petición AJAX
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
                    // Actualizar la fila en la tabla sin recargar
                    const row = document.querySelector(`tr[data-id="${itemId}"][data-tipo="${tipo}"]`);
                    if (row) {
                        row.setAttribute('data-nombre', data.data.nombre);
                        row.querySelector('.nombre-column').textContent = data.data.nombre;
                        
                        // Si es nivel, actualizar también costo y ubicación
                        if (tipo === 'nivel' && data.data.costo && data.data.ubicacion) {
                            row.setAttribute('data-costo', data.data.costo);
                            row.setAttribute('data-ubicacion-id', data.data.ubicacion_id);
                            row.setAttribute('data-ubicacion-nombre', data.data.ubicacion);
                            
                            const costoCell = row.querySelector('.costo-column');
                            const ubicacionCell = row.querySelector('.ubicacion-column');
                            
                            if (costoCell) {
                                costoCell.textContent = `Q ${parseFloat(data.data.costo).toFixed(2)}`;
                            }
                            if (ubicacionCell) {
                                ubicacionCell.textContent = data.data.ubicacion;
                            }
                        }
                    }

                    // Mostrar mensaje de éxito
                    mostrarExito(data.message);

                    // Cerrar modal
                    cerrarModal('editar');
                } else {
                    mostrarError(data.error || 'Error al actualizar el elemento');
                }
            })
            .catch(error => {
                console.error('Error: ', error);
                mostrarError('Error al procesar la solicitud. Por favor, intente nuevamente.');
            })
            .finally(() => {
                // Restaurar botón
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = btnTextoOriginal;
            });
        });
    }
});

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
    const costoInput = document.getElementById('costo-editar');
    
    // Validar nombre (no números)
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

    // Validar costo (solo números y punto decimal)
    if (costoInput) {
        costoInput.addEventListener('input', function(e) {
            let valor = e.target.value;
            
            // Permitir solo números, punto decimal y máximo 2 decimales
            const regex = /^\d*\.?\d{0,2}$/;
            
            if (!regex.test(valor) && valor !== '') {
                // Si no cumple el patrón, revertir al último valor válido
                e.target.value = valor.slice(0, -1);
                mostrarAdvertencia('Solo se permiten números con máximo 2 decimales');
            }
        });

        // Formatear al perder el foco
        costoInput.addEventListener('blur', function(e) {
            let valor = e.target.value;
            if (valor && !isNaN(valor)) {
                e.target.value = parseFloat(valor).toFixed(2);
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

// Función para validar campos vacíos
function validarCampo(campo) {
    return campo && campo.trim().length > 0;
}

// Función para capitalizar texto
function capitalizar(texto) {
    if (!texto) return '';
    return texto.charAt(0).toUpperCase() + texto.slice(1).toLowerCase();
}

// Función para formatear moneda
function formatearMoneda(valor) {
    return `Q ${parseFloat(valor).toFixed(2)}`;
}