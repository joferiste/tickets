// ============== Esperar a que cargue el DOM ==============
document.addEventListener('DOMContentLoaded', function() {
    initNotifications();
    initSubmenuToggles();
    initFlashMessages();
});

// ============== Sistema de Notificaciones ==============
function initNotifications() {
    const notifBtn = document.querySelector('.notif-btn');
    const notifDropdown = document.querySelector('.notif-dropdown');
    
    if (!notifBtn || !notifDropdown) return;
    
    // Toggle notificaciones al hacer click en el botón
    notifBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        notifDropdown.classList.toggle('show');
    });
    
    // Cerrar al hacer click fuera
    document.addEventListener('click', function(e) {
        if (!notifDropdown.contains(e.target) && !notifBtn.contains(e.target)) {
            notifDropdown.classList.remove('show');
        }
    });
    
    // Prevenir que clicks dentro del dropdown lo cierren
    notifDropdown.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    // Manejar clicks en items de notificación
    const notifItems = document.querySelectorAll('.notif-item');
    notifItems.forEach(item => {
        item.addEventListener('click', function() {
            // Aquí puedes agregar lógica para marcar como leída
            this.style.opacity = '0.6';
            updateNotifCount();
        });
    });
}

// Actualizar contador de notificaciones
function updateNotifCount() {
    const notifCount = document.querySelector('.notif-count');
    const unreadItems = document.querySelectorAll('.notif-item:not([style*="opacity"])');
    const count = unreadItems.length;
    
    if (notifCount) {
        notifCount.textContent = count;
        if (count === 0) {
            notifCount.style.display = 'none';
        }
    }
}

// ============== Submenús del Sidebar ==============
function initSubmenuToggles() {
    const toggleButtons = document.querySelectorAll('.submenu-toggle');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const submenuId = this.getAttribute('data-submenu');
            const submenu = document.querySelector(`[data-submenu-id="${submenuId}"]`);
            
            if (!submenu) return;
            
            // Toggle estado
            const isOpen = submenu.classList.contains('open');
            
            // Cerrar todos los otros submenús (opcional - comentar para permitir múltiples abiertos)
            // closeAllSubmenus();
            
            if (isOpen) {
                closeSubmenu(this, submenu);
            } else {
                openSubmenu(this, submenu);
            }
        });
    });
    
    // Abrir submenú si contiene un link activo
    const activeLinks = document.querySelectorAll('.submenu-link.active');
    activeLinks.forEach(link => {
        const submenu = link.closest('.submenu');
        if (submenu) {
            const submenuId = submenu.getAttribute('data-submenu-id');
            const toggle = document.querySelector(`[data-submenu="${submenuId}"]`);
            if (toggle) {
                openSubmenu(toggle, submenu);
            }
        }
    });
}

function openSubmenu(button, submenu) {
    button.classList.add('open');
    submenu.classList.add('open');
}

function closeSubmenu(button, submenu) {
    button.classList.remove('open');
    submenu.classList.remove('open');
}

function closeAllSubmenus() {
    document.querySelectorAll('.submenu').forEach(submenu => {
        submenu.classList.remove('open');
    });
    document.querySelectorAll('.submenu-toggle').forEach(button => {
        button.classList.remove('open');
    });
}

// ============== Mensajes Flash ==============
function initFlashMessages() {
    const closeButtons = document.querySelectorAll('.alert-close');
    
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.closest('.alert');
            if (alert) {
                alert.style.animation = 'slideOut 0.4s ease';
                setTimeout(() => {
                    alert.remove();
                    // Si no quedan más alertas, remover el contenedor
                    const flashContainer = document.querySelector('.flash-container');
                    if (flashContainer && flashContainer.children.length === 0) {
                        flashContainer.remove();
                    }
                }, 400);
            }
        });
    });
    
    // Auto-cerrar después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.alert-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });
}

// Animación de salida para las alertas
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ============== Funciones de Utilidad ==============

// Función para manejar responsive (móvil)
function initMobileMenu() {
    const menuToggle = document.createElement('button');
    menuToggle.className = 'mobile-menu-toggle';
    menuToggle.innerHTML = '☰';
    menuToggle.style.cssText = `
        display: none;
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 1001;
        background: var(--primary-bg);
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 8px;
        font-size: 20px;
        cursor: pointer;
    `;
    
    if (window.innerWidth <= 768) {
        menuToggle.style.display = 'block';
        document.body.appendChild(menuToggle);
        
        menuToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.toggle('open');
            }
        });
    }
}

// Inicializar menú móvil
initMobileMenu();

// Reinicializar en resize
window.addEventListener('resize', function() {
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    if (window.innerWidth <= 768) {
        if (!menuToggle) {
            initMobileMenu();
        }
    } else {
        if (menuToggle) {
            menuToggle.remove();
        }
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.remove('open');
        }
    }
});

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

});

