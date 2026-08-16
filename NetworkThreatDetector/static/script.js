let lastPacketId = -1;
let lastAlertId = -1;

// Initialize Chart.js
const ctx = document.getElementById('protocolChart').getContext('2d');
const protocolChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['TCP', 'UDP', 'OTHER'],
        datasets: [{
            data: [0, 0, 0],
            backgroundColor: [
                '#38bdf8', // accent-blue
                '#f59e0b', // accent-yellow
                '#94a3b8'  // text-muted
            ],
            borderWidth: 0,
            hoverOffset: 4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: { color: '#f8fafc' }
            }
        },
        cutout: '70%'
    }
});

// Update UI
async function updateDashboard() {
    try {
        const res = await fetch('/api/data');
        const data = await res.json();

        // 1. Update Global Stats
        document.getElementById('total-packets').textContent = data.stats.total_packets;
        
        let alertCount = data.alerts.filter(a => a.level === 'danger' || a.level === 'warning').length;
        document.getElementById('total-alerts').textContent = alertCount;

        // 2. Update Chart
        protocolChart.data.datasets[0].data = [
            data.stats.protocols.TCP,
            data.stats.protocols.UDP,
            data.stats.protocols.OTHER
        ];
        protocolChart.update();

        // 3. Update Top IPs
        const topIpsList = document.getElementById('top-ips-list');
        topIpsList.innerHTML = '';
        data.stats.top_ips.forEach(([ip, count]) => {
            const li = document.createElement('li');
            li.innerHTML = `<span class="ip-addr">${ip}</span> <span class="count">${count} pkts</span>`;
            topIpsList.appendChild(li);
        });

        // 4. Update Packets Table (ID-based prepend)
        const tbody = document.getElementById('packet-table-body');
        let newPackets = [];
        
        if (lastPacketId === -1) {
            newPackets = data.packets;
        } else {
            newPackets = data.packets.filter(p => p.id > lastPacketId);
        }
        
        if (newPackets.length > 0) {
            lastPacketId = Math.max(...data.packets.map(p => p.id));
            
            // data.packets is newest-first. Reverse to prepend in correct order (oldest of the new ones first)
            for (let i = newPackets.length - 1; i >= 0; i--) {
                const p = newPackets[i];
                let badgeClass = p.protocol.toLowerCase();
                if(!['tcp', 'udp'].includes(badgeClass)) badgeClass = 'other';
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${p.time}</td>
                    <td class="ip-addr">${p.src}</td>
                    <td class="ip-addr">${p.dst}</td>
                    <td><span class="badge ${badgeClass}">${p.protocol}</span></td>
                    <td>${p.info}</td>
                    <td><span class="payload-preview">${p.payload}</span></td>
                `;
                tbody.prepend(tr);
            }
            
            // Remove extra rows if any (keep up to 100)
            while (tbody.children.length > 100) {
                tbody.removeChild(tbody.lastChild);
            }
        }

        // 5. Update Alerts (ID-based prepend)
        const alertsFeed = document.getElementById('alerts-feed');
        let newAlerts = [];
        
        if (lastAlertId === -1) {
            newAlerts = data.alerts;
            alertsFeed.innerHTML = ''; // clear initial msg
        } else {
            newAlerts = data.alerts.filter(a => a.id > lastAlertId);
        }
        
        if (newAlerts.length > 0) {
            lastAlertId = Math.max(...data.alerts.map(a => a.id));
            
            for (let i = newAlerts.length - 1; i >= 0; i--) {
                const a = newAlerts[i];
                const div = document.createElement('div');
                div.className = `alert ${a.level}`;
                div.innerHTML = `
                    <span class="time">${a.time}</span>
                    <span class="msg">${a.message}</span>
                `;
                alertsFeed.prepend(div);
            }
            
            // Remove extra alerts
            while (alertsFeed.children.length > 50) {
                alertsFeed.removeChild(alertsFeed.lastChild);
            }
        }

        // 6. Update Button State
        const btn = document.getElementById('toggle-sniff-btn');
        if (data.is_sniffing) {
            btn.textContent = 'Stop Sniffing';
            btn.className = 'btn btn-danger';
        } else {
            btn.textContent = 'Start Sniffing';
            btn.className = 'btn btn-success';
        }

    } catch (err) {
        console.error('Error fetching data:', err);
    }
}

// Toggle Sniffing
document.getElementById('toggle-sniff-btn').addEventListener('click', async () => {
    try {
        await fetch('/api/toggle', { method: 'POST' });
        updateDashboard(); // refresh immediately
    } catch (err) {
        console.error('Error toggling sniffing:', err);
    }
});

// Tab Navigation Logic
const navBtns = document.querySelectorAll('.nav-btn');
const views = document.querySelectorAll('.view-section');

navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all buttons and views
        navBtns.forEach(b => b.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));

        // Add active class to clicked button and corresponding view
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-target');
        document.getElementById(targetId).classList.add('active');
    });
});

// Poll every 1 second
setInterval(updateDashboard, 1000);
updateDashboard(); // initial call
