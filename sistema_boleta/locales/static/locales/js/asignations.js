document.addEventListener('DOMContentLoaded', function () {
    const abrir = document.getElementById('abrirModal');
    const cerrar = document.querySelector('#modalAsignacion .cerrar');
    const modal = document.getElementById('modalAsignacion');


    if (abrir) abrir.onclick = () => modal.style.display = 'block';
    if (cerrar) cerrar.onclick = () => modal.style.display = 'none';

    window.onclick = (e) => {
        if (e.target === modal) modal.style.display = 'none';
        if (e.target === document.getElementById('modal-confirmacion')) {
            document.getElementById('modal-confirmacion').style.display = 'none';
            enlaceConfirmacion = null;
        }
    };

    setTimeout(function () {
        const mensajes = document.querySelectorAll('.mensaje');
        mensajes.forEach(msg => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-80%)';
            setTimeout(() => msg.remove(), 500);
        });
    }, 4000);
});

let enlaceConfirmacion = null;

function modalConfirmacion(mensaje, url) {
    const cerrarModal = document.getElementById('cerrarModalConfirmacion')
    const modal = document.getElementById('modal-confirmacion');
    const texto = document.getElementById('mensaje-confirmacion');
    const btnConfirmar = document.getElementById('btn-confirmar');
    const btnCancelar = document.getElementById('btn-cancelar');

    cerrarModal.onclick = () => {
        modal.style.display = 'none';
    };

    texto.textContent = mensaje;
    modal.style.display = 'block';
    enlaceConfirmacion = url;

    btnConfirmar.onclick = () => {
        modal.style.display = 'none';
        if (typeof enlaceConfirmacion === 'function') {
            enlaceConfirmacion();
        } else if (typeof enlaceConfirmacion === 'string') {
            window.location.href = enlaceConfirmacion;
        }
        enlaceConfirmacion = null;
    };

    btnCancelar.onclick = () => {
        modal.style.display = 'none';
        enlaceConfirmacion = null;
    };
}

function abrirModal(localId, localNombre) {
    document.getElementById('local_id_modal').value = localId;
    document.getElementById('local_nombre_modal').textContent = `Local: ${localNombre}`;
    document.getElementById('modalAsignacion').style.display = 'block';
} 


function modalConfirmacionReiniciar() {
    modalConfirmacion("¿Deseas reiniciar el orden de los locales?", function () {
        document.getElementById('form-reiniciar').submit();
    });
}