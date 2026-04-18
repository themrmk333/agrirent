// static/js/script.js

document.addEventListener('DOMContentLoaded', () => {
    // Auto-hide flash messages
    const flashes = document.querySelectorAll('.flash');
    if (flashes.length > 0) {
        setTimeout(() => {
            flashes.forEach(flash => {
                flash.style.opacity = '0';
                flash.style.transition = 'opacity 0.5s ease';
                setTimeout(() => flash.remove(), 500);
            });
        }, 3000);
    }

    // Geolocation API for Location Feature
    const locationBtn = document.getElementById('findLocationBtn');
    const nearbyResults = document.getElementById('nearbyResults');
    
    if (locationBtn) {
        locationBtn.addEventListener('click', () => {
            if ("geolocation" in navigator) {
                locationBtn.innerHTML = "Locating... ⏳";
                locationBtn.disabled = true;
                
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        
                        // Fetch nearby equipment using simulated API
                        fetch(`/api/location_equipment?lat=${lat}&lng=${lng}`)
                            .then(response => response.json())
                            .then(data => {
                                locationBtn.innerHTML = "📍 Location Found";
                                displayNearby(data);
                            })
                            .catch(err => {
                                console.error(err);
                                locationBtn.innerHTML = "Try Again";
                                locationBtn.disabled = false;
                            });
                    },
                    (error) => {
                        console.error("Error getting location: ", error);
                        alert("Could not get your location. Please check browser permissions.");
                        locationBtn.innerHTML = "Find Nearby Equipment 📍";
                        locationBtn.disabled = false;
                    }
                );
            } else {
                alert("Geolocation is not supported by your browser");
            }
        });
    }
    
    function displayNearby(data) {
        if (!nearbyResults) return;
        
        nearbyResults.innerHTML = '';
        
        if (data.length === 0) {
            nearbyResults.innerHTML = '<p>No equipment found nearby.</p>';
            return;
        }
        
        const grid = document.createElement('div');
        grid.className = 'grid';
        grid.style.marginTop = '20px';
        
        data.forEach(item => {
            grid.innerHTML += `
                <div class="card glass-panel">
                    <img src="/static/images/${item.image}" alt="${item.name}" class="card-img" onerror="this.onerror=null;this.src='/static/images/default.jpg';">
                    <div class="card-body">
                        <span class="card-badge">📍 ~5 km away</span>
                        <h3 class="card-title">${item.name}</h3>
                        <p style="font-size: 0.9rem; margin-bottom: 8px; opacity: 0.8;">📍 ${item.location}</p>
                        <p class="card-price">₹ ${item.price} / day</p>
                        <div class="card-actions">
                            <a href="/booking/${item.id}" class="btn btn-block">Rent Now</a>
                        </div>
                    </div>
                </div>
            `;
        });
        
        nearbyResults.appendChild(grid);
    }

    // Initialize Payment UI Interaction
    const paymentForm = document.getElementById('paymentForm');
    if (paymentForm) {
        // Toggle payment type
        const methodSelect = document.getElementById('paymentMethod');
        const cardDetails = document.getElementById('cardDetails');
        const upiDetails = document.getElementById('upiDetails');

        if (methodSelect) {
            methodSelect.addEventListener('change', (e) => {
                if (e.target.value === 'card') {
                    cardDetails.style.display = 'block';
                    upiDetails.style.display = 'none';
                    // Set required state
                    document.getElementById('cardNumber').required = true;
                    document.getElementById('upiId').required = false;
                } else {
                    cardDetails.style.display = 'none';
                    upiDetails.style.display = 'block';
                    document.getElementById('cardNumber').required = false;
                    document.getElementById('upiId').required = true;
                }
            });
            // trigger change on load
            methodSelect.dispatchEvent(new Event('change'));
        }

        paymentForm.addEventListener('submit', (e) => {
            const btn = paymentForm.querySelector('button[type="submit"]');
            btn.innerHTML = 'Processing Payment... 🔄';
            btn.disabled = true;
            // Allow form to submit naturally
        });
    }

    // Booking page: Set min date to today
    const dateInput = document.getElementById('date');
    if (dateInput) {
        dateInput.min = new Date().toISOString().split("T")[0];
    }
});
