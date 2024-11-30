function sendDataToServer() {
    const message = document.getElementById('message').value;
    const initData = Telegram.WebApp.initData;

            fetch('/submit_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message, initData: initData }),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Server response:', data);
            });
        }
