function toggleSidebar() {
    const sidebar = document.getElementById('snippet-sidebar');
    const main = document.querySelector('.main-content');
    const toggle = document.getElementById('sidebar-toggle');
    sidebar.classList.toggle('open');
    main.classList.toggle('sidebar-open');
    if (toggle) toggle.classList.toggle('rotated');
}

function switchSidebarTab(name, btn) {
    document.querySelectorAll('.sidebar-tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('snippet-list').classList.toggle('hidden', name !== 'snippets');
    document.getElementById('results-list').classList.toggle('hidden', name !== 'results');
    if (name === 'results' && !window._resultsLoaded) {
        window._resultsLoaded = true;
        loadResults();
    }
}

function activateTab(btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

function countWords(text) {
    const trimmed = text.trim();
    return trimmed ? trimmed.split(/\s+/).length : 0;
}

function updateWordCount(textareaId, labelId) {
    const el = document.getElementById(textareaId);
    const label = document.getElementById(labelId);
    if (!el || !label) return;
    const base = label.dataset.baseLabel;
    const count = countWords(el.value);
    label.textContent = base + (count > 0 ? ' (' + count + ')' : '');
}

function initWordCounts() {
    document.querySelectorAll('[data-word-count]').forEach(el => {
        const textareaId = el.dataset.wordCount;
        const textarea = document.getElementById(textareaId);
        if (textarea) {
            textarea.addEventListener('input', () => updateWordCount(textareaId, el.id));
            updateWordCount(textareaId, el.id);
        }
    });
}

function saveTextareaHeights() {
    document.querySelectorAll('#tab-content textarea[id]').forEach(el => {
        if (el.id && el.style.height) {
            localStorage.setItem('ta_height_' + el.id, el.style.height);
        }
    });
}

function restoreTextareaHeights() {
    document.querySelectorAll('#tab-content textarea[id]').forEach(el => {
        if (el.id) {
            const saved = localStorage.getItem('ta_height_' + el.id);
            if (saved) el.style.height = saved;
        }
    });
}

function saveCurrentTabData(proposalId) {
    const data = {};
    const summaryEl = document.getElementById('project-summary');
    const scopeEl = document.getElementById('project-scope');
    const qualsEl = document.getElementById('qualifications-text');
    const clientEl = document.getElementById('client-name');
    const subtitleEl = document.getElementById('proposal-subtitle');
    if (summaryEl) data.project_summary = summaryEl.value;
    if (scopeEl) data.scope = scopeEl.value;
    if (qualsEl) data.qualifications = qualsEl.value;
    if (clientEl) data.client_name = clientEl.value;
    if (subtitleEl) data.subtitle = subtitleEl.value;

    const indirectEl = document.getElementById('indirect-percent');
    if (indirectEl) data.indirect_percent = parseFloat(indirectEl.value) || 0;

    const budgetDescEl = document.getElementById('budget-description');
    const showBudgetDescEl = document.getElementById('show-budget-description');
    if (showBudgetDescEl) data.show_budget_description = showBudgetDescEl.checked;
    if (budgetDescEl) data.budget_description = budgetDescEl.value;

    const taskList = document.getElementById('task-list');
    if (taskList) {
        const cards = taskList.querySelectorAll('.task-card');
        data.tasks = [];
        cards.forEach(card => {
            data.tasks.push({
                id: card.dataset.taskId,
                name: card.querySelector('.task-name-input').value,
                description: card.querySelector('.task-desc-input').value,
            });
        });
    }

    const timelineInputs = document.getElementById('timeline-inputs');
    if (document.getElementById('start-month')) {
        const useDays = document.getElementById('timeline-use-days')?.checked;
        const startMonth = parseInt(document.getElementById('start-month')?.value) || 1;
        const startYear = parseInt(document.getElementById('start-year')?.value) || 2025;
        data.start_date = startYear + '-' + String(startMonth).padStart(2, '0') + '-01';
        const endMonth = parseInt(document.getElementById('end-month')?.value) || startMonth;
        const endYear = parseInt(document.getElementById('end-year')?.value) || startYear + 1;
        data.end_date = endYear + '-' + String(endMonth).padStart(2, '0') + '-01';
        data.timeline_use_days = !!useDays;
        data.timeline_show_budget = !!document.getElementById('timeline-show-budget')?.checked;

        if (timelineInputs) {
            const saveTasks = [];
            const budgetTimings = {};
            const taskBudgetItems = {};

            timelineInputs.querySelectorAll('.timeline-input-card:not(.budget-timeline-item)').forEach(card => {
                taskBudgetItems[card.dataset.taskId] = [];
            });

            timelineInputs.querySelectorAll('.budget-timeline-item').forEach(sub => {
                    const taskId = sub.dataset.taskId;
                    if (!taskBudgetItems[taskId]) taskBudgetItems[taskId] = [];
                    let itemDuration = parseInt(sub.querySelector('.duration-months').value) || 1;
                    if (useDays) itemDuration = Math.ceil(itemDuration / 30);
                    const itemStartMonth = parseInt(sub.querySelector('.item-start-month')?.value) || startMonth;
                    const itemStartYear = parseInt(sub.querySelector('.item-start-year')?.value) || startYear;
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

            timelineInputs.querySelectorAll('.timeline-input-card:not(.budget-timeline-item)').forEach(card => {
                const taskId = card.dataset.taskId;
                const items = taskBudgetItems[taskId] || [];
                let taskStartMonth = startMonth;
                let taskStartYear = startYear;
                let taskDuration = 1;

                if (items.length > 0) {
                    let minOffset = Infinity, maxEnd = -Infinity;
                    items.forEach(item => {
                        const offset = (item.start_year - startYear) * 12 + (item.start_month - startMonth);
                        const end = offset + item.duration_months;
                        if (offset < minOffset) minOffset = offset;
                        if (end > maxEnd) maxEnd = end;
                    });
                    const absStart = startMonth + minOffset - 1;
                    taskStartMonth = (absStart % 12) + 1;
                    taskStartYear = startYear + Math.floor(absStart / 12);
                    taskDuration = maxEnd - minOffset;
                    if (taskDuration < 1) taskDuration = 1;
                }

                saveTasks.push({
                    id: taskId,
                    name: card.querySelector('.timeline-task-name')?.textContent?.trim() || '',
                    lead_entity: card.querySelector('.lead-entity')?.value || '',
                    start_month: taskStartMonth,
                    start_year: taskStartYear,
                    duration_months: taskDuration,
                    recurring: !!card.querySelector('.task-recurring')?.checked,
                    recurring_interval: parseInt(card.querySelector('.task-recurring-interval')?.value) || 3
                });
            });

            data.tasks = saveTasks;
            data.budget_item_timings = budgetTimings;
        }
    }

    const mapMode = document.getElementById('map-context-mode');
    if (mapMode) {
        const mapUrl = document.getElementById('map-context-url');
        const mapCheckbox = document.getElementById('map-show-in-preview');
        const mapImageUrl = document.getElementById('map-image-url');
        const mapConfig = { mode: mapMode.value };
        if (mapMode.value === 'project_url' && mapUrl) {
            mapUrl.value = normalizeProjectUrl(mapUrl.value);
            mapConfig.url = mapUrl.value;
        } else if (mapMode.value === 'data_url' && mapUrl) {
            mapConfig.url = mapUrl.value.trim();
        }
        if (mapCheckbox) mapConfig.show_in_preview = mapCheckbox.checked;
        if (mapImageUrl) mapConfig.image_url = mapImageUrl.value.trim();
        data.map_config = mapConfig;
    }

    if (Object.keys(data).length > 0) {
        return fetch('/api/proposal/' + proposalId, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    return Promise.resolve();
}

async function switchTab(proposalId, tabName, btn) {
    const routes = {
        scope: '/scope/',
        budget: '/budget/',
        qualifications: '/qualifications/',
        timeline: '/timeline/',
        'custom-sections': '/custom-sections/',
        map: '/map/',
        preview: '/preview/'
    };

    await saveCurrentTabData(proposalId);
    saveTextareaHeights();

    const response = await fetch(routes[tabName] + proposalId + '?t=' + Date.now());
    const html = await response.text();
    document.getElementById('tab-content').innerHTML = html;

    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    document.querySelectorAll('#tab-content [hx-trigger]').forEach(el => {
        htmx.process(el);
    });

    initWordCounts();
    restoreTextareaHeights();

    if (tabName === 'timeline') {
        autoInitGantt();
    }

    if (tabName === 'map') {
        toggleMapUrlInput();
        toggleMapImageField();
    }
}

function exportProposal(proposalId, format) {
    const t = '?t=' + Date.now();
    if (format === 'pdf') {
        window.open('/export/pdf/' + proposalId + t, '_blank');
    } else if (format === 'html') {
        window.open('/export/html/' + proposalId + t, '_blank');
    } else if (format === 'docx') {
        window.open('/export/docx/' + proposalId + t, '_blank');
    }
}

function exportTimelinePng(proposalId) {
    window.open('/export/timeline/png/' + proposalId + '?t=' + Date.now(), '_blank');
}

function loadProposalList() {
    const modal = document.getElementById('proposal-modal');
    const body = document.getElementById('proposal-list-body');
    modal.classList.remove('hidden');

    fetch('/api/proposals')
        .then(r => r.json())
        .then(proposals => {
            if (proposals.length === 0) {
                body.innerHTML = '<p style="text-align:center;color:#64748b;">' + t('No proposals yet.') + '</p>';
                return;
            }
            body.innerHTML = proposals.map(p => `
                <div class="proposal-card" style="margin-bottom:8px;">
                    <h3 style="font-size:14px;">${p.title || t('Untitled')}</h3>
                    <p style="font-size:12px;color:#64748b;">${p.client_name || t('No funder')}${p.subtitle ? ' · ' + p.subtitle : ''} &middot; ${p.updated_at ? p.updated_at.slice(0,10) : ''}</p>
                    <div class="card-actions" style="margin-top:8px;">
                        <a href="/editor/${p.id}" class="btn btn-primary btn-sm">${t('Edit')}</a>
                        <button class="btn btn-danger btn-sm" onclick="deleteProposal('${p.id}')">${t('Delete')}</button>
                    </div>
                </div>
            `).join('');
        });
}

function closeModal() {
    document.getElementById('proposal-modal').classList.add('hidden');
}

function deleteProposal(id) {
    if (!confirm(t('Delete this proposal?'))) return;
    fetch('/api/proposal/' + id, { method: 'DELETE' })
        .then(() => {
            const card = document.querySelector(`[data-proposal-id="${id}"]`);
            if (card) card.remove();
            const currentPath = window.location.pathname;
            if (currentPath.includes(id)) {
                window.location.href = '/';
            } else {
                loadProposalList();
            }
        });
}

function addTask(proposalId) {
    const nameInput = document.getElementById('new-task-name');
    const descInput = document.getElementById('new-task-desc');
    const name = nameInput.value.trim();
    const description = descInput ? descInput.value.trim() : '';
    if (!name) return;

    fetch('/api/task/' + proposalId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, description: description })
    })
    .then(r => r.json())
    .then(task => {
        const taskList = document.getElementById('task-list');
        const card = document.createElement('div');
        card.className = 'task-card';
        card.dataset.taskId = task.id;
        card.innerHTML = `
            <div class="task-header">
                <input type="text" class="task-name-input" value="${task.name}"
                       placeholder="${t('Task name')}"
                       hx-trigger="keyup changed delay:500ms, change"
                       hx-put="/api/proposal/${proposalId}"
                       hx-vals='{"tasks": "JS(getUpdatedTasks())"}'>
                <button class="btn-icon btn-danger-icon"
                        hx-delete="/api/task/${proposalId}/${task.id}"
                        hx-target="closest .task-card"
                        hx-swap="outerHTML"
                        hx-confirm="${t('Remove this task and its budget items?')}">&times;</button>
            </div>
            <textarea class="task-desc-input" rows="2"
                      placeholder="${t('Task description...')}"
                      hx-trigger="keyup changed delay:1000ms, change"
                      hx-put="/api/proposal/${proposalId}"
                      hx-vals='{"tasks": "JS(getUpdatedTasks())"}'>${task.description || ''}</textarea>
        `;
        taskList.appendChild(card);
        htmx.process(card);
        nameInput.value = '';
        if (descInput) descInput.value = '';
        nameInput.focus();
    });
}

function getUpdatedTasks() {
    const cards = document.querySelectorAll('.task-card');
    const tasks = [];
    cards.forEach(card => {
        tasks.push({
            id: card.dataset.taskId,
            name: card.querySelector('.task-name-input').value,
            description: card.querySelector('.task-desc-input').value,
        });
    });
    return tasks;
}

function openSaveAsModal() {
    const modal = document.getElementById('save-as-modal');
    const input = document.getElementById('save-as-title');
    const titleEl = document.getElementById('proposal-title');
    input.value = titleEl ? (titleEl.textContent || '') : '';
    modal.classList.remove('hidden');
    input.focus();
    input.select();
}

function openNewProposalModal() {
    const modal = document.getElementById('new-proposal-modal');
    const input = document.getElementById('new-proposal-title');
    if (!modal) return;
    input.value = '';
    modal.classList.remove('hidden');
    input.focus();
}

function closeNewProposalModal() {
    const modal = document.getElementById('new-proposal-modal');
    if (modal) modal.classList.add('hidden');
}

function createNewProposal() {
    const title = document.getElementById('new-proposal-title').value.trim();
    if (!title) {
        alert(t('Please enter a title.'));
        return;
    }
    fetch('/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title })
    })
    .then(r => r.json())
    .then(data => {
        if (data.id) {
            window.location.href = '/editor/' + data.id;
        } else {
            alert(data.error || t('Failed to save.'));
        }
    });
}

function closeSaveAsModal() {
    document.getElementById('save-as-modal').classList.add('hidden');
}

function openSaveAsTemplateModal() {
    const modal = document.getElementById('save-as-template-modal');
    const nameInput = document.getElementById('template-name');
    const titleEl = document.getElementById('proposal-title');
    nameInput.value = titleEl ? (titleEl.textContent || '') : '';
    modal.classList.remove('hidden');
    nameInput.focus();
    nameInput.select();
}

function closeSaveAsTemplateModal() {
    document.getElementById('save-as-template-modal').classList.add('hidden');
}

function saveProposalAsTemplate() {
    const name = document.getElementById('template-name').value.trim();
    const category = document.getElementById('template-category').value.trim();
    if (!name) {
        alert(t('Please enter a template name.'));
        return;
    }
    const proposalId = window.location.pathname.split('/').pop();
    fetch('/api/proposal/' + proposalId + '/save-as-template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_name: name, template_category: category })
    })
    .then(r => r.json())
    .then(data => {
        if (data.id) {
            closeSaveAsTemplateModal();
            alert(t('Template saved!'));
        } else {
            alert(data.error || t('Failed to save template.'));
        }
    });
}

function saveProposalAs() {
    const title = document.getElementById('save-as-title').value.trim();
    if (!title) {
        alert(t('Please enter a title.'));
        return;
    }

    const proposalId = window.location.pathname.split('/').pop();

    fetch('/api/proposal/' + proposalId + '/save-as', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title })
    })
    .then(r => r.json())
    .then(data => {
        if (data.id) {
            window.location.href = '/editor/' + data.id;
        } else {
            alert(data.error || t('Failed to save.'));
        }
    });
}

function toggleHamburgerMenu() {
    const dd = document.getElementById('hamburger-dropdown');
    const wasHidden = dd.classList.contains('hidden');
    dd.classList.toggle('hidden');
    if (wasHidden) {
        setTimeout(() => {
            document.addEventListener('click', closeHamburgerOnOutsideClick);
        }, 0);
    }
}

function closeHamburger() {
    document.getElementById('hamburger-dropdown').classList.add('hidden');
    document.removeEventListener('click', closeHamburgerOnOutsideClick);
}

function closeHamburgerOnOutsideClick(e) {
    if (!e.target.closest('.hamburger-menu')) {
        closeHamburger();
    }
}

function toggleDarkMode() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('propongo-theme', newTheme);
    updateDarkModeLabel();
}

function updateDarkModeLabel() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const label = document.getElementById('dark-mode-label');
    if (label) label.textContent = isDark ? t('Dark Mode: On') : t('Dark Mode: Off');
}

(function() {
    const saved = localStorage.getItem('propongo-theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    }
    updateDarkModeLabel();
})();

// Custom Sections functions
async function addCustomSection(proposalId) {
    const response = await fetch(`/api/section/${proposalId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title: t('New Section'),
            content: ''
        })
    });
    
    if (response.ok) {
        const btn = document.querySelector('[data-tab="custom-sections"]');
        if (btn) await switchTab(proposalId, 'custom-sections', btn);
    }
}

async function updateSection(proposalId, sectionId) {
    const card = document.querySelector(`[data-section-id="${sectionId}"]`);
    if (!card) return;
    
    const title = card.querySelector('.section-title-input').value;
    const content = card.querySelector('.section-content-input').value;
    
    await fetch(`/api/section/${proposalId}/${sectionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content })
    });
    
    // Update preview
    const preview = card.querySelector('.markdown-preview');
    if (preview) {
        const response = await fetch(`/api/section/${proposalId}/${sectionId}`);
        // Note: You may want to add a GET endpoint for individual sections
        // For now, we'll just reload the tab
    }
}

async function deleteSection(proposalId, sectionId) {
    if (!confirm(t('Delete this section?'))) return;
    
    const response = await fetch(`/api/section/${proposalId}/${sectionId}`, {
        method: 'DELETE'
    });
    
    if (response.ok) {
        const btn = document.querySelector('[data-tab="custom-sections"]');
        if (btn) await switchTab(proposalId, 'custom-sections', btn);
    }
}

async function moveSectionUp(proposalId, sectionId) {
    const sections = Array.from(document.querySelectorAll('.custom-section-card'));
    const currentIndex = sections.findIndex(s => s.dataset.sectionId === sectionId);
    
    if (currentIndex <= 0) return;
    
    const sectionOrder = sections.map(s => s.dataset.sectionId);
    [sectionOrder[currentIndex - 1], sectionOrder[currentIndex]] = 
    [sectionOrder[currentIndex], sectionOrder[currentIndex - 1]];
    
    await fetch(`/api/section/${proposalId}/reorder`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section_order: sectionOrder })
    });
    
    const btn = document.querySelector('[data-tab="custom-sections"]');
    if (btn) await switchTab(proposalId, 'custom-sections', btn);
}

async function moveSectionDown(proposalId, sectionId) {
    const sections = Array.from(document.querySelectorAll('.custom-section-card'));
    const currentIndex = sections.findIndex(s => s.dataset.sectionId === sectionId);
    
    if (currentIndex < 0 || currentIndex >= sections.length - 1) return;
    
    const sectionOrder = sections.map(s => s.dataset.sectionId);
    [sectionOrder[currentIndex], sectionOrder[currentIndex + 1]] = 
    [sectionOrder[currentIndex + 1], sectionOrder[currentIndex]];
    
    await fetch(`/api/section/${proposalId}/reorder`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section_order: sectionOrder })
    });
    
    const btn = document.querySelector('[data-tab="custom-sections"]');
    if (btn) await switchTab(proposalId, 'custom-sections', btn);
}

function openExcelImportModal(proposalId) {
    const modal = document.getElementById('excel-import-modal');
    modal.classList.remove('hidden');
    document.getElementById('excel-section-title').value = '';
    document.getElementById('excel-file-input').value = '';
}

function closeExcelImportModal() {
    document.getElementById('excel-import-modal').classList.add('hidden');
}

async function uploadExcelFile(proposalId) {
    const titleInput = document.getElementById('excel-section-title');
    const fileInput = document.getElementById('excel-file-input');
    
    const title = titleInput.value.trim();
    const file = fileInput.files[0];
    
    if (!file) {
        alert(t('Please select an Excel file.'));
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title || file.name);
    
    try {
        const response = await fetch(`/api/section/${proposalId}/import-excel`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            closeExcelImportModal();
            const btn = document.querySelector('[data-tab="custom-sections"]');
            if (btn) await switchTab(proposalId, 'custom-sections', btn);
        } else {
            alert(result.error || t('Failed to import Excel file.'));
        }
    } catch (error) {
        alert(t('Error importing Excel file: ') + error.message);
    }
}

window.addEventListener('beforeunload', function() {
    const match = window.location.pathname.match(/\/editor\/([^/]+)/);
    if (!match) return;
    const proposalId = match[1];
    const data = {};
    const summaryEl = document.getElementById('project-summary');
    const scopeEl = document.getElementById('project-scope');
    const qualsEl = document.getElementById('qualifications-text');
    const clientEl = document.getElementById('client-name');
    const subtitleEl = document.getElementById('proposal-subtitle');
    if (summaryEl) data.project_summary = summaryEl.value;
    if (scopeEl) data.scope = scopeEl.value;
    if (qualsEl) data.qualifications = qualsEl.value;
    if (clientEl) data.client_name = clientEl.value;
    if (subtitleEl) data.subtitle = subtitleEl.value;

    const indirectEl = document.getElementById('indirect-percent');
    if (indirectEl) data.indirect_percent = parseFloat(indirectEl.value) || 0;

    const budgetDescEl = document.getElementById('budget-description');
    const showBudgetDescEl = document.getElementById('show-budget-description');
    if (showBudgetDescEl) data.show_budget_description = showBudgetDescEl.checked;
    if (budgetDescEl) data.budget_description = budgetDescEl.value;

    const timelineInputs = document.getElementById('timeline-inputs');
    if (document.getElementById('start-month')) {
        const useDays = document.getElementById('timeline-use-days')?.checked;
        const startMonth = parseInt(document.getElementById('start-month')?.value) || 1;
        const startYear = parseInt(document.getElementById('start-year')?.value) || 2025;
        data.start_date = startYear + '-' + String(startMonth).padStart(2, '0') + '-01';
        const endMonth = parseInt(document.getElementById('end-month')?.value) || startMonth;
        const endYear = parseInt(document.getElementById('end-year')?.value) || startYear + 1;
        data.end_date = endYear + '-' + String(endMonth).padStart(2, '0') + '-01';
        data.timeline_use_days = !!useDays;
        data.timeline_show_budget = !!document.getElementById('timeline-show-budget')?.checked;

        if (timelineInputs) {
            const saveTasks = [];
            const budgetTimings = {};
            const taskBudgetItems = {};

            timelineInputs.querySelectorAll('.timeline-input-card:not(.budget-timeline-item)').forEach(card => {
                taskBudgetItems[card.dataset.taskId] = [];
            });

            timelineInputs.querySelectorAll('.budget-timeline-item').forEach(sub => {
                    const taskId = sub.dataset.taskId;
                    if (!taskBudgetItems[taskId]) taskBudgetItems[taskId] = [];
                    let itemDuration = parseInt(sub.querySelector('.duration-months').value) || 1;
                    if (useDays) itemDuration = Math.ceil(itemDuration / 30);
                    const itemStartMonth = parseInt(sub.querySelector('.item-start-month')?.value) || startMonth;
                    const itemStartYear = parseInt(sub.querySelector('.item-start-year')?.value) || startYear;
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

            timelineInputs.querySelectorAll('.timeline-input-card:not(.budget-timeline-item)').forEach(card => {
                const taskId = card.dataset.taskId;
                const items = taskBudgetItems[taskId] || [];
                let taskStartMonth = startMonth;
                let taskStartYear = startYear;
                let taskDuration = 1;

                if (items.length > 0) {
                    let minOffset = Infinity, maxEnd = -Infinity;
                    items.forEach(item => {
                        const offset = (item.start_year - startYear) * 12 + (item.start_month - startMonth);
                        const end = offset + item.duration_months;
                        if (offset < minOffset) minOffset = offset;
                        if (end > maxEnd) maxEnd = end;
                    });
                    const absStart = startMonth + minOffset - 1;
                    taskStartMonth = (absStart % 12) + 1;
                    taskStartYear = startYear + Math.floor(absStart / 12);
                    taskDuration = maxEnd - minOffset;
                    if (taskDuration < 1) taskDuration = 1;
                }

                saveTasks.push({
                    id: taskId,
                    name: card.querySelector('.timeline-task-name')?.textContent?.trim() || '',
                    lead_entity: card.querySelector('.lead-entity')?.value || '',
                    start_month: taskStartMonth,
                    start_year: taskStartYear,
                    duration_months: taskDuration,
                    recurring: !!card.querySelector('.task-recurring')?.checked,
                    recurring_interval: parseInt(card.querySelector('.task-recurring-interval')?.value) || 3
                });
            });

            data.tasks = saveTasks;
            data.budget_item_timings = budgetTimings;
        }
    }

    if (Object.keys(data).length > 0) {
        fetch('/api/proposal/' + proposalId, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
            keepalive: true
        });
    }
});

// Map tab functions
function toggleMapUrlInput() {
    const mode = document.getElementById('map-context-mode');
    const url = document.getElementById('map-context-url');
    if (!mode || !url) return;
    const urlGroup = document.getElementById('map-context-url-group');
    if (mode.value === 'basemap') {
        url.disabled = true;
        if (urlGroup) urlGroup.style.opacity = '0.5';
    } else {
        url.disabled = false;
        if (urlGroup) urlGroup.style.opacity = '1';
    }
}

function normalizeProjectUrl(url) {
    url = url.trim();
    if (url.includes('share.geolibre.app') && !url.endsWith('.geolibre.json')) {
        url = url.replace(/\/+$/, '') + '.geolibre.json';
    }
    return url;
}

function toggleMapImageField() {
    const checkbox = document.getElementById('map-show-in-preview');
    const imageGroup = document.getElementById('map-image-url-group');
    if (!checkbox || !imageGroup) return;
    imageGroup.style.display = checkbox.checked ? '' : 'none';
}

function readMapConfig() {
    const mode = document.getElementById('map-context-mode');
    const url = document.getElementById('map-context-url');
    const checkbox = document.getElementById('map-show-in-preview');
    const imageUrl = document.getElementById('map-image-url');
    const mapConfig = { mode: mode ? mode.value : 'basemap' };
    if (mode && mode.value === 'project_url' && url) {
        url.value = normalizeProjectUrl(url.value);
        mapConfig.url = url.value;
    } else if (mode && mode.value === 'data_url' && url) {
        mapConfig.url = url.value.trim();
    }
    if (checkbox) mapConfig.show_in_preview = checkbox.checked;
    if (imageUrl) mapConfig.image_url = imageUrl.value.trim();
    return mapConfig;
}

async function autosaveMapConfig(proposalId) {
    await fetch(`/api/proposal/${proposalId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ map_config: readMapConfig() })
    });
}

async function saveMapConfig(proposalId) {
    await autosaveMapConfig(proposalId);
    const btn = document.querySelector('[data-tab="map"]');
    if (btn) await switchTab(proposalId, 'map', btn);
}

document.addEventListener('DOMContentLoaded', function() {
    initWordCounts();
    restoreTextareaHeights();

    document.addEventListener('resize', function(e) {
        if (e.target.tagName === 'TEXTAREA' && e.target.id) {
            localStorage.setItem('ta_height_' + e.target.id, e.target.style.height);
        }
    }, true);
});
