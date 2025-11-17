function updateClock() {
    const now = new Date();
    const h = now.getHours().toString().padStart(2,'0');
    const m = now.getMinutes().toString().padStart(2,'0');
    const s = now.getSeconds().toString().padStart(2,'0');
    const clockDiv = document.getElementById('clock');
    if(clockDiv) {
        clockDiv.textContent = `${h}:${m}:${s}`;
    }
}
setInterval(updateClock, 1000);
updateClock();
