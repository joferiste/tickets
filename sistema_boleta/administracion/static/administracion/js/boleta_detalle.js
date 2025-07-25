document.addEventListener("DOMContentLoaded", function() {
    const modal = document.getElementById("imagenModal");
    const openBtn = document.getElementById("OpenImageModal");
    const closeBtn = document.getElementById("closeModal");
    const boletaImage = document.getElementById("boletaImage");

    let currentRotation = 0;
    let currentScale = 1;

    // Abrir modal
    openBtn.addEventListener("click", () => {
        modal.classList.remove("hidden");
        resetImage();
    });

    // Cerrar modal
    closeBtn.addEventListener("click", () => {
        modal.classList.add("hidden");
    });

    // Cerrar al hacer click fuera del contenido
    modal.addEventListener("click", (e) => {
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
        boletaImage.style.transform = `rotate(${currentRotation}deg) scale(${currentScale})`;
    }
});