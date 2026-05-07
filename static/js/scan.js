document.addEventListener('DOMContentLoaded', function() {
    // Generate or get device UUID
    let deviceId = localStorage.getItem('device_uuid');
    if (!deviceId) {
        deviceId = crypto.randomUUID ? crypto.randomUUID() : 'id-' + Math.random().toString(36).substr(2, 16);
        localStorage.setItem('device_uuid', deviceId);
    }

    const html5QrcodeScanner = new Html5QrcodeScanner(
        "reader", 
        { 
            fps: 10, 
            qrbox: {width: 250, height: 250},
            supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA]
        },
        /* verbose= */ false
    );

    let isProcessing = false;

    function onScanSuccess(decodedText, decodedResult) {
        if (isProcessing) return;
        
        const nameInput = document.getElementById('student-name').value;
        const passwordInput = document.getElementById('student-password').value;
        const resultDiv = document.getElementById('scan-result');

        if (!nameInput || !passwordInput) {
            resultDiv.className = 'alert mt-3 alert-warning';
            resultDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Silakan isi Nama dan Password terlebih dahulu.';
            resultDiv.classList.remove('hidden');
            return;
        }
        
        isProcessing = true;
        // Stop scanner visually
        document.getElementById('reader').style.opacity = '0.5';
        
        resultDiv.className = 'alert mt-3 alert-info';
        resultDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses absensi...';
        resultDiv.classList.remove('hidden');

        // Send to backend
        fetch('/attendance/api/submit_scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: decodedText,
                device_id: deviceId,
                name: nameInput,
                password: passwordInput
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                html5QrcodeScanner.clear();
                resultDiv.className = 'alert mt-3 alert-success';
                resultDiv.innerHTML = `<i class="fas fa-check-circle"></i> ${data.message}`;
                
                // Clear password field for security
                document.getElementById('student-password').value = '';
                
                setTimeout(() => {
                    // Refresh scanner state instead of full page reload to make it faster for the next student
                    window.location.reload();
                }, 2000);
            } else {
                resultDiv.className = 'alert mt-3 alert-danger';
                resultDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${data.message}`;
                isProcessing = false;
                document.getElementById('reader').style.opacity = '1';
                
                // If wrong password, clear it
                if (data.message.includes('Password')) {
                    document.getElementById('student-password').value = '';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultDiv.className = 'alert mt-3 alert-danger';
            resultDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> Terjadi kesalahan koneksi.';
            isProcessing = false;
            document.getElementById('reader').style.opacity = '1';
        });
    }

    function onScanFailure(error) {
        // handle scan failure, usually better to ignore and keep scanning
    }

    html5QrcodeScanner.render(onScanSuccess, onScanFailure);
});
