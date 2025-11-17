document.addEventListener("DOMContentLoaded", function() {
    const openBtn = document.getElementById("open-modal-btn");
    const cancelBtn = document.getElementById("cancel-modal-btn");
    const modal = document.getElementById("banco-modal");
    const form = document.getElementById("form-banco");
    const mainForm = document.querySelector(".config-container");

    const alerts = document.querySelectorAll('.alert');


     openBtn.addEventListener("click", () => {
        const isOpen = !modal.classList.contains("show");

        modal.classList.toggle("show");
        modal.classList.remove("hidden");
        openBtn.classList.toggle('active');

        if (isOpen) {
            mainForm.classList.add("push-left");
        } else {
            mainForm.classList.remove("push-left");
            form.reset(); 
        }
    }); 

    cancelBtn.addEventListener("click", () => {
        modal.classList.remove("show");
        modal.classList.remove("hidden");
        mainForm.classList.remove("push-left");
        openBtn.classList.remove('active');
        form.reset();
    });
    
    form.addEventListener("submit", function(e) {
        e.preventDefault();
        const nombre = form.nombre.value;
        const numero_cuenta = form.numero_cuenta.value;

        fetch("/configuracion/crear_banco/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({ nombre, numero_cuenta })
        })
        .then(res => res.json())
        .then(data => {
            console.log("Respuesta del server: ", data);
            const selectBanco = document.querySelector("select[name=banco_principal]");
            if (data.success || data.duplicado) {
                const optionExistente = [...selectBanco.options].find(opt => opt.value == data.id);
                if (optionExistente) {
                    optionExistente.selected = true;
                } else {
                    const option = document.createElement("option");
                    option.value = data.id;
                    option.text = data.nombre;
                    option.selected = true;
                    selectBanco.appendChild(option);
                }
                mostrarMensaje(data.success ? "Nuevo Banco creado satisfactoriamente" : "Este banco ya existe y fue seleccionado","info");
                cancelBtn.click(); // cerrar modal

                // Limpiar el formulario del modal
                document.querySelector("input[name=nombre]").value = "";
                document.querySelector("input[name=numero_cuenta]").value = "";

            } else {
                if (data.errors) {
                    let mensajes = [];

                    Object.entries(data.errors).forEach(([campo, errores]) => {
                        const campoFormateado = campo.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase());
                        errores.forEach(error => {
                            // Solo se muestran los errores que existen (como ya ocurre)
                            mensajes.push(`${campoFormateado}: ${error}`);
                        });
                    });
                    mostrarMensaje(mensajes.join("<br>"), "error");

                } else {
                    mostrarMensaje("Error al guardar el banco.");
                }
            }
        })
        .catch(error => {
            console.error("Error en la solicitud", error);
        });
    }); // ← Cierre del addEventListener

    function mostrarMensaje(texto, tipo = "info") {
        let msg = document.createElement("div");

        msg.className = `alerta alerta-${tipo}`;
        msg.innerHTML = texto;
        document.body.appendChild(msg);

        setTimeout(() => {
            msg.classList.add("visible");
        }, 100);

        setTimeout(() => {
            msg.classList.remove("visible");
            setTimeout(() => msg.remove(), 800);
        }, 4000);
    }

    alerts.forEach(function (alert){
         setTimeout(function () {
        alert.classList.add("hide");
        setTimeout(() => alert.style.display = "none", 600); 
        }, 4000);
    });
});
