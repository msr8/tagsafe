const notifDiv  = document.getElementById("notif");
const notifText = document.getElementById("notif-text");




function notify(message) {
    notifDiv.style.display = "block";
    notifText.innerText    = message;
}




function login() {
    // When clicking the login button, hide any notif
    notifDiv.style.display = "none";

    let email_or_username = document.getElementById("email-or-username-input").value;
    let password = document.getElementById("password-input").value;

    if (email_or_username == "") {
        notify("Please enter your email or username");
        return;
    }
    if (password == "") {
        notify("Please enter your password");
        return;
    }

    fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            email_or_username: email_or_username,
            password: password
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status == "error") {
                notify(data["message"]);
            } else if (data.status == "redirect") {
                window.location.href = data.url;
            }
            else {
                notify("An error occurred. Please try again later");
            }
        })
        .catch((error) => {
            console.error("Error:", error);
            notify("An error occurred. Please try again later");
        });
}