/* charts.js – Chart.js and D3.js visualization utilities */

const COLORS = {
    highly_similar:   '#10B981',
    partially_similar:'#F59E0B',
    unrelated:        '#EF4444',
    blue:  '#3B82F6',
    teal:  '#14B8A6',
    purple:'#8B5CF6',
};

const PALETTE = [
    '#3B82F6','#10B981','#F59E0B','#8B5CF6','#EF4444',
    '#14B8A6','#F97316','#06B6D4','#84CC16','#EC4899',
];

// ── Bar chart helper ──────────────────────────────────────────────────
function renderBarChart(canvasId, labels, values, colorArr, title) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    if (ctx._chartInstance) { ctx._chartInstance.destroy(); }
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: title || '',
                data: values,
                backgroundColor: colorArr || labels.map((_, i) => PALETTE[i % PALETTE.length]),
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const dataArr = ctx.dataset.data || [];
                            const total = dataArr.reduce((a, b) => a + b, 0);
                            const val = ctx.raw || 0;
                            const pctStr = total > 0 ? ` (${((val / total) * 100).toFixed(1)}%)` : '';
                            return ` ${ctx.formattedValue} topics${pctStr}`;
                        }
                    }
                }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: '#F3F4F6' } },
                x: { grid: { display: false }, ticks: { maxRotation: 40, font: { size: 11 } } }
            }
        }
    });
    ctx._chartInstance = chart;
    return chart;
}

// ── Doughnut / Pie helper ─────────────────────────────────────────────
function renderDoughnut(canvasId, labels, values, colors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    if (ctx._chartInstance) { ctx._chartInstance.destroy(); }
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors || labels.map((_, i) => PALETTE[i % PALETTE.length]),
                borderWidth: 2,
                borderColor: '#fff',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 12 } },
                tooltip: { callbacks: { label: c => ` ${c.label}: ${c.formattedValue}` } }
            },
            cutout: '60%',
        }
    });
    ctx._chartInstance = chart;
    return chart;
}

// ── Grouped bar chart for unit comparison ─────────────────────────────
function renderGroupedBar(canvasId, labels, datasetA, datasetB, labelA, labelB) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    if (ctx._chartInstance) { ctx._chartInstance.destroy(); }
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: labelA || 'Syllabus A',
                    data: datasetA,
                    backgroundColor: 'rgba(59,130,246,0.75)',
                    borderRadius: 5,
                },
                {
                    label: labelB || 'Syllabus B',
                    data: datasetB,
                    backgroundColor: 'rgba(16,185,129,0.75)',
                    borderRadius: 5,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
            },
            scales: {
                y: { beginAtZero: true, grid: { color: '#F3F4F6' } },
                x: { grid: { display: false }, ticks: { maxRotation: 45, font: { size: 10 } } }
            }
        }
    });
    ctx._chartInstance = chart;
    return chart;
}

// ── Confusion Matrix ──────────────────────────────────────────────────
function renderConfusionMatrix(canvasId, matrix, labels) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    if (ctx._chartInstance) { ctx._chartInstance.destroy(); }

    const n = labels.length;
    const flatData = [];
    const flatLabels = [];

    // Build dataset for Chart.js scatter-style matrix
    const datasets = [];
    const colors = { 0: 'rgba(59,130,246,', 1: 'rgba(59,130,246,', 2: 'rgba(59,130,246,' };
    const data = [];
    const bgColors = [];

    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            const val = matrix[r][c];
            const maxVal = Math.max(...matrix.flat());
            const opacity = maxVal ? 0.15 + 0.75 * (val / maxVal) : 0.15;
            data.push({ x: c, y: n - 1 - r, v: val });
            bgColors.push(`rgba(59,130,246,${opacity})`);
        }
    }

    const chart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                data,
                backgroundColor: bgColors,
                pointStyle: 'rect',
                pointRadius: 30,
                borderWidth: 1,
                borderColor: 'rgba(255,255,255,0.5)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const pt = ctx.raw;
                            const actual = labels[n - 1 - pt.y];
                            const predicted = labels[pt.x];
                            return `Actual: ${actual} | Predicted: ${predicted} | Count: ${pt.v}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    min: -0.5, max: n - 0.5,
                    ticks: {
                        stepSize: 1,
                        callback: val => labels[val] ? labels[val].replace('_', ' ') : '',
                        font: { size: 10 },
                    },
                    title: { display: true, text: 'Predicted', font: { size: 12, weight: 'bold' } },
                    grid: { display: false }
                },
                y: {
                    type: 'linear',
                    min: -0.5, max: n - 0.5,
                    ticks: {
                        stepSize: 1,
                        callback: val => labels[n - 1 - val] ? labels[n - 1 - val].replace('_', ' ') : '',
                        font: { size: 10 },
                    },
                    title: { display: true, text: 'Actual', font: { size: 12, weight: 'bold' } },
                    grid: { display: false }
                }
            }
        },
        plugins: [{
            id: 'cmLabels',
            afterDraw(chart) {
                const { ctx: c, scales: { x, y } } = chart;
                chart.data.datasets[0].data.forEach(pt => {
                    const px = x.getPixelForValue(pt.x);
                    const py = y.getPixelForValue(pt.y);
                    c.fillStyle = '#1E3A5F';
                    c.font = 'bold 14px Segoe UI, sans-serif';
                    c.textAlign = 'center';
                    c.textBaseline = 'middle';
                    c.fillText(pt.v, px, py);
                });
            }
        }]
    });
    ctx._chartInstance = chart;
}

// ── D3 Force-Directed Topic Graph ─────────────────────────────────────
function renderTopicGraph(containerId, topics, edges) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    const W = container.clientWidth || 700;
    const H = 480;

    const clusterColors = PALETTE;

    const svg = d3.select('#' + containerId).append('svg')
        .attr('width', '100%').attr('height', H)
        .attr('viewBox', `0 0 ${W} ${H}`);

    // Arrow marker
    svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '-0 -5 10 10')
        .attr('refX', 16).attr('refY', 0)
        .attr('orient', 'auto').attr('markerWidth', 6).attr('markerHeight', 6)
        .append('path').attr('d', 'M 0,-5 L 10,0 L 0,5').attr('fill', '#CBD5E1');

    const simulation = d3.forceSimulation(topics)
        .force('link', d3.forceLink(edges).id(d => d.topic_index).distance(d => 120 - d.score * 60).strength(0.3))
        .force('charge', d3.forceManyBody().strength(-120))
        .force('center', d3.forceCenter(W / 2, H / 2))
        .force('collision', d3.forceCollide(28));

    const link = svg.append('g').selectAll('line').data(edges).join('line')
        .attr('stroke', '#CBD5E1').attr('stroke-width', d => 1 + d.score * 2)
        .attr('stroke-opacity', 0.6);

    // Tooltip
    const tooltip = d3.select('body').append('div').attr('class', 'graph-tooltip').style('opacity', 0);

    const node = svg.append('g').selectAll('g').data(topics).join('g')
        .call(d3.drag()
            .on('start', (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
            .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
            .on('end', (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

    node.append('circle')
        .attr('r', 12)
        .attr('fill', d => clusterColors[(d.cluster || 0) % clusterColors.length])
        .attr('stroke', '#fff').attr('stroke-width', 2)
        .attr('opacity', 0.85);

    node.append('text')
        .attr('dy', 22).attr('text-anchor', 'middle')
        .attr('font-size', '8px').attr('fill', '#374151')
        .text(d => d.topic_name ? d.topic_name.slice(0, 20) : '');

    node.on('mouseover', (event, d) => {
        tooltip.transition().duration(150).style('opacity', .95);
        tooltip.html(`<strong>${d.topic_name || ''}</strong><br/>Unit: ${d.unit_name || ''}<br/>Cluster: ${d.cluster ?? '—'}`)
            .style('left', (event.clientX + 12) + 'px').style('top', (event.clientY - 28) + 'px');
    }).on('mouseout', () => tooltip.transition().duration(200).style('opacity', 0));

    simulation.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('transform', d => `translate(${Math.max(15, Math.min(W-15, d.x))},${Math.max(15, Math.min(H-15, d.y))})`);
    });

    return simulation;
}

// ── D3 Heatmap ────────────────────────────────────────────────────────
function renderHeatmapD3(containerId, classifiedPairs, topicsA, topicsB, limit) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    const sliceA = topicsA.slice(0, limit);
    const sliceB = topicsB.slice(0, limit);

    if (!sliceA.length || !sliceB.length) {
        container.innerHTML = '<p style="color:#9CA3AF;text-align:center;padding:2rem;">Not enough topics to render heatmap.</p>';
        return;
    }

    // Build lookup: {aIdx -> {bIdx -> pair}}
    const pairMap = {};
    classifiedPairs.forEach(p => {
        const ai = p.topic_a.topic_index;
        const bi = p.topic_b.topic_index;
        if (!pairMap[ai]) pairMap[ai] = {};
        pairMap[ai][bi] = p;
    });

    // For cells with no classified pair, show a grey "not evaluated" cell
    const colorScale = lbl =>
        lbl === 'highly_similar'   ? '#10B981' :
        lbl === 'partially_similar'? '#F59E0B' :
        lbl === 'unrelated'        ? '#EF4444' : '#D1D5DB';

    const cellSize = Math.max(22, Math.min(36, Math.floor(560 / Math.max(sliceB.length, sliceA.length))));
    const margin = { top: 150, right: 30, bottom: 20, left: 200 };
    const W = margin.left + sliceB.length * cellSize + margin.right;
    const H = margin.top  + sliceA.length * cellSize + margin.bottom;

    const svg = d3.select('#' + containerId).append('svg')
        .attr('width',   Math.max(W, 500))
        .attr('height',  H)
        .style('overflow', 'visible');

    const tooltip = d3.select('body').select('.hm-tooltip').node()
        ? d3.select('.hm-tooltip')
        : d3.select('body').append('div').attr('class', 'hm-tooltip').style('opacity', 0);

    // Column labels (Syllabus B) – rotated
    svg.append('g').selectAll('text').data(sliceB).join('text')
        .attr('x', (_, i) => margin.left + i * cellSize + cellSize / 2)
        .attr('y', margin.top - 10)
        .attr('transform', (_, i) => `rotate(-45, ${margin.left + i * cellSize + cellSize / 2}, ${margin.top - 10})`)
        .attr('text-anchor', 'start')
        .attr('font-size', '9px')
        .attr('fill', '#374151')
        .text(d => d.topic_name ? d.topic_name.slice(0, 20) : '');

    // Row labels (Syllabus A)
    svg.append('g').selectAll('text').data(sliceA).join('text')
        .attr('x', margin.left - 8)
        .attr('y', (_, i) => margin.top + i * cellSize + cellSize / 2)
        .attr('text-anchor', 'end')
        .attr('dominant-baseline', 'middle')
        .attr('font-size', '9px')
        .attr('fill', '#374151')
        .text(d => d.topic_name ? d.topic_name.slice(0, 26) : '');

    // Cells – draw every A×B cell
    sliceA.forEach((ta, ri) => {
        sliceB.forEach((tb, ci) => {
            const pair = pairMap[ta.topic_index]?.[tb.topic_index];
            const lbl  = pair?.predicted_label ?? 'none';
            const conf = pair?.confidence;
            const hasData = !!pair;

            const opacity = hasData
                ? (lbl === 'unrelated' ? 0.55 : 0.85)
                : 0.18;

            svg.append('rect')
                .attr('class', 'hm-cell')
                .attr('x',      margin.left + ci * cellSize)
                .attr('y',      margin.top  + ri * cellSize)
                .attr('width',  cellSize - 2)
                .attr('height', cellSize - 2)
                .attr('rx', 3)
                .attr('fill',    colorScale(lbl))
                .attr('opacity', opacity)
                .attr('stroke',  hasData ? 'rgba(255,255,255,0.4)' : 'none')
                .attr('stroke-width', 1)
                .on('mouseover', event => {
                    tooltip.style('opacity', .97)
                        .html(
                            `<strong>A:</strong> ${ta.topic_name}<br/>` +
                            `<strong>B:</strong> ${tb.topic_name}<br/>` +
                            `<strong>Label:</strong> ${hasData ? lbl.replace('_',' ') : 'Not evaluated'}<br/>` +
                            `<strong>Confidence:</strong> ${conf != null ? (conf*100).toFixed(1)+'%' : '—'}`
                        )
                        .style('left', (event.clientX + 14) + 'px')
                        .style('top',  (event.clientY - 40) + 'px');
                })
                .on('mousemove', event => {
                    tooltip.style('left', (event.clientX + 14) + 'px').style('top', (event.clientY - 40) + 'px');
                })
                .on('mouseout', () => tooltip.style('opacity', 0));
        });
    });

    // Legend
    const legendData = [
        { lbl: 'Highly Similar',   color: '#10B981' },
        { lbl: 'Partially Similar',color: '#F59E0B' },
        { lbl: 'Unrelated',        color: '#EF4444' },
        { lbl: 'Not Evaluated',    color: '#D1D5DB' },
    ];
    const legendG = svg.append('g').attr('transform', `translate(${margin.left}, 14)`);
    legendData.forEach((d, i) => {
        const x = i * 135;
        legendG.append('rect').attr('x', x).attr('y', 0).attr('width', 14).attr('height', 14).attr('rx', 3).attr('fill', d.color);
        legendG.append('text').attr('x', x + 18).attr('y', 11).attr('font-size', '10px').attr('fill', '#374151').text(d.lbl);
    });
}
