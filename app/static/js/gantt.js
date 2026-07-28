let ganttUseDays = false;

const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December'];

function toggleTimelineUnits() {
    ganttUseDays = document.getElementById('timeline-use-days').checked;
    const label = document.querySelectorAll('.duration-label');
    label.forEach(l => {
        l.textContent = ganttUseDays ? 'Duration (days)' : 'Duration (months)';
    });
}

function toggleBudgetInTimeline() {
    const show = document.getElementById('timeline-show-budget').checked;
    document.querySelectorAll('.budget-timeline-subitems').forEach(el => {
        el.style.display = show ? 'block' : 'none';
    });
}

function autoInitGantt() {
    const inputs = document.getElementById('timeline-inputs');
    if (!inputs) return;

    const useDays = document.getElementById('timeline-use-days')?.checked;
    const showBudget = document.getElementById('timeline-show-budget')?.checked;
    ganttUseDays = useDays;
    const projectStartMonth = parseInt(document.getElementById('start-month').value) || 1;
    const projectStartYear = parseInt(document.getElementById('start-year').value) || 2025;

    document.querySelectorAll('.budget-timeline-subitems').forEach(el => {
        el.style.display = 'block';
    });

    const allTasks = [];
    const taskBudgetMap = {};

    inputs.querySelectorAll('.budget-timeline-item').forEach(function(sub) {
        const taskId = sub.dataset.taskId;
        if (!taskBudgetMap[taskId]) taskBudgetMap[taskId] = [];
        let itemDuration = parseInt(sub.querySelector('.duration-months').value) || 1;
        if (useDays) itemDuration = Math.ceil(itemDuration / 30);
        taskBudgetMap[taskId].push({
            id: sub.dataset.itemId,
            name: sub.querySelector('.timeline-task-name').textContent,
            lead_entity: sub.querySelector('.lead-entity')?.value || '',
            start_month: parseInt(sub.querySelector('.item-start-month')?.value) || projectStartMonth,
            start_year: parseInt(sub.querySelector('.item-start-year')?.value) || projectStartYear,
            duration_months: itemDuration,
            recurring: !!sub.querySelector('.item-recurring')?.checked,
            recurring_interval: parseInt(sub.querySelector('.item-recurring-interval')?.value) || 3,
            is_budget: true
        });
    });

    inputs.querySelectorAll('.timeline-input-card:not(.budget-timeline-item)').forEach(function(card) {
        const taskId = card.dataset.taskId;
        const items = taskBudgetMap[taskId] || [];
        let taskStartMonth = projectStartMonth;
        let taskStartYear = projectStartYear;
        let taskDuration = 1;

        if (items.length > 0) {
            let minOffset = Infinity, maxEnd = -Infinity;
            items.forEach(function(item) {
                const offset = (item.start_year - projectStartYear) * 12 + (item.start_month - projectStartMonth);
                const end = offset + item.duration_months;
                if (offset < minOffset) minOffset = offset;
                if (end > maxEnd) maxEnd = end;
            });
            const absStart = projectStartMonth + minOffset - 1;
            taskStartMonth = (absStart % 12) + 1;
            taskStartYear = projectStartYear + Math.floor(absStart / 12);
            taskDuration = maxEnd - minOffset;
            if (taskDuration < 1) taskDuration = 1;
        }

        const recurring = !!card.querySelector('.task-recurring')?.checked;
        const recurringInterval = parseInt(card.querySelector('.task-recurring-interval')?.value) || 3;

        allTasks.push({
            id: taskId,
            name: card.querySelector('.timeline-task-name').textContent,
            lead_entity: card.querySelector('.lead-entity')?.value || '',
            start_month: taskStartMonth,
            start_year: taskStartYear,
            duration_months: taskDuration,
            recurring: recurring,
            recurring_interval: recurringInterval
        });

        items.forEach(function(sub) { allTasks.push(sub); });
    });

    if (allTasks.length > 0) {
        renderGantt(allTasks);
    }
}

function toggleItemRecurring(checkbox) {
    const wrapper = checkbox.closest('.timeline-input-card').querySelector('.item-recurring-interval-wrapper');
    if (wrapper) wrapper.style.display = checkbox.checked ? '' : 'none';
}

function toggleTaskRecurring(checkbox) {
    const wrapper = checkbox.closest('.timeline-input-card').querySelector('.task-recurring-interval-wrapper');
    if (wrapper) wrapper.style.display = checkbox.checked ? '' : 'none';
}

function updateStartDate(proposalId) {
    const month = parseInt(document.getElementById('start-month').value);
    const year = parseInt(document.getElementById('start-year').value);
    const startDate = year + '-' + String(month).padStart(2, '0') + '-01';

    document.querySelectorAll('.item-start-month').forEach(sel => {
        sel.value = month;
    });
    document.querySelectorAll('.item-start-year').forEach(sel => {
        sel.value = year;
    });

    autoSaveTimeline(proposalId);
}

let autoSaveTimelineTimer = null;

function autoSaveTimeline(proposalId) {
    clearTimeout(autoSaveTimelineTimer);
    autoSaveTimelineTimer = setTimeout(function() {
        const useDays = document.getElementById('timeline-use-days')?.checked;
        const projectStartMonth = parseInt(document.getElementById('start-month').value) || 1;
        const projectStartYear = parseInt(document.getElementById('start-year').value) || 2025;
        const startDate = projectStartYear + '-' + String(projectStartMonth).padStart(2, '0') + '-01';
        const projectEndMonth = parseInt(document.getElementById('end-month')?.value) || projectStartMonth;
        const projectEndYear = parseInt(document.getElementById('end-year')?.value) || projectStartYear + 1;
        const endDate = projectEndYear + '-' + String(projectEndMonth).padStart(2, '0') + '-01';

        const body = {
            start_date: startDate,
            end_date: endDate,
            timeline_use_days: !!document.getElementById('timeline-use-days')?.checked,
            timeline_show_budget: !!document.getElementById('timeline-show-budget')?.checked
        };

        const inputs = document.getElementById('timeline-inputs');
        if (inputs) {
            const saveTasks = [];
            const budgetTimings = {};
            const taskBudgetItems = {};

            inputs.querySelectorAll('.timeline-input-card:not(.budget-timeline-item)').forEach(card => {
                taskBudgetItems[card.dataset.taskId] = [];
            });

            inputs.querySelectorAll('.budget-timeline-item').forEach(sub => {
                const taskId = sub.dataset.taskId;
                if (!taskBudgetItems[taskId]) taskBudgetItems[taskId] = [];
                let itemDuration = parseInt(sub.querySelector('.duration-months').value) || 1;
                if (useDays) itemDuration = Math.ceil(itemDuration / 30);
                const itemStartMonth = parseInt(sub.querySelector('.item-start-month')?.value) || projectStartMonth;
                const itemStartYear = parseInt(sub.querySelector('.item-start-year')?.value) || projectStartYear;
                taskBudgetItems[taskId].push({
                    start_month: itemStartMonth,
                    start_year: itemStartYear,
                    duration_months: itemDuration
                });
                budgetTimings[sub.dataset.itemId] = {
                    start_month: itemStartMonth,
                    start_year: itemStartYear,
                    duration_months: itemDuration,
                    lead_entity: sub.querySelector('.lead-entity')?.value || '',
                    recurring: !!sub.querySelector('.item-recurring')?.checked,
                    recurring_interval: parseInt(sub.querySelector('.item-recurring-interval')?.value) || 3
                };
            });

            inputs.querySelectorAll('.timeline-input-card:not(.budget-timeline-item)').forEach(card => {
                const taskId = card.dataset.taskId;
                const leadEntity = card.querySelector('.lead-entity')?.value || '';
                const items = taskBudgetItems[taskId] || [];

                let taskStartMonth = projectStartMonth;
                let taskStartYear = projectStartYear;
                let taskDuration = 1;

                if (items.length > 0) {
                    let minOffset = Infinity;
                    let maxEnd = -Infinity;
                    items.forEach(item => {
                        const offset = (item.start_year - projectStartYear) * 12 + (item.start_month - projectStartMonth);
                        const end = offset + item.duration_months;
                        if (offset < minOffset) minOffset = offset;
                        if (end > maxEnd) maxEnd = end;
                    });
                    const absStart = projectStartMonth + minOffset - 1;
                    taskStartMonth = (absStart % 12) + 1;
                    taskStartYear = projectStartYear + Math.floor(absStart / 12);
                    taskDuration = maxEnd - minOffset;
                    if (taskDuration < 1) taskDuration = 1;
                }

                saveTasks.push({
                    id: taskId,
                    name: card.querySelector('.timeline-task-name').textContent,
                    lead_entity: leadEntity,
                    start_month: taskStartMonth,
                    start_year: taskStartYear,
                    duration_months: taskDuration,
                    recurring: !!card.querySelector('.task-recurring')?.checked,
                    recurring_interval: parseInt(card.querySelector('.task-recurring-interval')?.value) || 3
                });
            });

            body.tasks = saveTasks;
            body.budget_item_timings = budgetTimings;
        }

        fetch('/api/proposal/' + proposalId, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then(function() {
            autoInitGantt();
        });
    }, 500);
}

function updateTimeline(proposalId) {
    const taskCards = document.querySelectorAll('#timeline-inputs > .timeline-input-card:not(.budget-timeline-item)');
    const showBudget = document.getElementById('timeline-show-budget')?.checked;
    const useDays = document.getElementById('timeline-use-days')?.checked;
    ganttUseDays = useDays;

    const projectStartMonth = parseInt(document.getElementById('start-month').value) || 1;
    const projectStartYear = parseInt(document.getElementById('start-year').value) || 2025;
    const startDate = projectStartYear + '-' + String(projectStartMonth).padStart(2, '0') + '-01';
    const projectEndMonth = parseInt(document.getElementById('end-month')?.value) || projectStartMonth;
    const projectEndYear = parseInt(document.getElementById('end-year')?.value) || projectStartYear + 1;
    const endDate = projectEndYear + '-' + String(projectEndMonth).padStart(2, '0') + '-01';

    const tasks = [];
    const taskBudgetItems = {};

    taskCards.forEach(card => {
        taskBudgetItems[card.dataset.taskId] = [];
    });

    taskCards.forEach(card => {
        const subitems = card.nextElementSibling;
        if (subitems && subitems.classList.contains('budget-timeline-subitems')) {
            subitems.querySelectorAll('.budget-timeline-item').forEach(sub => {
                const taskId = sub.dataset.taskId;
                if (!taskBudgetItems[taskId]) taskBudgetItems[taskId] = [];
                let itemDuration = parseInt(sub.querySelector('.duration-months').value) || 1;
                if (useDays) itemDuration = Math.ceil(itemDuration / 30);
                const itemStartMonth = parseInt(sub.querySelector('.item-start-month')?.value) || projectStartMonth;
                const itemStartYear = parseInt(sub.querySelector('.item-start-year')?.value) || projectStartYear;
                taskBudgetItems[taskId].push({
                    start_month: itemStartMonth,
                    start_year: itemStartYear,
                    duration_months: itemDuration,
                    lead_entity: sub.querySelector('.lead-entity')?.value || '',
                    name: sub.querySelector('.timeline-task-name').textContent,
                    id: sub.dataset.itemId,
                    recurring: !!sub.querySelector('.item-recurring')?.checked,
                    recurring_interval: parseInt(sub.querySelector('.item-recurring-interval')?.value) || 3
                });
            });
        }
    });

    taskCards.forEach(card => {
        const taskId = card.dataset.taskId;
        const leadEntity = card.querySelector('.lead-entity')?.value || '';
        const items = taskBudgetItems[taskId] || [];

        let taskStartMonth = projectStartMonth;
        let taskStartYear = projectStartYear;
        let taskDuration = 1;

        if (items.length > 0) {
            let minOffset = Infinity, maxEnd = -Infinity;
            items.forEach(item => {
                const offset = (item.start_year - projectStartYear) * 12 + (item.start_month - projectStartMonth);
                const end = offset + item.duration_months;
                if (offset < minOffset) minOffset = offset;
                if (end > maxEnd) maxEnd = end;
            });
            const absStart = projectStartMonth + minOffset - 1;
            taskStartMonth = (absStart % 12) + 1;
            taskStartYear = projectStartYear + Math.floor(absStart / 12);
            taskDuration = maxEnd - minOffset;
            if (taskDuration < 1) taskDuration = 1;
        }

        tasks.push({
            id: taskId,
            name: card.querySelector('.timeline-task-name').textContent,
            lead_entity: leadEntity,
            start_month: taskStartMonth,
            start_year: taskStartYear,
            duration_months: taskDuration,
            recurring: !!card.querySelector('.task-recurring')?.checked,
            recurring_interval: parseInt(card.querySelector('.task-recurring-interval')?.value) || 3
        });

        if (showBudget) {
            items.forEach(item => {
                tasks.push({
                    id: 'budget_' + item.id,
                    name: item.name,
                    lead_entity: item.lead_entity,
                    start_month: item.start_month,
                    start_year: item.start_year,
                    duration_months: item.duration_months,
                    recurring: item.recurring,
                    recurring_interval: item.recurring_interval,
                    is_budget: true
                });
            });
        }
    });

    const saveTasks = tasks.filter(t => !t.is_budget).map(t => ({
        id: t.id,
        name: t.name || '',
        lead_entity: t.lead_entity,
        start_month: t.start_month,
        start_year: t.start_year,
        duration_months: t.duration_months,
        recurring: t.recurring,
        recurring_interval: t.recurring_interval
    }));

    const budgetTimings = {};
    tasks.filter(t => t.is_budget).forEach(t => {
        const rawId = t.id.replace('budget_', '');
        budgetTimings[rawId] = {
            start_month: t.start_month,
            start_year: t.start_year,
            duration_months: t.duration_months,
            lead_entity: t.lead_entity,
            recurring: t.recurring,
            recurring_interval: t.recurring_interval
        };
    });

    fetch('/api/proposal/' + proposalId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            tasks: saveTasks,
            budget_item_timings: budgetTimings,
            start_date: startDate,
            end_date: endDate,
            timeline_use_days: useDays,
            timeline_show_budget: showBudget
        })
    })
    .then(() => renderGantt(tasks));
}

function monthsBetween(year1, month1, year2, month2) {
    return (year2 - year1) * 12 + (month2 - month1);
}

function renderGantt(tasks) {
    const container = document.getElementById('gantt-chart');
    if (!tasks.length) {
        container.innerHTML = '<div class="gantt-placeholder">No tasks to display.</div>';
        return;
    }

    const projectStartMonth = parseInt(document.getElementById('start-month')?.value) || 1;
    const projectStartYear = parseInt(document.getElementById('start-year')?.value) || 2025;

    const endMonth = parseInt(document.getElementById('end-month')?.value);
    const endYear = parseInt(document.getElementById('end-year')?.value);
    let maxEnd;
    if (endMonth && endYear) {
        maxEnd = monthsBetween(projectStartYear, projectStartMonth, endYear, endMonth) + 1;
    } else {
        maxEnd = 0;
        tasks.forEach(t => {
            const offset = monthsBetween(projectStartYear, projectStartMonth, t.start_year, t.start_month);
            const end = offset + (t.duration_months || 1);
            if (end > maxEnd) maxEnd = end;
        });
    }
    const maxMonths = Math.max(1, Math.min(60, maxEnd));
    const monthWidth = 60;

    const startDate = new Date(projectStartYear, projectStartMonth - 1, 1);

    const months = [];
    for (let i = 0; i < maxMonths; i++) {
        const d = new Date(startDate.getFullYear(), startDate.getMonth() + i, 1);
        months.push({
            label: d.toLocaleString('default', { month: 'short' }),
            year: d.getFullYear(),
            monthIndex: i,
            isFirstOfMonth: i === 0 || months[i - 1]?.year !== d.getFullYear()
        });
    }

    let yearHTML = '<div class="gantt-year-row"><div class="gantt-label-col"></div><div class="gantt-year-cells">';
    let currentYear = null;
    let yearStartIdx = 0;
    months.forEach((m, i) => {
        if (m.isFirstOfMonth || i === 0) {
            if (currentYear !== null) {
                const span = i - yearStartIdx;
                yearHTML += `<div class="gantt-year-cell" style="min-width:${span * monthWidth}px;flex:${span}">${currentYear}</div>`;
            }
            currentYear = m.year;
            yearStartIdx = i;
        }
    });
    if (currentYear !== null) {
        const span = months.length - yearStartIdx;
        yearHTML += `<div class="gantt-year-cell" style="min-width:${span * monthWidth}px;flex:${span}">${currentYear}</div>`;
    }
    yearHTML += '</div></div>';

    let headerHTML = '<div class="gantt-header"><div class="gantt-label-col"></div><div class="gantt-month-cells">';
    months.forEach(m => {
        headerHTML += `<div class="gantt-month" style="min-width:${monthWidth}px">${m.label}</div>`;
    });
    headerHTML += '</div></div>';

    let rowsHTML = '';

    const taskItems = {};
    tasks.forEach(t => {
        if (t.is_budget) {
            const parentId = t.id.replace('budget_', '');
            if (!taskItems[parentId]) taskItems[parentId] = [];
            taskItems[parentId].push(t);
        }
    });

    const rowTasks = {};
    tasks.forEach(task => {
        const lead = monthsBetween(projectStartYear, projectStartMonth, task.start_year, task.start_month);
        const duration = task.duration_months || 1;
        const isBudget = task.is_budget;
        const recurring = task.recurring;
        const interval = task.recurring_interval || 3;
        const key = `${task.id}_${isBudget ? 'b' : 't'}`;

        if (!rowTasks[key]) {
            rowTasks[key] = { ...task, _bars: [], _isBudget: isBudget };
        }

        if (recurring) {
            let offset = lead;
            while (offset < maxMonths) {
                rowTasks[key]._bars.push({ offset, duration });
                offset += interval;
            }
        } else {
            rowTasks[key]._bars.push({ offset: lead, duration });
        }
    });

    Object.values(rowTasks).forEach(task => {
        const isBudget = task._isBudget;
        const bars = task._bars;
        const entityLabel = task.lead_entity ? ` (${task.lead_entity})` : '';

        let totalLead = Infinity;
        let totalEnd = 0;
        bars.forEach(b => {
            if (b.offset < totalLead) totalLead = b.offset;
            if (b.offset + b.duration > totalEnd) totalEnd = b.offset + b.duration;
        });

        if (!isBudget && taskItems[task.id] && taskItems[task.id].length > 0) {
            taskItems[task.id].forEach(item => {
                const itemLead = monthsBetween(projectStartYear, projectStartMonth, item.start_year, item.start_month);
                const itemEnd = itemLead + (item.duration_months || 1);
                if (itemLead < totalLead) totalLead = itemLead;
                if (itemEnd > totalEnd) totalEnd = itemEnd;
            });
        }

        const rowClass = isBudget ? 'gantt-row gantt-row-budget' : 'gantt-row';
        const labelClass = isBudget ? 'gantt-row-label gantt-row-label-budget' : 'gantt-row-label';
        const barClass = isBudget ? 'gantt-bar gantt-bar-budget' : 'gantt-bar';

        rowsHTML += `<div class="${rowClass}">
            <div class="${labelClass}">${task.name}${entityLabel}</div>
            <div class="gantt-bar-container">`;

        for (let i = 0; i < maxMonths; i++) {
            const m = months[i];
            let inBar = false;
            for (const b of bars) {
                if (i >= b.offset && i < b.offset + b.duration) {
                    inBar = true;
                    break;
                }
            }
            if (inBar) {
                const barStart = bars.find(b => i >= b.offset && i < b.offset + b.duration);
                const barDur = barStart.duration;
                rowsHTML += `<div class="gantt-cell" style="min-width:${monthWidth}px">
                    <div class="${barClass}" style="width:${barDur * monthWidth}px"></div>
                </div>`;
                i += barDur - 1;
            } else {
                rowsHTML += `<div class="gantt-cell" style="min-width:${monthWidth}px"></div>`;
            }
        }

        rowsHTML += '</div></div>';
    });

    container.innerHTML = yearHTML + headerHTML + rowsHTML;
}
