function updateTaskStatus(proposalId, taskId, field, value) {
    const data = {};
    data[field] = field === 'progress_pct' ? parseInt(value) || 0 : value;

    fetch('/api/tracker/' + proposalId + '/task/' + taskId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(() => {
        if (field === 'status' || field === 'progress_pct') {
            const card = document.querySelector('[data-task-id="' + taskId + '"]');
            if (card) {
                const fill = card.querySelector('.progress-bar-fill');
                if (fill && field === 'progress_pct') {
                    fill.style.width = value + '%';
                }
            }
        }
    });
}

function updateBudgetActual(proposalId, itemId, value) {
    fetch('/api/tracker/' + proposalId + '/budget/' + itemId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actual_cost: parseFloat(value) || 0 })
    });
}

function addMilestone(proposalId) {
    const name = document.getElementById('new-milestone-name').value.trim();
    const date = document.getElementById('new-milestone-date').value;
    if (!name) return;

    fetch('/api/tracker/' + proposalId + '/milestone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, date: date })
    })
    .then(r => r.json())
    .then(m => {
        const list = document.getElementById('milestone-list');
        const li = document.createElement('li');
        li.className = 'milestone-item';
        li.dataset.milestoneId = m.id;
        li.innerHTML = `
            <input type="checkbox" onchange="toggleMilestone('${proposalId}', '${m.id}', this.checked)">
            <span class="milestone-text">${m.name}</span>
            <span class="milestone-date">
                <input type="date" class="tracker-input" value="${m.date || ''}"
                       onchange="updateMilestone('${proposalId}', '${m.id}', 'date', this.value)">
            </span>
            <button class="btn-icon btn-danger-icon milestone-delete"
                    onclick="deleteMilestone('${proposalId}', '${m.id}')">&times;</button>
        `;
        list.appendChild(li);
        document.getElementById('new-milestone-name').value = '';
        document.getElementById('new-milestone-date').value = '';
    });
}

function toggleMilestone(proposalId, milestoneId, completed) {
    fetch('/api/tracker/' + proposalId + '/milestone/' + milestoneId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: completed })
    });
}

function updateMilestone(proposalId, milestoneId, field, value) {
    const data = {};
    data[field] = value;
    fetch('/api/tracker/' + proposalId + '/milestone/' + milestoneId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}

function deleteMilestone(proposalId, milestoneId) {
    if (!confirm(t('Delete this milestone?'))) return;
    fetch('/api/tracker/' + proposalId + '/milestone/' + milestoneId, {
        method: 'DELETE'
    }).then(() => {
        const item = document.querySelector('[data-milestone-id="' + milestoneId + '"]');
        if (item) item.remove();
    });
}

function addReport(proposalId) {
    const title = document.getElementById('new-report-title').value.trim();
    if (!title) return;

    fetch('/api/tracker/' + proposalId + '/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title, date: new Date().toISOString().slice(0, 10), content: '' })
    })
    .then(r => r.json())
    .then(report => {
        const list = document.getElementById('report-list');
        const div = document.createElement('div');
        div.className = 'report-card';
        div.dataset.reportId = report.id;
        div.innerHTML = `
            <div class="report-header">
                <strong>${report.title}</strong>
                <span class="report-date">
                    <input type="date" class="tracker-input" value="${report.date}"
                           onchange="updateReport('${proposalId}', '${report.id}', 'date', this.value)">
                    <button class="btn-icon btn-danger-icon milestone-delete"
                            onclick="deleteReport('${proposalId}', '${report.id}')">&times;</button>
                </span>
            </div>
            <textarea class="notes-textarea" placeholder="${t('Report content...')}"
                      onchange="updateReport('${proposalId}', '${report.id}', 'content', this.value)"></textarea>
        `;
        list.appendChild(div);
        document.getElementById('new-report-title').value = '';
    });
}

function updateReport(proposalId, reportId, field, value) {
    const data = {};
    data[field] = value;
    fetch('/api/tracker/' + proposalId + '/report/' + reportId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}

function deleteReport(proposalId, reportId) {
    if (!confirm(t('Delete this report?'))) return;
    fetch('/api/tracker/' + proposalId + '/report/' + reportId, {
        method: 'DELETE'
    }).then(() => {
        const card = document.querySelector('[data-report-id="' + reportId + '"]');
        if (card) card.remove();
    });
}

function exportTracker(proposalId, format) {
    const t = '?t=' + Date.now();
    if (format === 'pdf') {
        window.open('/export/tracker/pdf/' + proposalId + t, '_blank');
    } else if (format === 'html') {
        window.open('/export/tracker/html/' + proposalId + t, '_blank');
    } else if (format === 'markdown') {
        window.open('/export/tracker/markdown/' + proposalId + t, '_blank');
    }
}
