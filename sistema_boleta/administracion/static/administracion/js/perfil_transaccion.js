function abrirModal() {
    document.getElementById('validar_modal').style.display = 'flex';
    document.body.style.overflow = 'hidden'; //Previene scroll de fondo
}

function cerrarModal() {
    document.getElementById('validar_modal').style.display = 'none';
    document.body.style.overflow = 'auto'; //Restaurar scroll
}

function validarTransaccion(validado, transaccionId) {
    console.log("Transaccion: ", transaccionId)

    //Mostrar loading en el boton
    const btnValidar = document.querySelector('.btn-validation');
    const textoOriginal = btnValidar.innerHTML;
    const url = `/administracion/validar_transaccion/${transaccionId}`
    console.log('URL generada:', url)
    btnValidar.innerHTML = validado ? 'Validando...' : 'Rechazando...';
    btnValidar.disabled = true;

    fetch(`/administracion/validar_transaccion/${transaccionId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'validado': validado 
        })
    })
    .then(response => {
        console.log("Status", response.status);
        console.log("Headers:", response.headers.get('content-type'));

        // Debugging: Ver que devuelve el servidor
        return response.text(); // Cambiar a text temporalmente
    })
    .then(responseText => {
        console.log("response text: ", responseText)

        // Parseando con json 
        try {
            const data = JSON.parse(responseText);
            console.log("parsed data:", data)
            
            if (data.status === 'success') {
                cerrarModal();
                // Mostrar mensaje de exito
                mostrarNotificacion(validado ? 'Transaccion validada exitosamente' : 'Transaccion rechazada', 'success');
                // Recargar pagina despues de un momento
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                throw new Error(`Error del servidor: ${data.message || 'Respuesta invalida'}`);
            }
        }catch (parseError) {
            console.error('Error parsing JSON:', parseError);
            console.error('Raw response:', responseText);
            throw new Error('El servidor no devolvió JSON válido');
        }
    })
    .catch(error => {
        console.error("Error completo:", error);
        mostrarNotificacion('Error al procesar la validacion', 'error');
        btnValidar.innerHTML = textoOriginal;
        btnValidar.disabled = false;
    });
}

function generarRecibo(transaccionId, negocioId) {
    
    // Abrir en nueva ventana
    window.open(`/administracion/generar_recibo/${transaccionId}/`, '_blank');

    // Redigir a la pestaña actual de perfil de negocio con un pequeno delay
    setTimeout(function() {
        window.location.href = `/negocios/${negocioId}/perfil`;
    }, 1500); // 1,5 Seconds  
}

function mostrarNotificacion(mensaje, tipo) {
    // Crear notificacion simple
    const notificacion = document.createElement('div');
    notificacion.style.cssText = `
        position: fixed;
        top: 20px;
        right: 80px;
        padding: 15px 20px;
        border-radius: 12px;
        color: white;
        font-weight: 500;
        z-index: 1001;
        animation: slideIn 0.3s ease;
        background-color: ${tipo === 'success' ? '#31a94dff' : '#cf1a2cff'};
    `;
    notificacion.textContent = mensaje;
    document.body.appendChild(notificacion);

    // Remover despues de 3 segundos
    setTimeout(() => {
        notificacion.remove();
    }, 3000);
}

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

// Cerrar el modal al hacer click fuera de el
document.addEventListener('click', function(event) {
    const modal = document.getElementById('validar_modal');
    if (event.target === modal) {
        cerrarModal();
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        cerrarModal();
    }
})

