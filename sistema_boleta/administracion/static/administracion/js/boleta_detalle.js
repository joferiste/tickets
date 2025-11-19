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

// Visor de imágenes mejorado con todas las funcionalidades

// Variables globales

let currentTranslateX = 0;
let currentTranslateY = 0;

// Variables para arrastrar
let isDragging = false;
let startX = 0;
let startY = 0;
let scrollLeft = 0;
let scrollTop = 0;

// Referencias a elementos

const viewport = document.getElementById('imageViewport');
const container = document.getElementById('imageContainer');
const image = document.getElementById('boletaImage');
const zoomLevelDisplay = document.getElementById('zoomLevel');

// Constantes
const MIN_SCALE = 0.1;
const MAX_SCALE = 5;
const ZOOM_STEP = 0.1;

// ============================================
// FUNCIONES DE TRANSFORMACIÓN
// ============================================

function updateTransform() {
    // Aplicar transformación CSS
    image.style.transform = `
        translate(${currentTranslateX}px, ${currentTranslateY}px)
        rotate(${currentRotation}deg)
        scale(${currentScale})
    `;
    
    // Actualizar display de zoom
    updateZoomDisplay();
    
    // Actualizar tamaño del contenedor para permitir scroll
    updateContainerSize();
}

function updateZoomDisplay() {
    const percentage = Math.round(currentScale * 100);
    zoomLevelDisplay.textContent = `${percentage}%`;
}

function updateContainerSize() {
    // Calcular dimensiones de la imagen transformada
    const rect = image.getBoundingClientRect();
    const viewportRect = viewport.getBoundingClientRect();
    
    // Si la imagen es más grande que el viewport, ajustar el contenedor
    if (rect.width > viewportRect.width || rect.height > viewportRect.height) {
        container.style.width = `${rect.width + 100}px`;
        container.style.height = `${rect.height + 100}px`;
    } else {
        container.style.width = '100%';
        container.style.height = '100%';
    }
}

function resetImage() {
    currentRotation = 0;
    currentScale = 1;
    currentTranslateX = 0;
    currentTranslateY = 0;
    viewport.scrollLeft = 0;
    viewport.scrollTop = 0;
    updateTransform();
}

function fitToScreen() {
    // Ajustar la imagen al tamaño del viewport
    const viewportRect = viewport.getBoundingClientRect();
    const imageRect = image.getBoundingClientRect();
    
    const scaleX = viewportRect.width / image.naturalWidth;
    const scaleY = viewportRect.height / image.naturalHeight;
    
    currentScale = Math.min(scaleX, scaleY) * 0.9; // 90% para dejar margen
    currentRotation = 0;
    currentTranslateX = 0;
    currentTranslateY = 0;
    
    updateTransform();
}

// ============================================
// ZOOM CON RUEDA DEL MOUSE
// ============================================

viewport.addEventListener('wheel', (e) => {
    e.preventDefault();
    
    // Obtener posición del mouse relativa al viewport
    const rect = viewport.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Guardar escala anterior
    const oldScale = currentScale;
    
    // Calcular nueva escala
    const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
    currentScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, currentScale + delta));
    
    // Calcular el factor de escala
    const scaleFactor = currentScale / oldScale;
    
    // Ajustar la posición del scroll para mantener el punto bajo el mouse
    const newScrollLeft = mouseX + (viewport.scrollLeft - mouseX) * scaleFactor;
    const newScrollTop = mouseY + (viewport.scrollTop - mouseY) * scaleFactor;
    
    updateTransform();
    
    // Aplicar nuevo scroll después de un pequeño delay para que la transformación se complete
    requestAnimationFrame(() => {
        viewport.scrollLeft = newScrollLeft - mouseX;
        viewport.scrollTop = newScrollTop - mouseY;
    });
});

// ============================================
// ARRASTRAR IMAGEN
// ============================================

viewport.addEventListener('mousedown', (e) => {
    // Solo arrastrar si la imagen es más grande que el viewport
    if (currentScale > 1 || container.scrollWidth > viewport.clientWidth) {
        isDragging = true;
        viewport.style.cursor = 'grabbing';
        
        startX = e.pageX - viewport.offsetLeft;
        startY = e.pageY - viewport.offsetTop;
        scrollLeft = viewport.scrollLeft;
        scrollTop = viewport.scrollTop;
        
        e.preventDefault();
    }
});

viewport.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    
    e.preventDefault();
    
    const x = e.pageX - viewport.offsetLeft;
    const y = e.pageY - viewport.offsetTop;
    
    const walkX = (x - startX) * 1.5; // Multiplicador para hacer el arrastre más rápido
    const walkY = (y - startY) * 1.5;
    
    viewport.scrollLeft = scrollLeft - walkX;
    viewport.scrollTop = scrollTop - walkY;
});

viewport.addEventListener('mouseup', () => {
    isDragging = false;
    viewport.style.cursor = 'grab';
});

viewport.addEventListener('mouseleave', () => {
    isDragging = false;
    viewport.style.cursor = 'grab';
});

// ============================================
// CONTROLES DE BOTONES
// ============================================

// Rotar
document.getElementById('rotateLeft').addEventListener('click', () => {
    currentRotation -= 90;
    updateTransform();
});

document.getElementById('rotateRight').addEventListener('click', () => {
    currentRotation += 90;
    updateTransform();
});

// Zoom con botones
document.getElementById('zoomIn').addEventListener('click', () => {
    if (currentScale < MAX_SCALE) {
        currentScale = Math.min(MAX_SCALE, currentScale + ZOOM_STEP);
        updateTransform();
    }
});

document.getElementById('zoomOut').addEventListener('click', () => {
    if (currentScale > MIN_SCALE) {
        currentScale = Math.max(MIN_SCALE, currentScale - ZOOM_STEP);
        updateTransform();
    }
});

// Ajustar a pantalla
document.getElementById('fitToScreen').addEventListener('click', fitToScreen);

// Restaurar
document.getElementById('resetImage').addEventListener('click', resetImage);

// ============================================
// ATAJOS DE TECLADO
// ============================================

document.addEventListener('keydown', (e) => {
    // Solo funcionar si el modal está visible
    if (modal.classList.contains('hidden')) return;
    
    // Ctrl/Cmd + Plus: Zoom in
    if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
        e.preventDefault();
        document.getElementById('zoomIn').click();
    }
    
    // Ctrl/Cmd + Minus: Zoom out
    if ((e.ctrlKey || e.metaKey) && e.key === '-') {
        e.preventDefault();
        document.getElementById('zoomOut').click();
    }
    
    // Ctrl/Cmd + 0: Reset
    if ((e.ctrlKey || e.metaKey) && e.key === '0') {
        e.preventDefault();
        resetImage();
    }
    
    // ESC: Cerrar modal
    if (e.key === 'Escape') {
        closeImageModal();
    }
    
    // Flechas: Mover imagen (si está con zoom)
    if (currentScale > 1) {
        const scrollSpeed = 50;
        
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            viewport.scrollLeft -= scrollSpeed;
        }
        if (e.key === 'ArrowRight') {
            e.preventDefault();
            viewport.scrollLeft += scrollSpeed;
        }
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            viewport.scrollTop -= scrollSpeed;
        }
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            viewport.scrollTop += scrollSpeed;
        }
    }
});

// ============================================
// ABRIR/CERRAR MODAL
// ============================================

function openImageModal() {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    
    // Ajustar imagen al abrir
    setTimeout(() => {
        fitToScreen();
    }, 100);
}

function closeImageModal() {
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
    resetImage();
}

// Botón de cerrar
document.getElementById('closeModal').addEventListener('click', closeImageModal);

// Cerrar al hacer click fuera de la imagen
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        closeImageModal();
    }
});

// ============================================
// INICIALIZACIÓN
// ============================================

// Cuando la imagen se carga, ajustar al tamaño del viewport
image.addEventListener('load', () => {
    updateTransform();
});

// Prevenir el comportamiento por defecto del arrastre de imagen
image.addEventListener('dragstart', (e) => {
    e.preventDefault();
});

// Actualizar contenedor cuando se redimensiona la ventana
window.addEventListener('resize', () => {
    if (!modal.classList.contains('hidden')) {
        updateContainerSize();
    }
});

// ============================================
// FUNCIÓN PARA ABRIR EL MODAL (llamar desde tu código)
// ============================================

// Ejemplo de uso:
// <button onclick="openImageModal()">Ver Imagen</button>

console.log('✅ Visor de imágenes mejorado cargado correctamente');



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