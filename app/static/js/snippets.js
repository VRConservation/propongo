document.addEventListener('DOMContentLoaded', loadSnippets);

let lastFocusedField = null;
let currentSnippets = {};

const CATEGORY_LABELS = { organization: 'Organization', deliverables: 'Deliverables', custom: 'Custom' };

function categoryLabel(category) {
    const known = Object.keys(CATEGORY_LABELS).find(k => k === String(category).toLowerCase());
    return known ? t(CATEGORY_LABELS[known]) : category;
}

function sortCategories(categories) {
    const known = ['organization', 'deliverables', 'custom'].filter(c => categories.includes(c));
    const extra = categories
        .filter(c => !known.includes(c))
        .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
    return known.concat(extra);
}

document.addEventListener('focusin', function(e) {
    if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') {
        lastFocusedField = e.target;
    }
});

function loadSnippets() {
    fetch('/snippets')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('snippet-list');
            if (!container) return;

            currentSnippets = {};
            const groups = {};
            ['organization', 'deliverables', 'custom'].forEach(source => {
                (data[source] || []).forEach(s => {
                    s.source = source;
                    currentSnippets[s.id] = s;
                    const cat = s.category || 'custom';
                    (groups[cat] = groups[cat] || []).push(s);
                });
            });

            let html = '<datalist id="snippet-category-options">';
            sortCategories(Object.keys(groups)).forEach(cat => {
                html += `<option value="${escapeHTML(cat)}">`;
            });
            html += '</datalist>';

            sortCategories(Object.keys(groups)).forEach(cat => {
                html += '<div class="snippet-category"><h4>' + escapeHTML(categoryLabel(cat)) + '</h4>';
                groups[cat].forEach(s => {
                    html += snippetHTML(s);
                });
                html += '</div>';
            });

            if (!Object.keys(currentSnippets).length) {
                html += '<p class="snippet-loading">' + t('No snippets yet. Add one below.') + '</p>';
            }

            html += `
                <div class="snippet-add-form">
                    <h4 style="margin-bottom:8px;font-size:13px;">${t('Add Custom Snippet')}</h4>
                    <input type="text" id="new-snippet-title" placeholder="${t('Title')}">
                    <textarea id="new-snippet-content" rows="3" placeholder="${t('Markdown content...')}"></textarea>
                    <input type="text" id="new-snippet-category" list="snippet-category-options" placeholder="${t('Category')}">
                    <button class="btn btn-primary btn-sm" onclick="addCustomSnippet()" style="width:100%">${t('Add Snippet')}</button>
                </div>
                <div class="snippet-add-form" style="margin-top:12px;border-top:1px solid var(--border);padding-top:12px;">
                    <h4 style="margin-bottom:8px;font-size:13px;">${t('Import from File')}</h4>
                    <p style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">${t('Supports .md, .txt, and .docx files')}</p>
                    <input type="file" id="import-file-input" accept=".md,.markdown,.txt,.docx" style="display:none" onchange="importSnippetFile()">
                    <button class="btn btn-secondary btn-sm" onclick="document.getElementById('import-file-input').click()" style="width:100%">${t('Choose File to Import')}</button>
                </div>
            `;

            container.innerHTML = html;
        })
        .catch(() => {
            const container = document.getElementById('snippet-list');
            if (container) {
                container.innerHTML = '<p class="snippet-loading">' + t('Failed to load snippets.') + '</p>';
            }
        });
}

function snippetHTML(snippet) {
    const preview = snippet.content ? snippet.content.substring(0, 80) + (snippet.content.length > 80 ? '...' : '') : '';
    return `
        <div class="snippet-item" data-snippet-id="${escapeHTML(snippet.id)}" onclick="insertSnippet('${escapeAttr(snippet.content)}')">
            <div class="snippet-title">${escapeHTML(snippet.title)}
                <button class="btn-icon btn-danger-icon snippet-delete btn-sm"
                        onclick="event.stopPropagation(); deleteSnippet('${snippet.source}', '${snippet.id}')">&times;</button>
                <button class="btn-icon snippet-edit-btn btn-sm"
                        onclick="event.stopPropagation(); editSnippet('${snippet.id}')">&#9998;</button>
            </div>
            <div class="snippet-preview">${escapeHTML(preview)}</div>
        </div>
    `;
}

function editSnippet(id) {
    const s = currentSnippets[id];
    if (!s) return;
    const card = document.querySelector(`.snippet-item[data-snippet-id="${CSS.escape(id)}"]`);
    if (!card) return;

    card.onclick = null;
    card.innerHTML = `
        <div class="snippet-edit-form">
            <input type="text" id="edit-snippet-title" value="${escapeHTML(s.title)}" placeholder="${t('Title')}">
            <input type="text" id="edit-snippet-category" list="snippet-category-options" value="${escapeHTML(s.category || '')}" placeholder="${t('Category')}">
            <textarea id="edit-snippet-content" rows="5" placeholder="${t('Markdown content...')}">${escapeHTML(s.content)}</textarea>
            <div class="snippet-edit-actions">
                <button class="btn btn-primary btn-sm" onclick="saveSnippet('${id}')">${t('Save')}</button>
                <button class="btn btn-secondary btn-sm" onclick="loadSnippets()">${t('Cancel')}</button>
            </div>
        </div>
    `;
    document.getElementById('edit-snippet-title').focus();
}

function saveSnippet(id) {
    const s = currentSnippets[id];
    if (!s) return;
    const title = document.getElementById('edit-snippet-title').value.trim();
    const content = document.getElementById('edit-snippet-content').value.trim();
    const category = document.getElementById('edit-snippet-category').value.trim() || 'custom';
    if (!title || !content) {
        alert(t('Enter a title and content.'));
        return;
    }

    fetch(`/snippets/${s.source}/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content, category })
    })
    .then(r => r.json().then(data => ({ ok: r.ok, data })))
    .then(({ ok, data }) => {
        if (!ok) {
            alert(data.error || t('Failed to update snippet.'));
            return;
        }
        showToast(t('Snippet updated!'));
        loadSnippets();
    });
}

function insertSnippet(content) {
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
        showToast(t('Snippet inserted!'));
    } else if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(decoded).then(() => {
            showToast(t('Snippet copied to clipboard — paste it where you need it.'));
        }).catch(() => {
            prompt(t('Copy this snippet:'), decoded);
        });
    } else {
        prompt(t('Copy this snippet:'), decoded);
    }
}

function showToast(message) {
    let toast = document.getElementById('snippet-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'snippet-toast';
        toast.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#1e293b;color:#fff;padding:10px 18px;border-radius:6px;font-size:13px;z-index:9999;transition:opacity 0.3s;box-shadow:0 2px 8px rgba(0,0,0,0.2);';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = '1';
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => { toast.style.opacity = '0'; }, 2500);
}

function addCustomSnippet() {
    const title = document.getElementById('new-snippet-title').value.trim();
    const content = document.getElementById('new-snippet-content').value.trim();
    const category = document.getElementById('new-snippet-category').value.trim() || 'custom';
    if (!title || !content) {
        alert(t('Enter a title and content.'));
        return;
    }

    fetch('/snippets/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content, category })
    })
    .then(() => {
        document.getElementById('new-snippet-title').value = '';
        document.getElementById('new-snippet-content').value = '';
        document.getElementById('new-snippet-category').value = '';
        loadSnippets();
    });
}

function deleteSnippet(category, id) {
    if (!confirm(t('Delete this snippet?'))) return;
    fetch(`/snippets/${category}/${id}`, { method: 'DELETE' })
        .then(() => loadSnippets());
}

function importSnippetFile() {
    const input = document.getElementById('import-file-input');
    const file = input.files[0];
    if (!file) return;

    const title = prompt(t('Snippet title:'), file.name.replace(/\.[^.]+$/, ''));
    if (title === null) {
        input.value = '';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title.trim() || file.name.replace(/\.[^.]+$/, ''));

    fetch('/snippets/import', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        input.value = '';
        if (data.error) {
            alert(data.error);
        } else {
            loadSnippets();
        }
    });
}

function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeAttr(str) {
    if (!str) return '';
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
}
