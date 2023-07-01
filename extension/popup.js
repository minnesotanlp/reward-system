document.addEventListener('DOMContentLoaded', function () {
    var checkbox = document.querySelector('input[type="checkbox"]');
    chrome.storage.local.get(['username'], function(result) {
        if (result.username !== undefined){
            var loginForm = document.getElementById("loginForm");
            loginForm.style.display = "none";
            var welcomeMessage = document.getElementById("welcomeMessage");
            welcomeMessage.innerHTML = "Welcome, " + result.username;
            welcomeMessage.style.display = "block";
        }
    });
    chrome.storage.local.get('enabled', function (result) {
        if (result.enabled != null) {
            checkbox.checked = result.enabled;
        }
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {toggle: checkbox.checked}, function (response) {
            });
        });
    });
    checkbox.addEventListener('click', function () {
        console.log(checkbox.checked);
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {toggle: checkbox.checked}, function (response) {
            });
        });
        chrome.storage.local.set({ 'enabled': checkbox.checked }, function () {
            console.log("confirmed");
        });
    });
    var login = document.querySelector('button[type="submit"]');
    var username = document.getElementById("username");
    var password = document.getElementById("password");
    username.addEventListener('click', function(){
        var errMessage = document.querySelector('p[style="color: red; font-size: 14px;"]');
        console.log(errMessage);
        if (errMessage !== null){
            username.parentNode.removeChild(errMessage);
        }
    })
    password.addEventListener('click', function(){
        var errMessage = document.querySelector('p[style="color: red; font-size: 14px;"]');
        if (errMessage !== null){
            username.parentNode.removeChild(errMessage);
        }
    })
    login.addEventListener('click', function(){
        var usernameInput = username.value;
        var passwordInput = password.value;
        if (usernameInput == "" || passwordInput == ""){
            var textElement = document.createElement("p");
            textElement.innerText = "Invalid username/password, please try again";
            textElement.style.color = "red";
            textElement.style.fontSize = "14px";
            login.parentNode.insertBefore(textElement, login);
        }
        else {
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                chrome.tabs.sendMessage(tabs[0].id, {message: "login", username: usernameInput, password: passwordInput}, function (response) {
                });
            });
            chrome.storage.local.set({'username': usernameInput}, function() {
              console.log('Data saved successfully!');
            });
        }
    });
});