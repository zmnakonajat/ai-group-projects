"""
Dashboard Agent

PERCEIVES: RAM_DATA, RAM_HIGH, RAM_NORMAL messages from the bus
ACTS: Serves live RAM data via Flask API
"""

import time
import threading
import logging
from flask import Flask, jsonify, render_template_string
from core.base_agent import BaseAgent
from core.message_bus import MessageBus

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class DashboardAgent(BaseAgent):

    def __init__(self, bus: MessageBus):
        super().__init__("DashboardAgent", bus)
        self.bus.subscribe("RAM_DATA", self.on_ram_data)
        self.bus.subscribe("RAM_HIGH", self.on_ram_high)
        self.bus.subscribe("RAM_NORMAL", self.on_ram_normal)

        # Latest data storage
        self.latest = {
            "ram_percent": 0,
            "top_processes": [],
            "status": "normal"
        }

    def run(self):
        print(f"[{self.name}] Starting dashboard on http://localhost:5000")
        app.config['agent'] = self
        threading.Thread(
            target=lambda: app.run(port=5000, debug=False, use_reloader=False),
            daemon=True
        ).start()
        while True:
            time.sleep(1)


    def on_ram_data(self, message):
        self.latest["ram_percent"] = message.payload["ram_percent"]
        self.latest["top_processes"] = message.payload["top_processes"]

    def on_ram_high(self, message):
        self.latest["status"] = "high"

    def on_ram_normal(self, message):
        self.latest["status"] = "normal"


@app.route('/api/status')
def status():
    agent = app.config['agent']
    return jsonify(agent.latest)


@app.route('/')
def index():
    return render_template_string(HTML)


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAM Monitor</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #030b14;
            --panel: #060f1a;
            --border: #0d2137;
            --cyan: #00e5ff;
            --green: #00ff9d;
            --orange: #ff9500;
            --red: #ff2d55;
            --yellow: #ffe600;
            --text: #a8d4e8;
            --dim: #2a4a5e;
            --glow-cyan: 0 0 20px rgba(0,229,255,0.4);
            --glow-green: 0 0 20px rgba(0,255,157,0.4);
            --glow-red: 0 0 20px rgba(255,45,85,0.4);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'Rajdhani', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Scanline overlay */
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0,0,0,0.08) 2px,
                rgba(0,0,0,0.08) 4px
            );
            pointer-events: none;
            z-index: 1000;
        }

        /* Grid background */
        body::after {
            content: '';
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background-image:
                linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
            background-size: 40px 40px;
            pointer-events: none;
            z-index: 0;
        }

        .container {
            position: relative;
            z-index: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }

        /* HEADER */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            border: 2px solid var(--cyan);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            box-shadow: var(--glow-cyan);
        }

        .logo-icon::before {
            content: '';
            position: absolute;
            width: 20px;
            height: 20px;
            background: var(--cyan);
            opacity: 0.2;
            animation: pulse 2s ease-in-out infinite;
        }

        .logo-icon svg {
            width: 20px;
            height: 20px;
            fill: var(--cyan);
            position: relative;
            z-index: 1;
        }

        .logo-text {
            font-family: 'Share Tech Mono', monospace;
            font-size: 18px;
            color: var(--cyan);
            letter-spacing: 3px;
            text-transform: uppercase;
        }

        .logo-sub {
            font-size: 11px;
            color: var(--dim);
            letter-spacing: 2px;
            margin-top: 2px;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .live-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 12px;
            color: var(--green);
            letter-spacing: 2px;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            background: var(--green);
            border-radius: 50%;
            box-shadow: var(--glow-green);
            animation: blink 1.2s ease-in-out infinite;
        }

        .timestamp {
            font-family: 'Share Tech Mono', monospace;
            font-size: 12px;
            color: var(--dim);
            letter-spacing: 1px;
        }

        /* MAIN GRID */
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            grid-template-rows: auto auto;
            gap: 20px;
        }

        /* PANEL */
        .panel {
            background: var(--panel);
            border: 1px solid var(--border);
            padding: 24px;
            position: relative;
            overflow: hidden;
            animation: fadeIn 0.6s ease forwards;
            opacity: 0;
        }

        .panel::before {
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--cyan), transparent);
            opacity: 0.5;
        }

        /* Corner decorations */
        .panel::after {
            content: '';
            position: absolute;
            top: 8px; right: 8px;
            width: 16px; height: 16px;
            border-top: 2px solid var(--cyan);
            border-right: 2px solid var(--cyan);
            opacity: 0.4;
        }

        .panel-label {
            font-family: 'Share Tech Mono', monospace;
            font-size: 10px;
            color: var(--dim);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .panel-label::before {
            content: '';
            width: 4px;
            height: 4px;
            background: var(--cyan);
            display: inline-block;
        }

        /* RAM GAUGE - spans 2 cols */
        .ram-gauge {
            grid-column: span 2;
        }

        .gauge-wrapper {
            display: flex;
            align-items: center;
            gap: 40px;
        }

        .gauge-circle {
            position: relative;
            width: 200px;
            height: 200px;
            flex-shrink: 0;
        }

        .gauge-circle svg {
            width: 200px;
            height: 200px;
            transform: rotate(-90deg);
        }

        .gauge-bg {
            fill: none;
            stroke: var(--border);
            stroke-width: 8;
        }

        .gauge-fill {
            fill: none;
            stroke: var(--green);
            stroke-width: 8;
            stroke-linecap: round;
            stroke-dasharray: 565;
            stroke-dashoffset: 565;
            transition: stroke-dashoffset 1s ease, stroke 0.5s ease;
            filter: drop-shadow(0 0 8px currentColor);
        }

        .gauge-center {
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }

        .gauge-value {
            font-family: 'Share Tech Mono', monospace;
            font-size: 52px;
            color: var(--green);
            line-height: 1;
            transition: color 0.5s ease;
            text-shadow: 0 0 20px currentColor;
        }

        .gauge-unit {
            font-family: 'Share Tech Mono', monospace;
            font-size: 16px;
            color: var(--dim);
            letter-spacing: 2px;
        }

        .gauge-info {
            flex: 1;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border: 1px solid var(--green);
            font-family: 'Share Tech Mono', monospace;
            font-size: 13px;
            color: var(--green);
            letter-spacing: 2px;
            margin-bottom: 24px;
            transition: all 0.5s ease;
            box-shadow: inset 0 0 20px rgba(0,255,157,0.05);
        }

        .status-badge.warning {
            border-color: var(--orange);
            color: var(--orange);
            box-shadow: inset 0 0 20px rgba(255,149,0,0.05), 0 0 15px rgba(255,149,0,0.2);
        }

        .status-badge.critical {
            border-color: var(--red);
            color: var(--red);
            box-shadow: inset 0 0 20px rgba(255,45,85,0.05), 0 0 15px rgba(255,45,85,0.2);
            animation: criticalPulse 1s ease-in-out infinite;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
        }

        .stat-row:last-child { border-bottom: none; }

        .stat-label {
            font-size: 13px;
            color: var(--dim);
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .stat-value {
            font-family: 'Share Tech Mono', monospace;
            font-size: 14px;
            color: var(--cyan);
        }

        /* BAR CHART */
        .bar-chart { grid-column: span 1; }

        .process-list { display: flex; flex-direction: column; gap: 14px; margin-top: 8px; }

        .process-item {}

        .process-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }

        .process-name {
            font-family: 'Share Tech Mono', monospace;
            font-size: 12px;
            color: var(--text);
            letter-spacing: 1px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 160px;
        }

        .process-pct {
            font-family: 'Share Tech Mono', monospace;
            font-size: 12px;
            color: var(--cyan);
        }

        .bar-track {
            width: 100%;
            height: 4px;
            background: var(--border);
            position: relative;
            overflow: hidden;
        }

        .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--cyan), var(--green));
            transition: width 1s ease;
            box-shadow: 0 0 8px var(--cyan);
            position: relative;
        }

        .bar-fill::after {
            content: '';
            position: absolute;
            right: 0; top: 0;
            width: 4px; height: 100%;
            background: white;
            opacity: 0.8;
        }

        /* HISTORY CHART */
        .history-chart {
            grid-column: span 3;
        }

        .chart-area {
            position: relative;
            height: 120px;
            margin-top: 12px;
        }

        canvas#historyCanvas {
            width: 100%;
            height: 120px;
        }

        /* AGENTS STATUS */
        .agents-panel { grid-column: span 3; }

        .agents-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            margin-top: 8px;
        }

        .agent-card {
            border: 1px solid var(--border);
            padding: 14px;
            text-align: center;
            position: relative;
            transition: all 0.3s ease;
        }

        .agent-card.active {
            border-color: var(--green);
            box-shadow: inset 0 0 20px rgba(0,255,157,0.05);
        }

        .agent-card.active::before {
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 2px;
            background: var(--green);
            box-shadow: 0 0 8px var(--green);
        }

        .agent-icon {
            font-size: 24px;
            margin-bottom: 8px;
        }

        .agent-name {
            font-family: 'Share Tech Mono', monospace;
            font-size: 10px;
            color: var(--dim);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .agent-status {
            font-size: 11px;
            color: var(--green);
            letter-spacing: 1px;
        }

        .agent-status.idle { color: var(--dim); }

        /* THRESHOLD LINE */
        .threshold-info {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
        }

        .threshold-line {
            width: 30px;
            height: 2px;
            background: var(--red);
            box-shadow: 0 0 6px var(--red);
        }

        .threshold-text {
            font-family: 'Share Tech Mono', monospace;
            font-size: 11px;
            color: var(--dim);
        }

        /* ANIMATIONS */
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.2; }
            50% { transform: scale(1.5); opacity: 0.4; }
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        @keyframes fadeIn {
            to { opacity: 1; transform: translateY(0); }
            from { opacity: 0; transform: translateY(10px); }
        }

        @keyframes criticalPulse {
            0%, 100% { box-shadow: inset 0 0 20px rgba(255,45,85,0.05), 0 0 15px rgba(255,45,85,0.2); }
            50% { box-shadow: inset 0 0 20px rgba(255,45,85,0.15), 0 0 30px rgba(255,45,85,0.5); }
        }

        .panel:nth-child(1) { animation-delay: 0.1s; }
        .panel:nth-child(2) { animation-delay: 0.2s; }
        .panel:nth-child(3) { animation-delay: 0.3s; }
        .panel:nth-child(4) { animation-delay: 0.4s; }
        .panel:nth-child(5) { animation-delay: 0.5s; }
    </style>
</head>
<body>
<div class="container">

    <header>
        <div class="logo">
            <div class="logo-icon">
                <svg viewBox="0 0 24 24"><path d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/></svg>
            </div>
            <div>
                <div class="logo-text">RAM Monitor</div>
                <div class="logo-sub">SYSTEM INTELLIGENCE v1.0</div>
            </div>
        </div>
        <div class="header-right">
            <div class="live-badge">
                <div class="live-dot"></div>
                LIVE
            </div>
            <div class="timestamp" id="clock">--:--:--</div>
        </div>
    </header>

    <div class="grid">

        <!-- RAM GAUGE -->
        <div class="panel ram-gauge">
            <div class="panel-label">RAM Usage</div>
            <div class="gauge-wrapper">
                <div class="gauge-circle">
                    <svg viewBox="0 0 200 200">
                        <circle class="gauge-bg" cx="100" cy="100" r="90"/>
                        <circle class="gauge-fill" id="gaugeFill" cx="100" cy="100" r="90"/>
                    </svg>
                    <div class="gauge-center">
                        <div class="gauge-value" id="ramValue">0</div>
                        <div class="gauge-unit">%</div>
                    </div>
                </div>
                <div class="gauge-info">
                    <div class="status-badge" id="statusBadge">
                        <span>●</span> NORMAL
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Threshold</span>
                        <span class="stat-value" id="threshold">50%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">High Since</span>
                        <span class="stat-value" id="highSince">—</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Next Alert</span>
                        <span class="stat-value" id="nextAlert">—</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Last Update</span>
                        <span class="stat-value" id="lastUpdate">—</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- TOP PROCESSES -->
        <div class="panel bar-chart">
            <div class="panel-label">Top Processes</div>
            <div class="process-list" id="processList">
                <div class="process-item">
                    <div class="process-header">
                        <span class="process-name">—</span>
                        <span class="process-pct">0%</span>
                    </div>
                    <div class="bar-track"><div class="bar-fill" style="width:0%"></div></div>
                </div>
            </div>
        </div>

        <!-- HISTORY CHART -->
        <div class="panel history-chart">
            <div class="panel-label">RAM History (last 20 readings)</div>
            <div class="chart-area">
                <canvas id="historyCanvas"></canvas>
            </div>
            <div class="threshold-info">
                <div class="threshold-line"></div>
                <span class="threshold-text">THRESHOLD</span>
            </div>
        </div>

        <!-- AGENTS STATUS -->
        <div class="panel agents-panel">
            <div class="panel-label">Agent Status</div>
            <div class="agents-grid">
                <div class="agent-card active">
                    <div class="agent-icon">📡</div>
                    <div class="agent-name">Monitor</div>
                    <div class="agent-status">RUNNING</div>
                </div>
                <div class="agent-card active" id="alertCard">
                    <div class="agent-icon">🔔</div>
                    <div class="agent-name">Alert</div>
                    <div class="agent-status idle" id="alertStatus">STANDBY</div>
                </div>
                <div class="agent-card active" id="emailCard">
                    <div class="agent-icon">📧</div>
                    <div class="agent-name">Email</div>
                    <div class="agent-status idle" id="emailStatus">STANDBY</div>
                </div>
                <div class="agent-card active" id="restartCard">
                    <div class="agent-icon">🔄</div>
                    <div class="agent-name">Restart</div>
                    <div class="agent-status idle" id="restartStatus">STANDBY</div>
                </div>
                <div class="agent-card active">
                    <div class="agent-icon">📊</div>
                    <div class="agent-name">Dashboard</div>
                    <div class="agent-status">SERVING</div>
                </div>
            </div>
        </div>

    </div>
</div>

<script>
    const THRESHOLD = 50;
    let history = [];
    let highSinceTime = null;

    // Clock
    function updateClock() {
        document.getElementById('clock').textContent = new Date().toLocaleTimeString('en-GB');
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Get color based on RAM level
    function getColor(ram) {
        if (ram >= 80) return getComputedStyle(document.documentElement).getPropertyValue('--red').trim();
        if (ram >= 60) return getComputedStyle(document.documentElement).getPropertyValue('--orange').trim();
        if (ram >= 40) return getComputedStyle(document.documentElement).getPropertyValue('--yellow').trim();
        return getComputedStyle(document.documentElement).getPropertyValue('--green').trim();
    }

    // Update gauge
    function updateGauge(ram) {
        const circumference = 565;
        const offset = circumference - (ram / 100) * circumference;
        const fill = document.getElementById('gaugeFill');
        const value = document.getElementById('ramValue');
        const color = getColor(ram);

        fill.style.strokeDashoffset = offset;
        fill.style.stroke = color;
        value.style.color = color;
        value.textContent = ram;

        // Status badge
        const badge = document.getElementById('statusBadge');
        if (ram >= 80) {
            badge.className = 'status-badge critical';
            badge.innerHTML = '<span>●</span> CRITICAL';
        } else if (ram >= THRESHOLD) {
            badge.className = 'status-badge warning';
            badge.innerHTML = '<span>●</span> WARNING';
        } else {
            badge.className = 'status-badge';
            badge.innerHTML = '<span>●</span> NORMAL';
        }
    }

    // Update processes
    function updateProcesses(processes) {
        const list = document.getElementById('processList');
        if (!processes || processes.length === 0) return;

        const max = processes[0].memory || 1;
        list.innerHTML = processes.map(p => `
            <div class="process-item">
                <div class="process-header">
                    <span class="process-name">${p.name}</span>
                    <span class="process-pct">${p.memory}%</span>
                </div>
                <div class="bar-track">
                    <div class="bar-fill" style="width:${(p.memory/max)*100}%"></div>
                </div>
            </div>
        `).join('');
    }

    // Draw history chart
    function drawHistory() {
        const canvas = document.getElementById('historyCanvas');
        const ctx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth;
        canvas.height = 120;

        const w = canvas.width;
        const h = canvas.height;
        const pad = 10;

        ctx.clearRect(0, 0, w, h);

        if (history.length < 2) return;

        // Threshold line
        const ty = h - pad - ((THRESHOLD / 100) * (h - pad * 2));
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = 'rgba(255,45,85,0.4)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(pad, ty);
        ctx.lineTo(w - pad, ty);
        ctx.stroke();
        ctx.setLineDash([]);

        // Fill area
        const gradient = ctx.createLinearGradient(0, 0, 0, h);
        gradient.addColorStop(0, 'rgba(0,229,255,0.3)');
        gradient.addColorStop(1, 'rgba(0,229,255,0)');

        ctx.beginPath();
        history.forEach((val, i) => {
            const x = pad + (i / (history.length - 1)) * (w - pad * 2);
            const y = h - pad - ((val / 100) * (h - pad * 2));
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
        ctx.lineTo(pad + ((history.length - 1) / (history.length - 1)) * (w - pad * 2), h - pad);
        ctx.lineTo(pad, h - pad);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // Line
        ctx.beginPath();
        history.forEach((val, i) => {
            const x = pad + (i / (history.length - 1)) * (w - pad * 2);
            const y = h - pad - ((val / 100) * (h - pad * 2));
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
        ctx.strokeStyle = '#00e5ff';
        ctx.lineWidth = 2;
        ctx.shadowColor = '#00e5ff';
        ctx.shadowBlur = 6;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Dots
        history.forEach((val, i) => {
            const x = pad + (i / (history.length - 1)) * (w - pad * 2);
            const y = h - pad - ((val / 100) * (h - pad * 2));
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fillStyle = getColor(val);
            ctx.shadowColor = getColor(val);
            ctx.shadowBlur = 8;
            ctx.fill();
            ctx.shadowBlur = 0;
        });
    }

    // Update agent statuses
    function updateAgents(status, ram) {
        const alertEl = document.getElementById('alertStatus');
        const emailEl = document.getElementById('emailStatus');
        const restartEl = document.getElementById('restartStatus');

        if (status === 'high') {
            alertEl.textContent = 'ACTIVE';
            alertEl.className = 'agent-status';
            alertEl.style.color = '#ff9500';
        } else {
            alertEl.textContent = 'STANDBY';
            alertEl.className = 'agent-status idle';
            alertEl.style.color = '';
        }

        if (status === 'email_sent') {
            emailEl.textContent = 'SENT';
            emailEl.className = 'agent-status';
            emailEl.style.color = '#00e5ff';
        }

        if (status === 'restarting') {
            restartEl.textContent = 'TRIGGERED';
            restartEl.className = 'agent-status';
            restartEl.style.color = '#ff2d55';
        }
    }

    // Main fetch
    function fetchStatus() {
        fetch('/api/status')
            .then(res => res.json())
            .then(data => {
                const ram = data.ram_percent;
                const processes = data.top_processes;
                const status = data.status;

                updateGauge(ram);
                updateProcesses(processes);
                updateAgents(status, ram);

                history.push(ram);
                if (history.length > 20) history.shift();
                drawHistory();

                // High since
                if (status !== 'normal') {
                    if (!highSinceTime) highSinceTime = new Date();
                    document.getElementById('highSince').textContent = highSinceTime.toLocaleTimeString('en-GB');
                } else {
                    highSinceTime = null;
                    document.getElementById('highSince').textContent = '—';
                }

                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString('en-GB');
                document.getElementById('threshold').textContent = THRESHOLD + '%';
            })
            .catch(() => {
                document.getElementById('ramValue').textContent = '??';
            });
    }

    fetchStatus();
    setInterval(fetchStatus, 10000);
    window.addEventListener('resize', drawHistory);
</script>
</body>
</html>
"""