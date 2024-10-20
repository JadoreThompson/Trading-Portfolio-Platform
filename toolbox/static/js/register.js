document.addEventListener('DOMContentLoaded', async function(){
    const registerErrorContainer = document.querySelector('.r-errors');
    const registerForm = document.getElementById('register-form');
    const registerCard = document.querySelector('.auth-card');

    const confirmErrorContainer = document.querySelector('.c-errors');
    const confirmEmailCard = document.querySelector('.confirm-email-card');
    const confirmForm = document.getElementById('confirm-form');

    let email;

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
            console.log(this.email);
            console.log(formData);
            console.log(formData.email);
            email = formData.get('email');
            registerCard.style.display = 'none';
            confirmEmailCard.style.display = 'flex';
        })
        .catch(e => {
            let error = document.createElement('span');
            error.maxWidth = '100%';
            error.textContent = e.message;
            registerErrorContainer.appendChild(error);
        });

        this.reset();
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

        this.reset();
    });

    document.getElementById('resend-email').addEventListener('click', function(e){
        e.preventDefault();
        fetch(this.getAttribute('href'), {
            method: 'POST',
            body: JSON.stringify({email: email})
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
            const span = document.createElement('span');
            span.textContent = data['message'];
            this.nextSibling = span;
        })
        .catch(e => {
            const error = document.createElement('span');
            error.textContent = e.message;
            confirmErrorContainer.appendChild(error);
        });
    });

});