document.addEventListener('DOMContentLoaded', () => {

    // --- View Navigation ---
    const navLinks = document.querySelectorAll('.nav-links li');
    const views = document.querySelectorAll('.view-section');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navLinks.forEach(n => n.classList.remove('active'));
            link.classList.add('active');

            const viewId = link.getAttribute('data-view');
            views.forEach(v => {
                if (v.id === viewId) v.classList.add('active');
                else v.classList.remove('active');
            });
        });
    });

    // --- Sniffer Engine Controls ---
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');

    let pollingInterval = null;

    function updateSnifferStatusUI(isRunning) {
        if (isRunning) {
            statusDot.className = 'dot running';
            statusText.textContent = 'Running';
            if (!pollingInterval) pollingInterval = setInterval(fetchLiveTraffic, 2000);
        } else {
            statusDot.className = 'dot stopped';
            statusText.textContent = 'Stopped';
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        }
    }

    async function toggleSniffer(action) {
        try {
            const res = await fetch('/api/sniffer/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });
            const data = await res.json();
            if (data.status === 'running') updateSnifferStatusUI(true);
            else if (data.status === 'stopped') updateSnifferStatusUI(false);
        } catch (e) {
            console.error("Failed to toggle sniffer", e);
        }
    }

    btnStart.addEventListener('click', () => toggleSniffer('start'));
    btnStop.addEventListener('click', () => toggleSniffer('stop'));

    // Check initial status
    fetch('/api/sniffer/status')
        .then(r => r.json())
        .then(d => { updateSnifferStatusUI(d.is_sniffing); });

    // --- Live & Attacks Fetching ---
    async function fetchLiveTraffic() {
        try {
            const resLive = await fetch('/api/traffic/live');
            const flows = await resLive.json();
            renderLiveTable(flows);

            const resAttacks = await fetch('/api/traffic/attacks');
            const attacks = await resAttacks.json();
            renderAttacksTable(attacks);
        } catch(e) {
            console.error("Traffic fetch error", e);
        }
    }

    function renderLiveTable(flows) {
        const tbody = document.getElementById('live-table-body');
        tbody.innerHTML = '';
        flows.forEach(f => {
            const statusClass = f.is_anomaly ? 'status-badge danger' : 'status-badge normal';
            const statusText = f.is_anomaly ? 'ANOMALY' : 'NORMAL';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${f.src_ip}:${f.src_port}</td>
                <td>${f.dst_ip}:${f.dst_port}</td>
                <td>${f.protocol}</td>
                <td>${f.duration}</td>
                <td>${f.packets}</td>
                <td>${f.bytes}</td>
                <td>${f.packets_per_sec}</td>
                <td>${f.bytes_per_sec}</td>
                <td><span class="${statusClass}">${statusText}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    function renderAttacksTable(attacks) {
        const tbody = document.getElementById('attacks-table-body');
        const sidebarFeed = document.getElementById('sidebar-attacks-feed');
        
        tbody.innerHTML = '';
        sidebarFeed.innerHTML = '';

        if(attacks.length === 0) {
            sidebarFeed.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.8rem; text-align: center; padding: 1rem;">No recent attacks detected.</p>';
        }

        attacks.forEach(a => {
            const d = new Date(a.timestamp * 1000);
            const timeStr = d.toLocaleTimeString();

            // 1. Populate Main Table
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${a.src_ip}</td>
                <td>${a.dst_ip}</td>
                <td>${a.protocol}</td>
                <td>${a.packets_per_sec}</td>
                <td>${a.bytes_per_sec}</td>
                <td>${timeStr}</td>
                <td><strong>${a.reason}</strong></td>
            `;
            tbody.appendChild(tr);

            // 2. Populate Sidebar Feed
            const card = document.createElement('div');
            card.className = 'feed-card';
            card.innerHTML = `
                <div class="f-reason"><i class="fa-solid fa-triangle-exclamation"></i> ${a.reason}</div>
                <div class="f-ip">${a.src_ip} ➔ ${a.dst_ip}</div>
                <div style="font-size: 0.65rem; color: #64748b; margin-top: 4px;">${timeStr}</div>
            `;
            sidebarFeed.appendChild(card);
        });
    }

    // --- ML Model Evaluation ---
    const btnEval = document.getElementById('btn-eval');
    const modelSelect = document.getElementById('model-select');
    const evalLoading = document.getElementById('eval-loading');

    btnEval.addEventListener('click', async () => {
        const modelName = modelSelect.value;
        evalLoading.classList.remove('hidden');
        document.getElementById('metric-acc').textContent = '--';
        document.getElementById('metric-prec').textContent = '--';
        document.getElementById('metric-rec').textContent = '--';
        document.getElementById('metric-f1').textContent = '--';

        try {
            const res = await fetch('/api/models/eval', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_name: modelName })
            });
            const data = await res.json();
            if (data.error) {
                alert(data.error);
            } else {
                document.getElementById('metric-acc').textContent = (data.accuracy * 100).toFixed(1) + '%';
                document.getElementById('metric-prec').textContent = (data.precision * 100).toFixed(1) + '%';
                document.getElementById('metric-rec').textContent = (data.recall * 100).toFixed(1) + '%';
                document.getElementById('metric-f1').textContent = (data.f1_score * 100).toFixed(1) + '%';
            }
        } catch(e) {
            console.error("Evaluation error", e);
        } finally {
            evalLoading.classList.add('hidden');
        }
    });

    // --- CSV Uploading ---
    const fileInput = document.getElementById('csv-file');
    const fileNameDisplay = document.getElementById('file-name');
    const btnUpload = document.getElementById('btn-upload');
    const uploadResults = document.getElementById('upload-results');

    fileInput.addEventListener('change', () => {
        if(fileInput.files.length > 0) {
            fileNameDisplay.innerHTML = `<i class="fa-solid fa-file-csv"></i> ${fileInput.files[0].name}`;
            btnUpload.classList.remove('hidden');
        } else {
            fileNameDisplay.textContent = '';
            btnUpload.classList.add('hidden');
        }
    });

    btnUpload.addEventListener('click', async () => {
        if(fileInput.files.length === 0) return;
        
        btnUpload.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Processing...';
        btnUpload.disabled = true;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const res = await fetch('/api/csv/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if(data.error) {
                alert("Error: " + data.error);
            } else {
                document.getElementById('r-total').textContent = data.total_rows;
                document.getElementById('r-normal').textContent = data.normal;
                document.getElementById('r-anomalies').textContent = data.anomalies;
                uploadResults.classList.remove('hidden');
            }
        } catch(e) {
            console.error("Upload error", e);
        } finally {
            btnUpload.innerHTML = '<i class="fa-solid fa-server"></i> Process File';
            btnUpload.disabled = false;
        }
    });

});
