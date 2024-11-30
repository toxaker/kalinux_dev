kdocument.addEventListener('DOMContentLoaded', () => {
    const logsTable = document.getElementById('logs-table').querySelector('tbody');
    const ruleCount = document.getElementById('rule-count');
    const logCount = document.getElementById('log-count');
    const serverUptime = document.getElementById('server-uptime');
    const activeUsers = document.getElementById('active-users');
    const spinner = document.getElementById('spinner');

    // Fetch Logs and Populate Table
    async function loadLogs() {
        spinner.style.display = 'block'; // Show spinner
        try {
            const response = await fetch('/api/logs'); // Replace with your actual API endpoint
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

    // Fetch Stats and Populate Dashboard
    async function loadStats() {
        try {
            const response = await fetch('/api/dashboard-stats'); // Replace with your actual API endpoint
            const stats = await response.json();
            ruleCount.textContent = stats.rule_count || 0;
            logCount.textContent = stats.log_count || 0;
            serverUptime.textContent = stats.uptime || 'N/A';
            activeUsers.textContent = stats.active_users || 0;
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    // Sort Table by Column
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

    // Attach Event Listeners to Table Headers for Sorting
    document.querySelectorAll('#logs-table th').forEach((th, index) => {
        th.addEventListener('click', () => sortTable(index));
    });

    // Initialize Dashboard
    loadLogs();
    loadStats();
});

