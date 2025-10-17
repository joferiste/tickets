// ==================== GRÁFICO DE LÍNEA ====================
document.addEventListener("DOMContentLoaded", function() {
    const ctxLinea = document.getElementById("chartLinea").getContext("2d");

    
    new Chart(ctxLinea, {
        type: 'line',
        data: {
            labels: estadisticas.meses_labels,
            datasets: [{
                label: 'Monto Pagado (Q.)',
                data: estadisticas.meses_montos,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // ==================== GRÁFICO DE PASTEL ====================
    const ctxPie = document.getElementById('chartPie').getContext('2d');

    new Chart(ctxPie, {
        type: 'doughnut',
        data: {
            labels: ['Efectivo', 'No Efectivo'],
            datasets: [{
                data: [
                    estadisticas.metodos.efectivo,
                    estadisticas.metodos.no_efectivo
                ],
                backgroundColor: ['#48bb78', '#667eea']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

})