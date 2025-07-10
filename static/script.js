const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

// Event listeners for switching between sign-up and sign-in
signUpButton.addEventListener('click', () => {
    container.classList.add('right-panel-active');
});

signInButton.addEventListener('click', () => {
    container.classList.remove('right-panel-active');
});

// Function to auto-hide flash messages after 5 seconds
document.addEventListener("DOMContentLoaded", function () {
    const flashMessages = document.querySelectorAll(".flash-message");
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = "0";
            setTimeout(() => message.remove(), 500); // Remove from DOM after fade-out
        }, 5000);
    });
});
