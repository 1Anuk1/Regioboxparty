// dashboard.js
document.addEventListener('DOMContentLoaded', () => {
    const paleta = {
        rojoOscuro: 'rgba(178,34,34,0.7)',
        contraste: 'rgba(122,132,80,0.7)', 
        rojo: 'rgba(187,53,53,0.7)',
        naranja: 'rgba(231,135,106,0.7)',
        dorado: 'rgba(201,162,39,0.7)',
        marron: 'rgba(158,87,58,0.7)',
        gris: '#3A3A40'
    };

    const borderPaleta = {
        rojoOscuro: 'rgba(178,34,34,1)',
        contraste: 'rgba(122,132,80,1)',
        rojo: 'rgba(187,53,53,1)',
        naranja: 'rgba(231,135,106,1)',
        dorado: 'rgba(201,162,39,1)',
        marron: 'rgba(158,87,58,1)'
    };

    // Función para obtener JSON de los scripts generados por json_script
    function getData(id) {
        return JSON.parse(document.getElementById(id).textContent);
    }

    // Función para crear gráficos de pastel
    function crearPieChart(canvasId, colores, borderColores, labels, values) {
        const canvas = document.getElementById(canvasId);
        new Chart(canvas.getContext('2d'), {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colores,
                    borderColor: borderColores,
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'right',
                        align: 'start',
                        labels: {
                            color: paleta.gris,
                            font: { size: 14 },
                            boxWidth: 20,
                            padding: 10
                        }
                    }
                }
            }
        });
    }

    // Función para crear gráficos de barras
    function crearBarChart(canvasId, colores, borderColores, labels, values, horizontal=false) {
        const canvas = document.getElementById(canvasId);
        new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Cantidad',
                    data: values,
                    backgroundColor: colores,
                    borderColor: borderColores,
                    borderWidth: 2,
                    borderRadius: 8,
                    hoverBackgroundColor: paleta.rojoOscuro,
                    hoverBorderColor: borderPaleta.rojoOscuro
                }]
            },
            options: {
                responsive: true,
                indexAxis: horizontal ? 'y' : 'x',
                scales: {
                    x: { grid: { display: false }, beginAtZero: true },
                    y: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // Obtener todos los datos desde los json_script
    const origenLabels = getData('origen-labels');
    const origenValues = getData('origen-values');

    const productosLabels = getData('productos-labels');
    const productosValues = getData('productos-values');

    const cotOrigenLabels = getData('cot-origen-labels');
    const cotOrigenValues = getData('cot-origen-values');

    const estadoLabels = getData('estado-labels');
    const estadoValues = getData('estado-values');

    // Inicializar todos los gráficos
    crearPieChart('origenChart', [paleta.rojo, paleta.naranja], [borderPaleta.rojo, borderPaleta.naranja], origenLabels, origenValues);

    crearBarChart('productosChart',
        [paleta.rojo, paleta.contraste, paleta.naranja, paleta.dorado, paleta.marron],
        [borderPaleta.rojo, borderPaleta.contraste, borderPaleta.naranja, borderPaleta.dorado, borderPaleta.marron],
        productosLabels, productosValues, true
    );

    crearPieChart('cotOrigenChart', [paleta.rojo, paleta.naranja], [borderPaleta.rojo, borderPaleta.naranja], cotOrigenLabels, cotOrigenValues);

    crearBarChart('estadoChart',
        [paleta.contraste, paleta.dorado, paleta.naranja, paleta.marron],
        [borderPaleta.contraste, borderPaleta.dorado, borderPaleta.naranja, borderPaleta.marron],
        estadoLabels, estadoValues, false
    );

});
