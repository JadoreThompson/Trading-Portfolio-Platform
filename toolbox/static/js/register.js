document.addEventListener('DOMContentLoaded', async function(){
    const registerErrorContainer = document.querySelector('.r-errors');
    const registerForm = document.getElementById('register-form');
    const registerCard = document.querySelector('.auth-card');

    const confirmErrorContainer = document.querySelector('.c-errors');
    const confirmEmailCard = document.querySelector('.confirm-email-card');
    const confirmForm = document.getElementById('confirm-form');

    registerForm.addEventListener('submit', async function(e){
        e.preventDefault();
        const formData = new FormData(this);

        fetch('/accounts/register', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data['error']);
                })
            }
            return response.json();
        })
        .then(data => {
            registerCard.style.display = 'none';
            confirmEmailCard.style.display = 'flex';
        })
        .catch(e => {
            let error = document.createElement('span');
            error.maxWidth = '100%';
            error.textContent = e.message;
            registerErrorContainer.appendChild(error);
        });
    });

    confirmForm.addEventListener('submit', function(e){
        e.preventDefault();
        const formData = new FormData(this);

        fetch('/accounts/confirm-email', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data['error']);
                })
            }
            return response.json();
        })
        .then(data => {
            window.location.href = '/dashboard';
        })
        .catch(e => {
            let error = document.createElement('span');
            error.maxWidth = '100%';
            error.textContent = e.message;
            confirmErrorContainer.appendChild(error);
        });
    });
});