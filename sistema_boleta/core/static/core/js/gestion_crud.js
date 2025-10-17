document.addEventListener('DOMContentLoaded', function() {
    
    // Verificar que estamos en la página correcta
    const crudContainer = document.querySelector('.crud-container');
    if (!crudContainer) return; // Salir si no estamos en la página CRUD
    
    // Sistema de Tabs
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabButtons.length === 0) return; // Salir si no hay tabs
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const targetTab = this.dataset.tab;
            
            // Remover active de todos los botones y contenidos
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Activar el botón clickeado y su contenido
            this.classList.add('active');
            const targetContent = document.querySelector(`[data-content="${targetTab}"]`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
            
            // Guardar en sessionStorage (en lugar de localStorage)
            sessionStorage.setItem('crud_active_tab', targetTab);
        });
    });
    
    // Restaurar tab activa desde sessionStorage
    const savedTab = sessionStorage.getItem('crud_active_tab');
    if (savedTab) {
        const savedButton = document.querySelector(`[data-tab="${savedTab}"]`);
        if (savedButton) {
            // Simular click sin evento
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            savedButton.classList.add('active');
            const targetContent = document.querySelector(`[data-content="${savedTab}"]`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        }
    }
    
    // Animación de entrada para las cards
    const cards = document.querySelectorAll('.crud-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Efecto de ripple en las cards
    cards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Solo crear ripple si no es un link (para evitar conflictos)
            if (this.tagName.toLowerCase() === 'a') return;
            
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                top: ${y}px;
                left: ${x}px;
                background: rgba(102, 126, 234, 0.3);
                border-radius: 50%;
                pointer-events: none;
                animation: ripple 0.4s ease-out;
                z-index: 5;
            `;
            
            this.style.position = 'relative';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 400);
        });
    });
    
    // Contador animado para stats
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(stat => {
        const finalValue = parseInt(stat.textContent);
        if (!isNaN(finalValue) && finalValue > 0) {
            animateCounter(stat, finalValue);
        }
    });
    
    function animateCounter(element, finalValue) {
        const duration = 1500;
        const steps = 60;
        const increment = finalValue / steps;
        let currentValue = 0;
        
        const interval = setInterval(() => {
            currentValue += increment;
            if (currentValue >= finalValue) {
                element.textContent = finalValue;
                clearInterval(interval);
            } else {
                element.textContent = Math.floor(currentValue);
            }
        }, duration / steps);
    }
    
    console.log('✓ Sistema CRUD cargado correctamente');
});

// Agregar estilos de animación SOLO si no existen
if (!document.getElementById('crud-ripple-styles')) {
    const style = document.createElement('style');
    style.id = 'crud-ripple-styles';
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}