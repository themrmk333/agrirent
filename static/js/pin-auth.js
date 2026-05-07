// pin-auth.js
document.addEventListener('DOMContentLoaded', () => {
    const bookingForm = document.getElementById('bookingForm');
    const pinModal = document.getElementById('pinModal');
    const pinBoxes = document.querySelectorAll('.pin-box');
    const verifyPinBtn = document.getElementById('verifyPinBtn');
    const cancelPin = document.getElementById('cancelPin');
    const pinStatus = document.getElementById('pinStatus');
    const pinAmountText = document.getElementById('pinAmountText');

    if (!bookingForm || !pinModal) return;

    // Open Modal on Form Submit
    bookingForm.addEventListener('submit', (e) => {
        if (bookingForm.dataset.pinVerified === 'true') {
            return; // Allow form to submit
        }

        e.preventDefault();

        // Calculate Amount for Modal
        const startDate = new Date(document.getElementById('start_date').value);
        const endDate = new Date(document.getElementById('end_date').value);
        const price = parseFloat(document.getElementById('itemPrice').value);
        
        if (startDate && endDate && !isNaN(price)) {
            const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
            const total = days * price;
            pinAmountText.innerText = `₹ ${total}`;
        }

        pinModal.style.display = 'flex';
        pinBoxes[0].focus();
    });

    // PIN Box Input Logic
    pinBoxes.forEach((box, index) => {
        // Handle input
        box.addEventListener('input', (e) => {
            if (e.target.value.length === 1) {
                if (index < pinBoxes.length - 1) {
                    pinBoxes[index + 1].focus();
                }
            }
            updateVerifyButtonState();
        });

        // Handle Backspace
        box.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !e.target.value && index > 0) {
                pinBoxes[index - 1].focus();
            }
        });
    });

    function updateVerifyButtonState() {
        const pin = Array.from(pinBoxes).map(box => box.value).join('');
        verifyPinBtn.disabled = pin.length !== 6;
        if (pin.length === 6) {
            pinStatus.innerText = "TAP TO AUTHORIZE";
        } else {
            pinStatus.innerText = "ENTER 6-DIGIT PIN";
        }
    }

    // Verify PIN via AJAX
    verifyPinBtn.addEventListener('click', async () => {
        const pin = Array.from(pinBoxes).map(box => box.value).join('');
        
        verifyPinBtn.disabled = true;
        verifyPinBtn.innerText = "Verifying...";
        pinStatus.innerText = "AUTHENTICATING...";
        pinStatus.className = "pin-status";

        try {
            const response = await fetch('/api/verify-pin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin })
            });

            const data = await response.json();

            if (data.success) {
                pinStatus.innerText = "AUTHORIZED!";
                pinStatus.className = "pin-status success";
                
                setTimeout(() => {
                    bookingForm.dataset.pinVerified = 'true';
                    bookingForm.submit();
                }, 800);
            } else {
                throw new Error(data.error || "Incorrect PIN");
            }
        } catch (error) {
            pinStatus.innerText = error.message;
            pinStatus.className = "pin-status error";
            verifyPinBtn.disabled = false;
            verifyPinBtn.innerText = "Verify & Pay";
            
            // Clear PIN boxes on error
            pinBoxes.forEach(box => box.value = '');
            pinBoxes[0].focus();
        }
    });

    // Cancel PIN Modal
    cancelPin.addEventListener('click', () => {
        pinModal.style.display = 'none';
        pinBoxes.forEach(box => box.value = '');
        pinStatus.innerText = "READY";
        pinStatus.className = "pin-status";
    });
});
