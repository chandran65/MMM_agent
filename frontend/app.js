// ===================================
// STATE MANAGEMENT
// ===================================
const state = {
    fileId: null, // ID from backend
    pipelineId: null, // ID from backend
    pipelineRunning: false,
    currentStage: null,
    results: null,
    config: {
        autoApprove: false
    }
};

// ===================================
// CONFIGURATION
// ===================================
const API_BASE_URL = 'http://localhost:8080/api';

// ===================================
// DOM ELEMENTS
// ===================================
const elements = {
    uploadDataBtn: document.getElementById('uploadDataBtn'),
    quickStartBtn: document.getElementById('quickStartBtn'),
    runPipelineBtn: document.getElementById('runPipelineBtn'),
    uploadModal: document.getElementById('uploadModal'),
    closeUploadModal: document.getElementById('closeUploadModal'),
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    browseBtn: document.getElementById('browseBtn'),
    checkpointModal: document.getElementById('checkpointModal'),
    approveCheckpoint: document.getElementById('approveCheckpoint'),
    rejectCheckpoint: document.getElementById('rejectCheckpoint'),
    pipelineSection: document.getElementById('pipeline-section'),
    resultsSection: document.getElementById('results-section'),
    insightsSection: document.getElementById('insights-section')
};

// ===================================
// INITIALIZATION
// ===================================
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeHeroChart();
    checkApiHealth(); // Check if backend is reachable
});

function initializeEventListeners() {
    // Upload Modal
    elements.uploadDataBtn.addEventListener('click', () => openModal('uploadModal'));
    elements.closeUploadModal.addEventListener('click', () => closeModal('uploadModal'));
    elements.browseBtn.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', handleFileUpload);

    // Upload Area Drag & Drop
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);

    // Pipeline
    elements.runPipelineBtn.addEventListener('click', startPipeline);

    // Checkpoint Modal
    elements.approveCheckpoint.addEventListener('click', () => handleCheckpointDecision(true));
    elements.rejectCheckpoint.addEventListener('click', () => handleCheckpointDecision(false));

    // Quick Start
    elements.quickStartBtn.addEventListener('click', showQuickStart);

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = link.getAttribute('href').substring(1);
            navigateToSection(target);
        });
    });
}

async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            console.log('Backend API is healthy');
        } else {
            showNotification('Backend API is not reachable', 'error');
        }
    } catch (e) {
        showNotification('Cannot connect to backend server', 'error');
        console.error(e);
    }
}

// ===================================
// MODAL FUNCTIONS
// ===================================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('active');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('active');
}

// ===================================
// FILE UPLOAD
// ===================================
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        uploadFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    elements.uploadArea.classList.add('drag-over');
}

function handleDragLeave(event) {
    event.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
}

function handleDrop(event) {
    event.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    const file = event.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) {
        uploadFile(file);
    } else {
        showNotification('Please upload a CSV file', 'error');
    }
}

async function uploadFile(file) {
    showNotification(`Uploading ${file.name}...`, 'info');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            state.fileId = data.file_id;
            elements.runPipelineBtn.disabled = false;
            closeModal('uploadModal');
            showNotification(`${data.filename} uploaded successfully!`, 'success');
        } else {
            showNotification(`Upload failed: ${data.error}`, 'error');
        }
    } catch (e) {
        showNotification(`Upload error: ${e.message}`, 'error');
    }
}

// ===================================
// PIPELINE EXECUTION
// ===================================
async function startPipeline() {
    if (!state.fileId) {
        showNotification('Please upload data first', 'error');
        return;
    }

    state.pipelineRunning = true;
    elements.runPipelineBtn.disabled = true;
    elements.runPipelineBtn.innerHTML = `
        <svg class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
        </svg>
        Running...
    `;

    // Reset Stages
    resetStageUI();

    try {
        const response = await fetch(`${API_BASE_URL}/pipeline/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: state.fileId,
                config: state.config
            })
        });

        const data = await response.json();

        if (data.success) {
            state.pipelineId = data.pipeline_id;
            pollPipelineStatus();
        } else {
            showNotification(`Failed to start: ${data.error}`, 'error');
            resetPipeline();
        }
    } catch (e) {
        showNotification(`Connection error: ${e.message}`, 'error');
        resetPipeline();
    }
}

function pollPipelineStatus() {
    if (!state.pipelineId) return;

    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/pipeline/${state.pipelineId}/status`);
            const data = await response.json();

            updatePipelineUI(data);

            if (data.status === 'completed') {
                clearInterval(pollInterval);
                completePipeline();
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                showNotification(`Pipeline failed: ${data.error}`, 'error');
                resetPipeline();
            } else if (data.status === 'stopped') {
                clearInterval(pollInterval);
                showNotification('Pipeline stopped by user', 'warning');
                resetPipeline();
            }

            // Handle Checkpoint
            if (data.checkpoint && data.checkpoint.pending) {
                // Only show if not already showing
                if (!document.getElementById('checkpointModal').classList.contains('active')) {
                    showCheckpointModal(data.checkpoint);
                }
            }

        } catch (e) {
            console.error('Polling error:', e);
        }
    }, 1000);
}

function updatePipelineUI(statusData) {
    const stages = ['segmentation', 'trend', 'baseline', 'model', 'budget', 'insight'];
    const currentStage = statusData.current_stage;
    const progress = statusData.progress;

    // Map backend stage names to frontend IDs if they differ slightly
    // Backend: 'trend_scanner' -> Frontend: 'trend'
    // Backend: 'model_optimization' -> Frontend: 'model'
    // etc. Use simple mapping
    let stageId = currentStage;
    if (stageId === 'trend_scanner') stageId = 'trend';
    if (stageId === 'model_optimization') stageId = 'model';
    if (stageId === 'budget_optimization') stageId = 'budget';
    if (stageId === 'insight_generation') stageId = 'insight';

    // Update active stage
    if (stageId && stages.includes(stageId)) {
        updateStageUI(stageId, 'running');

        // Update previous stages to completed
        const currentIndex = stages.indexOf(stageId);
        for (let i = 0; i < currentIndex; i++) {
            updateStageUI(stages[i], 'completed');
            setStageProgress(stages[i], 100);
        }

        // Approximation of progress within stage (backend gives total progress)
        // Let's just use the backend progress roughly distributed
        setStageProgress(stageId, (progress % 20) * 5); // Fake intra-stage
    }
}

function updateStageUI(stageName, status) {
    const stageCard = document.querySelector(`[data-stage="${stageName}"]`);
    if (!stageCard) return;

    const icon = stageCard.querySelector('.stage-icon');
    const badge = stageCard.querySelector('.status-badge');

    // Remove all status classes
    icon.classList.remove('pending', 'running', 'completed');
    badge.classList.remove('pending', 'running', 'completed');
    stageCard.classList.remove('active', 'completed');

    // Add new status
    icon.classList.add(status);
    badge.classList.add(status);
    badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);

    if (status === 'running') {
        stageCard.classList.add('active');
    } else if (status === 'completed') {
        stageCard.classList.add('completed');
    }
}

function setStageProgress(stageName, percent) {
    const stageCard = document.querySelector(`[data-stage="${stageName}"]`);
    if (stageCard) {
        stageCard.querySelector('.progress-fill').style.width = `${percent}%`;
    }
}

function resetStageUI() {
    document.querySelectorAll('.stage-card').forEach(card => {
        const stage = card.getAttribute('data-stage');
        updateStageUI(stage, 'pending');
        card.querySelector('.progress-fill').style.width = '0%';
    });
}

// ===================================
// CHECKPOINTS
// ===================================
function showCheckpointModal(checkpoint) {
    const checkpointTitle = document.getElementById('checkpointTitle');
    const checkpointDescription = document.getElementById('checkpointDescription');
    const checkpointData = document.getElementById('checkpointData');

    // Use message from backend
    checkpointTitle.textContent = `Checkpoint: ${checkpoint.stage.toUpperCase()}`;
    checkpointDescription.textContent = checkpoint.message || 'Review required';

    // Show data if available
    if (checkpoint.data) {
        checkpointData.innerHTML = `<pre>${JSON.stringify(checkpoint.data, null, 2)}</pre>`;
        checkpointData.style.display = 'block';
    } else {
        checkpointData.style.display = 'none';
    }

    openModal('checkpointModal');
}

async function handleCheckpointDecision(approved) {
    closeModal('checkpointModal');

    try {
        const response = await fetch(`${API_BASE_URL}/pipeline/${state.pipelineId}/checkpoint`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approved })
        });

        const data = await response.json();
        if (data.success) {
            showNotification(approved ? 'Checkpoint approved' : 'Checkpoint rejected', approved ? 'success' : 'warning');
        } else {
            showNotification(`Error: ${data.error}`, 'error');
        }
    } catch (e) {
        showNotification(`Network error: ${e.message}`, 'error');
    }
}


// ===================================
// COMPLETION & RESULTS
// ===================================

async function completePipeline() {
    state.pipelineRunning = false;
    elements.runPipelineBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 6L9 17l-5-5"/>
        </svg>
        Completed
    `;

    showNotification('Pipeline completed successfully!', 'success');

    // Fetch Results
    try {
        const response = await fetch(`${API_BASE_URL}/pipeline/${state.pipelineId}/results`);
        const data = await response.json();

        if (data.results) {
            showResults(data.results);
        }
    } catch (e) {
        showNotification('Failed to fetch results', 'error');
    }
}

function resetPipeline() {
    state.pipelineRunning = false;
    elements.runPipelineBtn.disabled = false;
    elements.runPipelineBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        Run Pipeline
    `;
}

// ===================================
// RESULTS DISPLAY
// ===================================
function showResults(results) {
    state.results = results;

    // Show results section
    elements.resultsSection.style.display = 'block';
    elements.insightsSection.style.display = 'block';

    // Scroll to results
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });

    // DOM Updates for Metrics (Assume similar structure to mock)
    // ... Implement specifics based on real backend response structure ...
    // For now we assume backend sends matched structure or we map it

    // Initialize charts
    initializeCharts(results);

    // Populate recommendations table
    populateRecommendationsTable(results);

    // Render Insights
    renderInsights(results.insights);
}

function renderInsights(insights) {
    // ... logic to render insights cards ...
    // Using existing HTML structure
}

// ===================================
// CHART DRAWING FUNCTIONS (Reuse existing)
// ===================================
// ... (Keep existing chart functions: initializeCharts, drawBarChart, etc.) ...

function initializeCharts(results) {
    if (results.channels) {
        initializeContributionsChart(results.channels);
        initializeAllocationChart(results.channels);
        initializeResponseCurvesChart(results.channels);
    }
}

function initializeContributionsChart(channels) {
    const canvas = document.getElementById('contributionsChart');
    const ctx = canvas.getContext('2d');

    const colors = [
        'rgba(102, 126, 234, 0.8)',
        'rgba(118, 75, 162, 0.8)',
        'rgba(240, 147, 251, 0.8)',
        'rgba(79, 172, 254, 0.8)',
        'rgba(16, 185, 129, 0.8)'
    ];

    drawBarChart(ctx, canvas.width, canvas.height, {
        labels: channels.map(c => c.name),
        values: channels.map(c => c.contribution),
        colors: colors,
        title: ''
    });
}

function initializeAllocationChart(channels) {
    const canvas = document.getElementById('allocationChart');
    const ctx = canvas.getContext('2d');

    drawGroupedBarChart(ctx, canvas.width, canvas.height, {
        labels: channels.map(c => c.name),
        datasets: [
            { name: 'Current', values: channels.map(c => c.current / 1000), color: 'rgba(168, 168, 179, 0.6)' },
            { name: 'Optimized', values: channels.map(c => c.optimized / 1000), color: 'rgba(102, 126, 234, 0.8)' }
        ]
    });
}

function initializeResponseCurvesChart(channels) {
    const canvas = document.getElementById('responseCurvesChart');
    const ctx = canvas.getContext('2d');

    const colors = [
        'rgba(102, 126, 234, 0.8)',
        'rgba(118, 75, 162, 0.8)',
        'rgba(240, 147, 251, 0.8)',
        'rgba(79, 172, 254, 0.8)',
        'rgba(16, 185, 129, 0.8)'
    ];

    drawMultiLineChart(ctx, canvas.width, canvas.height, channels, colors);
}

// Keep the drawing helpers from previous version
function drawBarChart(ctx, width, height, data) {
    ctx.clearRect(0, 0, width, height);
    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    const barWidth = chartWidth / data.labels.length - 20;
    const maxValue = Math.max(...data.values) || 100;

    data.labels.forEach((label, i) => {
        const value = data.values[i];
        const barHeight = (value / maxValue) * chartHeight;
        const x = padding + (chartWidth / data.labels.length) * i + 10;
        const y = height - padding - barHeight;

        ctx.fillStyle = data.colors[i % data.colors.length];
        ctx.fillRect(x, y, barWidth, barHeight);

        ctx.fillStyle = '#ffffff';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        ctx.fillText(`${value.toFixed(1)}%`, x + barWidth / 2, y - 5);
        ctx.fillStyle = '#a8a8b3';
        ctx.fillText(label, x + barWidth / 2, height - padding + 20);
    });
}

function drawGroupedBarChart(ctx, width, height, data) {
    ctx.clearRect(0, 0, width, height);
    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    const groupWidth = chartWidth / data.labels.length;
    const barWidth = groupWidth / (data.datasets.length + 1);
    const allValues = data.datasets.flatMap(d => d.values);
    const maxValue = Math.max(...allValues) || 100;

    data.labels.forEach((label, i) => {
        data.datasets.forEach((dataset, j) => {
            const value = dataset.values[i];
            const barHeight = (value / maxValue) * chartHeight;
            const x = padding + groupWidth * i + barWidth * j;
            const y = height - padding - barHeight;
            ctx.fillStyle = dataset.color;
            ctx.fillRect(x, y, barWidth - 5, barHeight);
        });
        ctx.fillStyle = '#a8a8b3';
        ctx.textAlign = 'center';
        ctx.fillText(label, padding + groupWidth * i + groupWidth / 2, height - padding + 20);
    });
}

function drawMultiLineChart(ctx, width, height, channels, colors) {
    ctx.clearRect(0, 0, width, height);
    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    channels.forEach((channel, channelIdx) => {
        ctx.strokeStyle = colors[channelIdx % colors.length];
        ctx.lineWidth = 2;
        ctx.beginPath();
        const points = 50;
        for (let i = 0; i <= points; i++) {
            const spend = (i / points) * channel.optimized * 2;
            const response = hillFunction(spend, channel.optimized, 0.5); // Simplified visual
            const x = padding + (i / points) * chartWidth;
            const y = height - padding - (response / 100) * chartHeight * 0.5; // Scale down for visuals
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
    });

    // Axes
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.stroke();
}

function hillFunction(spend, halfSaturation, slope) {
    return 100 * Math.pow(spend, slope) / (Math.pow(halfSaturation, slope) + Math.pow(spend, slope));
}

// ===================================
// TABLE POPULATION
// ===================================
function populateRecommendationsTable(results) {
    const tbody = document.getElementById('recommendationsTable');
    tbody.innerHTML = '';

    if (results.channels) {
        results.channels.forEach(channel => {
            const change = ((channel.optimized - channel.current) / channel.current * 100).toFixed(1);
            const changeClass = change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral';
            const changeSymbol = change > 0 ? '↑' : change < 0 ? '↓' : '→';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${channel.name}</strong></td>
                <td>$${(channel.current / 1000).toFixed(0)}K</td>
                <td>$${(channel.optimized / 1000).toFixed(0)}K</td>
                <td class="metric-change ${changeClass}">${changeSymbol} ${Math.abs(change)}%</td>
                <td>${channel.roi.toFixed(1)}x</td>
                <td>${channel.contribution.toFixed(1)}%</td>
            `;
            tbody.appendChild(row);
        });
    }
}

// ===================================
// NAVIGATION & UTILS
// ===================================
function navigateToSection(section) {
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));

    // Find link matching section
    const link = document.querySelector(`[href="#${section}"]`);
    if (link) link.classList.add('active');

    if (section === 'results' && state.results) {
        elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    } else if (section === 'insights' && state.results) {
        elements.insightsSection.scrollIntoView({ behavior: 'smooth' });
    } else if (section === 'pipeline') {
        elements.pipelineSection.scrollIntoView({ behavior: 'smooth' });
    } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${type === 'success' ? 'rgba(16, 185, 129, 0.2)' : type === 'error' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.2)'};
        color: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        padding: 1rem 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid currentColor;
        z-index: 1001;
        font-weight: 600;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function initializeHeroChart() {
    const canvas = document.getElementById('heroChart');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        // Simple animation loop placeholder
        let offset = 0;
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = 'rgba(102, 126, 234, 0.8)';
            ctx.lineWidth = 3;
            ctx.beginPath();
            for (let x = 0; x <= canvas.width; x += 2) {
                const y = 150 + Math.sin((x + offset) * 0.02) * 30;
                if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.stroke();
            offset++;
            requestAnimationFrame(draw);
        }
        draw();
    }
}

function showQuickStart() {
    showNotification('See QUICKSTART_WEB.md for details', 'info');
}
