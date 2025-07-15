    const notificaciones = [
    "Nueva boleta recibida",
    "Boleta pendiente de revision",
    "Boleta aprobada exitosamente"
];

const notifDropdown = document.getElementById("notif-dropdown");
const notifCount = document.getElementById("notif-count");
const bellIcon = document.getElementById("notif-icon");

function toggleNotifications(){
    notifDropdown.classList.toggle("show")
}

function actualizarNotificaciones(){
    if (notificaciones.length > 0){
        notifCount.textContent = notificaciones.length;
        notifCount.style.display = "inline-block";
        bellIcon.style.filter = "invert(100%)";
        notifDropdown.innerHTML = notificaciones.map(n => `<div class="notif-item">${n}</div>`).join("");
    } else {
        notifCount.style.display = "none";
        bellIcon.style.filter = "grayscale(100%) opacity(0.4)";
        notifDropdown.innerHTML = `<div class="notif-item"> Sin notificaciones nuevas </div>`;
    }
}

actualizarNotificaciones()

// Ocultar dropdown si se hace clic afuera
document.addEventListener("click", function (e){
    const notifArea = document.querySelector(".notifications");
    if (!notifArea.contains(e.target)){
        notifDropdown.classList.remove("show");
    }
});


function toggleSubmenu(id){
    const allSubmenus = document.querySelectorAll('.submenu');
    const allButtons = document.querySelectorAll('.submenu-toggle');
    const selectedMenu = document.getElementById(id);
    const selectedBtn  = document.querySelector(`[onclick="toggleSubmenu('${id}')"]`);

    const isOpen = selectedMenu.classList.contains('open');

    // Cierra todos los submenus
    allSubmenus.forEach(menu => menu.classList.remove('open'));
    allButtons.forEach(btn => btn.classList.remove('open'));

    //Sino esta abierto, abrir el actual
    if (!isOpen){
        selectedMenu.classList.toggle('open');
        selectedBtn.classList.toggle('open');
    }
}


/* Mantener abierto el submenú que contiene el link activo */
document.addEventListener('DOMContentLoaded', () => {
    const locales = document.querySelectorAll('.local');

    // ---------------------- RESALTAR AL PASAR EL MOUSE ----------------------
    document.addEventListener('mouseover', function (event) {
        const negocioLink = event.target.closest('[data-negocio]');
        if (!negocioLink || (!negocioLink.classList.contains('business-name') && !negocioLink.closest('.business-name'))) {
            return;
        }

        const nombreNegocio = negocioLink.dataset.negocio?.trim();

        locales.forEach(local => {
            if (local.dataset.negocio?.trim() === nombreNegocio) {
                local.classList.add('resaltado');
            }
        });
    });

    document.addEventListener('mouseout', function () {
        locales.forEach(local => {
            local.classList.remove('resaltado');
        });
    });

    // ---------------------- ABRIR SUBMENÚ ACTIVO ----------------------
    const activeLink = document.querySelector('.sidebar a.active');
    if (activeLink) {
        const submenu = activeLink.closest('.submenu');
        if (submenu) {
            submenu.classList.add('open');
            submenu.previousElementSibling.classList.add('open');
        }
    }

    
});

