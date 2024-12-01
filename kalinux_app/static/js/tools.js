document.addEventListener('DOMContentLoaded', function () {
    /**
     * Utility Functions
     */
    function displayError(errorMessage, elementId) {
        document.getElementById(elementId).innerHTML = `<div class="error">${errorMessage}</div>`;
    }

    function displayLoader(elementId) {
        document.getElementById(elementId).innerHTML = `<div class="loading">Загрузка...</div>`;
    }

    function renderResult(result, elementId) {
        document.getElementById(elementId).innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
    }


    function handleFormSubmit(formId, endpoint, resultId, renderFunction) {
        document.getElementById(formId).addEventListener('submit', function (event) {
            event.preventDefault();

            const formData = new FormData(document.getElementById(formId));
            const data = Object.fromEntries(formData.entries());

            displayLoader(resultId);

            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            })
                .then(response => response.json())
                .then(result => {
                    if (result.error) {
                        displayError(`Ошибка: ${result.error}`, resultId);
                    } else {
                        renderFunction(result, resultId);
                    }
                })
                .catch(error => {
                    displayError(`Error: ${error.message}`, resultId);
                });
        });
    }


    function renderIpInfo(data, resultId) {
        document.getElementById(resultId).innerHTML = `
            <h3>IP Info:</h3>
            <p><strong>IP:</strong> ${data.ip}</p>
            <p><strong>City:</strong> ${data.city}</p>
            <p><strong>Region:</strong> ${data.region}</p>
            <p><strong>Country:</strong> ${data.country}</p>
            <p><strong>Location:</strong> ${data.loc}</p>
            <p><strong>ISP:</strong> ${data.org}</p>`;
    }

    function renderDnsInfo(data, resultId) {
        document.getElementById(resultId).innerHTML = `
            <h3>DNS Lookup:</h3>
            <pre>${data.dns_records}</pre>`;
    }

    function renderReverseDnsInfo(data, resultId) {
        document.getElementById(resultId).innerHTML = `
            <h3>Reverse DNS Lookup:</h3>
            <pre>${data.reverse_dns}</pre>`;
    }

    function renderScanResult(data, resultId) {
        document.getElementById(resultId).innerHTML = `
            <h3>Open Ports:</h3>
            <p>${data.open_ports.join(', ')}</p>`;
    }

    function renderWhoisInfo(data, resultId) {
        document.getElementById(resultId).innerHTML = `
            <h3>WHOIS Info:</h3>
            <pre>${data.output}</pre>`;
    }


    handleFormSubmit('portScannerForm', '/scan_ports', 'scanResult', renderScanResult);
    handleFormSubmit('add-rule-form', '/add_rule', 'alert', renderResult);
    handleFormSubmit('remove-rule-form', '/remove_rule', 'alert', renderResult);
    handleFormSubmit('dnsLookupForm', '/dns_lookup', 'dnsInfo', renderDnsInfo);
    handleFormSubmit('reverseDnsForm', '/reverse_dns_lookup', 'reverseDnsInfo', renderReverseDnsInfo);
    handleFormSubmit('whoisForm', '/get_more_info', 'whoisResult', renderWhoisInfo);

    /**
     * Preloader Handling
     */
    window.onload = function () {
        document.getElementById('preloader').style.display = 'none';
    };

    /**
     * Scroll Event Handling (Optional)
     */
    window.addEventListener('scroll', function () {
        if (window.scrollY + window.innerHeight >= document.body.offsetHeight) {
            document.body.classList.add('show-footer');
        } else {
            document.body.classList.remove('show-footer');
        }
    });
});



document.addEventListener("DOMContentLoaded", () => {
    /**
     * Display a loading spinner
     */
    function displayLoader(elementId) {
        document.getElementById(elementId).innerHTML = `<div class="loading">Loading...</div>`;
    }

    /**
     * Display error messages
     */
    function displayError(errorMessage, elementId) {
        document.getElementById(elementId).innerHTML = `<div class="error">Error: ${errorMessage}</div>`;
    }

    /**
     * Handle API form submission
     */
    function handleFormSubmit(formId, endpoint, resultId, renderFunction) {
        document.getElementById(formId).addEventListener("submit", async (e) => {
            e.preventDefault();

            const formData = new FormData(document.getElementById(formId));
            const payload = Object.fromEntries(formData.entries());

            displayLoader(resultId);

            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) throw new Error(await response.text());
                const data = await response.json();

                if (data.success) {
                    renderFunction(data.data, resultId);
                } else {
                    displayError(data.error, resultId);
                }
            } catch (error) {
                displayError(error.message, resultId);
            }
        });
    }

    /**
     * Render functions
     */
    const renderIpInfo = (data, resultId) => {
        document.getElementById(resultId).innerHTML = `
            <h3>IP Info:</h3>
            <p><strong>IP:</strong> ${data.ip}</p>
            <p><strong>City:</strong> ${data.city || "N/A"}</p>
            <p><strong>Region:</strong> ${data.region || "N/A"}</p>
            <p><strong>Country:</strong> ${data.country || "N/A"}</p>
            <p><strong>ISP:</strong> ${data.org || "N/A"}</p>`;
    };

    const renderDnsInfo = (data, resultId) => {
        document.getElementById(resultId).innerHTML = `
            <h3>DNS Records:</h3>
            <ul>${data.dns_records.map(record => `<li>${record}</li>`).join("")}</ul>`;
    };

    const renderReverseDnsInfo = (data, resultId) => {
        document.getElementById(resultId).innerHTML = `
            <h3>Reverse DNS:</h3>
            <p>${data.reverse_dns}</p>`;
    };

    const renderScanResult = (data, resultId) => {
        document.getElementById(resultId).innerHTML = `
            <h3>Open Ports:</h3>
            <p>${data.open_ports.join(", ")}</p>`;
    };

    /**
     * Bind forms to their respective API endpoints
     */
    handleFormSubmit("portScannerForm", "/scan_ports", "scanResult", renderScanResult);
    handleFormSubmit("ipForm", "/get_ip_info", "ipInfoResult", renderIpInfo);
    handleFormSubmit("dnsLookupForm", "/dns_lookup", "dnsInfo", renderDnsInfo);
    handleFormSubmit("reverseDnsForm", "/reverse_dns_lookup", "reverseDnsInfo", renderReverseDnsInfo);
});

document.addEventListener("DOMContentLoaded", () => {
    // Real-time system metrics
    const socket = io.connect("http://localhost:5000");

    socket.on("system_metrics", (data) => {
        document.getElementById("cpuUsage").innerText = `${data.cpu_usage}%`;
        document.getElementById("memoryUsage").innerText = `${data.memory_usage}%`;
        document.getElementById("diskUsage").innerText = `${data.disk_usage}%`;
        document.getElementById("bytesSent").innerText = `${(data.network.bytes_sent / 1024).toFixed(2)} KB`;
        document.getElementById("bytesReceived").innerText = `${(data.network.bytes_received / 1024).toFixed(2)} KB`;
    });

    socket.on("connect_error", () => {
        document.getElementById("cpuUsage").innerText = "Connection Error";
        document.getElementById("memoryUsage").innerText = "Connection Error";
        document.getElementById("diskUsage").innerText = "Connection Error";
        document.getElementById("bytesSent").innerText = "Connection Error";
        document.getElementById("bytesReceived").innerText = "Connection Error";
    });
});

const toggleButton = document.getElementById('theme-toggle');
const app = document.getElementById('app');

toggleButton.addEventListener('click', () => {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  if (currentTheme === 'light') {
    document.documentElement.removeAttribute('data-theme');
    toggleButton.textContent = 'Сменить тему';
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    toggleButton.textContent = 'Вернуть тему';
  }
});

// Fade-in Effect on Scroll
const sections = document.querySelectorAll('.section');
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  },
  { threshold: 0.1 }
);

sections.forEach((section) => {
  observer.observe(section);
});

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
