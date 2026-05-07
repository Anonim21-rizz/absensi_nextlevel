document.addEventListener('DOMContentLoaded', function() {
    
    // QR Code Refresh Logic
    function refreshQR() {
        fetch('/admin/api/generate_qr')
            .then(response => response.json())
            .then(data => {
                const qrDisplay = document.getElementById('qr-display');
                qrDisplay.innerHTML = `<img src="${data.qr_image}" alt="QR Code Absensi">`;
                
                // Reset timer badge
                let seconds = 10;
                const badge = document.getElementById('timer-badge');
                
                if (window.qrCountdown) clearInterval(window.qrCountdown);
                
                badge.innerText = `Refresh: ${seconds}s`;
                window.qrCountdown = setInterval(() => {
                    seconds--;
                    badge.innerText = `Refresh: ${seconds}s`;
                    if (seconds <= 0) clearInterval(window.qrCountdown);
                }, 1000);
            })
            .catch(error => console.error('Error fetching QR:', error));
    }

    // Recent Scans Fetch Logic
    function fetchRecentScans() {
        fetch('/admin/api/recent_scans')
            .then(response => response.json())
            .then(data => {
                const tableBody = document.getElementById('recent-scans-table');
                
                if (data.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Belum ada absensi hari ini</td></tr>';
                    return;
                }
                
                tableBody.innerHTML = '';
                data.forEach(scan => {
                    const statusClass = scan.status === 'Hadir' ? 'text-green' : '';
                    tableBody.innerHTML += `
                        <tr>
                            <td><strong>${scan.name}</strong></td>
                            <td>${scan.tanggal} <br> <small class="text-muted">${scan.jam} WIB</small></td>
                            <td class="${statusClass}"><span class="badge" style="background:var(--success);color:white">${scan.status}</span></td>
                        </tr>
                    `;
                });
            })
            .catch(error => console.error('Error fetching recent scans:', error));
    }

    // Initial load
    refreshQR();
    fetchRecentScans();

    // Set intervals
    setInterval(refreshQR, 10000); // 10 seconds for QR
    setInterval(fetchRecentScans, 5000); // 5 seconds for recent scans
});
