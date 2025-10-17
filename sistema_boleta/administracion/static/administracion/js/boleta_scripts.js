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
