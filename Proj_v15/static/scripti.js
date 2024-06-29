function showHome() {
    hideLoginForm();
    document.getElementById("home").style.display = "block";
    document.getElementById("team").style.display = "none";
    document.getElementById("field").style.display = "none";
    
}

function showTeam() {
    hideLoginForm();
    document.getElementById("home").style.display = "none";
    document.getElementById("team").style.display = "block";
    document.getElementById("field").style.display = "none";
    
}

function showField()
{
    hideLoginForm();
    document.getElementById("home").style.display = "none";
    document.getElementById("team").style.display = "none";
    document.getElementById("field").style.display = "block";
    

}

function togglePasswordVisibility(element) {
    const passwordField = document.getElementById("password");
    const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
    passwordField.setAttribute("type", type);
    element.querySelector("i").classList.toggle("fa-eye");
    element.querySelector("i").classList.toggle("fa-eye-slash");

    setTimeout(() => {
        passwordField.setAttribute("type", "password");
        element.querySelector("i").classList.toggle("fa-eye");
        element.querySelector("i").classList.toggle("fa-eye-slash");
    }, 2000);
}

function toggleLoginForm() {
    var h1Element = document.querySelector("h1");
    var loginFormBox = document.getElementById("loginFormBox");

    document.getElementById("home").style.display = "none";
    document.getElementById("team").style.display = "none";
    document.getElementById("field").style.display = "none";

    if (loginFormBox.style.display === "none") {
        loginFormBox.style.display = "block";
        h1Element.style.left = Math.max(window.innerWidth / 4, 0) + "px";
        loginFormBox.style.right = "0";
    } 
    else {
        loginFormBox.style.display = "none";
        h1Element.style.left = "50%";
        loginFormBox.style.right = "-50%";
    }
}

function hideLoginForm() {
    var loginFormBox = document.getElementById("loginFormBox");
    loginFormBox.style.display = "none";
}

function validateEmail() {
    var emailInput = document.getElementById("email");
    var emailError = document.getElementById("emailError");
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (emailInput.value.trim() === '') {
        emailError.textContent = 'Email address is required';
        return false;
    }   else if (!emailRegex.test(emailInput.value)) {
        emailError.textContent = 'Invalid email address';
        return false;
    }   else {
        emailError.textContent = '';
        return true;
    }
}

function handleLogin() {
    if (validateEmail()) {
        document.getElementById('signal').value = 'login';
        document.getElementById('loginForm').submit();
        window.location.href = '/page';
    }
}
document.addEventListener("DOMContentLoaded", function() {
    // Smooth scrolling for menu links
    document.querySelectorAll('nav a').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            window.scrollTo({
                top: targetElement.offsetTop - document.querySelector('nav').offsetHeight,
                behavior: 'smooth'
            });
        });
    });
});