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
function openEditModalUsuario(idUsuario) {
    fetch(`/usuarios/editar_usuario/${idUsuario}/`)
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
            mostrarMensajeFlash("❌ Ocurrió un error al abrir el formulario de edición", "error");
        });
}

function openDeleteModalUsuario(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.setAttribute('aria-hidden', 'true');
        document.getElementById("modal-content").innerHTML = "";
    }
}

function openDeleteModal(id, nombre){
    document.getElementById('delete_id').value = id;
    document.getElementById('delete_text').textContent = `¿Estás seguro de querer eliminar al usuario "${nombre}"?`;
    const modal = document.getElementById('deleteModal');
    modal.removeAttribute('aria-hidden');
}

function closeModal(id){
    const modal = document.getElementById(id);
    if (modal) {
        modal.setAttribute('aria-hidden', 'true');
    }
}

// ============== Formulario de Actualización ==============
document.addEventListener("submit", function (e) {
    console.log("Submit detectado en elemento", e.target.tagName, "con ID", e.target.id);

    if (e.target.matches("#formEditarUsuarios")) {
        console.log("🟢 Formulario de edición detectado");
        e.preventDefault();
        e.stopPropagation();

        const form = e.target;
        const formData = new FormData(form);

        console.log("formData creado:", [...formData.entries()]);

        // Validación del frontend antes de entrar al backend
        if (!validarCamposFormulario()) {
            console.log("❌ Validación de campos fallida.");
            return;
        }

        if (!formData.get('id')) {
            console.error("ID del usuario no encontrado en el formulario");
            mostrarMensajeFlash("❌ Error: ID del usuario no encontrado", "error");
            return;
        }

        console.log("Iniciando petición AJAX...");

        // Deshabilitar botón mientras se procesa
        const btnSubmit = form.querySelector('button[type="submit"]');
        const textoOriginal = btnSubmit ? btnSubmit.textContent : '';
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.textContent = 'Guardando...';
        }

        fetch("/usuarios/actualizar_usuario/", {
            method: "POST",
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
            body: formData
        })
        .then(response => {
            console.log("Respuesta recibida:", response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Respuesta del servidor:", data);

            // Mostrar mensaje
            if (data.message) {
                mostrarMensajeFlash(data.message, data.message_type || "success");
            }

            if (data.success) {
                openDeleteModalUsuario("modal");

                // ACTUALIZAR FILA CON NUEVA ESTRUCTURA HTML
                const fila = document.getElementById(`usuario-${data.usuario.id}`);
                if (fila) {
                    // Actualizar nombre y avatar
                    const usuarioNombre = fila.querySelector(".usuario-nombre");
                    if (usuarioNombre) {
                        usuarioNombre.textContent = data.usuario.nombre;
                    }

                    // Actualizar avatar (primera letra)
                    const usuarioAvatar = fila.querySelector(".usuario-avatar");
                    if (usuarioAvatar) {
                        usuarioAvatar.textContent = data.usuario.nombre.charAt(0).toUpperCase();
                    }

                    // Actualizar NIT
                    const usuarioNit = fila.querySelector(".usuario-nit");
                    if (usuarioNit) {
                        usuarioNit.textContent = `NIT: ${data.usuario.nit || '---'}`;
                    }

                    // Actualizar DPI
                    const dpiCell = fila.querySelector("td.dpi");
                    if (dpiCell) {
                        dpiCell.textContent = data.usuario.dpi;
                    }

                    // Actualizar teléfonos
                    const telefonoInfo = fila.querySelector(".telefono-info");
                    if (telefonoInfo) {
                        let telefonoHTML = `<span>${data.usuario.telefono1}</span>`;
                        if (data.usuario.telefono2) {
                            telefonoHTML += `<span class="telefono-alt">${data.usuario.telefono2}</span>`;
                        }
                        telefonoInfo.innerHTML = telefonoHTML;
                    }

                    // Actualizar email
                    const emailCell = fila.querySelector("td.email");
                    if (emailCell) {
                        emailCell.textContent = data.usuario.email || '---';
                    }

                    // Actualizar badge de estado
                    const estadoBadge = fila.querySelector(".badge");
                    if (estadoBadge) {
                        estadoBadge.className = `badge badge-${data.usuario.estado.toLowerCase()}`;
                        estadoBadge.textContent = data.usuario.estado;
                    }

                    // Aplicar animación de actualización
                    fila.style.animation = 'none';
                    setTimeout(() => {
                        fila.style.animation = 'fadeIn 0.5s ease';
                    }, 10);
                }
            } else if (data.html) {
                // Reemplazar contenido del modal con errores
                document.getElementById("modal-content").innerHTML = data.html;
            }
        })
        .catch(error => {
            console.error("Error:", error);
            mostrarMensajeFlash("❌ Ocurrió un error al actualizar el usuario", "error");
        })
        .finally(() => {
            // Restaurar botón
            if (btnSubmit) {
                btnSubmit.disabled = false;
                btnSubmit.textContent = textoOriginal;
            }
        });
    }
});

// ============== Validación de Campos ==============
function validarCamposFormulario() {
    let valido = true;

    const campos = [
        {
            id: "id_nombre",
            tipo: "texto",
            mensaje: "El nombre sólo debe contener letras y no debe quedar vacío."
        },
        {
            id: "id_direccionCompleta",
            tipo: "direcciones",
            mensaje: "La dirección debe estar compuesta por letras y dígitos."
        },
        {
            id: "id_nit",
            tipo: "nit",
            mensaje: "El NIT debe estar compuesto por 6 a 9 dígitos."
        },
        {
            id: "id_dpi",
            tipo: "dpi",
            mensaje: "El DPI debe estar compuesto por 13 dígitos."
        },
        {
            id: "id_telefono1",
            tipo: "telefonico",
            mensaje: "El número telefónico debe llevar el formato 44444444 o 4444-4444."
        },
        {
            id: "id_telefono2",
            tipo: "telefonicoNulo",
            mensaje: "El número telefónico debe llevar el formato 44444444 o 4444-4444."
        },
        {
            id: "id_email",
            tipo: "email",
            mensaje: "Ajústese al formato válido de correo."
        },
        {
            id: "id_estado",
            tipo: "select",
            mensaje: "Debe seleccionar un estado válido."
        }
    ];

    campos.forEach(({ id, tipo, mensaje }) => {
        const campo = document.getElementById(id);
        const errorDiv = document.getElementById(`error-${id}`);

        if (!campo || !errorDiv) return;

        let error = false;

        if (tipo === "texto") {
            const regex = /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/;
            if (!regex.test(campo.value.trim())) error = true;
        }

        if (tipo === "direcciones") {
            const regex = /^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ\s\-\.\,\;]+$/;
            if (!regex.test(campo.value.trim())) error = true;
        }

        if (tipo === "nit") {
            const valor = campo.value.trim();
            const regex = /^[1-9][0-9]{5,8}$/;
            if (valor !== "" && !regex.test(valor)) {
                error = true;
            }
        }

        if (tipo === "dpi") {
            const regex = /^[1-9][0-9]{12}$/;
            if (!regex.test(campo.value.trim())) error = true;
        }

        if (tipo === "telefonico") {
            const regex = /^(?:[1-9][0-9]{7}|[1-9][0-9]{3}-[0-9]{4})$/;
            if (!regex.test(campo.value.trim())) error = true;
        }

        if (tipo === "telefonicoNulo") {
            const valor = campo.value.trim();
            const regex = /^(?:[1-9][0-9]{7}|[1-9][0-9]{3}-[0-9]{4})$/;
            if (valor !== "" && !regex.test(valor)) {
                error = true;
            }
        }
        
        if (tipo === "email") {
            const valor = campo.value.trim();
            const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (valor !== "" && !regex.test(valor)) {
                error = true;
            }
        }

        if (tipo === "select") {
            if (!campo.value || campo.value.trim() === "") error = true;
        }

        if (error) {
            campo.classList.add("input-error");
            campo.classList.add('shake');

            setTimeout(() => {
                campo.classList.remove('shake');
            }, 550);

            errorDiv.textContent = mensaje;
            errorDiv.style.display = "block";
            setTimeout(() => {
                errorDiv.style.display = "none";
            }, 4000);
            valido = false;
        } else {
            campo.classList.remove("input-error");
            errorDiv.textContent = "";
            errorDiv.style.display = "none";
        }
    });

    return valido;
}

// ============== Formulario de Eliminación ==============
document.addEventListener("DOMContentLoaded", () => {
    const deleteForm = document.querySelector("#deleteModal form");
    const modalDelete = document.getElementById('deleteModal');
    const modal = document.getElementById('modal');

    // Cerrar modales al hacer clic en el backdrop
    if (modalDelete) {
        const backdrop = modalDelete.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', () => {
                closeModal('deleteModal');
            });
        }
    }

    if (modal) {
        const backdrop = modal.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', () => {
                openDeleteModalUsuario('modal');
            });
        }
    }

    if (deleteForm) {
        deleteForm.addEventListener("submit", function (e) {
            e.preventDefault();
            
            const formData = new FormData(deleteForm);

            fetch(deleteForm.action, {
                method: "POST",
                headers: {
                    "X-CSRFToken": formData.get("csrfmiddlewaretoken")
                },
                body: formData
            }) 
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const fila = document.getElementById(`usuario-${data.usuario_id}`);
                    if (fila) {
                        fila.style.animation = 'fadeOut 0.5s ease';
                        setTimeout(() => fila.remove(), 500);
                    }
                    
                    closeModal("deleteModal");
                    mostrarMensajeFlash("✅ Usuario eliminado correctamente", "success");
                } else {
                    closeModal("deleteModal");
                    mostrarMensajeFlash(data.error || "❌ No se pudo eliminar el usuario", "error");
                }
            })
            .catch(err => {
                console.error("Error al eliminar:", err);
                mostrarMensajeFlash("❌ Error inesperado al intentar eliminar", "error");
            });
        });
    }
});

// Animación de fadeOut para eliminación
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: scale(1);
        }
        to {
            opacity: 0;
            transform: scale(0.95);
        }
    }
`;
document.head.appendChild(style);