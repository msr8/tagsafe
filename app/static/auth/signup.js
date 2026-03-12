const notifDiv  = document.getElementById("notif");
const notifText = document.getElementById("notif-text");




function notify(message) {
    notifDiv.style.display = "block";
    notifText.innerText    = message;
}




function signup() {
    // When clicking the signup button, hide any notif
    notifDiv.style.display = "none";

    let email    = document.getElementById("email-input").value;
    let username = document.getElementById("username-input").value;
    let password = document.getElementById("password-input").value;

    // Check if all 3 are present
    if (email == "")    { notify("Please enter your email");    return; }
    if (username == "") { notify("Please enter your username"); return; }
    if (password == "") { notify("Please enter your password"); return; }

    fetch("/api/auth/signup", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            email: email,
            username: username,
            password: password
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status == "error") {
                notify(data["message"]);
            }
            else if (data.status == "redirect") {
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


