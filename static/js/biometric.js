
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
            
            // Convert options from JSON (base64url) to Uint8Array
            options.challenge = base64urlToBuffer(options.challenge);
            options.user.id = base64urlToBuffer(options.user.id);
            if (options.excludeCredentials) {
                options.excludeCredentials.forEach(c => c.id = base64urlToBuffer(c.id));
            }

            const credential = await navigator.credentials.create({ publicKey: options });
            
            // Convert credential to JSON-friendly format
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
            
            // Convert options
            options.challenge = base64urlToBuffer(options.challenge);
            if (options.allowCredentials) {
                options.allowCredentials.forEach(c => c.id = base64urlToBuffer(c.id));
            }

            const assertion = await navigator.credentials.get({ publicKey: options });
            
            // Convert assertion to JSON
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
// Handle Registration Form Submission
document.addEventListener("DOMContentLoaded", () => {
    const regForm = document.getElementById("registerForm");
    if (regForm) {
        regForm.addEventListener("submit", async function(event) {
            const credentialIdInput = document.getElementById('credential_id');
            const publicKeyInput = document.getElementById('public_key');

            // If we already have the biometric data, let the form submit normally
            if (credentialIdInput.value && publicKeyInput.value) {
                console.log("Biometric success - Submitting form");
                return;
            }

            // Prevent default form submission
            event.preventDefault();
            console.log("Form blocked");

            // Check for WebAuthn support
            if (!window.PublicKeyCredential) {
                alert("Your browser does not support biometric authentication. Please use a modern browser on a secure (HTTPS) connection.");
                return;
            }

            const username = document.getElementById('username').value;
            if (!username) {
                alert("Please enter a username first.");
                return;
            }

            const bioModal = document.getElementById('bioModal');
            const bioStatus = document.getElementById('bioStatus');
            
            if (bioModal) bioModal.style.display = 'flex';
            if (bioStatus) {
                bioStatus.textContent = 'Touch fingerprint sensor to complete registration';
                bioStatus.className = 'bio-status';
            }

            console.log("Starting biometric");

            try {
                const result = await BioAuth.register(username);
                
                if (result && result.success) {
                    console.log("Biometric success");
                    if (bioStatus) {
                        bioStatus.textContent = 'Verification successful';
                        bioStatus.className = 'bio-status bio-success-text';
                    }
                    
                    // Save the biometric credentials
                    credentialIdInput.value = result.credential_id;
                    publicKeyInput.value = result.public_key;
                    
                    // Finalize registration
                    setTimeout(() => {
                        if (bioModal) bioModal.style.display = 'none';
                        regForm.submit(); // This submits the form without triggering this event again
                    }, 1000);
                } else {
                    throw new Error(result ? result.error : 'Verification failed');
                }
            } catch (err) {
                console.error("Registration Biometric Error:", err);
                if (bioStatus) {
                    bioStatus.textContent = 'Fingerprint Verification Failed';
                    bioStatus.className = 'bio-status bio-error-text';
                }
                
                // Keep registration blocked
                setTimeout(() => {
                    if (bioModal) bioModal.style.display = 'none';
                }, 2500);
            }
        });

        const cancelBio = document.getElementById('cancelBio');
        if (cancelBio) {
            cancelBio.addEventListener('click', () => {
                const bioModal = document.getElementById('bioModal');
                if (bioModal) bioModal.style.display = 'none';
            });
        }
    }
});
