const API = "/stats";

async function update() {

    const response = await fetch(API);

    const data = await response.json();

    document.getElementById("cpu").innerText =
        `${data.cpu}% | ${data.cpu_temp}°C`;

    const gpu = data.gpu || {};

    document.getElementById("gpu").textContent =
        `${gpu.usage ?? "-"}% | ${gpu.temp ?? "-"}°C | VRAM ${(gpu.vram_used ?? 0).toFixed(1)}/${(gpu.vram_total ?? 0).toFixed(1)} GB`;

    document.getElementById("ram").innerText =
        `${data.ram.used}/${data.ram.total} GB`;

    document.getElementById("network").innerText =
        `↓ ${data.network.download} Mbps | ↑ ${data.network.upload} Mbps | ${data.network.ping} ms`;
}

update();

setInterval(update, 1000);