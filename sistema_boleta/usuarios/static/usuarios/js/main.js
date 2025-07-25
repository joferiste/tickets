document.addEventListener("DOMContentLoaded", function(){
    const firstInput = document.querySelector('.styled-form input:not([type="hidden"]), .styled-form select, .styled-form textarea');
    const alerts = document.querySelectorAll('.alert');

    const openBtn = document.getElementById("open-modal-btn"); //
    const cancelBtn = document.getElementById("cancel-modal-btn");
    const modal = document.getElementById("estado-modal"); //
    const form = document.getElementById("estado-form");
    const mainForm = document.querySelector(".main-usuario");
    const rows = document.querySelectorAll(".tabla-usuarios tbody tr");

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                observer.unobserve(entry.target); // Solo una vez
            }
        });
    }, {
        threshold: 0.1
    });
 
    rows.forEach(row => {
        observer.observe(row);
    });

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
    

form.addEventListener("submit", function (e) {
        e.preventDefault();
        const nombre = form.nombre.value;

        fetch("/usuarios/crear_estado/", {
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
                mostrarMensaje("Nuevo estado creado satisfactoriomente.", "info");
                // Cierre del modal
                cancelBtn.click();
            } else if (data.duplicado) {
                const selectEstado = document.querySelector("select[name=estado]");
                const optionExistente = [...selectEstado.options].find(opt => opt.value == data.id);
                if (optionExistente){
                    optionExistente.selected = true;
                } else {
                    const nueva = document.createElement("option");
                    nueva.value = data.id;
                    nueva.text = data.nombre;
                    nueva.selected = true;
                    selectEstado.appendChild(nueva);
                }
                mostrarMensaje("Este estado ya existe y fue seleccionado.", "info");
                cancelBtn.click();
            } else {
                if (data.errors && data.errors.nombre){
                    mostrarMensaje("Error: " + data.errors.nombre.join(", "));
                } else {
                    mostrarMensaje("Error al guardar el estado.");
                }
            }
        })
        .catch(error => {
            console.error("Error en la solicitud: ", error);
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

});

function safeValue(value) {
    return value === null || value === 'None' || value === undefined ? '' : value;
}

function openEditModal(id, nombre, nit, direccionCompleta, email, telefono1, telefono2, estado_id){
    document.getElementById('edit_id').value = id;
    document.getElementById('edit_nombre').value = safeValue(nombre);
    document.getElementById('edit_nit').value = safeValue(nit);
    document.getElementById('edit_direccion').value = safeValue(direccionCompleta);
    document.getElementById('edit_email').value = safeValue(email);
    document.getElementById('edit_telefono1').value = safeValue(telefono1);
    document.getElementById('edit_telefono2').value = safeValue(telefono2);
    document.getElementById('edit_estado').value = estado_id;
    document.getElementById('editModal').classList.remove('hidden');
};


function openDeleteModal(id, nombre){
    document.getElementById('delete_id').value = id;
    document.getElementById('delete_text').textContent = `¿Estás seguro de querer eliminar al usuario: "${nombre}"?`;
    document.getElementById('deleteModal').classList.remove('hidden');
};

function closeModal(id){ 
    document.getElementById(id).classList.add('hidden');
};


document.addEventListener('DOMContentLoaded', function () {
    const editForm = document.querySelector('#editModal form');

    editForm.addEventListener('submit', function (event) {
        const nombre = document.getElementById('edit_nombre').value.trim();
        const telefono1 = document.getElementById('edit_telefono1').value.trim();
        const telefono2 = document.getElementById('edit_telefono2').value.trim();
        const nit = document.getElementById('edit_nit').value.trim();

        removeErrorMessages();
        let hasError = false;
        let firstErrorField = null;

        // Regex
        const nombreRegex = /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/;
        const telefonoRegex = /^\d{4}-?\d{4}$/;
        const NITRegex = /^[1-9]\d{6,10}$/;

        if (nit && !NITRegex.test(nit)) {
            showError('edit_nit', 'El NIT debe tener entre 7 y 10 digitos, sin guiones y no puede comenzar con 0');
            hasError = true;
            firstErrorField = firstErrorField || 'edit_nit';
        }


        if (!nombre) {
            showError('edit_nombre', 'El nombre es obligatorio');
            hasError = true;
            firstErrorField = firstErrorField || 'edit_nombre';
        } else if (!nombreRegex.test(nombre)) {
            showError('edit_nombre', 'El nombre no debe contener números ni caracteres especiales');
            hasError = true;
            firstErrorField = firstErrorField || 'edit_nombre';
        }

        if (!telefono1) {
            showError('edit_telefono1', 'El teléfono es obligatorio');
            hasError = true;
            firstErrorField = firstErrorField || 'edit_telefono1';
        } else if (!telefonoRegex.test(telefono1)) {
            showError('edit_telefono1', 'El teléfono debe tener 8 dígitos, con o sin guion');
            hasError = true;
            firstErrorField = firstErrorField || 'edit_telefono1';
        }

        if (telefono2 && !telefonoRegex.test(telefono2)){
            showError('edit_telefono2', 'El telefono secundario debe tener 8 digitos, con o sin guion');
            hasError = true;
            firstErrorField = firstErrorField || 'edit_telefono2';
        }

        if (hasError) {
            event.preventDefault();
            document.getElementById(firstErrorField).focus()

            const modal = document.querySelector('#editModal .modal-content');
            modal.classList.remove('modal-shake');
            void modal.offsetWidth;
            modal.classList.add('modal-shake');
        }
    });

    function showError(inputId, message) {
        const input = document.getElementById(inputId);

        // Crear el tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-error';
        tooltip.textContent = message;

        // Posicionarlo justo encima o al lado del input
        const rect = input.getBoundingClientRect();
        tooltip.style.top = `${rect.bottom + window.scrollY + 3}px`;
        tooltip.style.left = `${rect.left + window.scrollX + 60}px`;

        document.body.appendChild(tooltip);

        // Marcar visualmente el input
        input.classList.add('input-invalid');

        // Quitar el tooltip despues de 4 segundos
        setTimeout(() => {
            tooltip.classList.add('fade-out');
            setTimeout(() => tooltip.remove(), 500);  //Esperar el fade 
        }, 4000);
    }

    function removeErrorMessages() {
        document.querySelectorAll('.tooltip-error').forEach(el => el.remove());
        document.querySelectorAll('.input-invalid').forEach(el => el.classList.remove('input-invalid'));
    }
});
