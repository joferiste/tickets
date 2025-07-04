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
                modal.classList.remove("hidden");
            })
            .catch(error => {
                console.error("Error:", error);
                alert("Ocurrió un error al abrir el formulario de edición");
            });
    }

    // Delegación del evento submit para formularios dinámicos
    document.addEventListener("submit", function (e) {
        console.log("Submit detectado en elemento ", e.target.tagName, "con ID", e.target.id);

        if (e.target.matches("#formEditarLocales")) {
            console.log("🟢 Formulario de edicion detectado");
            e.preventDefault();
            e.stopPropagation();

            const form = e.target;
            const formData = new FormData(form);

            console.log("formData creado: ", [...formData.entries()])

            // Validacion del frontend antes de entrar al backend
            if (!validarCamposFormulario()) {
            console.log("❌ Validación de campos fallida.");
            return; // Evita el envío si hay errores
        }

            if (!formData.get('id')){
                console.error("id del local no encontrado en el formulario");
                alert("Error: id de local no encontrado");
                return;
            }

            console.log("Iniciando peticion AJAX...");

            fetch("/locales/actualizar_local/", {
                method: "POST",
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                },
                body: formData
            })
            .then(response => {
                console.log("Respuesta recibida:", response.status);
                if (!response.ok) {
                    throw new Error (`HTTP error! status: ${response.status}`)
                }
                return response.json();
            })
            .then(data => {
                console.log("Respuesta del servidor:", data)
                if (data.success) {
                    openDeleteModalLocal("modal");
                    showAlert("✅ Local actualizado correctamente", "success");

                    const fila = document.getElementById(`local-${data.local.id}`);
                    if (fila) {
                        fila.querySelector(".nombre").textContent = data.local.nombre;
                        fila.querySelector(".estado").textContent = data.local.estado;
                        fila.querySelector(".nivel").textContent = data.local.nivel;
                    }
                } else {
                    // Reemplaza el contenido del modal con errores (mantiene funcionalidad del nuevo form)
                    document.getElementById("modal-content").innerHTML = data.html;
                }
            })
            .catch(error => {
                console.error("Error:", error);
                showAlert("Ocurrió un error al actualizar el local", "error");
            });
        }
    });

    function showAlert(message, type = "success") {
        const alertBox = document.getElementById("alert-container");
 
        alertBox.className = `alert-container ${type} show`;
        alertBox.textContent = message;

        setTimeout(() => {
            alertBox.classList.remove("show");
        }, 4500);
    }

    function validarCamposFormulario() {
    let valido = true;

    const campos = [
        {
            id: "id_nombre",
            tipo: "texto",
            mensaje: "El nombre sólo debe contener letras y no debe quedar vacío."
        },
        {
            id: "id_nivel",
            tipo: "select",
            mensaje: "Debe seleccionar un nivel válido."
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

        if (tipo === "select") {
            if (!campo.value || campo.value.trim() === "") error = true;
        }

        if (error) {
            campo.classList.add("input-error");
            errorDiv.textContent = mensaje;
            errorDiv.style.display = "block";
            setTimeout(() => {
                errorDiv.style.display = "none";
            }, 4000);
            valido = false;
        } else {
            errorDiv.textContent = "";
            errorDiv.style.display = "none";
        }
    });

    return valido;
    }

    function openDeleteModalLocal(id) {
        document.getElementById(id).classList.add("hidden");
        document.getElementById("modal-content").innerHTML = "";
    }

    function openDeleteModal(id, nombre){
        document.getElementById('delete_id').value = id;
        document.getElementById('delete_text').textContent = `¿Estás seguro de querer eliminar el Local: "${nombre}"?`;
        document.getElementById('deleteModal').classList.remove('hidden');
    };

    function closeModal(id){
        document.getElementById(id).classList.add('hidden');
    };

    
    document.addEventListener("DOMContentLoaded", () => {
    const deleteForm = document.querySelector("#deleteModal form");

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
                const fila = document.getElementById(`local-${data.local_id}`);
                if (fila) fila.remove();
                
                closeModal("deleteModal");
                showAlert("✅ Local eliminado correctamente", "success");
            } else {
                closeModal("deleteModal");
                showAlert(data.error || "❌ No se pudo eliminar el Local", "error");
            }
        })
        .catch(err => {
            console.error("Error al eliminar:", err);
            showAlert("❌ Error inesperado al intentar eliminar", "error");
        });
    });
});