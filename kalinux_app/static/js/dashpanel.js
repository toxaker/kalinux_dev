document.addEventListener('DOMContentLoaded', () => {
    const spinner = document.getElementById('spinner');
    const logsTable = document.getElementById('logs-table').querySelector('tbody');
    const ruleCount = document.getElementById('rule-count');
    const logCount = document.getElementById('log-count');

    // Load logs dynamically
    async function loadLogs() {
        spinner.style.display = 'block'; // Show spinner
        try {
            const response = await fetch('/api/logs'); // Assuming an API endpoint exists
            const logs = await response.json();
            logsTable.innerHTML = ''; // Clear existing logs

            logs.forEach(log => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${log.timestamp}</td>
                    <td>${log.ip_address}</td>
                    <td>${log.action}</td>
                    <td>${log.user_agent}</td>
                    <td>${log.geo_info}</td>
                `;
                logsTable.appendChild(row);
            });

            spinner.style.display = 'none'; // Hide spinner
        } catch (error) {
            console.error('Failed to load logs:', error);
            spinner.style.display = 'none';
        }
    }

    // Load counts dynamically
    async function loadCounts() {
        try {
            const response = await fetch('/api/dashboard-stats'); // Assuming an API endpoint exists
            const stats = await response.json();
            ruleCount.textContent = stats.rule_count;
            logCount.textContent = stats.log_count;
        } catch (error) {
            console.error('Failed to load counts:', error);
        }
    }

    // Sort table by column
    function sortTable(columnIndex) {
        const rows = Array.from(logsTable.querySelectorAll('tr'));
        const isAscending = logsTable.dataset.sortOrder !== 'asc';

        rows.sort((a, b) => {
            const aText = a.cells[columnIndex].textContent.trim();
            const bText = b.cells[columnIndex].textContent.trim();
            return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
        });

        logsTable.innerHTML = ''; // Clear table
        rows.forEach(row => logsTable.appendChild(row));
        logsTable.dataset.sortOrder = isAscending ? 'asc' : 'desc';
    }

    // Initialize dashboard
    loadLogs();
    loadCounts();
});

document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signup-form');

    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(signupForm);

        try {
            const response = await fetch('/api/signup', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                alert('Request submitted successfully!');
                signupForm.reset();
            } else {
                alert('Failed to submit request. Please try again.');
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            alert('An error occurred. Please try again later.');
        }
    });
});
