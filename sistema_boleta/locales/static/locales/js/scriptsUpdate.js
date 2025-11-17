function mostrarMensajeFlash(mensaje, tipo = 'success') {
        // Remover mensajes anteriores si existen
        const mensajeAnterior = document.querySelector('.mensaje-dinamico');
        if (mensajeAnterior) {
            mensajeAnterior.remove();
        }

        // Crear el contenedor de mensajes si no existe
        let flashContainer = document.querySelector('.flash-container');
        if (!flashContainer) {
            flashContainer = document.createElement('div');
            flashContainer.className = 'flash-container';
            document.body.appendChild(flashContainer);
        }

        // Crear el mensaje con el mismo formato que los mensajes Django
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${tipo} mensaje-dinamico`;
        alertDiv.innerHTML = `
            ${mensaje}
            <button class="alert-close" type="button" aria-label="Cerrar">&times;</button>
        `;

        flashContainer.appendChild(alertDiv);

        // Evento para cerrar manualmente
        const closeBtn = alertDiv.querySelector('.alert-close');
        closeBtn.addEventListener('click', () => {
            cerrarMensaje(alertDiv);
        });

        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            cerrarMensaje(alertDiv);
        }, 5000);
    }

    // Función para cerrar mensaje con animación
    function cerrarMensaje(alertDiv) {
        if (!alertDiv || alertDiv.classList.contains('alert-closing')) {
            return;
        }

        alertDiv.classList.add('alert-closing');

        setTimeout(() => {
            alertDiv.remove();
            
            // Si no quedan más alertas, remover el contenedor
            const flashContainer = document.querySelector('.flash-container');
            if (flashContainer && flashContainer.children.length === 0) {
                flashContainer.remove();
            }
        }, 600);
    }

// ============== Funciones de Modal ==============
function openEditModalLocal(idLocal) {
    fetch(`/locales/editar_local/${idLocal}/`)
        .then(response => {
            if (!response.ok) throw new Error("Error en la respuesta del servidor");
            return response.json();
        })
        .then(data => {
            const modal = document.getElementById("modal");
            const modalContent = document.getElementById("modal-content");
            modalContent.innerHTML = data.html;
            modal.removeAttribute('aria-hidden');
        })
        .catch(error => {
            console.error("Error:", error);
            mostrarMensajeFlash("❌ Ocurrió un error al abrir el formulario", "error");
        });
}

function openDeleteModalLocal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.setAttribute('aria-hidden', 'true');
        document.getElementById("modal-content").innerHTML = "";
    }
}

function openDeleteModal(id, nombre) {
    document.getElementById('delete_id').value = id;
    document.getElementById('delete_text').textContent = `¿Estás seguro de querer eliminar el local "${nombre}"?`;
    const modal = document.getElementById('deleteModal');
    modal.removeAttribute('aria-hidden');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.setAttribute('aria-hidden', 'true');
}

// ============== Formulario de Actualización ==============
document.addEventListener("submit", function (e) {
    if (e.target.matches("#formEditarLocales")) {
        console.log("🟢 Formulario de edición detectado");
        e.preventDefault();
        e.stopPropagation();

        const form = e.target;
        const formData = new FormData(form);

        if (!validarCamposFormulario()) {
            console.log("❌ Validación fallida");
            return;
        }

        if (!formData.get('id')) {
            mostrarMensajeFlash("❌ Error: ID del local no encontrado", "error");
            return;
        }

        const btnSubmit = form.querySelector('button[type="submit"]');
        const textoOriginal = btnSubmit ? btnSubmit.textContent : '';
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.textContent = 'Guardando...';
        }

        fetch("/locales/actualizar_local/", {
            method: "POST",
            headers: {'X-CSRFToken': formData.get('csrfmiddlewaretoken')},
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                mostrarMensajeFlash(data.message, data.message_type || "success");
            }

            if (data.success) {
                openDeleteModalLocal("modal");

                const fila = document.getElementById(`local-${data.local.id}`);
                if (fila) {
                    // Actualizar nombre y avatar
                    const localNombre = fila.querySelector(".local-nombre");
                    if (localNombre) localNombre.textContent = data.local.nombre;

                    const localAvatar = fila.querySelector(".local-avatar");
                    if (localAvatar) localAvatar.textContent = data.local.nombre.charAt(0).toUpperCase();

                    // Actualizar nivel
                    const nivelCell = fila.querySelector("td.nivel");
                    if (nivelCell) nivelCell.textContent = data.local.nivel;

                    // Actualizar estado badge
                    const estadoBadge = fila.querySelector(".badge-disponible, .badge-ocupado");
                    if (estadoBadge) {
                        estadoBadge.className = `badge badge-${data.local.estado.toLowerCase()}`;
                        estadoBadge.textContent = data.local.estado;
                    }

                    fila.style.animation = 'none';
                    setTimeout(() => fila.style.animation = 'fadeIn 0.5s ease', 10);
                }
            } else if (data.html) {
                document.getElementById("modal-content").innerHTML = data.html;
            }
        })
        .catch(error => {
            console.error("Error:", error);
            mostrarMensajeFlash("❌ Ocurrió un error al actualizar", "error");
        })
        .finally(() => {
            if (btnSubmit) {
                btnSubmit.disabled = false;
                btnSubmit.textContent = textoOriginal;
            }
        });
    }
});

// ============== Validación ==============
function validarCamposFormulario() {
    let valido = true;
    const campos = [
        {id: "id_nombre", tipo: "texto", mensaje: "El nombre sólo debe contener letras."},
        {id: "id_nivel", tipo: "select", mensaje: "Seleccione un nivel válido."},
        {id: "id_estado", tipo: "select", mensaje: "Seleccione un estado válido."}
    ];

    campos.forEach(({ id, tipo, mensaje }) => {
        const campo = document.getElementById(id);
        const errorDiv = document.getElementById(`error-${id}`);
        if (!campo || !errorDiv) return;

        let error = false;

        if (tipo === "texto" && !/^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(campo.value.trim())) error = true;
        if (tipo === "select" && (!campo.value || campo.value.trim() === "")) error = true;

        if (error) {
            campo.classList.add("input-error");
            errorDiv.textContent = mensaje;
            errorDiv.style.display = "block";
            setTimeout(() => errorDiv.style.display = "none", 4000);
            valido = false;
        } else {
            campo.classList.remove("input-error");
            errorDiv.textContent = "";
            errorDiv.style.display = "none";
        }
    });

    return valido;
}

// ============== Eliminación ==============
document.addEventListener("DOMContentLoaded", () => {
    const deleteForm = document.querySelector("#deleteModal form");
    
    if (deleteForm) {
        deleteForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(deleteForm);

            fetch(deleteForm.action, {
                method: "POST",
                headers: {"X-CSRFToken": formData.get("csrfmiddlewaretoken")},
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const fila = document.getElementById(`local-${data.local_id}`);
                    if (fila) {
                        fila.style.animation = 'fadeOut 0.5s ease';
                        setTimeout(() => fila.remove(), 500);
                    }
                    closeModal("deleteModal");
                    mostrarMensajeFlash("✅ Local eliminado correctamente", "success");
                } else {
                    closeModal("deleteModal");
                    mostrarMensajeFlash(data.error || "❌ No se pudo eliminar", "error");
                }
            })
            .catch(err => {
                console.error("Error:", err);
                mostrarMensajeFlash("❌ Error al eliminar", "error");
            });
        });
    }
});

const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: scale(1); }
        to { opacity: 0; transform: scale(0.95); }
    }
`;
document.head.appendChild(style);