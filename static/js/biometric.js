
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
