document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        var flashMessages = document.querySelectorAll('.flash-messages .alert');
        flashMessages.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Initialize Tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Copy to clipboard functionality
    const copyBtns = document.querySelectorAll('.copy-btn');
    copyBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-clipboard-target');
            const targetEl = document.querySelector(targetId);
            
            if(targetEl) {
                targetEl.select();
                targetEl.setSelectionRange(0, 99999); /* For mobile devices */
                navigator.clipboard.writeText(targetEl.value).then(() => {
                    const originalIcon = this.innerHTML;
                    this.innerHTML = '<i class="bi bi-check2"></i> Copied!';
                    this.classList.replace('btn-outline-secondary', 'btn-success');
                    
                    setTimeout(() => {
                        this.innerHTML = originalIcon;
                        this.classList.replace('btn-success', 'btn-outline-secondary');
                    }, 2000);
                });
            }
        });
    });

    // Client-side filtering for Audit Logs
    const logSearchInput = document.getElementById('logSearch');
    if (logSearchInput) {
        logSearchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('#auditLogTable tbody tr');
            
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if(text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});
