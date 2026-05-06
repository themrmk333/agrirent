console.log("BIO SCRIPT LOADED");
console.log(window.PublicKeyCredential);
console.log(location.origin);

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
        try {
            const options = await generateAuthenticationOptions(username);
            options.challenge = base64urlToBuffer(options.challenge);
            if (options.allowCredentials) {
                options.allowCredentials.forEach(c => c.id = base64urlToBuffer(c.id));
            }
            const assertion = await navigator.credentials.get({ publicKey: options });
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
            const verification = await verifyAuthentication(assertionJSON, username);
            return verification;
        } catch (err) {
            console.error("Biometric Authentication Error:", err);
            throw err;
        }
    }
};

document.addEventListener("DOMContentLoaded", () => {
    // 1. Handle Registration Form
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        console.log("Register form detected");
        
        registerForm.addEventListener("submit", async function(event) {
            // 1. Check form validity first
            if (!registerForm.checkValidity()) {
                registerForm.reportValidity();
                return;
            }

            // If we already have the biometric data, let the form submit normally
            if (document.getElementById('credential_id').value && document.getElementById('public_key').value) {
                return;
            }

            event.preventDefault(); // STRICTLY PREVENT NORMAL FORM SUBMISSION
            console.log("Biometric Started for Registration");

            if (!window.PublicKeyCredential) {
                alert("Biometric authentication not supported on this device/browser. Use HTTPS.");
                return;
            }

            try {
                const usernameInput = document.getElementById('username');
                const username = usernameInput ? usernameInput.value : "user_" + Date.now();
                
                const bioModal = document.getElementById('bioModal');
                if (bioModal) bioModal.style.display = 'flex';

                const result = await BioAuth.register(username);

                if (result && result.success) {
                    console.log("Biometric Success");
                    document.getElementById('credential_id').value = result.credential_id;
                    document.getElementById('public_key').value = result.public_key;
                    alert("Fingerprint verification successful");
                    registerForm.submit();
                } else {
                    throw new Error(result ? result.error : "Verification failed");
                }
            } catch (error) {
                console.error(error);
                alert("Fingerprint verification failed: " + error.message);
                const bioModal = document.getElementById('bioModal');
                if (bioModal) bioModal.style.display = 'none';
            }
        });
    }

    // 2. Handle Payment Authentication (triggered in booking.html)
    const bookingForm = document.getElementById("bookingForm");
    if (bookingForm) {
        bookingForm.addEventListener("submit", async function(event) {
            if (bookingForm.dataset.bioVerified === "true") {
                return;
            }

            event.preventDefault();
            alert("Fingerprint verification required for payment");

            const bioModal = document.getElementById('bioModal');
            if (bioModal) bioModal.style.display = 'flex';

            try {
                const result = await BioAuth.authenticate(); // Uses session username
                if (result && result.success) {
                    alert("Fingerprint verified! Proceeding to payment...");
                    bookingForm.dataset.bioVerified = "true";
                    bookingForm.submit();
                } else {
                    throw new Error(result ? result.error : "Authentication failed");
                }
            } catch (error) {
                console.error(error);
                alert("Fingerprint authentication failed. Payment blocked.");
                if (bioModal) bioModal.style.display = 'none';
            }
        });
    // 3. Handle Cancel Button
    const cancelBio = document.getElementById('cancelBio');
    if (cancelBio) {
        cancelBio.addEventListener('click', () => {
            const bioModal = document.getElementById('bioModal');
            if (bioModal) bioModal.style.display = 'none';
        });
    }
});
