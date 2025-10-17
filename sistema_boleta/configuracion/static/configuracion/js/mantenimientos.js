document.addEventListener('DOMContentLoaded', () => {
    // --- FUNCIONES DE VALIDACIÓN ---
    function validarNombre(nombre) {
        const errores = [];
        const nombreTrim = nombre.trim();
        
        // Validar que no esté vacío
        if (!nombreTrim) {
            errores.push('El nombre es obligatorio');
            return errores;
        }
        
        // Validar solo letras y espacios
        const regexNombre = /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/;
        if (!regexNombre.test(nombreTrim)) {
            errores.push('El nombre únicamente debe contener letras y espacios');
        }
        
        return errores;
    }
    
    function validarNumeroCuenta(numero) {
        const errores = [];
        const numeroTrim = numero.trim();
        
        // Validar que no esté vacío
        if (!numeroTrim) {
            errores.push('El número de cuenta es obligatorio');
            return errores;
        }
        
        // Validar longitud máxima
        if (numeroTrim.length > 14) {
            errores.push('El número de cuenta no debe exceder los 14 caracteres');
        }
        
        // Validar solo dígitos y guiones
        const regexNumero = /^[0-9\-]+$/;
        if (!regexNumero.test(numeroTrim)) {
            errores.push('El número de cuenta sólo debe contener dígitos y guiones');
            return errores;
        }
        
        // Contar dígitos (sin guiones)
        const soloDigitos = numeroTrim.replace(/-/g, '');
        if (soloDigitos.length < 9 || soloDigitos.length > 11) {
            errores.push('El número de cuenta debe tener entre 9 y 11 dígitos');
        }
        
        // Validar guiones (si hay al menos uno, debe haber al menos dos)
        const cantidadGuiones = (numeroTrim.match(/-/g) || []).length;
        if (cantidadGuiones > 0 && cantidadGuiones < 2) {
            errores.push('Si usas guiones, debe contener al menos 2 (ej. 11-111111-11)');
        }
        
        return errores;
    }
    
    function mostrarErrores(errores) {
        if (errores.length === 0) return;
        
        const mensajeError = errores.join('\n');
        mostrarAlerta(mensajeError, 'error');
    }
    
    function mostrarAlerta(mensaje, tipo = 'success') {
        // Remover alertas anteriores
        const alertaPrevia = document.querySelector('.alerta-notificacion');
        if (alertaPrevia) {
            alertaPrevia.remove();
        }
        
        const alerta = document.createElement('div');
        alerta.className = `alerta-notificacion alerta-${tipo}`;
        alerta.innerHTML = `
            <span class="alerta-icono">${tipo === 'success' ? '✓' : '⚠'}</span>
            <span class="alerta-mensaje">${mensaje}</span>
        `;
        
        document.body.appendChild(alerta);
        
        // Animación de entrada
        setTimeout(() => alerta.classList.add('visible'), 10);
        
        // Remover después de 4 segundos
        setTimeout(() => {
            alerta.classList.remove('visible');
            setTimeout(() => alerta.remove(), 400);
        }, 4000);
    }
    
    // --- VALIDACIÓN EN TIEMPO REAL ---
    const inputNombre = document.getElementById('nombre');
    const inputNumero = document.getElementById('numero_cuenta');
    
    if (inputNombre) {
        inputNombre.addEventListener('input', (e) => {
            const valor = e.target.value;
            const errores = validarNombre(valor);
            
            if (errores.length > 0) {
                inputNombre.classList.add('input-error');
                inputNombre.classList.remove('input-success');
            } else if (valor.trim()) {
                inputNombre.classList.remove('input-error');
                inputNombre.classList.add('input-success');
            } else {
                inputNombre.classList.remove('input-error', 'input-success');
            }
        });
    }
    
    if (inputNumero) {
        inputNumero.addEventListener('input', (e) => {
            const valor = e.target.value;
            const errores = validarNumeroCuenta(valor);
            
            if (errores.length > 0 && valor.trim()) {
                inputNumero.classList.add('input-error');
                inputNumero.classList.remove('input-success');
            } else if (valor.trim()) {
                inputNumero.classList.remove('input-error');
                inputNumero.classList.add('input-success');
            } else {
                inputNumero.classList.remove('input-error', 'input-success');
            }
        });
    }
    
    // --- ABRIR MODAL ---
    window.abrirModalEditar = function(button) {
        const row = button.closest('tr');
        const id = row.dataset.id;
        const nombre = row.dataset.nombre;
        const numero = row.dataset.numero;
        
        document.getElementById('banco-id').value = id;
        document.getElementById('nombre').value = nombre;
        document.getElementById('numero_cuenta').value = numero;
        
        // Limpiar clases de validación
        inputNombre.classList.remove('input-error', 'input-success');
        inputNumero.classList.remove('input-error', 'input-success');
        
        const modal = document.getElementById('modal-editar');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    };
    
    // --- CERRAR MODAL ---
    window.cerrarModal = function() {
        const modal = document.getElementById('modal-editar');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    };
    
    window.cerrarModalEliminar = function() {
        const modal = document.getElementById('modal-eliminar');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    };
    
    // --- ABRIR MODAL ELIMINAR ---
    window.abrirModalEliminar = function(button) {
        const row = button.closest('tr');
        const id = row.dataset.id;
        const nombre = row.dataset.nombre;
        
        document.getElementById('eliminar-banco-id').value = id;
        document.getElementById('eliminar-banco-nombre').textContent = nombre;
        
        const modal = document.getElementById('modal-eliminar');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    };
    
    // Cerrar modales al hacer clic fuera
    const modalEditar = document.getElementById('modal-editar');
    if (modalEditar) {
        modalEditar.addEventListener('click', (e) => {
            if (e.target === modalEditar) {
                cerrarModal();
            }
        });
    }
    
    const modalEliminar = document.getElementById('modal-eliminar');
    if (modalEliminar) {
        modalEliminar.addEventListener('click', (e) => {
            if (e.target === modalEliminar) {
                cerrarModalEliminar();
            }
        });
    }
    
    // --- ENVÍO DEL FORMULARIO (AJAX) ---
    const form = document.getElementById('form-editar');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const id = document.getElementById('banco-id').value;
        const nombre = document.getElementById('nombre').value.trim();
        const numero = document.getElementById('numero_cuenta').value.trim();
        
        // Validar en frontend antes de enviar
        const erroresNombre = validarNombre(nombre);
        const erroresNumero = validarNumeroCuenta(numero);
        const todosLosErrores = [...erroresNombre, ...erroresNumero];
        
        if (todosLosErrores.length > 0) {
            mostrarErrores(todosLosErrores);
            return;
        }
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Deshabilitar botón mientras se procesa
        const btnGuardar = form.querySelector('.btn-save');
        const textoOriginal = btnGuardar.textContent;
        btnGuardar.disabled = true;
        btnGuardar.textContent = 'Guardando...';
        
        try {
            const response = await fetch(`/configuracion/editar/${id}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({
                    nombre: nombre,
                    numero_cuenta: numero
                })
            });
            
            if (response.ok) {
                // Actualizar fila en la tabla sin recargar
                const fila = document.querySelector(`tr[data-id='${id}']`);
                if (fila) {
                    fila.dataset.nombre = nombre;
                    fila.dataset.numero = numero;
                    fila.querySelector('td:nth-child(2)').textContent = nombre;
                    fila.querySelector('td:nth-child(3)').textContent = numero;
                }
                
                cerrarModal();
                mostrarAlerta('Banco actualizado exitosamente', 'success');
            } else {
                const data = await response.json();
                const erroresBackend = data.errors ? Object.values(data.errors).flat().join('\n') : 'Error al actualizar';
                mostrarAlerta(erroresBackend, 'error');
            }
        } catch (err) {
            console.error(err);
            mostrarAlerta('Error de conexión con el servidor', 'error');
        } finally {
            btnGuardar.disabled = false;
            btnGuardar.textContent = textoOriginal;
        }
    });
    
    // --- FORMULARIO DE ELIMINACIÓN (AJAX) ---
    const formEliminar = document.getElementById('form-eliminar');
    if (formEliminar) {
        formEliminar.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const id = document.getElementById('eliminar-banco-id').value;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Deshabilitar botón mientras se procesa
            const btnEliminar = formEliminar.querySelector('.btn-confirmar');
            const textoOriginal = btnEliminar.textContent;
            btnEliminar.disabled = true;
            btnEliminar.textContent = 'Eliminando...';
            
            try {
                const response = await fetch(`/configuracion/eliminar/${id}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken,
                    }
                });
                
                if (response.ok) {
                    // Remover fila de la tabla con animación
                    const fila = document.querySelector(`tr[data-id='${id}']`);
                    if (fila) {
                        fila.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                        fila.style.opacity = '0';
                        fila.style.transform = 'translateX(-20px)';
                        
                        setTimeout(() => {
                            fila.remove();
                            
                            // Verificar si no quedan bancos
                            const tbody = document.querySelector('.tabla-mantenimiento tbody');
                            if (tbody.children.length === 0) {
                                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px;">No hay bancos registrados.</td></tr>';
                            }
                        }, 300);
                    }
                    
                    cerrarModalEliminar();
                    mostrarAlerta('Banco eliminado exitosamente', 'success');
                } else {
                    const data = await response.json();
                    mostrarAlerta(data.error || 'Error al eliminar el banco', 'error');
                }
            } catch (err) {
                console.error(err);
                mostrarAlerta('Error de conexión con el servidor', 'error');
            } finally {
                btnEliminar.disabled = false;
                btnEliminar.textContent = textoOriginal;
            }
        });
    }
});