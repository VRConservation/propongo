let resultsData = [];
let _editingResultId = null;

function loadResults() {
    fetch('/api/results')
        .then(r => r.json())
        .then(data => {
            resultsData = data;
            populateResultCategories();
            renderResults();
        });
}

function populateResultCategories() {
    const filter = document.getElementById('results-category-filter');
    if (!filter) return;
    const current = filter.value;
    filter.innerHTML = '<option value="">' + t('All categories') + '</option>';
    const cats = [...new Set(resultsData.map(r => r.category).filter(Boolean))].sort();
    cats.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.textContent = c;
        filter.appendChild(opt);
    });
    filter.value = current;
}

function renderResults() {
    const container = document.getElementById('results-cards');
    if (!container) return;

    const search = (document.getElementById('results-search')?.value || '').toLowerCase();
    const cat = document.getElementById('results-category-filter')?.value || '';

    const filtered = resultsData.filter(r => {
        const matchesSearch = !search
            || (r.title || '').toLowerCase().includes(search)
            || (r.evidence || '').toLowerCase().includes(search)
            || (r.source || '').toLowerCase().includes(search);
        const matchesCat = !cat || r.category === cat;
        return matchesSearch && matchesCat;
    });

    let html = '';
    if (filtered.length === 0) {
        html += '<div class="empty-state" style="text-align:center;padding:20px 8px;color:var(--text-muted);">'
            + '<h3 style="margin-bottom:8px;font-size:14px;">' + t('No results yet') + '</h3>'
            + '<p style="font-size:12px;margin-bottom:12px;">' + t('Add your first evidence-based result to build your library.') + '</p>'
            + '<button class="btn btn-primary btn-sm" onclick="openResultModal()">' + t('+ Add Result') + '</button>'
            + '</div>';
    } else {
        filtered.forEach(r => {
            html += resultCardHTML(r);
        });
        html += '<div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);">'
            + '<button class="btn btn-primary btn-sm" style="width:100%" onclick="openResultModal()">' + t('+ Add Result') + '</button>'
            + '</div>';
    }
    container.innerHTML = html;
}

function resultCardHTML(r) {
    const ev = r.evidence || '';
    const preview = ev.substring(0, 90) + (ev.length > 90 ? '...' : '');
    return `
        <div class="snippet-item result-item" onclick="insertResult('${escapeAttr(ev)}')"
             title="${t('Click a result to insert its evidence into the focused field.')}">
            <div class="snippet-title">${escapeHTML(r.title || '')}
                <button class="btn-icon snippet-delete btn-sm"
                        onclick="event.stopPropagation(); openResultModal('${r.id}')"
                        title="${t('Edit')}">&#9998;</button>
                <button class="btn-icon btn-danger-icon snippet-delete btn-sm"
                        onclick="event.stopPropagation(); deleteResult('${r.id}')"
                        title="${t('Delete')}">&times;</button>
            </div>
            ${r.category ? `<span class="result-category">${escapeHTML(r.category)}</span>` : ''}
            <div class="snippet-preview">${escapeHTML(preview)}</div>
            ${r.source ? `<div class="result-source">${escapeHTML(r.source)}</div>` : ''}
        </div>
    `;
}

function openResultModal(id) {
    _editingResultId = id || null;
    const entry = id ? resultsData.find(r => r.id === id) : null;
    document.getElementById('result-modal-title').textContent = entry ? t('Edit') : t('Add Result');
    document.getElementById('result-title').value = entry ? (entry.title || '') : '';
    document.getElementById('result-category').value = entry ? (entry.category || '') : '';
    document.getElementById('result-evidence').value = entry ? (entry.evidence || '') : '';
    document.getElementById('result-source').value = entry ? (entry.source || '') : '';
    document.getElementById('result-modal').classList.remove('hidden');
}

function closeResultModal() {
    document.getElementById('result-modal').classList.add('hidden');
    _editingResultId = null;
}

function saveResult() {
    const title = document.getElementById('result-title').value.trim();
    if (!title) {
        alert(t('Please enter a title.'));
        return;
    }
    const payload = {
        title: title,
        category: document.getElementById('result-category').value.trim(),
        evidence: document.getElementById('result-evidence').value,
        source: document.getElementById('result-source').value.trim(),
    };
    const url = _editingResultId ? '/api/results/' + _editingResultId : '/api/results';
    fetch(url, {
        method: _editingResultId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(() => {
        closeResultModal();
        loadResults();
    });
}

function deleteResult(id) {
    if (!confirm(t('Delete this result?'))) return;
    fetch('/api/results/' + id, { method: 'DELETE' })
        .then(() => loadResults());
}

function insertResult(content) {
    const decoded = content.replace(/\\n/g, '\n').replace(/\\'/g, "'").replace(/\\"/g, '"');

    const field = lastFocusedField;
    if (field && (field.tagName === 'TEXTAREA' || field.tagName === 'INPUT')
        && document.body.contains(field)) {
        const start = field.selectionStart;
        const end = field.selectionEnd;
        const before = field.value.substring(0, start);
        const after = field.value.substring(end);
        field.value = before + decoded + after;
        field.selectionStart = field.selectionEnd = start + decoded.length;
        field.focus();
        field.dispatchEvent(new Event('input', { bubbles: true }));
        field.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
        showToast(t('Evidence inserted!'));
    } else if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(decoded).then(() => {
            showToast(t('Snippet copied to clipboard — paste it where you need it.'));
        });
    } else {
        prompt(t('Copy this snippet:'), decoded);
    }
}
