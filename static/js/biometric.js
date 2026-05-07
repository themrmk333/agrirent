console.log("BIO SCRIPT LOADED - V2.0 Production Ready");

async function generateRegistrationOptions(username) {
    const response = await fetch('/api/bio/register-options', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
    });
    return await response.json();
}

async function verifyRegistration(credential) {
    const response = await fetch('/api/bio/verify-registration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credential)
    });
    return await response.json();
}

async function generateAuthenticationOptions(username) {
    const response = await fetch('/api/bio/authenticate-options', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
    });
    return await response.json();
}

async function verifyAuthentication(credential, username) {
    const response = await fetch('/api/bio/verify-authentication', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...credential, username })
    });
    return await response.json();
}

// Helpers to convert between base64url and Uint8Array
function bufferToBase64url(buffer) {
    const bytes = new Uint8Array(buffer);
    let str = "";
    for (const charCode of bytes) {
        str += String.fromCharCode(charCode);
    }
    return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
}

function base64urlToBuffer(baseurl64) {
    const padding = "==".slice(0, (4 - (baseurl64.length % 4)) % 4);
    const base64 = baseurl64.replace(/-/g, "+").replace(/_/g, "/") + padding;
    const str = atob(base64);
    const buffer = new Uint8Array(str.length);
    for (let i = 0; i < str.length; i++) {
        buffer[i] = str.charCodeAt(i);
    }
    return buffer.buffer;
}

const BioAuth = {
    async register(username) {
        console.log("BIO STARTED for registration: " + username);
        try {
            const options = await generateRegistrationOptions(username);
            if (options.error) throw new Error(options.error);

            options.challenge = base64urlToBuffer(options.challenge);
            options.user.id = base64urlToBuffer(options.user.id);
            if (options.excludeCredentials) {
                options.excludeCredentials.forEach(c => c.id = base64urlToBuffer(c.id));
            }
            
            const credential = await navigator.credentials.create({ publicKey: options });
            if (!credential) throw new Error("No credential returned from browser");

            const credentialJSON = {
                id: credential.id,
                rawId: bufferToBase64url(credential.rawId),
                type: credential.type,
                response: {
                    attestationObject: bufferToBase64url(credential.response.attestationObject),
                    clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
                },
            };
            
            console.log("BIO VERIFIED locally, sending to server...");
            const verification = await verifyRegistration(credentialJSON);
            return verification;
        } catch (err) {
            console.error("Biometric Registration Error:", err);
            throw err;
        }
    },
    async enroll(username) {
        try {
            const options = await generateRegistrationOptions(username);
            options.challenge = base64urlToBuffer(options.challenge);
            options.user.id = base64urlToBuffer(options.user.id);
            if (options.excludeCredentials) {
                options.excludeCredentials.forEach(c => c.id = base64urlToBuffer(c.id));
            }
            const credential = await navigator.credentials.create({ publicKey: options });
            const credentialJSON = {
                id: credential.id,
                rawId: bufferToBase64url(credential.rawId),
                type: credential.type,
                response: {
                    attestationObject: bufferToBase64url(credential.response.attestationObject),
                    clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
                },
            };
            const response = await fetch('/api/bio/enroll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentialJSON)
            });
            return await response.json();
        } catch (err) {
            console.error("Biometric Enrollment Error:", err);
            throw err;
        }
    },
    async authenticate(username) {
        console.log("BIO STARTED for authentication: " + (username || "session user"));
        try {
            const options = await generateAuthenticationOptions(username);
            if (options.error) throw new Error(options.error);

            options.challenge = base64urlToBuffer(options.challenge);
            if (options.allowCredentials) {
                options.allowCredentials.forEach(c => c.id = base64urlToBuffer(c.id));
            }
            
            const assertion = await navigator.credentials.get({ publicKey: options });
            if (!assertion) throw new Error("No assertion returned from browser");

            const assertionJSON = {
                id: assertion.id,
                rawId: bufferToBase64url(assertion.rawId),
                type: assertion.type,
                response: {
                    authenticatorData: bufferToBase64url(assertion.response.authenticatorData),
                    clientDataJSON: bufferToBase64url(assertion.response.clientDataJSON),
                    signature: bufferToBase64url(assertion.response.signature),
                    userHandle: assertion.response.userHandle ? bufferToBase64url(assertion.response.userHandle) : null,
                },
            };
            
            console.log("BIO VERIFIED locally, sending to server...");
            const verification = await verifyAuthentication(assertionJSON, username);
            return verification;
        } catch (err) {
            console.error("Biometric Authentication Error:", err);
            throw err;
        }
    }
};

// Main entry point
document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM CONTENT LOADED - Initializing Biometric Listeners");

    // Helper to hide modal
    const hideBioModal = () => {
        const bioModal = document.getElementById('bioModal');
        if (bioModal) bioModal.style.display = 'none';
    };

    // 1. Handle Registration Form
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        console.log("Register form detected");
        
        registerForm.addEventListener("submit", async function(event) {
            // Check if already verified to allow the final submission
            if (document.getElementById('credential_id').value && document.getElementById('public_key').value) {
                console.log("FORM SUBMITTED with biometric data");
                return;
            }

            event.preventDefault(); // PREVENT submission to do biometric first
            
            // Validate basic form fields first
            if (!registerForm.checkValidity()) {
                registerForm.reportValidity();
                return;
            }

            console.log("BIO STARTED for Registration flow");

            if (!window.PublicKeyCredential) {
                console.error("REGISTRATION FAILED: Secure context/WebAuthn missing");
                alert("Biometric authentication not supported on this device/browser. Please ensure you are using HTTPS.");
                return;
            }

            const registerBtn = document.getElementById('registerBtn');
            if (registerBtn) {
                registerBtn.disabled = true;
                registerBtn.innerHTML = "Processing Biometric... 🔒";
            }

            try {
                const usernameInput = document.getElementById('username');
                const username = usernameInput && usernameInput.value ? usernameInput.value : "user_" + Date.now();
                
                const bioModal = document.getElementById('bioModal');
                if (bioModal) bioModal.style.display = 'flex';
                
                const bioStatus = document.getElementById('bioStatus');
                if (bioStatus) bioStatus.innerText = "WAITING FOR SCAN...";

                const result = await BioAuth.register(username);

                if (result && result.success) {
                    console.log("BIO VERIFIED successfully on server");
                    document.getElementById('credential_id').value = result.credential_id;
                    document.getElementById('public_key').value = result.public_key;
                    
                    if (bioStatus) bioStatus.innerText = "VERIFIED! SUBMITTING...";
                    console.log("REGISTRATION SUCCESS - Biometric Step");
                    
                    // Small delay for UI feedback
                    setTimeout(() => {
                        hideBioModal();
                        console.log("Final form submission...");
                        registerForm.submit();
                    }, 500);
                } else {
                    throw new Error(result ? result.error : "Verification failed");
                }
            } catch (error) {
                console.error("REGISTRATION FAILED:", error);
                alert("Fingerprint registration failed: " + error.message);
                hideBioModal();
                if (registerBtn) {
                    registerBtn.disabled = false;
                    registerBtn.innerHTML = "Complete Registration";
                }
            }
        });
    }

    // 2. Handle Payment Authentication
    const bookingForm = document.getElementById("bookingForm");
    if (bookingForm) {
        console.log("Booking form detected");
        bookingForm.addEventListener("submit", async function(event) {
            if (bookingForm.dataset.bioVerified === "true") {
                console.log("FORM SUBMITTED - Payment already verified");
                return;
            }

            event.preventDefault();
            
            const bioModal = document.getElementById('bioModal');
            if (bioModal) bioModal.style.display = 'flex';

            const bioStatus = document.getElementById('bioStatus');
            if (bioStatus) bioStatus.innerText = "AUTHENTICATING...";

            try {
                const result = await BioAuth.authenticate(); 
                if (result && result.success) {
                    console.log("BIO VERIFIED - Payment authorized");
                    if (bioStatus) bioStatus.innerText = "AUTHORIZED! PROCEEDING...";
                    
                    bookingForm.dataset.bioVerified = "true";
                    setTimeout(() => {
                        hideBioModal();
                        bookingForm.submit();
                    }, 500);
                } else {
                    throw new Error(result ? result.error : "Authentication failed");
                }
            } catch (error) {
                console.error("PAYMENT BIO FAILED:", error);
                alert("Fingerprint authentication failed. Payment cannot proceed.");
                hideBioModal();
            }
        });
    }

    // 3. Handle Global Cancel Button
    const cancelBio = document.getElementById('cancelBio');
    if (cancelBio) {
        cancelBio.addEventListener('click', () => {
            console.log("BIO CANCELLED by user");
            hideBioModal();
            // Re-enable registration button if present
            const registerBtn = document.getElementById('registerBtn');
            if (registerBtn) {
                registerBtn.disabled = false;
                registerBtn.innerHTML = "Complete Registration";
            }
        });
    }
});
