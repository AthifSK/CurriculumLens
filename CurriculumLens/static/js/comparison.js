/* comparison.js – Two-syllabus comparison page logic */

let _compResult = null;   // cached for heatmap re-render

document.addEventListener('DOMContentLoaded', () => {
    const fileA = document.getElementById('file-a');
    const fileB = document.getElementById('file-b');
    const nameA = document.getElementById('name-a');
    const nameB = document.getElementById('name-b');
    const dropA = document.getElementById('drop-a');
    const dropB = document.getElementById('drop-b');
    const compareBtn = document.getElementById('compare-btn');

    if (typeof setupDropZone === 'function') {
        setupDropZone(dropA, fileA, nameA);
        setupDropZone(dropB, fileB, nameB);
    }

    function checkBothUploaded() {
        const ready = (fileA.files && fileA.files.length > 0) && (fileB.files && fileB.files.length > 0);
        compareBtn.disabled = !ready;
        if (ready) {
            compareBtn.classList.remove('btn-disabled');
        } else {
            compareBtn.classList.add('btn-disabled');
        }
    }

    fileA.addEventListener('change', () => {
        if (fileA.files && fileA.files.length > 0) {
            const f = fileA.files[0];
            const sizeStr = typeof formatFileSize === 'function' && f.size ? ` (${formatFileSize(f.size)})` : '';
            nameA.innerHTML = `<span class="file-badge">📘 <strong>${escHtml(f.name)}</strong>${sizeStr} <span class="badge-ready">✓ Ready</span></span>`;
            dropA.classList.add('has-file');
        } else {
            nameA.textContent = '';
            dropA.classList.remove('has-file');
        }
        document.getElementById('error-compare').style.display = 'none';
        checkBothUploaded();
    });

    fileB.addEventListener('change', () => {
        if (fileB.files && fileB.files.length > 0) {
            const f = fileB.files[0];
            const sizeStr = typeof formatFileSize === 'function' && f.size ? ` (${formatFileSize(f.size)})` : '';
            nameB.innerHTML = `<span class="file-badge">📗 <strong>${escHtml(f.name)}</strong>${sizeStr} <span class="badge-ready">✓ Ready</span></span>`;
            dropB.classList.add('has-file');
        } else {
            nameB.textContent = '';
            dropB.classList.remove('has-file');
        }
        document.getElementById('error-compare').style.display = 'none';
        checkBothUploaded();
    });

    compareBtn.addEventListener('click', runComparison);
});

async function runComparison() {
    const fileA = document.getElementById('file-a');
    const fileB = document.getElementById('file-b');

    if (!fileA.files || !fileA.files.length) {
        showError('Please select Syllabus A (Existing Syllabus).');
        return;
    }
    if (!fileB.files || !fileB.files.length) {
        showError('Please select Syllabus B (Proposed Syllabus).');
        return;
    }

    const validExts = ['.pdf', '.txt', '.docx', '.doc'];
    const validA = validExts.some(ext => fileA.files[0].name.toLowerCase().endsWith(ext));
    const validB = validExts.some(ext => fileB.files[0].name.toLowerCase().endsWith(ext));
    if (!validA || !validB) {
        showError(`Unsupported file format. Please upload ${validExts.join(', ')} files.`);
        return;
    }

    setUI('loading');

    const formData = new FormData();
    formData.append('syllabus_a', fileA.files[0]);
    formData.append('syllabus_b', fileB.files[0]);

    try {
        const resp = await fetch('/api/compare', { method: 'POST', body: formData });
        const json = await resp.json();

        if (!resp.ok || !json.success) {
            showError(json.error || 'Comparison failed. Please verify document formatting.');
            return;
        }

        window._lastComparisonResult = json.result;
        _compResult = json.result;
        displayComparison(json.result);
        setUI('results');

        // Smooth scroll to comparison results
        setTimeout(() => {
            document.getElementById('results-compare')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);

    } catch (e) {
        showError('Network or server error: ' + e.message);
    }
}

function setUI(state) {
    document.getElementById('loading-compare').style.display = state === 'loading' ? 'block' : 'none';
    document.getElementById('results-compare').style.display = state === 'results'  ? 'block' : 'none';
    if (state !== 'error') document.getElementById('error-compare').style.display = 'none';
    document.getElementById('compare-btn').disabled = (state === 'loading');
}

function showError(msg) {
    document.getElementById('loading-compare').style.display = 'none';
    const err = document.getElementById('error-compare');
    err.style.display   = 'block';
    err.textContent     = '⚠ ' + msg;
    document.getElementById('compare-btn').disabled = false;
}

function displayComparison(result) {
    const matching = result.matching || {};
    const summary  = matching.summary || {};

    // Stats
    document.getElementById('stat-topics-a').textContent    = summary.total_topics_a    || '—';
    document.getElementById('stat-topics-b').textContent    = summary.total_topics_b    || '—';
    document.getElementById('stat-matched').textContent     = summary.topics_a_matched  || 0;
    document.getElementById('stat-partial').textContent     = summary.topics_a_partial  || 0;
    document.getElementById('stat-unmatched-a').textContent = summary.topics_a_unmatched || 0;
    document.getElementById('stat-new-b').textContent       = summary.topics_b_unmatched || 0;

    // Overlap percentage badge
    const ovPct = summary.overlap_percentage ?? null;
    const ovEl  = document.getElementById('stat-overlap');
    if (ovEl && ovPct !== null) {
        ovEl.textContent = ovPct + '%';
        ovEl.style.color = ovPct >= 60 ? '#10B981' : ovPct >= 30 ? '#F59E0B' : '#EF4444';
    }

    // ── Percentage Summary ─────────────────────────────────────────
    const totalA = summary.total_topics_a || 1;
    const matched   = summary.topics_a_matched   || 0;
    const partial   = summary.topics_a_partial   || 0;
    const unmatched = summary.topics_a_unmatched || 0;

    const pctMatched   = summary.pct_matched   != null ? summary.pct_matched   : Math.round(100 * matched   / totalA);
    const pctPartial   = summary.pct_partial   != null ? summary.pct_partial   : Math.round(100 * partial   / totalA);
    const pctUnmatched = summary.pct_unmatched != null ? summary.pct_unmatched : Math.round(100 * unmatched / totalA);
    const overlapTotal = summary.overlap_percentage != null ? summary.overlap_percentage : Math.round(100 * (matched + 0.5 * partial) / totalA);

    // Percentage stat cards
    const elPctOv = document.getElementById('stat-pct-overlap');
    if (elPctOv) elPctOv.textContent = overlapTotal + '%';

    const elPctMatch = document.getElementById('stat-pct-matched');
    if (elPctMatch) elPctMatch.textContent = pctMatched + '%';

    const elPctPart = document.getElementById('stat-pct-partial');
    if (elPctPart) elPctPart.textContent = pctPartial + '%';

    const elPctUnmatch = document.getElementById('stat-pct-unmatched');
    if (elPctUnmatch) elPctUnmatch.textContent = pctUnmatched + '%';

    // Percentage Banner Values
    const elValMatched = document.getElementById('pct-matched-val');
    if (elValMatched) elValMatched.textContent = pctMatched + '%';

    const elValPartial = document.getElementById('pct-partial-val');
    if (elValPartial) elValPartial.textContent = pctPartial + '%';

    const elValUnmatched = document.getElementById('pct-unmatched-val');
    if (elValUnmatched) elValUnmatched.textContent = pctUnmatched + '%';

    setTimeout(() => {
        document.getElementById('bar-matched').style.width   = pctMatched   + '%';
        document.getElementById('bar-partial').style.width   = pctPartial   + '%';
        document.getElementById('bar-unmatched').style.width = pctUnmatched + '%';
    }, 200);

    const verdictEl = document.getElementById('pct-verdict');
    if (verdictEl) {
        let verdict, color;
        if (overlapTotal >= 70) {
            verdict = `🟢 High Overlap — ${overlapTotal}% of topics in Syllabus A are covered (fully or partially) in Syllabus B.`;
            color   = '#10B981';
        } else if (overlapTotal >= 40) {
            verdict = `🟡 Moderate Overlap — ${overlapTotal}% of topics in Syllabus A have a match in Syllabus B. ${pctUnmatched}% are unmatched.`;
            color   = '#F59E0B';
        } else {
            verdict = `🔴 Low Overlap — Only ${overlapTotal}% of Syllabus A topics are covered in Syllabus B. ${pctUnmatched}% have no match.`;
            color   = '#EF4444';
        }
        verdictEl.textContent       = verdict;
        verdictEl.style.borderColor = color;
    }

    // Similarity distribution bar chart (topic-level similarity distribution)
    const mCount = summary.topics_a_matched   || 0;
    const pCount = summary.topics_a_partial   || 0;
    const uCount = summary.topics_a_unmatched || 0;
    const simLabels = [
        `Highly Similar (${pctMatched}%)`,
        `Partially Similar (${pctPartial}%)`,
        `Unrelated (${pctUnmatched}%)`
    ];
    if (typeof renderBarChart === 'function') {
        renderBarChart(
            'chart-sim-dist',
            simLabels,
            [mCount, pCount, uCount],
            ['#10B981','#F59E0B','#EF4444'],
            'Topics'
        );
    }

    // Coverage doughnut (Syllabus A)
    if (typeof renderDoughnut === 'function') {
        renderDoughnut(
            'chart-coverage',
            ['Matched', 'Partially Matched', 'Unmatched'],
            [summary.topics_a_matched||0, summary.topics_a_partial||0, summary.topics_a_unmatched||0],
            ['#10B981','#F59E0B','#EF4444']
        );
    }

    // Unit comparison chart
    const unitA = result.unit_distribution_a || {};
    const unitB = result.unit_distribution_b || {};
    const allUnits = [...new Set([...Object.keys(unitA), ...Object.keys(unitB)])];
    if (typeof renderGroupedBar === 'function') {
        renderGroupedBar(
            'chart-unit-compare',
            allUnits,
            allUnits.map(u => unitA[u] || 0),
            allUnits.map(u => unitB[u] || 0),
            result.name_a || 'Syllabus A',
            result.name_b || 'Syllabus B'
        );
    }

    // Heatmap
    renderHeatmap();

    // Matched table
    populateTable('matched-tbody', matching.topics_a_results || [], 'matched');
    populateTable('partial-tbody', matching.topics_a_results || [], 'partially_matched');

    // Unmatched A chips
    buildChips('unmatched-a-list', matching.topics_a_results || [], 'unmatched', false);
    // New B chips
    buildChips('new-b-list', matching.topics_b_results || [], 'unmatched', true);
}

function renderHeatmap() {
    if (!_compResult) return;
    const limit = parseInt(document.getElementById('heatmap-limit')?.value || '20');
    const matching = _compResult.matching || {};
    const pairsAll = matching.classified_pairs || [];

    // Collect topics from the result sets (authoritative order)
    const topicsA = (matching.topics_a_results || []).map(r => r.topic).slice(0, limit);
    const topicsB = (matching.topics_b_results || []).map(r => r.topic).slice(0, limit);

    if (typeof renderHeatmapD3 === 'function') {
        renderHeatmapD3('heatmap-container', pairsAll, topicsA, topicsB, limit);
    }
}
window.renderHeatmap = renderHeatmap;

function populateTable(tbodyId, results, status) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    tbody.innerHTML = '';
    const rows = results.filter(r => r.match_status === status);
    if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#9CA3AF;font-size:.85rem;padding:1.5rem;">No items in this category.</td></tr>';
        return;
    }
    rows.forEach(r => {
        const ta = r.topic;
        const best = r.best_match;
        const tb = best?.topic_b || {};
        const lbl = best?.predicted_label || '—';
        const conf = best?.confidence != null ? (best.confidence * 100).toFixed(1) + '%' : '—';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escHtml(ta.topic_name)}</strong></td>
            <td><small>${escHtml(ta.unit_name)}</small></td>
            <td>${escHtml(tb.topic_name || '—')}</td>
            <td><small>${escHtml(tb.unit_name || '—')}</small></td>
            <td><span class="label-badge label-${lbl}">${escHtml(lbl.replace('_', ' '))}</span></td>
            <td><strong>${conf}</strong></td>
        `;
        tbody.appendChild(tr);
    });
}

function buildChips(containerId, results, status, isNew) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    const items = results.filter(r => r.match_status === status);
    if (!items.length) {
        container.innerHTML = '<p style="color:#9CA3AF;font-size:.85rem;">None found in this category.</p>';
        return;
    }
    items.forEach(r => {
        const topic = r.topic;
        const chip = document.createElement('div');
        chip.className = 'topic-chip';
        chip.innerHTML = `
            <span>${isNew ? '🆕 ' : '❌ '}<strong>${escHtml(topic.topic_name)}</strong></span>
            <span class="chip-unit">${escHtml(topic.unit_name)}</span>
        `;
        container.appendChild(chip);
    });
}
