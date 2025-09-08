document.addEventListener("DOMContentLoaded", function() {
    const modal = document.getElementById("imagenModal");
    const openBtn = document.getElementById("OpenImageModal");
    const closeBtn = document.getElementById("closeModal");
    const boletaImage = document.getElementById("boletaImage");
    const alerts = document.querySelectorAll('.alert');

    let currentRotation = 0;
    let currentScale = 1;

    // Abrir modal
    openBtn?.addEventListener("click", () => {
        modal.classList.remove("hidden");
        resetImage();
    });

    // Cerrar modal
    closeBtn?.addEventListener("click", () => {
        modal.classList.add("hidden");
    });

    // Cerrar al hacer click fuera del contenido
    modal?.addEventListener("click", (e) => {
        if (e.target === modal) { // Si se hace click al fondo
            modal.classList.add("hidden");
        }
    });

    // Rotar
    document.getElementById("rotateLeft").addEventListener("click", () => {
        currentRotation -= 90;
        updateTransform();
    });

    document.getElementById("rotateRight").addEventListener("click", () => {
        currentRotation += 90;
        updateTransform();
    });

    // zoom
    document.getElementById("zoomIn").addEventListener("click", () => {
        currentScale += 0.17;
        updateTransform();
    });

    document.getElementById("zoomOut").addEventListener("click", () => {
        if (currentScale > 0.2) currentScale -= 0.17;
        updateTransform();
    });

    // Restaurar
    document.getElementById("resetImage").addEventListener("click", resetImage);

    function resetImage() {
        currentRotation = 0;
        currentScale = 1;
        updateTransform();
    }

    function updateTransform() {
        if (boletaImage){
            boletaImage.style.transform = `rotate(${currentRotation}deg) scale(${currentScale})`;
        }
    }

    // Modal de informacion
    const infoModal = document.getElementById("infoModal");
    const closeInfoBtn = document.getElementById("closeInfoModal")

    window.openInfoModal = function () {
        infoModal.style.display = "block";
    };

    window.closeInfoModal = function () {
        infoModal.style.display = "none";
    };

    closeInfoBtn?.addEventListener("click", () => {
        infoModal.style.display = "none";
    })

    // Cierra el modal si hacen clic fuera del contenido
    window.addEventListener("click", function (event) {
        if (event.target === infoModal) {
            infoModal.style.display = "none";
        }
    });

    alerts.forEach(function (alert){
        setTimeout(function () {
        alert.classList.add("hide");
        setTimeout(() => alert.style.display = "none", 600); 
        }, 4000);
    });


   
    const modal1 = document.getElementById("modalBlock");

    if(modal1){
        modal1.style.display = "flex"; // Mostrar modal al cargar
    }


});

function confirmarEliminacion(button) {
        const url = button.getAttribute('data-url');
        const mensaje = button.getAttribute('data-mensaje');
        document.getElementById('formEliminar').action = url;
        document.getElementById('mensajeConfirmacion').textContent = mensaje;
        document.getElementById('modalConfirmacion').style.display = 'flex';
}

    function cerrarModal() {
        const modal = document.getElementById('modalConfirmacion');
        modal.style.display = 'none';
}