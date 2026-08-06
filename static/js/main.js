// Global JS — extended per phase as interactive features are added

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss Bootstrap alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
});