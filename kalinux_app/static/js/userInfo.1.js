window.Telegram.WebApp.ready();
const userInfo = Telegram.WebApp.initDataUnsafe.user;
const userElement = document.getElementById('user-info');
userElement.innerHTML = `Hello, ${userInfo.first_name} ${userInfo.last_name}`;
document.getElementById('send-data-btn').addEventListener('click', () => {
    const data = { message: "User clicked the button!" };
    Telegram.WebApp.sendData(JSON.stringify(data));
});

document.addEventListener('DOMContentLoaded', function () {
    function displayError(errorMessage, elementId) {
        document.getElementById(elementId).innerHTML = `<div class="error">${errorMessage}</div>`;
    }

    function displayLoader(elementId) {
        document.getElementById(elementId).innerHTML = `<div class="loading">Загрузка...</div>`;
    }
});
