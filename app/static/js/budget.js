const BUDGET_MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

function budgetMonthOptions(selected) {
    let html = '';
    for (let m = 1; m <= 12; m++) {
        html += `<option value="${m}" ${m === selected ? 'selected' : ''}>${t(BUDGET_MONTHS[m - 1])}</option>`;
    }
    return html;
}

function budgetYearOptions(selected) {
    let html = '<option value="">' + t('Year') + '</option>';
    for (let y = 2024; y <= 2035; y++) {
        html += `<option value="${y}" ${y === selected ? 'selected' : ''}>${y}</option>`;
    }
    return html;
}

function budgetTimingLineHTML(card) {
    const sm = card.dataset.startMonth;
    const sy = card.dataset.startYear;
    const dur = card.dataset.duration;
    if (sm && sy) {
        return '<span class="budget-item-timing-text">' + t(BUDGET_MONTHS[parseInt(sm) - 1]) + ' ' + sy
            + ' &middot; ' + (dur || 1) + ' ' + t('months') + '</span>';
    }
    return '<span class="budget-item-timing-text unscheduled">' + t('Not scheduled') + '</span>';
}

function refreshBudgetByYear() {
    const body = document.getElementById('budget-year-body');
    if (!body) return;

    const byYear = {};
    let unscheduled = 0;
    let total = 0;

    document.querySelectorAll('.budget-item-card').forEach(card => {
        const amount = (parseFloat(card.dataset.cost) || 0) * (parseFloat(card.dataset.units) || 0);
        if (amount <= 0) return;
        total += amount;

        const sm = parseInt(card.dataset.startMonth);
        const sy = parseInt(card.dataset.startYear);
        const dur = parseInt(card.dataset.duration) || 1;
        if (sm && sy && dur > 0) {
            const start = sy * 12 + (sm - 1);
            const monthly = amount / dur;
            for (let m = 0; m < dur; m++) {
                const y = Math.floor((start + m) / 12);
                byYear[y] = (byYear[y] || 0) + monthly;
            }
        } else {
            unscheduled += amount;
        }
    });

    let html = '';
    Object.keys(byYear).sort((a, b) => a - b).forEach(y => {
        const amount = byYear[y];
        const pct = total > 0 ? (amount / total * 100).toFixed(1) : '';
        html += `<tr data-year="${y}"><td>${y}</td><td class="num">$${formatCurrency(amount)}</td><td class="num">${pct}%</td></tr>`;
    });
    if (unscheduled > 0) {
        const pct = total > 0 ? (unscheduled / total * 100).toFixed(1) : '';
        html += `<tr class="year-row-unscheduled" data-unscheduled><td>${t('Not scheduled')}</td><td class="num">$${formatCurrency(unscheduled)}</td><td class="num">${pct}%</td></tr>`;
    }

    body.innerHTML = html;

    const wrap = document.getElementById('budget-year-table-wrap');
    const empty = document.getElementById('budget-year-empty');
    if (wrap) wrap.classList.toggle('hidden', total <= 0);
    if (empty) empty.style.display = total > 0 ? 'none' : '';

    const hint = document.getElementById('budget-year-hint');
    if (hint) hint.style.display = unscheduled > 0 ? '' : 'none';
}

function formatCurrency(num) {
    return num.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function toggleBudgetDescription() {
    const checked = document.getElementById('show-budget-description').checked;
    document.getElementById('budget-description-wrapper').style.display = checked ? '' : 'none';
    const match = window.location.pathname.match(/\/editor\/([^/]+)/);
    if (match) {
        fetch('/api/proposal/' + match[1], {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ show_budget_description: checked })
        });
    }
}

function deleteBudgetItem(proposalId, itemId, btn) {
    if (!confirm(t('Delete this budget item?'))) return;
    fetch('/api/budget/' + proposalId + '/' + itemId, { method: 'DELETE' })
        .then(() => {
            const card = btn.closest('.budget-item-card');
            if (card) card.remove();
            checkEmptyGroups();
        });
}

function addBudgetItem(proposalId) {
    const taskId = document.getElementById('budget-task-select').value;
    const name = document.getElementById('budget-item-name').value.trim();
    const costPerUnit = parseFloat(document.getElementById('budget-cost').value) || 0;
    const units = parseFloat(document.getElementById('budget-units').value) || 1;
    const startMonth = document.getElementById('budget-start-month').value;
    const startYear = document.getElementById('budget-start-year').value;
    const duration = parseInt(document.getElementById('budget-duration').value) || 1;

    if (!taskId || !name) {
        alert(t('Select a task and enter an item name.'));
        return;
    }

    fetch('/api/budget/' + proposalId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            task_id: taskId,
            name: name,
            cost_per_unit: costPerUnit,
            units: units,
            start_month: startMonth || null,
            start_year: startYear || null,
            duration_months: duration,
        })
    })
    .then(r => r.json())
    .then(item => {
        const list = document.getElementById('budget-item-list');
        const emptyMsg = list.querySelector('.empty-text');
        if (emptyMsg) emptyMsg.remove();

        const taskSelect = document.getElementById('budget-task-select');
        const taskName = taskSelect.options[taskSelect.selectedIndex].text;

        const card = document.createElement('div');
        card.className = 'budget-item-card';
        card.dataset.itemId = item.id;
        card.dataset.taskId = item.task_id;
        card.dataset.name = item.name;
        card.dataset.cost = item.cost_per_unit;
        card.dataset.units = item.units;
        card.dataset.startMonth = startMonth || '';
        card.dataset.startYear = startYear || '';
        card.dataset.duration = duration;
        card.innerHTML = `
            <div class="budget-item-info">
                <span class="budget-item-name">${item.name}</span>
            </div>
            <div class="budget-item-numbers">
                <span>${formatCurrency(item.cost_per_unit)}/unit &times; ${item.units} ${t('units')}</span>
                <span class="budget-item-total">${formatCurrency(item.cost_per_unit * item.units)}</span>
            </div>
            <div class="budget-item-timing" data-timing-line>${budgetTimingLineHTML(card)}</div>
            <div class="budget-item-actions">
                <button class="btn-icon" onclick="editBudgetItem('${proposalId}', this)" title="${t('Edit')}">&#9998;</button>
                <button class="btn-icon btn-danger-icon"
                        onclick="deleteBudgetItem('${proposalId}', '${item.id}', this)">&times;</button>
            </div>
        `;
        htmx.process(card);

        let group = list.querySelector(`.budget-task-group[data-task-id="${taskId}"]`);
        if (!group) {
            group = document.createElement('div');
            group.className = 'budget-task-group';
            group.dataset.taskId = taskId;
            group.innerHTML = `
                <div class="budget-task-header">
                    <span class="budget-task-name">${taskName}</span>
                    <span class="budget-task-subtotal" data-task-id="${taskId}">$0</span>
                </div>
            `;
            list.appendChild(group);
        }

        group.appendChild(card);

        document.getElementById('budget-item-name').value = '';
        document.getElementById('budget-cost').value = '';
        document.getElementById('budget-units').value = '1';
        document.getElementById('budget-start-month').value = '';
        document.getElementById('budget-start-year').value = '';
        document.getElementById('budget-duration').value = '1';

        updateBudgetTotal();
        refreshBudgetByYear();
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function editBudgetItem(proposalId, btn) {
    const card = btn.closest('.budget-item-card');
    if (card.querySelector('.budget-item-edit-form')) return;

    const taskId = card.dataset.taskId;
    const name = card.dataset.name;
    const cost = card.dataset.cost;
    const units = card.dataset.units;
    const startMonth = card.dataset.startMonth ? parseInt(card.dataset.startMonth) : '';
    const startYear = card.dataset.startYear ? parseInt(card.dataset.startYear) : '';
    const duration = card.dataset.duration ? parseInt(card.dataset.duration) : 1;

    const taskSelect = document.getElementById('budget-task-select');
    let taskOptions = '';
    for (const opt of taskSelect.options) {
        if (opt.value) {
            taskOptions += `<option value="${escapeHtml(opt.value)}" ${opt.value === taskId ? 'selected' : ''}>${escapeHtml(opt.text)}</option>`;
        }
    }

    const info = card.querySelector('.budget-item-info');
    const numbers = card.querySelector('.budget-item-numbers');
    const timingLine = card.querySelector('.budget-item-timing');
    const actions = card.querySelector('.budget-item-actions');

    info.style.display = 'none';
    numbers.style.display = 'none';
    timingLine.style.display = 'none';
    actions.style.display = 'none';

    const form = document.createElement('div');
    form.className = 'budget-item-edit-form';
    form.innerHTML = `
        <div class="budget-edit-row">
            <select class="edit-task-id">${taskOptions}</select>
            <input type="text" class="edit-name" value="${escapeHtml(name)}" placeholder="${t('Item name')}">
            <input type="number" class="edit-cost" value="${cost}" min="0" step="0.01" placeholder="${t('Cost/unit')}">
            <input type="number" class="edit-units" value="${units}" min="0" step="1" placeholder="${t('Units')}">
        </div>
        <div class="budget-edit-row budget-timing-fields">
            <select class="edit-start-month">${budgetMonthOptions(startMonth)}</select>
            <select class="edit-start-year">${budgetYearOptions(startYear)}</select>
            <input type="number" class="edit-duration" value="${duration}" min="1" placeholder="${t('Months')}">
        </div>
        <div class="budget-item-edit-actions">
            <button class="btn btn-primary btn-sm" onclick="saveBudgetItem('${proposalId}', this)">${t('Save')}</button>
            <button class="btn btn-sm" onclick="cancelEditBudgetItem(this)">${t('Cancel')}</button>
        </div>
    `;
    card.insertBefore(form, actions);
}

function saveBudgetItem(proposalId, btn) {
    const card = btn.closest('.budget-item-card');
    const form = card.querySelector('.budget-item-edit-form');

    const startMonth = form.querySelector('.edit-start-month').value;
    const startYear = form.querySelector('.edit-start-year').value;

    const data = {
        task_id: form.querySelector('.edit-task-id').value,
        name: form.querySelector('.edit-name').value.trim(),
        cost_per_unit: parseFloat(form.querySelector('.edit-cost').value) || 0,
        units: parseFloat(form.querySelector('.edit-units').value) || 1,
        start_month: startMonth,
        start_year: startYear,
        duration_months: parseInt(form.querySelector('.edit-duration').value) || 1,
    };

    if (!data.task_id || !data.name) {
        alert(t('Select a task and enter an item name.'));
        return;
    }

    fetch(`/api/budget/${proposalId}/${card.dataset.itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
    .then(r => r.json())
    .then(() => {
        const taskSelect = document.getElementById('budget-task-select');
        let taskName = '';
        for (const opt of taskSelect.options) {
            if (opt.value === data.task_id) {
                taskName = opt.text;
                break;
            }
        }

        const oldTaskId = card.dataset.taskId;
        card.dataset.taskId = data.task_id;
        card.dataset.name = data.name;
        card.dataset.cost = data.cost_per_unit;
        card.dataset.units = data.units;
        card.dataset.startMonth = startMonth || '';
        card.dataset.startYear = startYear || '';
        card.dataset.duration = data.duration_months;

        const info = card.querySelector('.budget-item-info');
        const numbers = card.querySelector('.budget-item-numbers');
        const timingLine = card.querySelector('.budget-item-timing');
        const actions = card.querySelector('.budget-item-actions');

        info.querySelector('.budget-item-name').textContent = data.name;
        numbers.querySelector('span:first-child').innerHTML =
            `${formatCurrency(data.cost_per_unit)}/unit &times; ${data.units} ${t('units')}`;
        numbers.querySelector('.budget-item-total').textContent =
            `${formatCurrency(data.cost_per_unit * data.units)}`;
        timingLine.innerHTML = budgetTimingLineHTML(card);

        form.remove();
        info.style.display = '';
        numbers.style.display = '';
        timingLine.style.display = '';
        actions.style.display = '';

        if (oldTaskId !== data.task_id) {
            moveCardToGroup(card, data.task_id, taskName);
            checkEmptyGroups();
        }

        updateBudgetTotal();
        refreshBudgetByYear();
    });
}

function moveCardToGroup(card, newTaskId, taskName) {
    const list = document.getElementById('budget-item-list');
    let group = list.querySelector(`.budget-task-group[data-task-id="${newTaskId}"]`);

    if (!group) {
        group = document.createElement('div');
        group.className = 'budget-task-group';
        group.dataset.taskId = newTaskId;
        group.innerHTML = `
            <div class="budget-task-header">
                <span class="budget-task-name">${taskName}</span>
                <span class="budget-task-subtotal" data-task-id="${newTaskId}">$0</span>
            </div>
        `;
        list.appendChild(group);
    }

    group.appendChild(card);
}

function cancelEditBudgetItem(btn) {
    const card = btn.closest('.budget-item-card');
    const form = card.querySelector('.budget-item-edit-form');

    form.remove();
    card.querySelector('.budget-item-info').style.display = '';
    card.querySelector('.budget-item-numbers').style.display = '';
    card.querySelector('.budget-item-timing').style.display = '';
    card.querySelector('.budget-item-actions').style.display = '';
}

function checkEmptyGroups() {
    setTimeout(() => {
        document.querySelectorAll('.budget-task-group').forEach(group => {
            if (!group.querySelector('.budget-item-card')) {
                group.remove();
            }
        });
        updateBudgetTotal();
        refreshBudgetByYear();
    }, 50);
}

function updateBudgetTotal() {
    document.querySelectorAll('.budget-task-group').forEach(group => {
        let subtotal = 0;
        group.querySelectorAll('.budget-item-total').forEach(el => {
            subtotal += parseFloat(el.textContent.replace(/[$,]/g, '')) || 0;
        });
        const subtotalEl = group.querySelector('.budget-task-subtotal');
        if (subtotalEl) {
            subtotalEl.textContent = '$' + formatCurrency(subtotal);
        }
    });

    let total = 0;
    document.querySelectorAll('.budget-item-total').forEach(el => {
        total += parseFloat(el.textContent.replace(/[$,]/g, '')) || 0;
    });
    document.getElementById('budget-total').textContent = '$' + formatCurrency(total);

    const indirectInput = document.getElementById('indirect-percent');
    const percent = indirectInput ? (parseFloat(indirectInput.value) || 0) : 0;
    const indirectAmount = total * (percent / 100);
    const totalWithIndirect = total + indirectAmount;

    const indirectAmountEl = document.getElementById('indirect-amount');
    if (indirectAmountEl) {
        indirectAmountEl.textContent = '$' + formatCurrency(indirectAmount);
    }

    const indirectLabel = document.getElementById('indirect-label');
    if (indirectLabel) {
        indirectLabel.textContent = t('Indirect') + ` (${Math.round(percent)}%)`;
    }

    const totalWithIndirectEl = document.getElementById('budget-total-with-indirect');
    if (totalWithIndirectEl) {
        totalWithIndirectEl.textContent = '$' + formatCurrency(totalWithIndirect);
    }
}

function updateIndirect(proposalId) {
    const percentInput = document.getElementById('indirect-percent');
    const percent = parseFloat(percentInput.value) || 0;

    fetch('/api/proposal/' + proposalId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ indirect_percent: percent })
    });

    updateBudgetTotal();
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.budget-item-card').forEach(card => {
        card.querySelector('.btn-icon')?.addEventListener('click', () => {
            setTimeout(updateBudgetTotal, 100);
        });
    });
});

function openBudgetImportModal() {
    document.getElementById('budget-import-modal').classList.remove('hidden');
    document.getElementById('budget-import-file').value = '';
}

function closeBudgetImportModal() {
    document.getElementById('budget-import-modal').classList.add('hidden');
}

async function uploadBudgetExcel() {
    const fileInput = document.getElementById('budget-import-file');
    const file = fileInput.files[0];
    if (!file) {
        alert(t('Please select an Excel file.'));
        return;
    }

    const match = window.location.pathname.match(/\/editor\/([^/]+)/);
    if (!match) return;
    const proposalId = match[1];

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/proposal/' + proposalId + '/import-budget', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            closeBudgetImportModal();
            const msg = t('Imported') + ' ' + result.created_items + ' ' + t('budget items');
            const taskMsg = result.created_tasks > 0 ? ' ' + t('and') + ' ' + result.created_tasks + ' ' + t('new tasks') : '';
            alert(msg + taskMsg + '. Reloading...');
            window.location.reload();
        } else {
            alert(result.error || t('Failed to import budget.'));
        }
    } catch (error) {
        alert(t('Error importing file: ') + error.message);
    }
}
