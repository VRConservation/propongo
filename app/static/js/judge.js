const JUDGE_TAB_FOR_SECTION = { scope: 'scope', qualifications: 'qualifications' };

function judgeTabName(sectionKey) {
    return JUDGE_TAB_FOR_SECTION[sectionKey] || 'custom-sections';
}

async function scoreSection(proposalId, sectionKey, btn) {
    const select = document.getElementById(`judge-model-${sectionKey}`);
    const model = select ? select.value : 'ollama';

    const originalLabel = btn.textContent;
    btn.disabled = true;
    btn.textContent = t('Scoring…');

    try {
        const resp = await fetch(`/api/section/${proposalId}/${sectionKey}/score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model })
        });
        const data = await resp.json();
        if (!resp.ok) {
            alert(data.error || t('Scoring failed.'));
            return;
        }
        const tabName = judgeTabName(sectionKey);
        const tabBtn = document.querySelector(`[data-tab="${tabName}"]`);
        if (tabBtn) await switchTab(proposalId, tabName, tabBtn);
    } finally {
        btn.disabled = false;
        btn.textContent = originalLabel;
    }
}

async function sha256Hex(text) {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
    return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function judgeCheckStale(widget) {
    const result = widget.querySelector('.judge-result');
    const staleNote = widget.querySelector('.judge-stale-note');
    if (!result || !staleNote) return;
    const scoredHash = result.dataset.contentHash;
    if (!scoredHash) return;

    const contentEl = document.getElementById(widget.dataset.contentEl);
    if (!contentEl) return;

    const currentHash = await sha256Hex(contentEl.value);
    staleNote.style.display = currentHash === scoredHash ? 'none' : '';
}

document.addEventListener('input', (e) => {
    if (!e.target.id) return;
    document.querySelectorAll('.judge-widget').forEach((widget) => {
        if (widget.dataset.contentEl === e.target.id) {
            judgeCheckStale(widget);
        }
    });
});
