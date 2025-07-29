const API_BASE = '/api/v1';

async function loadHealth() {
  const res = await fetch('/health');
  const data = await res.json();
  document.getElementById('health').textContent = `API status: ${data.status}`;
}

async function loadDevices() {
  const res = await fetch(`${API_BASE}/devices/`);
  const data = await res.json();
  const tbody = document.querySelector('#devicesTable tbody');
  tbody.innerHTML = '';
  (data.devices || []).forEach(d => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${d.id}</td><td>${d.name}</td><td>${d.type}</td><td>${d.status}</td>`;
    tbody.appendChild(tr);
  });
}

document.getElementById('loadDevices').addEventListener('click', loadDevices);

loadHealth();