document.addEventListener('DOMContentLoaded', function() {
    
    // Animación de entrada para las cards
    const cards = document.querySelectorAll('.info-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Animación para los movimientos
    const movimientos = document.querySelectorAll('.movimiento-item');
    movimientos.forEach((movimiento, index) => {
        movimiento.style.opacity = '0';
        movimiento.style.transform = 'translateX(-20px)';
        
        setTimeout(() => {
            movimiento.style.transition = 'all 0.4s ease';
            movimiento.style.opacity = '1';
            movimiento.style.transform = 'translateX(0)';
        }, 500 + (index * 80));
    });
    
    // Confirmar antes de desasignar local (si implementas esta función)
    const btnDesasignar = document.querySelector('[data-action="desasignar"]');
    if (btnDesasignar) {
        btnDesasignar.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro de desasignar este local? Esta acción finalizará la ocupación actual.')) {
                e.preventDefault();
            }
        });
    }
    
    // Highlight de la fila de tabla al hacer hover
    const filasTabla = document.querySelectorAll('.tabla-ocupaciones tbody tr');
    filasTabla.forEach(fila => {
        fila.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.01)';
            this.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
        });
        
        fila.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = 'none';
        });
    });
    
    // Copiar información al portapapeles
    const btnCopiarInfo = document.querySelector('[data-action="copiar-info"]');
    if (btnCopiarInfo) {
        btnCopiarInfo.addEventListener('click', function() {
            const localNombre = document.querySelector('.local-info h1').textContent;
            const localEstado = document.querySelector('.badge-estado').textContent;
            const localCosto = document.querySelector('.card-value').textContent;
            
            let infoTexto = `Local: ${localNombre}\nEstado: ${localEstado}\nCosto: ${localCosto}`;
            
            const ocupacionNegocio = document.querySelector('.negocio-principal h3');
            if (ocupacionNegocio) {
                infoTexto += `\nOcupado por: ${ocupacionNegocio.textContent}`;
            }
            
            navigator.clipboard.writeText(infoTexto).then(() => {
                // Mostrar mensaje de éxito
                const mensaje = document.createElement('div');
                mensaje.textContent = '✓ Información copiada';
                mensaje.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #28a745;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                    z-index: 1000;
                    animation: slideIn 0.3s ease;
                `;
                
                document.body.appendChild(mensaje);
                
                setTimeout(() => {
                    mensaje.style.animation = 'slideOut 0.3s ease';
                    setTimeout(() => mensaje.remove(), 300);
                }, 2000);
            });
        });
    }
    
    // Tooltip mejorado para badges
    const badges = document.querySelectorAll('.badge-estado, .badge-categoria');
    badges.forEach(badge => {
        badge.style.cursor = 'help';
        badge.title = `Estado actual: ${badge.textContent}`;
    });
    
    // Contador animado para valores numéricos grandes
    function animarContador(elemento, valorFinal) {
        const duracion = 2500;
        const pasos = 80;
        const incremento = valorFinal / pasos;
        let valorActual = 0;
        
        const intervalo = setInterval(() => {
            valorActual += incremento;
            if (valorActual >= valorFinal) {
                // Formatear con Q y dos decimales
                elemento.textContent = 'Q. ' + valorFinal.toLocaleString('es-GT', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
                clearInterval(intervalo);
            } else {
                elemento.textContent = 'Q. ' + valorActual.toLocaleString('es-GT', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }, duracion / pasos);
    }
    
    // Animar el valor de COSTO del local
    const valorCosto = document.querySelector('.info-card.primary .card-value');
    if (valorCosto) {
        const numeroValor = parseFloat(valorCosto.dataset.valor);
         // Eliminar todo excepto dígitos y punto decimal
        
        console.log('Costo - Valor desde data-attribute:', numeroValor);
        
        if (!isNaN(numeroValor) && numeroValor > 0) {
            valorCosto.textContent = 'Q. 0.00';
            setTimeout(() => {
                animarContador(valorCosto, numeroValor);
            }, 400);
        }
    }
    
    // Animar el valor de INGRESOS si existe
    const valorIngresos = document.querySelector('.info-card.success .card-value');
    if (valorIngresos) {
        const numeroValor = parseFloat(valorIngresos.dataset.valor);
        
        console.log('Ingresos - desde data-attribute:', numeroValor);

        if (!isNaN(numeroValor) && numeroValor > 0) {
            valorIngresos.textContent = 'Q. 0.00';
            setTimeout(() => {
                animarContador(valorIngresos, numeroValor);
            }, 700);
        }
    }
    
    // Scroll suave a secciones
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Lazy loading para imágenes (si agregas imágenes después)
    const imagenes = document.querySelectorAll('img[data-src]');
    const observador = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observador.unobserve(img);
            }
        });
    });
    
    imagenes.forEach(img => observador.observe(img));
    
    // Actualizar "tiempo atrás" cada minuto
    function actualizarTiempos() {
        const elementosTiempo = document.querySelectorAll('[data-timestamp]');
        elementosTiempo.forEach(elemento => {
            const timestamp = parseInt(elemento.dataset.timestamp);
            const ahora = Date.now();
            const diferencia = ahora - timestamp;
            
            // Calcular tiempo transcurrido
            const minutos = Math.floor(diferencia / 60000);
            const horas = Math.floor(minutos / 60);
            const dias = Math.floor(horas / 24);
            
            let textoTiempo;
            if (dias > 0) {
                textoTiempo = `hace ${dias} día${dias > 1 ? 's' : ''}`;
            } else if (horas > 0) {
                textoTiempo = `hace ${horas} hora${horas > 1 ? 's' : ''}`;
            } else if (minutos > 0) {
                textoTiempo = `hace ${minutos} minuto${minutos > 1 ? 's' : ''}`;
            } else {
                textoTiempo = 'hace un momento';
            }
            
            elemento.textContent = textoTiempo;
        });
    }
    
    // Actualizar cada minuto
    setInterval(actualizarTiempos, 60000);
    
    // Efecto de pulso en badges importantes
    const badgesImportantes = document.querySelectorAll('.badge-actual, .badge-activo');
    badgesImportantes.forEach(badge => {
        setInterval(() => {
            badge.style.animation = 'pulse 1.5s ease-in-out';
            setTimeout(() => {
                badge.style.animation = '';
            }, 1500);
        }, 5000);
    });
    
    console.log('✓ Perfil del local cargado correctamente');
});

// Al final de detalle_local.js
// Animaciones CSS adicionales
if (!document.getElementById('detalle-local-styles')) {
    const style = document.createElement('style');
    style.id = 'detalle-local-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        @keyframes pulse {
            0%, 100% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.05);
            }
        }
    `;
    document.head.appendChild(style);
}