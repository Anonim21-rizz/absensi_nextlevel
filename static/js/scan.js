document.addEventListener('DOMContentLoaded', function() {
    // Generate or get device UUID
    let deviceId = localStorage.getItem('device_uuid');
    if (!deviceId) {
        deviceId = crypto.randomUUID ? crypto.randomUUID() : 'id-' + Math.random().toString(36).substr(2, 16);
        localStorage.setItem('device_uuid', deviceId);
    }

    // --- Persistent Login Setup ---
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const userRole = localStorage.getItem('user_role');
    
    // UI Elements
    const studentNameInput = document.getElementById('student-name');
    const studentPasswordInput = document.getElementById('student-password');
    const credentialsFormGroup = document.getElementById('student-credentials-form-group');
    const profileBadge = document.getElementById('student-profile-badge');
    const profileName = document.getElementById('profile-student-name');
    const profileEmail = document.getElementById('profile-student-email');
    const scanDescription = document.getElementById('scan-description');
    
    const navStudentName = document.getElementById('logged-in-student-nav-name');
    const btnAdminLogin = document.getElementById('btn-admin-login');

    if (isLoggedIn && userRole === 'user') {
        const studentName = localStorage.getItem('student_name');
        const studentEmail = localStorage.getItem('student_email');
        const studentPassword = localStorage.getItem('student_password');

        // Populate elements if they exist
        if (studentNameInput) studentNameInput.value = studentName || '';
        if (studentPasswordInput) studentPasswordInput.value = studentPassword || '';
        
        // Hide standard inputs & show profile badge
        if (credentialsFormGroup) credentialsFormGroup.style.display = 'none';
        if (profileBadge) {
            profileBadge.style.display = 'flex';
            if (profileName) profileName.textContent = studentName || '';
            if (profileEmail) profileEmail.textContent = studentEmail || '';
        }
        
        // Update header description
        if (scanDescription) {
            scanDescription.textContent = 'Arahkan kamera ke QR Code untuk melakukan absensi.';
        }

        // Show student name in navbar, hide admin login
        if (navStudentName) {
            navStudentName.textContent = `Halo, ${studentName}`;
            navStudentName.style.display = 'inline';
        }
        if (btnAdminLogin) {
            btnAdminLogin.style.display = 'none';
        }
    } else {
        // Fallback or double check: if user role is admin or not logged in at all, redirect to login
        if (window.location.pathname.includes('/attendance/scan')) {
            window.location.href = '/login';
            return;
        }
    }

    // --- Scanner Setup & Logic ---
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
        
        let nameInput = '';
        let passwordInput = '';

        if (isLoggedIn && userRole === 'user') {
            nameInput = localStorage.getItem('student_name');
            passwordInput = localStorage.getItem('student_password');
        } else {
            nameInput = studentNameInput ? studentNameInput.value : '';
            passwordInput = studentPasswordInput ? studentPasswordInput.value : '';
        }
        
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
                
                // Clear password field if inputs are shown
                if (studentPasswordInput) {
                    studentPasswordInput.value = '';
                }
                
                setTimeout(() => {
                    // Refresh scanner state instead of full page reload to make it faster for the next student
                    window.location.reload();
                }, 2000);
            } else {
                resultDiv.className = 'alert mt-3 alert-danger';
                resultDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${data.message}`;
                isProcessing = false;
                document.getElementById('reader').style.opacity = '1';
                
                // If wrong password and inputs are shown, clear it
                if (data.message.includes('Password') && studentPasswordInput) {
                    studentPasswordInput.value = '';
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
