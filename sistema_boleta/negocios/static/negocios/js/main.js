document.addEventListener("DOMContentLoaded", function(){
    const firstInput = document.querySelector('.styled-form input:not([type="hidden"]), .styled-form select, .styled-form textarea');
    const alerts = document.querySelectorAll('.alert');

    const openBtn = document.getElementById("open-modal-btn");
    const cancelBtn = document.getElementById("cancel-modal-btn");
    const modal = document.getElementById("estado-modal"); 
    const form = document.getElementById("form-estado");
    const mainForm = document.querySelector(".main-negocio");

    function actulizarPushLeft() {
        const modal1Abierto = document.getElementById("estado-modal").classList.contains("show");
        const modal2Abierto = document.getElementById("estado-modal-categoria").classList.contains("show");

        if (modal1Abierto || modal2Abierto) {
            mainForm.classList.add("push-left");
        } else {
            mainForm.classList.remove("push-left");
        }
    }

    openBtn.addEventListener("click", () => {
        const isOpen = !modal.classList.contains("show");

        modal.classList.toggle("show");
        modal.classList.remove("hidden");
        openBtn.classList.toggle('active');

        if (isOpen) {
            mainForm.classList.add("push-left");
        } else {
            actulizarPushLeft();
            form.reset();
        }
    });

    cancelBtn.addEventListener("click", () => {
        modal.classList.remove("show");
        modal.classList.remove("hidden");
        openBtn.classList.remove('active');
        actulizarPushLeft();
        form.reset();
    });

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const nombre = form.nombre.value;

        fetch("/negocios/crear_estado/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({ nombre })
        })
        .then(res => res.json())
        .then(data => {
            console.log("Respuesta del server: ", data);
            if (data.success){
                // Actualizar el select de Estado
                const selectEstado = document.querySelector("select[name=estado]");
                const option = document.createElement("option");
                option.value = data.id;
                option.text = data.nombre;
                option.selected = true;
                selectEstado.appendChild(option);
                mostrarMensaje("Nuevo estado creado satisfactoriamente!", "info");
                // Cierre del modal
                cancelBtn.click();
            } else if (data.duplicado) {
                const selectEstado = document.querySelector("select[name=estado]");
                const optionExistente = [...selectEstado.options].find(opt => opt.value == data.id);
                if (optionExistente) {
                    optionExistente.selected = true;
                } else {
                    const nueva = document.createElement("option");
                    nueva.value = data.id;
                    nueva.text = data.nombre;
                    nueva.selected = true;
                    selectEstado.appendChild(nueva);
                }
                mostrarMensaje("Este estado ya existe y fue seleccionado.", "info");
                cancelBtn.click()
            } else {
                if (data.errors && data.errors.nombre){
                    mostrarMensaje("Error: " + data.errors.nombre.join(", "));
                } else {
                    mostrarMensaje("Error al guardar el estado.");
                }
            }
        })
        .catch(error => {
            console.error("Error en la solicitud", error);
        });
    });


    // Modal de Categoria

    const openBtnCategoria = document.getElementById("open-modal-btn-categoria");
    const cancelBtnCategoria = document.getElementById("cancel-modal-btn-categoria");
    const modalCategoria = document.getElementById("estado-modal-categoria");
    const formCategoria = document.getElementById("form-categoria");

    openBtnCategoria.addEventListener("click", () => {
        const isOpening = !modalCategoria.classList.contains("show");

        modalCategoria.classList.toggle("show");
        modalCategoria.classList.remove("hidden");
        openBtnCategoria.classList.toggle('active');

        if (isOpening) {
            mainForm.classList.add("push-left");
        } else {
            actulizarPushLeft();
            formCategoria.reset();
        }
    });

    cancelBtnCategoria.addEventListener("click", () => {
        modalCategoria.classList.remove("show");
        modalCategoria.classList.remove("hidden");
        actulizarPushLeft();
        openBtnCategoria.classList.remove('active');
        formCategoria.reset();
    });

    formCategoria.addEventListener("submit", function (e) {
        e.preventDefault();
        const nombre = formCategoria.nombre.value;

        fetch("/negocios/crear_categoria/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({ nombre })
        })
        .then(res => res.json())
        .then(data => {
            console.log("Respuesta del servidor:", data);
            if (data.success){
                // Actualizar el select de Categoria
                const selectCategoria = document.querySelector("select[name=categoria]");
                const option = document.createElement("option");
                option.value = data.id;
                option.text = data.nombre;
                option.selected = true;
                selectCategoria.appendChild(option);
                mostrarMensaje("Categoria creada satisfactoriamente!", "info");
                // Cierre del modal
                cancelBtnCategoria.click(); 
            } else if (data.duplicado) {
                const selectCategoria = document.querySelector("select[name=categoria]");
                const optionExistente = [...selectCategoria.options].find(opt => opt.value == data.id);
                if (optionExistente){
                    optionExistente.selected = true;
                } else {
                    const nueva = document.createElement("option");
                    nueva.value = data.id;
                    nueva.text = data.nombre;
                    nueva.selected = true;
                    selectCategoria.appendChild(nueva);
                }
                mostrarMensaje("Esta categoria ya existe y fue seleccionada.", "info");
                cancelBtnCategoria.click();
            } else {
                if (data.errors && data.errors.nombre){
                    mostrarMensaje("Error: " + data.errors.nombre.join(", "));
                } else {
                    mostrarMensaje("Error al guardar la cateogoria.");
                }
            } 
        })
        .catch(error => {
            console.error("Error en la solicitud: ", error)
        });
    });


    if (firstInput){
        firstInput.focus();
    }


        function mostrarMensaje(texto, tipo="info"){
        let msg = document.createElement("div");

        msg.className = `alerta alerta-${tipo}`;
        msg.textContent = texto;
        document.body.appendChild(msg);

        setTimeout(() => {
            msg.classList.add("visible");
        }, 100);

        setTimeout(() => {
            msg.classList.remove("visible");
            setTimeout(() => msg.remove(), 500);
        }, 3000);
    }


    alerts.forEach(function (alert){
        setTimeout(function () {
            alert.style.transition = "opacity 0.6s ease";
            alert.style.opacity = "0";
            setTimeout(() =>  alert.remove(), 600); 
            }, 4000);
        });
 
    })

    function getCSRFToken(form) {
        return form.querySelector('[name=csrfmiddlewaretoken]').value;
    }


    document.addEventListener("submit", function (e) {
        if (e.target && e.target.id === "formEditarNegocio") {
            e.preventDefault();  // 🔒 Evita envío normal

            const form = e.target;
            const url = form.dataset.url;
            const formData = new FormData(form);

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(form),
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Actualizamos directamente la tabla sin recargar
                    const row = document.querySelector("#negocio-" + data.negocio.id);
                    row.querySelector('.negocio-nombre').textContent = data.negocio.nombre;
                    row.querySelector('.negocio-descripcion').textContent = data.negocio.descripcion;
                    row.querySelector('.negocio-telefono1').textContent = data.negocio.telefono1;
                    row.querySelector('.negocio-telefono2').textContent = data.negocio.telefono2;
                    row.querySelector('.negocio-email').textContent = data.negocio.email;
                    row.querySelector('.negocio-nit').textContent = data.negocio.nit;
                    row.querySelector('.negocio-estado').textContent = data.negocio.estado;
                    row.querySelector('.negocio-categoria').textContent = data.negocio.categoria;
                    row.querySelector('.negocio-usuario-nombre').textContent = data.negocio.usuario;  
                    // Cerrar el modal
                    document.getElementById("modal").classList.add("hidden");

                    mostrarMensaje("Negocio actualizado sin recargar", "info");

                } else if (data.html) {
                    mostrarMensaje("No se puedo actualizar el negocio", "info");
                    document.getElementById("modal-content").innerHTML = data.html;

                    const modalContent = document.getElementById("modal-content");
                    modalContent.classList.add("shake");

                    setTimeout(() => {
                        modalContent.classList.remove("shake");
                    }, 500);
                } else {
                    alert("Error inesperado en la respuesta.");
                }
            })
            .catch(error => {
                console.error("Error en la petición:", error);
                alert("Ocurrió un error al enviar el formulario. Por favor, intenta de nuevo.");
            });
        }
    });


    function openEditModal(id) {
        fetch(`/negocios/form_editar/${id}/`)
        .then(response => response.json())
        .then(data => {
            const modal = document.getElementById("modal");
            const modalContent = document.getElementById("modal-content");
            
            modalContent.innerHTML = data.html;
            modal.classList.remove("hidden");
        })
        .catch(error => {
            console.error("Error al cargar el modal: ", error)
        });
    }

   




