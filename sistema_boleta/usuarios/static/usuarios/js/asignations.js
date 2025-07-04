document.addEventListener('DOMContentLoaded', function() {
    const abrir = document.getElementById('abrirModal');
    const cerrar = document.getElementById('cerrarModal');
    const modal = document.getElementById('modalAsignacion');

    abrir.onclick = () => modal.style.display = 'block';
    cerrar.onclick = () => modal.style.display = 'none';
    window.onclick = (e) => {
        if (e.target == modal) modal.style.display = 'none';
    }

    setTimeout(function() {
        const mensajes = document.querySelectorAll('.mensaje');
        mensajes.forEach(msg => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-80%)';
            setTimeout(() => msg.remove(), 500);
        });
    }, 4000);

    window.onclick = (e) => {
        if (e.target == modal) {
            modal.style.display = 'none';
            enlaceConfirmacion = null;
        }
    };


})

let enlaceConfirmacion = null;
function modalConfirmacion(mensaje, url) {
    const modal = document.getElementById('modal-confirmacion');
    const texto = document.getElementById('mensaje-confirmacion');
    const btnConfirmar = document.getElementById('btn-confirmar');
    const btnCancelar = document.getElementById('btn-cancelar');

    texto.textContent = mensaje;
    modal.style.display = 'block';
    enlaceConfirmacion = url;

    btnConfirmar.onclick = () => {
        modal.style.display = 'none';
        if (enlaceConfirmacion) {
            window.location.href = enlaceConfirmacion;
        }
    };

    btnCancelar.onclick = () => {
        modal.style.display = 'none';
        enlaceConfirmacion = null;
    };

    // Cerrar si se da clic afuera
    window.onclick = (e) => {
        if (e.target == modal) {
            modal.style.display = 'none';
            enlaceConfirmacion = null;
        }
    };
}
