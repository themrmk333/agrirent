document.addEventListener('DOMContentLoaded', () => {

    // Check Chart.js loaded or not
    if (typeof Chart === 'undefined') {
        console.error("Chart.js not loaded!");
        return;
    }

    // Default Dark Theme
    Chart.defaults.color = '#e0e0e0';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.1)';

    console.log("mrLabels:", mrLabels);
    console.log("mrData:", mrData);
    console.log("mLabels:", mLabels);
    console.log("mData:", mData);

    // =========================
    // MOST RENTED CHART (BAR)
    // =========================
    const mostRentedCtx = document.getElementById('mostRentedChart');

    if (mostRentedCtx && mrLabels && mrData && mrLabels.length > 0) {
        new Chart(mostRentedCtx, {
            type: 'bar',
            data: {
                labels: mrLabels,
                datasets: [{
                    label: 'Number of Bookings',
                    data: mrData,
                    backgroundColor: 'rgba(76, 175, 80, 0.7)',
                    borderColor: '#4caf50',
                    borderWidth: 1,
                    borderRadius: 5
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
    } else {
        console.warn("Most rented chart data missing");
    }

    // =========================
    // MONTHLY CHART (LINE)
    // =========================
    const monthlyCtx = document.getElementById('monthlyChart');

    if (monthlyCtx && mLabels && mData && mLabels.length > 0) {
        new Chart(monthlyCtx, {
            type: 'line',
            data: {
                labels: mLabels,
                datasets: [{
                    label: 'Bookings per Month',
                    data: mData,
                    backgroundColor: 'rgba(251, 192, 45, 0.2)',
                    borderColor: '#fbc02d',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#fbc02d'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } else {
        console.warn("Monthly chart data missing");
    }

});