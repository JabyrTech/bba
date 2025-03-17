document.addEventListener("DOMContentLoaded", function() {
    // Simulate login error
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", function(event) {
            event.preventDefault();
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

            if (username === "" || password === "") {
                document.getElementById("error-msg").style.display = "block";
            } else {
                loginForm.submit();
            }
        });
    }
});

// Function to Add a New Class
function addClass() {
    let classList = document.getElementById("classList");
    let className = prompt("Enter the new class name:");
    if (className) {
        let newClass = document.createElement("li");
        newClass.innerHTML = `<a href="#">${className}</a>`;
        classList.appendChild(newClass);
    }
}

// Function to handle assignment submission
function submitAssignment(assignmentId) {
    alert("Assignment " + assignmentId + " submitted successfully!");
}





function checkLockStatus() {
    fetch("{{ url_for('check_lock_status') }}")
        .then(response => response.json())
        .then(data => {
            if (data.is_locked) {
                // alert("Your account has been locked by an admin!");
                window.location.href = "{{ url_for('home') }}";
            }
        })
        .catch(error => console.error("Error checking lock status:", error));
}

setInterval(checkLockStatus, 5000);
