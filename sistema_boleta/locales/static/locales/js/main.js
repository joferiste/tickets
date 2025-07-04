document.addEventListener("DOMContentLoaded", function(){
    const firstInput = document.querySelector('.styled-form input:not([type="hidden"]), .styled-form select, .styled-form textarea');
    const alerts = document.querySelectorAll('.alert');

    const openBtn = document.getElementById("open-modal-btn");
    const cancelBtn = document.getElementById("cancel-modal-btn");
    const modal = document.getElementById("estado-modal");
    const form = document.getElementById("form-estado");
    const mainForm = document.querySelector(".main-local");

    function actulizarPushLeft() {
        const modal1Abierto = document.getElementById("estado-modal").classList.contains("show");
        const modal2Abierto = document.getElementById("modal-nivel").classList.contains("show");

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

        fetch("/locales/crear_estado/", {
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
                mostrarMensaje("Nuevo estado creado satisfactoriamente", "info");
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


    // Modal de ubicacion

    const openBtnUbicacion = document.getElementById("open-modal-btn-ubicacion");
    const cancelBtnUbicacion = document.getElementById("cancel-modal-btn-ubicacion");
    const modalUbicacion = document.getElementById("modal-ubicacion");
    const formUbicacion = document.getElementById("form-ubicacion");

    openBtnUbicacion.addEventListener("click", () => {
        const isOpening = !modalUbicacion.classList.contains("show");

        modalUbicacion.classList.toggle("show");
        modalUbicacion.classList.remove("hidden");
        openBtnUbicacion.classList.toggle('active');

     
    });

    cancelBtnUbicacion.addEventListener("click", () => {
        modalUbicacion.classList.remove("show");
        modalUbicacion.classList.remove("hidden");
        openBtnUbicacion.classList.remove('active');
        formUbicacion.reset();
    });

    formUbicacion.addEventListener("submit", function (e) {
        e.preventDefault();
        const nombre = formUbicacion.nombre.value;

        fetch("/locales/crear_ubicacion/", {
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
                // Actualizar el select de Ubicacion
                const selectUbicacion = document.querySelector("select[name=ubicacion]");
                const option = document.createElement("option");
                option.value = data.id;
                option.text = data.nombre;
                option.selected = true;
                selectUbicacion.appendChild(option);
                mostrarMensaje("Ubicación creada satisfactoriamente!", "info");
                // Cierre del modal
                cancelBtnUbicacion.click(); 
            } else if (data.duplicado) {
                const selectUbicacion = document.querySelector("select[name=ubicacion]");
                const optionExistente = [...selectUbicacion.options].find(opt => opt.value == data.id);
                if (optionExistente){
                    optionExistente.selected = true;
                } else {
                    const nueva = document.createElement("option");
                    nueva.value = data.id;
                    nueva.text = data.nombre;
                    nueva.selected = true;
                    selectUbicacion.appendChild(nueva);
                }
                mostrarMensaje("Esta ubicación ya existe y fue seleccionada.", "info");
                cancelBtnUbicacion.click();
            } else {
                if (data.errors && data.errors.nombre){
                    mostrarMensaje("Error: " + data.errors.nombre.join(", "));
                } else {
                    mostrarMensaje("Error al guardar la ubicación.");
                }
            } 
        })
        .catch(error => {
            console.error("Error en la solicitud: ", error)
        });
    });



    // Modal de Nivel

    const openBtnNivel = document.getElementById("open-modal-btn-nivel");
    const cancelBtnNivel = document.getElementById("cancel-modal-btn-nivel");
    const modalNivel = document.getElementById("modal-nivel");
    const formNivel = document.getElementById("form-nivel");

    openBtnNivel.addEventListener("click", () => {
        const istOpening = !modalNivel.classList.contains("show");

        modalNivel.classList.toggle("show");
        modalNivel.classList.remove("hidden");
        openBtnNivel.classList.toggle('active');

        if (istOpening) {
            mainForm.classList.add("push-left");
        } else {
            actulizarPushLeft();
            formNivel.reset();
        }
    });

    cancelBtnNivel.addEventListener("click", () => {
        modalNivel.classList.remove("show");
        modalNivel.classList.remove("hidden");
        actulizarPushLeft();
        openBtnNivel.classList.remove('active');
        formNivel.reset();
    });

    formNivel.addEventListener("submit", function (e) {
        e.preventDefault();
        const nombre = formNivel.nombre.value;
        const costo = formNivel.costo.value;
        const ubicacion = formNivel.ubicacion.value;

        fetch("/locales/crear_nivel/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({ nombre, costo, ubicacion })
        })
        .then(res => res.json())
        .then(data => {
            console.log("Respuesta del servidor:", data);
            if (data.success){
                // Actualizar el select de nivel
                const selectNivel = document.querySelector("select[name=nivel]");
                const option = document.createElement("option");
                option.value = data.id;
                option.text = data.nombre;
                option.selected = true;
                selectNivel.appendChild(option);
                mostrarMensaje("Nivel creado satisfactoriamente", "info");
                // Cierre del modal
                cancelBtnNivel.click(); 
            } else if (data.duplicado) {
                const selectNivel = document.querySelector("select[name=nivel]");
                const optionExistente = [...selectNivel.options].find(opt => opt.value == data.id);
                if (optionExistente){
                    optionExistente.selected = true;
                } else {
                    const nueva = document.createElement("option");
                    nueva.value = data.id;
                    nueva.text = data.nombre;
                    nueva.selected = true;
                    selectNivel.appendChild(nueva);
                }
                mostrarMensaje("Este nivel ya existe y fue seleccionado", "info");
                cancelBtnNivel.click();
            } else {
                if (data.errors && data.errors.nombre){
                    mostrarMensaje("Error: " + data.errors.nombre.join(", "));
                } else {
                    mostrarMensaje("Error al guardar el nivel");
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

