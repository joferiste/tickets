document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('btn-revisar-correos');
    const tablaBody = document.getElementById('tabla-boletas-body');
    const filterSelect = document.querySelector('.filter-select');

    // ============== FILTRADO DE BOLETAS ==============
    function filtrarBoletas(estadoFiltro) {
        const filas = tablaBody.querySelectorAll('tr:not(.no-resultados)');
        let visibles = 0;

        filas.forEach(fila => {
            const estadoBoleta = fila.getAttribute('data-estado');

            if (estadoFiltro === '' || estadoFiltro === estadoBoleta) {
                fila.style.display = '';
                visibles++;
            } else {
                fila.style.display = 'none';
            }
        });

        // Mensaje si no hay resultados
        const mensajeVacioExistente = document.querySelector('.no-resultados');
        
        if (visibles === 0) {
            if (!mensajeVacioExistente) {
                const mensajeVacio = document.createElement('tr');
                mensajeVacio.className = 'no-resultados';
                mensajeVacio.innerHTML = `
                    <td colspan="6" style="text-align: center; padding: 40px; color: #999;">
                        No se encontraron boletas con el estado seleccionado
                    </td>
                `;
                tablaBody.appendChild(mensajeVacio);
            }
        } else {
            if (mensajeVacioExistente) {
                mensajeVacioExistente.remove();
            }
        }
    }

    // Evento del select de filtrado
    if (filterSelect) {
        filterSelect.addEventListener('change', (e) => {
            const estadoSeleccionado = e.target.value;
            filtrarBoletas(estadoSeleccionado);
        });
    }

    // ============== REVISAR CORREOS ==============
    if (btn) {
        btn.addEventListener('click', () => {
            // Deshabilitar botón
            btn.disabled = true;
            const textoOriginal = btn.querySelector('.btn-text').textContent;
            btn.querySelector('.btn-text').textContent = 'Procesando...';

            fetch('/administracion/revisar/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                },
            })
            .then(response => response.json())
            .then(data => {
                // Simplemente recargar la página para que Django messages se muestren
                window.location.reload();
            })
            .catch(error => {
                console.error('Error:', error);
                // Restaurar botón en caso de error de red
                btn.disabled = false;
                btn.querySelector('.btn-text').textContent = textoOriginal;
                alert('Error de conexión con el servidor');
            });
        });
    }

    // Obtener CSRF Token
    function getCSRFToken() {
        let cookieValue = null;
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.slice(10));
            }
        }
        return cookieValue;
    }
});

window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        window.location.reload();
    }
});

function abrirModalEliminar(boletaId, remitente, estado, fecha, motivo = '') {
    const modal = document.getElementById('modal-eliminar-boleta');
    const form = document.getElementById('form-eliminar-boleta');
    
    // Llenar datos del modal
    document.getElementById('boleta-id-eliminar').value = boletaId;
    document.getElementById('boleta-remitente').textContent = remitente;
    document.getElementById('boleta-fecha').textContent = fecha;
    
    // Estado badge
    const estadoBadge = document.getElementById('boleta-estado-badge');
    if (estado === 'rechazada') {
        estadoBadge.textContent = 'Rechazada';
        estadoBadge.className = 'badge badge-rechazada';
    } else if (estado === 'sin_imagen') {
        estadoBadge.textContent = 'Sin Imagen';
        estadoBadge.className = 'badge badge-sin-imagen';
    }
    
    // Mostrar motivo si existe
    if (motivo) {
        document.getElementById('boleta-motivo').textContent = motivo;
        document.getElementById('motivo-container').style.display = 'flex';
    } else {
        document.getElementById('motivo-container').style.display = 'none';
    }
    
    // Construccion URL correcta (hardcored)
    form.action = `/administracion/sandbox/eliminar/${boletaId}`;

    console.log('URL de eliminacion', form.action);
    
    // Mostrar modal
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function cerrarModalEliminar() {
    const modal = document.getElementById('modal-eliminar-boleta');
    modal.classList.remove('show');
    document.body.style.overflow = 'auto';
}

// Cerrar con ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        cerrarModalEliminar();
    }
});

// Confirmar antes de eliminar
document.getElementById('form-eliminar-boleta').addEventListener('submit', function(e) {
    const btn = document.getElementById('btn-confirmar-eliminar');
    btn.disabled = true;
    btn.innerHTML = '<span>Eliminando...</span>';
});