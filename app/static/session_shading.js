let session_shading_enabled = document.getElementById('toggle-session-shading')?.checked ?? true;

document.addEventListener('DOMContentLoaded', () => {
    const checkbox = document.getElementById('toggle-session-shading');
    if (checkbox) {
        checkbox.addEventListener('change', () => {
            session_shading_enabled = checkbox.checked;
            shadeSession(); // trigger redraw on toggle
        });
    }
});

let previousSession = "";

function shadeSession() {
    if (!session_shading_enabled) return;

    const canvas = document.getElementById('sessionCanvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear previous

    fetch('/current_session')
        .then(response => response.json())
        .then(data => {
            const sessionText = data.session;

            if (sessionText !== previousSession && previousSession !== "") {
                showAlert(`Session Shift Detected: ${sessionText}`, "info");
                console.log("Alert Triggered:", sessionText);
            }
            previousSession = sessionText;

            let color = "#555";

            if (sessionText === "Premarket") {
                color = "#FFD700";
            } else if (sessionText === "Regular") {
                color = "#32CD32";
            } else if (sessionText === "AfterHours") {
                color = "#1E90FF";
            } else {
                color = "#FF4C4C";
            }

            ctx.fillStyle = color;
            ctx.globalAlpha = 0.15;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.globalAlpha = 1.0;
        })
        .catch(error => {
            console.error('Session shading failed:', error);
        });
}

setInterval(shadeSession, 30000); // Refresh shading every 30 seconds
shadeSession(); // Initial shading on page load