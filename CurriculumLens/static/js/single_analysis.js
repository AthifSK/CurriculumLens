/* single_analysis.js – Single syllabus analysis page logic */

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('syllabus-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    const nameEl = document.getElementById('selected-file-name');
    const dropZone = document.getElementById('drop-zone-single');

    if (typeof setupDropZone === 'function') {
        setupDropZone(dropZone, fileInput, nameEl);
    }

    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files.length > 0) {
            const f = fileInput.files[0];
            const sizeStr = typeof formatFileSize === 'function' && f.size ? ` (${formatFileSize(f.size)})` : '';
            nameEl.innerHTML = `<span class="file-badge">📄 <strong>${escHtml(f.name)}</strong>${sizeStr} <span class="badge-ready">✓ Ready</span></span>`;
            dropZone.classList.add('has-file');
            analyzeBtn.disabled = false;
            analyzeBtn.classList.remove('btn-disabled');
            document.getElementById('error-single').style.display = 'none';
        } else {
            nameEl.textContent = '';
            dropZone.classList.remove('has-file');
            analyzeBtn.disabled = true;
            analyzeBtn.classList.add('btn-disabled');
        }
    });

    analyzeBtn.addEventListener('click', runAnalysis);
});

async function runAnalysis() {
    const fileInput = document.getElementById('syllabus-file');
    if (!fileInput.files || !fileInput.files.length) {
        showError('Please choose a syllabus file first.');
        return;
    }

    const file = fileInput.files[0];
    const validExts = ['.pdf', '.txt', '.docx', '.doc'];
    const hasValidExt = validExts.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!hasValidExt) {
        showError(`Unsupported file format. Please upload a ${validExts.join(', ')} file.`);
        return;
    }

    setUI('loading');

    const formData = new FormData();
    formData.append('syllabus', file);

    try {
        const resp = await fetch('/api/analyze-single', { method: 'POST', body: formData });
        const json = await resp.json();

        if (!resp.ok || !json.success) {
            showError(json.error || 'Analysis failed. Please check the document format.');
            return;
        }

        window._lastSingleResult = json.result;
        displayResults(json.result);
        setUI('results');

        setTimeout(() => {
            document.getElementById('results-single')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);

    } catch (e) {
        showError('Network or server error: ' + e.message);
    }
}

function setUI(state) {
    const loading = document.getElementById('loading-single');
    const results = document.getElementById('results-single');
    const error   = document.getElementById('error-single');
    const btn     = document.getElementById('analyze-btn');

    loading.style.display = state === 'loading' ? 'block' : 'none';
    results.style.display = state === 'results' ? 'block' : 'none';
    if (state !== 'error') error.style.display = 'none';
    btn.disabled = (state === 'loading');
}

function showError(msg) {
    const loading = document.getElementById('loading-single');
    const error   = document.getElementById('error-single');
    const btn     = document.getElementById('analyze-btn');

    loading.style.display = 'none';
    error.style.display   = 'block';
    error.textContent     = '⚠ ' + msg;
    btn.disabled          = false;
}

function displayResults(result) {
    // ── High-Level Percentage Stat Cards ───────────────────────────
    const elCoherence = document.getElementById('stat-pct-coherence');
    if (elCoherence) elCoherence.textContent = (result.coherence_percentage ?? '—') + '%';

    const elConnected = document.getElementById('stat-pct-connected');
    if (elConnected) elConnected.textContent = (result.pct_connected ?? '—') + '%';

    const elCross = document.getElementById('stat-pct-cross');
    if (elCross) elCross.textContent = (result.pct_cross_unit ?? '—') + '%';

    const elStandalone = document.getElementById('stat-pct-standalone');
    if (elStandalone) elStandalone.textContent = (result.pct_standalone ?? '—') + '%';

    // ── Topic Details Counts ───────────────────────────────────────
    document.getElementById('stat-topics').textContent = result.total_topics || '—';
    document.getElementById('stat-units').textContent  = result.total_units  || '—';
    document.getElementById('stat-avg').textContent    = result.avg_topics_per_unit || '—';

    const elConnCount = document.getElementById('stat-conn-count');
    if (elConnCount) elConnCount.textContent = (result.connected_count || 0) + (result.partial_count ? ` (+${result.partial_count})` : '');

    // ── Animated Percentage Progress Bars ──────────────────────────
    const pctConn = result.pct_connected || 0;
    const pctCross = result.pct_cross_unit || 0;
    const pctStand = result.pct_standalone || 0;
    const coherence = result.coherence_percentage || 0;

    const elValConn = document.getElementById('pct-connected-val');
    if (elValConn) elValConn.textContent = pctConn + '%';

    const elValCross = document.getElementById('pct-cross-val');
    if (elValCross) elValCross.textContent = pctCross + '%';

    const elValStand = document.getElementById('pct-standalone-val');
    if (elValStand) elValStand.textContent = pctStand + '%';

    setTimeout(() => {
        const barConn = document.getElementById('bar-connected');
        if (barConn) barConn.style.width = pctConn + '%';

        const barCross = document.getElementById('bar-cross');
        if (barCross) barCross.style.width = pctCross + '%';

        const barStand = document.getElementById('bar-standalone');
        if (barStand) barStand.style.width = pctStand + '%';
    }, 200);

    // Dynamic Verdict Banner
    const verdictEl = document.getElementById('pct-verdict');
    if (verdictEl) {
        let verdict, color;
        if (coherence >= 65) {
            verdict = `🟢 High Curriculum Coherence (${coherence}%) — The syllabus exhibits strong conceptual flow and reinforcement across topics.`;
            color = '#10B981';
        } else if (coherence >= 40) {
            verdict = `🟡 Balanced Curriculum Structure (${coherence}%) — Well-integrated core topics with ${pctStand}% specialized standalone concepts.`;
            color = '#F59E0B';
        } else {
            verdict = `🔵 Modular Course Design (${coherence}%) — Topics are organized into distinct, specialized modules with minimal inter-topic dependency.`;
            color = '#3B82F6';
        }
        verdictEl.textContent = verdict;
        verdictEl.style.borderColor = color;
    }

    // ── Unit Distribution Bar Chart ────────────────────────────────
    const unitDist = result.unit_distribution || {};
    const unitLabels = Object.keys(unitDist);
    const unitValues = unitLabels.map(k => unitDist[k]);
    if (typeof renderBarChart === 'function') {
        renderBarChart('chart-unit-dist', unitLabels, unitValues, null, 'Topics per Unit');
    }

    // ── Topic Connectivity Doughnut Chart ──────────────────────────
    if (typeof renderDoughnut === 'function') {
        const connLabels = ['Strong Linkage', 'Moderate Linkage', 'Standalone / Focused'];
        const connValues = [result.connected_count || 0, result.partial_count || 0, result.standalone_count || 0];
        const connColors = ['#10B981', '#F59E0B', '#3B82F6'];
        renderDoughnut('chart-connectivity-dist', connLabels, connValues, connColors);
    }

    // ── Text Preview ───────────────────────────────────────────────
    const previewEl = document.getElementById('text-preview');
    if (previewEl) previewEl.textContent = result.extracted_text_preview || '';

    // ── Enhanced Topic Inventory Table ─────────────────────────────
    const tbody = document.getElementById('topic-tbody');
    tbody.innerHTML = '';
    (result.topics || []).forEach(t => {
        const tr = document.createElement('tr');
        const level = t.relation_level || 'standalone';
        const levelBadge = level === 'strong'
            ? `<span class="label-badge label-highly_similar">Strong Link</span>`
            : level === 'moderate'
            ? `<span class="label-badge label-partially_similar">Moderate Link</span>`
            : `<span class="label-badge" style="background:#EBF5FF;color:#1E40AF;">Independent</span>`;

        const crossBadge = t.is_cross_unit
            ? `<span style="background:#F5F3FF;color:#6D28D9;padding:3px 8px;border-radius:12px;font-size:.75rem;font-weight:600;">Cross-Unit</span>`
            : `<span style="color:#9CA3AF;font-size:.8rem;">Within Unit</span>`;

        const relText = t.best_related_topic && t.best_related_topic !== '—'
            ? `<strong>${escHtml(t.best_related_topic)}</strong> <br/><small style="color:#6B7280;">(${escHtml(t.best_related_unit || '')})</small>`
            : `<span style="color:#9CA3AF;">None</span>`;

        tr.innerHTML = `
            <td>${t.topic_index}</td>
            <td><small><strong>${escHtml(t.unit_name)}</strong></small></td>
            <td><strong>${escHtml(t.topic_name)}</strong></td>
            <td>${relText}</td>
            <td>${levelBadge}</td>
            <td>${crossBadge}</td>
        `;
        tbody.appendChild(tr);
    });

    // Topic search filter
    const searchInput = document.getElementById('topic-search');
    if (searchInput) {
        searchInput.value = '';
        searchInput.oninput = () => {
            const q = searchInput.value.toLowerCase();
            tbody.querySelectorAll('tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        };
    }
}
