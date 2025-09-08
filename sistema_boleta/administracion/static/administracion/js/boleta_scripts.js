let currentRotation = 0;
let currentScale = 1;

function openModal() {
    document.getElementById("boletaModal").classList.remove("hidden");
    resetImage();
}

function closeModal() {
    document.getElementById("boletaModal").classList.add("hidden");
}

function rotateLeft() {
    currentRotation -= 90;
    updateTransform();
}

function rotateRight() {
    currentRotation += 90;
    updateTransform();
}

function zoomIn() {
    currentScale += 0.2;
    updateTransform();
}

function zoomOut() {
    currentScale = Math.max(0.2, currentScale - 0.2);
    updateTransform();
}

function resetImage() {
    currentRotation = 0;
    currentScale = 1;
    updateTransform();
}

function updateTransform() {
    const img = document.getElementById("modalImage");
    if (img) {
        img.style.transform = `rotate(${currentRotation}deg) scale(${currentScale})`;
    }
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

// Esperar a que el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
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

     // Configurar event listener para cerrar modal (si existe)
    waitForElement('#resultadoModal', function(modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeResultadoModal();
            }
        });
    });
}); 

// Funciones globales
function showResultadoModal(tipo, mensaje, transaccionId) {
    console.log('Mostrando modal resultado:', tipo, mensaje);
    
    // Mapear tipos Backend a IDs frontend
    const mapTipos = {
        success: 'exitoso',
        pendiete: 'pendiente',
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
    
    if (seccion && mensajeElement) {
        seccion.classList.remove('hidden-1');
        mensajeElement.textContent = mensaje;
        console.log('Sección mostrada:', tipoMapped);
    } else {
        console.error('No se encontró la sección o mensaje para:', tipoMapped);
    }
    
    // Configurar el botón de ver transacción (redigir directamente)
    const verBtn = document.getElementById('verTransaccionBtn');
    if (transaccionId && verBtn) {
        verBtn.onclick = function() {
            window.location.href = `/administracion/transaccion/${transaccionId}/`;
        };
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

function closeResultadoModal() {
    const resultadoModal = document.getElementById('resultadoModal');
    if (resultadoModal) {
        resultadoModal.classList.add('hidden-1');
        console.log('Modal resultado cerrado');
    }
}