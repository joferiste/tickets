let reciboIdActual = null;
let botonActual = null;

// Enviar recibo - abrir modal
function enviarRecibo(reciboId, button) {
    reciboIdActual = reciboId;
    botonActual = button;

    document.getElementById('confirmarEnvioModal').style.display = 'flex';
}

// Enviar recibo - confirmar y ejecutar
function confirmarEnvio() {
    console.log('confirmarEnvio() ejecutado.');
    console.log('reciboIdActual:', reciboIdActual);
    console.log('boton actual:', botonActual);

    cerrarModalConfimacion();

    // Cambiar boton a estado de carga
    const textoOriginal = botonActual.innerHTML;
    botonActual.innerHTML = 'Enviando...'
    botonActual.disabled = true;

    fetch(`/negocios/enviar_recibo/${reciboIdActual}/`, {
        methhod: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') 
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            mostrarResultado('✅', 'Recibo Enviado', 'El recibo se envio correctamente.');
        } else {
            mostrarResultado('❌', 'Error', data.message || 'Error al enviar el recibo.');
            botonActual.innerHTML = textoOriginal;
            botonActual.disabled = false;
        }
    })
    .catch(error => {
        mostrarResultado('❌', 'Error', 'Error de conexion.');
        botonActual.innerHTML = textoOriginal;
        botonActual.disabled = false;
    });
}

// REENVIAR RECIBO - Abrir modal
function reenviarRecibo(reciboId, button) {
    reciboIdActual = reciboId;
    botonActual = button;
    document.getElementById('confirmarReenvioModal').style.display = 'flex';
}

// REENVIAR RECIBO - Confirmar y ejecutar
function confirmarReenvio() {
    cerrarModalReenvio();
    
    // Cambiar botón a estado de carga
    const textoOriginal = botonActual.innerHTML;
    botonActual.innerHTML = 'Reenviando...';
    botonActual.disabled = true;
    
    fetch(`/negocios/reenviar_recibo/${reciboIdActual}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            mostrarResultado('✅', 'Recibo Reenviado', 'El recibo se reenvió correctamente');
        } else {
            mostrarResultado('❌', 'Error', data.message || 'Error al reenviar el recibo');
            botonActual.innerHTML = textoOriginal;
            botonActual.disabled = false;
        }
    })
    .catch(error => {
        mostrarResultado('❌', 'Error', 'Error de conexión');
        botonActual.innerHTML = textoOriginal;
        botonActual.disabled = false;
    });
}

// Funciones de modales
function cerrarModalConfimacion() {
    document.getElementById('confirmarEnvioModal').style.display = 'none';
}

function cerrarModalReenvio() {
    document.getElementById('confirmarReenvioModal').style.display = 'none';
}

function cerrarModalResultado() {
    document.getElementById('resultadoModal').style.display = 'none';
}

// Dar clic fuera del modal para salir
window.onclick = function(event) {
    const modales = [
        'confirmarEnvioModal',
        'confirmarReenvioModal'
    ];
    
    modales.forEach(id => {
        const modal = document.getElementById(id);
        if (modal && event.target === modal) {
            modal.style.display = 'none';
        }    
    });
};


function mostrarResultado(icono, titulo, mensaje) {
    document.getElementById('resultadoIcon').innerHTML = icono;
    document.getElementById('resultadoTitulo').textContent = titulo;
    document.getElementById('resultadoMensaje').textContent = mensaje;
    document.getElementById('resultadoModal').style.display = 'flex';

    // Auto-cerrar despues de 3 segundos si es exitoso
    if (icono === '✅') {
        setTimeout(() => {
            cerrarModalResultado();
            location.reload();
        }, 3000);
    }
}

// FUNCIÓN AUXILIAR PARA CSRF TOKEN
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function verDetalles(idRecibo) {
    const url = `/negocios/recibo_detalles/${idRecibo}`;
    window.open(url, '_blank')
}