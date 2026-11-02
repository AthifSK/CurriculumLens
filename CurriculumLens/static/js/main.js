/* main.js – shared utilities for CurriculumLens */

function toggleSection(id) {
    const el = document.getElementById(id);
    const icon = el?.previousElementSibling?.querySelector('.toggle-icon');
    if (el) {
        el.classList.toggle('hidden');
        if (icon) icon.classList.toggle('rotated');
    }
}

// Shared last analysis results for export
window._lastSingleResult = null;
window._lastComparisonResult = null;

function formatFileSize(bytes) {
    if (!bytes && bytes !== 0) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function escHtml(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

async function exportCSV(mode) {
    const result = mode === 'single' ? window._lastSingleResult : window._lastComparisonResult;
    if (!result) { alert('No analysis results to export.'); return; }
    try {
        const resp = await fetch('/api/export/csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, result }),
        });
        if (!resp.ok) { alert('Failed to generate CSV.'); return; }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = mode === 'single' ? 'syllabus_analysis.csv' : 'curriculum_comparison.csv';
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) { alert('Export failed: ' + e.message); }
}

async function exportPDF(mode) {
    const result = mode === 'single' ? window._lastSingleResult : window._lastComparisonResult;
    if (!result) { alert('No analysis results to export.'); return; }
    try {
        const resp = await fetch('/api/export/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, result }),
        });
        if (!resp.ok) { alert('Failed to generate PDF.'); return; }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = mode === 'single' ? 'syllabus_analysis.pdf' : 'curriculum_comparison.pdf';
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) { alert('Export failed: ' + e.message); }
}

// Drag-and-drop & Click-to-upload helper
function setupDropZone(dropEl, inputEl, nameEl) {
    if (!dropEl || !inputEl) return;

    // Drag-over styling
    dropEl.addEventListener('dragover', e => {
        e.preventDefault();
        dropEl.classList.add('drag-over');
    });

    dropEl.addEventListener('dragleave', e => {
        dropEl.classList.remove('drag-over');
    });

    // Drop handler
    dropEl.addEventListener('drop', e => {
        e.preventDefault();
        dropEl.classList.remove('drag-over');
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            try {
                inputEl.files = e.dataTransfer.files;
            } catch (err) {
                try {
                    const dt = new DataTransfer();
                    dt.items.add(e.dataTransfer.files[0]);
                    inputEl.files = dt.files;
                } catch (e2) {}
            }
            inputEl.dispatchEvent(new Event('change', { bubbles: true }));
        }
    });

    // Clicking anywhere on the drop zone opens file picker
    dropEl.addEventListener('click', e => {
        if (e.target !== inputEl && !e.target.closest('label') && !e.target.closest('button')) {
            inputEl.click();
        }
    });
}
