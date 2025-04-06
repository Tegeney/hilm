document.addEventListener('DOMContentLoaded', function() {
    // Task completion
    document.querySelectorAll('.complete-task').forEach(button => {
        button.addEventListener('click', async function() {
            const taskId = this.getAttribute('data-task-id');
            try {
                const response = await fetch(`/complete_task/${taskId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });
                const data = await response.json();
                
                if (data.error) {
                    alert(data.error);
                } else {
                    // Update balance display
                    document.querySelectorAll('.balance-display').forEach(el => {
                        el.textContent = `${data.balance.toFixed(2)} ETB`;
                    });
                    // Remove completed task
                    this.closest('.task-card').remove();
                    alert(data.message);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to complete task');
            }
        });
    });

    // Invest form
    const investForm = document.getElementById('invest-form');
    if (investForm) {
        investForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            try {
                const response = await fetch('/invest', {
                    method: 'POST',
                    body: formData,
                });
                const data = await response.json();
                
                if (data.error) {
                    alert(data.error);
                } else {
                    // Update balance display
                    document.querySelectorAll('.balance-display').forEach(el => {
                        el.textContent = `${data.balance.toFixed(2)} ETB`;
                    });
                    alert(data.message);
                    bootstrap.Modal.getInstance(document.getElementById('investModal')).hide();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Investment failed');
            }
        });
    }

    // Withdraw form
    const withdrawForm = document.getElementById('withdraw-form');
    if (withdrawForm) {
        withdrawForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            try {
                const response = await fetch('/withdraw', {
                    method: 'POST',
                    body: formData,
                });
                const data = await response.json();
                
                if (data.error) {
                    alert(data.error);
                } else {
                    // Update balance display
                    document.querySelectorAll('.balance-display').forEach(el => {
                        el.textContent = `${data.balance.toFixed(2)} ETB`;
                    });
                    alert(data.message);
                    bootstrap.Modal.getInstance(document.getElementById('withdrawModal')).hide();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Withdrawal failed');
            }
        });
    }

    // Toggle password visibility
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentNode.querySelector('input');
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('bi-eye', 'bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('bi-eye-slash', 'bi-eye');
            }
        });
    });

    // Refresh CAPTCHA
    const refreshCaptcha = document.getElementById('refresh-captcha');
    if (refreshCaptcha) {
        refreshCaptcha.addEventListener('click', function() {
            const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
            let captcha = '';
            for (let i = 0; i < 6; i++) {
                captcha += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            document.getElementById('captcha-text').textContent = captcha;
        });
    }

    // Password strength indicator
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const strength = calculatePasswordStrength(this.value);
            const progressBar = document.querySelector('.password-strength .progress-bar');
            progressBar.style.width = strength.percentage + '%';
            progressBar.className = 'progress-bar ' + strength.class;
        });
    }

    function calculatePasswordStrength(password) {
        let strength = 0;
        if (password.length > 7) strength += 1;
        if (password.match(/[a-z]/)) strength += 1;
        if (password.match(/[A-Z]/)) strength += 1;
        if (password.match(/[0-9]/)) strength += 1;
        if (password.match(/[^a-zA-Z0-9]/)) strength += 1;

        const classes = ['bg-danger', 'bg-warning', 'bg-info', 'bg-primary', 'bg-success'];
        const percentages = [20, 40, 60, 80, 100];
        
        return {
            class: classes[strength - 1] || 'bg-danger',
            percentage: percentages[strength - 1] || 0
        };
    }
});