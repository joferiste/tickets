// ============== Sistema de Mensajes Unificado ==============
function mostrarMensajeFlash(mensaje, tipo = 'success') {
    const mensajeAnterior = document.querySelector('.mensaje-dinamico');
    if (mensajeAnterior) {
        mensajeAnterior.remove();
    }

    let flashContainer = document.querySelector('.flash-container');
    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.className = 'flash-container';
        document.body.appendChild(flashContainer);
    }

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo} mensaje-dinamico`;
    alertDiv.innerHTML = `
        ${mensaje}
        <button class="alert-close" type="button" aria-label="Cerrar">&times;</button>
    `;

    flashContainer.appendChild(alertDiv);

    const closeBtn = alertDiv.querySelector('.alert-close');
    closeBtn.addEventListener('click', () => cerrarMensaje(alertDiv));

    setTimeout(() => cerrarMensaje(alertDiv), 5000);
}

function cerrarMensaje(alertDiv) {
    if (!alertDiv || alertDiv.classList.contains('alert-closing')) return;
    
    alertDiv.classList.add('alert-closing');
    setTimeout(() => {
        alertDiv.remove();
        const flashContainer = document.querySelector('.flash-container');
        if (flashContainer && flashContainer.children.length === 0) {
            flashContainer.remove();
        }
    }, 600);
}

// ============== Funciones de Modal ==============
function openEditModalNegocio(idNegocio) {
    fetch(`/negocios/editar_negocio/${idNegocio}/`)
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

function openDeleteModalNegocio(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.setAttribute('aria-hidden', 'true');
        document.getElementById("modal-content").innerHTML = "";
    }
}

function openDeleteModal(id, nombre) {
    document.getElementById('delete_id').value = id;
    document.getElementById('delete_text').textContent = `¿Estás seguro de querer eliminar el negocio "${nombre}"?`;
    const modal = document.getElementById('deleteModal');
    modal.removeAttribute('aria-hidden');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.setAttribute('aria-hidden', 'true');
}

// ============== Formulario de Actualización ==============
document.addEventListener("submit", function (e) {
    if (e.target.matches("#formEditarNegocio")) {
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
            mostrarMensajeFlash("❌ Error: ID del negocio no encontrado", "error");
            return;
        }

        const btnSubmit = form.querySelector('button[type="submit"]');
        const textoOriginal = btnSubmit ? btnSubmit.textContent : '';
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.textContent = 'Guardando...';
        }

        fetch("/negocios/actualizar_negocio/", {
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
                openDeleteModalNegocio("modal");

                const fila = document.getElementById(`negocio-${data.negocio.id}`);
                if (fila) {
                    // Actualizar nombre y avatar
                    const negocioNombre = fila.querySelector(".negocio-nombre");
                    if (negocioNombre) negocioNombre.textContent = data.negocio.nombre;

                    const negocioAvatar = fila.querySelector(".negocio-avatar");
                    if (negocioAvatar) negocioAvatar.textContent = data.negocio.nombre.charAt(0).toUpperCase();

                    const negocioDesc = fila.querySelector(".negocio-desc");
                    if (negocioDesc) negocioDesc.textContent = data.negocio.descripcion.substring(0, 30) + '...';

                    // Actualizar otros campos
                    const categoriaCell = fila.querySelector("td.categoria .badge");
                    if (categoriaCell) categoriaCell.textContent = data.negocio.categoria;

                    const usuarioCell = fila.querySelector("td.usuario");
                    if (usuarioCell) usuarioCell.textContent = data.negocio.usuario;

                    const contactoInfo = fila.querySelector(".contacto-info");
                    if (contactoInfo) {
                        let html = `<span class="telefono1">📞 ${data.negocio.telefono1}</span>`;
                        if (data.negocio.email) {
                            html += `<span class="email">✉️ ${data.negocio.email}</span>`;
                        }
                        contactoInfo.innerHTML = html;
                    }

                    const estadoBadge = fila.querySelector(".badge-activo, .badge-inactivo");
                    if (estadoBadge) {
                        estadoBadge.className = `badge badge-${data.negocio.estado.toLowerCase()}`;
                        estadoBadge.textContent = data.negocio.estado;
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
        {id: "id_descripcion", tipo: "direcciones", mensaje: "La descripción debe contener letras y dígitos."},
        {id: "id_nit", tipo: "nit", mensaje: "El NIT debe tener 6 a 9 dígitos."},
        {id: "id_telefono1", tipo: "telefonico", mensaje: "Formato: 44444444 o 4444-4444."},
        {id: "id_telefono2", tipo: "telefonicoNulo", mensaje: "Formato: 44444444 o 4444-4444."},
        {id: "id_email", tipo: "email", mensaje: "Formato de correo inválido."},
        {id: "id_estado", tipo: "select", mensaje: "Seleccione un estado."},
        {id: "id_categoria", tipo: "select", mensaje: "Seleccione una categoría."},
        {id: "id_usuario", tipo: "select", mensaje: "Seleccione un usuario."}
    ];

    campos.forEach(({ id, tipo, mensaje }) => {
        const campo = document.getElementById(id);
        const errorDiv = document.getElementById(`error-${id}`);
        if (!campo || !errorDiv) return;

        let error = false;

        if (tipo === "texto" && !/^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(campo.value.trim())) error = true;
        if (tipo === "direcciones" && !/^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ\s\-\.\,\;]+$/.test(campo.value.trim())) error = true;
        if (tipo === "nit") {
            const val = campo.value.trim();
            if (val !== "" && !/^[1-9][0-9]{5,8}$/.test(val)) error = true;
        }
        if (tipo === "telefonico" && !/^(?:[1-9][0-9]{7}|[1-9][0-9]{3}-[0-9]{4})$/.test(campo.value.trim())) error = true;
        if (tipo === "telefonicoNulo") {
            const val = campo.value.trim();
            if (val !== "" && !/^(?:[1-9][0-9]{7}|[1-9][0-9]{3}-[0-9]{4})$/.test(val)) error = true;
        }
        if (tipo === "email") {
            const val = campo.value.trim();
            if (val !== "" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) error = true;
        }
        if (tipo === "select" && (!campo.value || campo.value.trim() === "")) error = true;

        if (error) {
            campo.classList.add("input-error", "shake");
            setTimeout(() => campo.classList.remove("shake"), 550);
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
                    const fila = document.getElementById(`negocio-${data.negocio_id}`);
                    if (fila) {
                        fila.style.animation = 'fadeOut 0.5s ease';
                        setTimeout(() => fila.remove(), 500);
                    }
                    closeModal("deleteModal");
                    mostrarMensajeFlash("✅ Negocio eliminado correctamente", "success");
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