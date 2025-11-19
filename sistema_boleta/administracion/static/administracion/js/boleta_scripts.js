// ========================================
// MODAL DE BOLETA - JAVASCRIPT COMPLETO
// ========================================

// Variables globales del visor
let currentRotation = 0;
let currentScale = 1;
let isDragging = false;
let startX = 0;
let startY = 0;
let translateX = 0;
let translateY = 0;
let initialTranslateX = 0;
let initialTranslateY = 0;

// Configuración
const ZOOM_STEP = 0.2;
const MIN_SCALE = 0.3;
const MAX_SCALE = 5;
const WHEEL_ZOOM_STEP = 0.1;

// ========================================
// FUNCIONES PRINCIPALES DEL MODAL
// ========================================

function openModal() {
    const modal = document.getElementById("boletaModal");
    modal.classList.remove("hidden");
    resetImage();
    initImageViewer();
}

function closeModal() {
    const modal = document.getElementById("boletaModal");
    modal.classList.add("hidden");
    removeImageViewerListeners();
}

// ========================================
// FUNCIONES DE TRANSFORMACIÓN
// ========================================

function rotateLeft() {
    currentRotation -= 90;
    updateTransform();
}

function rotateRight() {
    currentRotation += 90;
    updateTransform();
}

function zoomIn() {
    currentScale = Math.min(MAX_SCALE, currentScale + ZOOM_STEP);
    updateTransform();
    updateZoomDisplay();
}

function zoomOut() {
    currentScale = Math.max(MIN_SCALE, currentScale - ZOOM_STEP);
    updateTransform();
    updateZoomDisplay();
}

function resetImage() {
    currentRotation = 0;
    currentScale = 1;
    translateX = 0;
    translateY = 0;
    initialTranslateX = 0;
    initialTranslateY = 0;
    updateTransform();
    updateZoomDisplay();
}

function fitToScreen() {
    const viewport = document.getElementById("imageViewportForm");
    const img = document.getElementById("modalImage");
    
    if (!viewport || !img) return;
    
    const viewportRect = viewport.getBoundingClientRect();
    const imgRect = img.getBoundingClientRect();
    
    // Calcular escala para ajustar
    const scaleX = viewportRect.width / (imgRect.width / currentScale);
    const scaleY = viewportRect.height / (imgRect.height / currentScale);
    const newScale = Math.min(scaleX, scaleY) * 0.9; // 90% para margen
    
    currentScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));
    translateX = 0;
    translateY = 0;
    
    updateTransform();
    updateZoomDisplay();
}

function updateTransform() {
    const img = document.getElementById("modalImage");
    if (img) {
        img.style.transform = `
            translate(${translateX}px, ${translateY}px) 
            rotate(${currentRotation}deg) 
            scale(${currentScale})
        `;
    }
}

function updateZoomDisplay() {
    const zoomDisplay = document.getElementById("zoomLevelForm");
    if (zoomDisplay) {
        zoomDisplay.textContent = `${Math.round(currentScale * 100)}%`;
    }
}

// ========================================
// FUNCIONES DE ARRASTRE
// ========================================

function handleMouseDown(e) {
    if (e.target.id !== "modalImage") return;
    
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    initialTranslateX = translateX;
    initialTranslateY = translateY;
    
    const viewport = document.getElementById("imageViewportForm");
    if (viewport) {
        viewport.style.cursor = "grabbing";
    }
    
    e.preventDefault();
}

function handleMouseMove(e) {
    if (!isDragging) return;
    
    const deltaX = e.clientX - startX;
    const deltaY = e.clientY - startY;
    
    translateX = initialTranslateX + deltaX;
    translateY = initialTranslateY + deltaY;
    
    updateTransform();
}

function handleMouseUp() {
    if (isDragging) {
        isDragging = false;
        const viewport = document.getElementById("imageViewportForm");
        if (viewport) {
            viewport.style.cursor = "grab";
        }
    }
}

function handleMouseLeave() {
    if (isDragging) {
        handleMouseUp();
    }
}

// ========================================
// FUNCIÓN DE ZOOM CON RUEDA DEL MOUSE
// ========================================

function handleWheel(e) {
    e.preventDefault();
    
    const delta = e.deltaY > 0 ? -WHEEL_ZOOM_STEP : WHEEL_ZOOM_STEP;
    const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, currentScale + delta));
    
    if (newScale === currentScale) return;
    
    // Obtener posición del mouse relativa al viewport
    const viewport = document.getElementById("imageViewportForm");
    const rect = viewport.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Calcular el centro del viewport
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    // Ajustar la traducción para hacer zoom hacia el mouse
    const scaleFactor = newScale / currentScale;
    translateX = mouseX - (mouseX - translateX) * scaleFactor - (mouseX - centerX) * (scaleFactor - 1);
    translateY = mouseY - (mouseY - translateY) * scaleFactor - (mouseY - centerY) * (scaleFactor - 1);
    
    currentScale = newScale;
    updateTransform();
    updateZoomDisplay();
}

// ========================================
// INICIALIZACIÓN Y LIMPIEZA DE EVENTOS
// ========================================

function initImageViewer() {
    const viewport = document.getElementById("imageViewportForm");
    
    if (viewport) {
        // Eventos de mouse para arrastre
        viewport.addEventListener("mousedown", handleMouseDown);
        viewport.addEventListener("mousemove", handleMouseMove);
        viewport.addEventListener("mouseup", handleMouseUp);
        viewport.addEventListener("mouseleave", handleMouseLeave);
        
        // Evento de rueda para zoom
        viewport.addEventListener("wheel", handleWheel, { passive: false });
    }
    
    updateZoomDisplay();
}

function removeImageViewerListeners() {
    const viewport = document.getElementById("imageViewportForm");
    
    if (viewport) {
        viewport.removeEventListener("mousedown", handleMouseDown);
        viewport.removeEventListener("mousemove", handleMouseMove);
        viewport.removeEventListener("mouseup", handleMouseUp);
        viewport.removeEventListener("mouseleave", handleMouseLeave);
        viewport.removeEventListener("wheel", handleWheel);
    }
}

// ========================================
// ATAJOS DE TECLADO
// ========================================

document.addEventListener("keydown", function(e) {
    const modal = document.getElementById("boletaModal");
    if (modal && !modal.classList.contains("hidden")) {
        switch(e.key) {
            case "Escape":
                closeModal();
                break;
            case "+":
            case "=":
                e.preventDefault();
                zoomIn();
                break;
            case "-":
            case "_":
                e.preventDefault();
                zoomOut();
                break;
            case "f":
            case "F":
                e.preventDefault();
                fitToScreen();
                break;
        }
    }
});

// ========================================
// VALIDACIÓN DEL FORMULARIO
// ========================================

// Validación en tiempo real del número de boleta
const numeroBoleta = document.getElementById("numeroBoleta");
if (numeroBoleta) {
    numeroBoleta.addEventListener("input", function(e) {
        this.value = this.value.replace(/[^\d]/g, "");
    });
}

// Validación en tiempo real del monto
const montoInput = document.getElementById("monto");
if (montoInput) {
    montoInput.addEventListener("input", function(e) {
        let value = this.value.replace(/[^\d.,]/g, "");
        value = value.replace(/,/g, ".");
        
        const parts = value.split(".");
        if (parts.length > 2) {
            value = parts[0] + "." + parts.slice(1).join("");
        }
        
        if (parts[1] && parts[1].length > 2) {
            value = parts[0] + "." + parts[1].substring(0, 2);
        }
        
        this.value = value;
    });
}

// Prevenir envío duplicado del formulario
const form = document.getElementById("procesarBoletaForm");
if (form) {
    form.addEventListener("submit", function(e) {
        const submitBtn = document.getElementById("btn-procesar");
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M12 6v6l4 2"></path>
                </svg>
                Procesando...
            `;
            
            // Reactivar después de 3 segundos por si hay error
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Procesar Boleta
                `;
            }, 3000);
        }
    });
}

// Funcion para esperar a que el elemento este disponible
function waitForElement(selector, callback, maxAttempts = 50) {
    let attempts = 0;

    function check() {
        const element = document.querySelector(selector);

        if (element) {
            callback(element);
        } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(check, 100) // Reintentar cada 100ms 
        } else {
            console.error(`Elemento ${selector} no encontrado despues de ${maxAttempts} intentos.`)
        }
    }

    check();
}

function sanitizeDigits(el) {
    // Solo digitos, no espacios
    el.value = el.value.replace(/\D+/g, '');
}

function sanitizeMoney(el) {
    // Solo digitos y un separador decimal (coma o punto)
    let v = el.value.replace(/[^\d.,]/g, '');
    // Si hay mas de una coma o punto, conservar solo el primero
    const parts = v.split(/[.,]/);
    if (parts.lenght > 2) {
        v = parts[0] + '.' + parts.slice(1).join('').replace(/[^\d]/g, '');
    } else if (parts.lenght === 2) {
        v = parts[0] + '.' + parts[1];
    }
    el.value = v;
}


// Esperar a que el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    const numeroBoleta = document.getElementById('numeroBoleta');
    const monto = document.getElementById('monto');
    const fechaInput = document.getElementById('fechaDeposito');

    if (fechaInput) {
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0); // Normalizando

        fechaInput.addEventListener('change', function() {
            const valor = new Date(this.value);

            if (valor > hoy) {
                showResultadoModal('error', 'La fecha no puede ser mayor a la actual');
                this.value = hoy.toISOString().split('T')[0];
            }
        });
    }

    if (numeroBoleta) {
        numeroBoleta.addEventListener('input', () => sanitizeDigits(numeroBoleta));
    }

    if (monto) {
        monto.addEventListener('input', () => sanitizeMoney(monto))
    }

    // Validacion extra al enviar (ademas del patter html)

    const form = document.getElementById('procesarBoletaForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            const nb = (numeroBoleta?.value || '').trim();
            const mt = (monto?.value || '').trim();
            const reBoleta = /^\d{4,10}$/;
            const remonto = /^\d+([.,]\d{1,2})?$/;

            if (!reBoleta.test(nb)) {
                e.preventDefault();
                showResultadoModal('error', 'Numero de boleta invalido, favor de ingresar solo digitos (4 - 10)', null);
                return;
            }

            if (!remonto.test(mt)) {
                e.preventDefault();
                showResultadoModal('error', 'Monto invalido: use formato 1234.56 o o 1234.56', null);
                return;
            }
        }, { capture: true });
    }

    console.log('DOM Content Loaded');
    
    // Esperar a que el formulario esté disponible
    waitForElement('#procesarBoletaForm', function(form) {
        console.log('Formulario encontrado, configurando event listeners...');
        
        // Interceptar el envío del formulario para usar AJAX
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Formulario enviado, procesando...');
            
            const formData = new FormData(this);
            
            // Hacer petición AJAX
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => {
                console.log('Respuesta recibida:', response.status);
                
                // Verificar si la respuesta es JSON válida
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    // Si no es JSON, obtener el texto para debug
                    return response.text().then(text => {
                        console.error('Respuesta HTML recibida:', text);
                        throw new Error('La respuesta no es JSON válida - posiblemente una redirección o error de servidor');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Datos JSON recibidos:', data);
                
                // Cerrar el modal de ingreso
                if (typeof closeModal === 'function') {
                    closeModal();
                }
                
                // Mostrar el modal de resultado
                showResultadoModal(data.tipo, data.mensaje, data.transaccion_id);
            })
            .catch(error => {
                console.error('Error en el proceso:', error);
                showResultadoModal('error', 'Ocurrió un error inesperado al procesar la boleta.', null);
            });
        });
    });

   
}); 

function showResultadoModal(tipo, mensaje, transaccionId) {
    console.log('Mostrando modal resultado:', tipo, mensaje);

    // Mapear tipos Backend a IDs frontend
    const mapTipos = {
        success: 'exitoso',
        pendiente: 'pendiente',
        error: 'error'
    };
    const tipoMapped = mapTipos[tipo] || tipo;

    // Ocultar todas las secciones
    document.querySelectorAll('.resultado-section').forEach(section => {
        section.classList.add('hidden-1');
    });

    // Mostrar la sección correspondiente
    const seccion = document.getElementById(`resultado-${tipoMapped}`);
    const mensajeElement = document.getElementById(`mensaje-${tipoMapped}`);

    if (!seccion || !mensajeElement) {
        console.error('No se encontró la sección o elemento de mensaje para:', tipoMapped);
        return
    }

    seccion.classList.remove('hidden-1');
    mensajeElement.textContent = mensaje;
    console.log('Sección mostrada:', tipoMapped);

    // Buscar el botón "Ver Transacción" DENTRO de la sección activa.
    // Intentamos por id local, luego por clase y finalmente por data-attribute.
    let verBtn = seccion.querySelector('#verTransaccionBtn') 
            || seccion.querySelector('.btn-resultado.primary')
            || seccion.querySelector('button[data-action="ver-transaccion"]');

    if (verBtn) {
        // Reemplazar el botón por su clon para limpiar todos los event listeners previos
        const nuevoBtn = verBtn.cloneNode(true);
        verBtn.parentNode.replaceChild(nuevoBtn, verBtn);
        verBtn = nuevoBtn;

        if (transaccionId) {
            verBtn.style.display = ''; // asegurarnos visible
            verBtn.addEventListener('click', function () {
                window.location.href = `/administracion/transaccion/${transaccionId}/`;
            });
        } else {
            // si no hay id, ocultarlo
            verBtn.style.display = 'none';
        }
    } else {
        console.warn('No se encontró botón "Ver Transacción" dentro de la sección activa.');
    }
    // 🔹 BOTÓN: Salir al Home
    let salirBtn = seccion.querySelector('#salirHome')
        || seccion.querySelector('.btn-resultado.secondary')
        || seccion.querySelector('button[data-action="salir-home"]');

    if (salirBtn) {
        const nuevoSalirBtn = salirBtn.cloneNode(true);
        salirBtn.parentNode.replaceChild(nuevoSalirBtn, salirBtn);
        salirBtn = nuevoSalirBtn;

        salirBtn.addEventListener('click', function () {
            // Cerrar animación (opcional)
            const resultadoModal = document.getElementById('resultadoModal');
            if (resultadoModal) {
                resultadoModal.classList.add('hidden-1');
                console.log('Modal cerrado, redirigiendo al Home...');
                setTimeout(() => {
                    window.location.href = "/";
                }, 200); // 0.2s para dejar animar el cierre
            } else {
                window.location.href = "/";
            }
        });
    } else {
        console.warn('No se encontró botón "Cerrar / Salir".');
    } 

    // Mostrar el modal de resultado
    const resultadoModal = document.getElementById('resultadoModal');
    if (resultadoModal) {
        resultadoModal.classList.remove('hidden-1');
        console.log('Modal resultado mostrado');
    } else {
        console.error('No se encontró el modal de resultado');
    }
}
