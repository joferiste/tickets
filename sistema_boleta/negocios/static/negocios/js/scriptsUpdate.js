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

        if (e.target.matches("#formEditarNegocio")) {
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
                console.error("id del negocio no encontrado en el formulario");
                showAlert("Error: id de negocio no encontrado");
                return;
            }

            console.log("Iniciando peticion AJAX...");

            fetch("/negocios/actualizar_negocio/", {
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
                    openDeleteModalNegocio("modal");
                    showAlert("✅ Negocio actualizado correctamente", "success");

                    const fila = document.getElementById(`negocio-${data.negocio.id}`);
                    if (fila) {
                        fila.querySelector(".nombre").textContent = data.negocio.nombre;
                        fila.querySelector(".descripcion").textContent = data.negocio.descripcion;
                        fila.querySelector(".telefono1").textContent = data.negocio.telefono1;
                        fila.querySelector(".telefono2").textContent = data.negocio.telefono2;
                        fila.querySelector(".email").textContent = data.negocio.email;
                        fila.querySelector(".nit").textContent = data.negocio.nit;
                        fila.querySelector(".categoria").textContent = data.negocio.categoria;
                        fila.querySelector(".usuario").textContent = data.negocio.usuario;
                        fila.querySelector(".estado").textContent = data.negocio.estado;
                    }
                } else {
                    // Reemplaza el contenido del modal con errores (mantiene funcionalidad del nuevo form)
                    document.getElementById("modal-content").innerHTML = data.html;
                }
            })
            .catch(error => {
                console.error("Error:", error);
                showAlert("Ocurrió un error al actualizar el negocio", "error");
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
            id: "id_descripcion",
            tipo: "direcciones",
            mensaje: "La dirección debe estar compuesta por letras y dígitos."
        },
                {
            id: "id_nit",
            tipo: "nit",
            mensaje: "El nit debe estar compuesto por 6 a 9 dígitos."
        },
                {
            id: "id_telefono1",
            tipo: "telefonico",
            mensaje: "El número telefónico debe de llevar el siguiente formato 44444444 o 4444-4444."
        },
                {
            id: "id_telefono2",
            tipo: "telefonicoNulo",
            mensaje: "El número telefónico debe de llevar el siguiente formato 44444444 o 4444-4444."
        },
                {
            id: "id_email",
            tipo: "email",
            mensaje: "Ajústese al formato de correo válido."
        },
        {
            id: "id_estado",
            tipo: "select",
            mensaje: "Debe seleccionar un estado válido."
        },

        {
            id: "id_categoria",
            tipo: "select",
            mensaje: "Debe seleccionar una categoría válida."
        },

        {
            id: "id_usuario",
            tipo: "select",
            mensaje: "Debe seleccionar un usuario válido."
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

            if (valor != "" && !regex.test(valor)){
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
            if (valor != "" && !regex.test(valor)) {
                error = true;
            }
        }
        
        if (tipo === "email") {
            const valor = campo.value.trim();
            const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (valor != "" && !regex.test(valor)) {
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
            
            errorDiv.textContent = "";
            errorDiv.style.display = "none";
        }
    });


    return valido;
    }

       function openDeleteModalNegocio(id) {
        document.getElementById(id).classList.add("hidden");
        document.getElementById("modal-content").innerHTML = "";
    } 

    function openDeleteModal(id, nombre){
        document.getElementById('delete_id').value = id;
        document.getElementById('delete_text').textContent = `¿Estás seguro de querer eliminar al Negocio: "${nombre}"?`;
        document.getElementById('deleteModal').classList.remove('hidden');

    };

    function closeModal(id){
        document.getElementById(id).classList.add('hidden');
    };



    document.addEventListener("DOMContentLoaded", () => {
    const deleteForm = document.querySelector("#deleteModal form");
    const modalDelete = document.getElementById('deleteModal')
    const modal = document.getElementById('modal');

    window.addEventListener('click', function (event) {
        if (event.target === modalDelete) {
            modalDelete.classList.add('hidden');
        }
    });

    window.onclick = function (event) {
        if (event.target === modal) {
            modal.classList.add('hidden');
        }
    };

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
                const fila = document.getElementById(`negocio-${data.negocio_id}`);
                if (fila) fila.remove();

                closeModal("deleteModal");
                showAlert("✅ Negocio eliminado correctamente", "success");
            } else {
                closeModal("deleteModal");
                showAlert(data.error || "❌ No se pudo eliminar el negocio", "error");
            }
        })
        .catch(err => {
            console.error("Error al eliminar:", err);
            showAlert("❌ Error inesperado al intentar eliminar", "error");
        });
    });
});
