document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('btn-revisar-correos');
    const mensajeDiv = document.getElementById('mensaje-correos');
    const tablaBody = document.getElementById('tabla-boletas-body');
    const alerts = document.querySelectorAll('.alert');

    btn.addEventListener('click', () => {
        fetch('/administracion/revisar/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
        })
        .then(response => response.json())
        .then(data => {
            mensajeDiv.textContent = data.mensaje;
            mensajeDiv.style.display = 'block';
            mensajeDiv.classList.add('success');

            //Cargar la nueva tabla
            fetch('/administracion/boleta-parcial/')
                .then(res => res.json())
                .then(tabla => {
                    tablaBody.innerHTML = tabla.html;
                });


            // Ocultar despues de unos segundos
            setTimeout(() => {
                mensajeDiv.style.display = 'none';
            }, 4000);
        })
        .catch(error => {
            mensajeDiv.textContent = "Ocurrió un error al revisar el correo electrónico.";
            mensajeDiv.style.display = 'block';
            mensajeDiv.classList.add('error');
        });
    });

    // Obtener CSRF Token de la cookie
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

    alerts.forEach(function (alert){
        setTimeout(function () {
        alert.classList.add("hide");
        setTimeout(() => alert.style.display = "none", 600); 
        }, 4000);
    });
});

window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        // La pagina viene del caché (al usar atrás)
        window.location.reload()
    }
});