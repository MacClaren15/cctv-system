// CCTV System - Frontend JavaScript

const API_BASE = "/api/v1";
let autoRefreshInterval;

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  console.log("Initializing CCTV Dashboard");

  // Setup event listeners
  setupEventListeners();

  // Initial data load
  loadDashboard();

  // Auto-refresh every 5 seconds
  autoRefreshInterval = setInterval(loadDashboard, 5000);
});

// Setup event listeners
function setupEventListeners() {
  document.getElementById("btn-start").addEventListener("click", startSystem);
  document.getElementById("btn-stop").addEventListener("click", stopSystem);
  document
    .getElementById("btn-restart")
    .addEventListener("click", restartSystem);
  document
    .getElementById("btn-filter-events")
    .addEventListener("click", filterEvents);
  document
    .getElementById("btn-refresh-events")
    .addEventListener("click", loadEvents);

  // Setup layout toggle buttons
  const layoutBtns = document.querySelectorAll(".layout-btn");
  const savedLayout = localStorage.getItem("cameraLayout") || "grid-1x2";

  layoutBtns.forEach((btn) => {
    btn.addEventListener("click", function () {
      const layout = this.getAttribute("data-layout");
      setupCameraLayout(layout);
    });

    // Set active button based on saved layout
    if (btn.getAttribute("data-layout") === savedLayout) {
      btn.classList.add("active");
    }
  });

  // Apply saved layout on load
  applyLayout(savedLayout);
}

// Load all dashboard data
async function loadDashboard() {
  try {
    await Promise.all([
      loadStatus(),
      loadCameras(),
      loadStatistics(),
      loadEvents(),
      loadAlerts(),
      loadCameraStats(),
    ]);
  } catch (error) {
    console.error("Error loading dashboard:", error);
  }
}

// Load system status
async function loadStatus() {
  try {
    const response = await fetch(`${API_BASE}/status`);
    const data = await response.json();

    const statusIndicator = document.querySelector(".status-indicator");
    const statusText = document.getElementById("status-text");

    if (data.is_running) {
      statusIndicator.classList.add("active");
      statusText.textContent = "System Active";
    } else {
      statusIndicator.classList.remove("active");
      statusText.textContent = "System Inactive";
    }

    // Update summary statistics
    document.getElementById("stat-frames").textContent = formatNumber(
      data.stats.camera_1?.total_frames || 0,
    );
    document.getElementById("stat-motion").textContent = formatNumber(
      data.total_events || 0,
    );
    document.getElementById("stat-objects").textContent = formatNumber(
      data.total_detections || 0,
    );
    document.getElementById("stat-alerts").textContent = formatNumber(
      data.total_alerts || 0,
    );
  } catch (error) {
    console.error("Error loading status:", error);
  }
}

// Load cameras
async function loadCameras() {
  try {
    const response = await fetch(`${API_BASE}/cameras`);
    const data = await response.json();

    const camerasGrid = document.getElementById("cameras-grid");
    camerasGrid.innerHTML = "";

    for (const [name, camera] of Object.entries(data.cameras)) {
      const card = createCameraCard(name, camera);
      camerasGrid.appendChild(card);
    }
  } catch (error) {
    console.error("Error loading cameras:", error);
  }
}

// Create camera card element
function createCameraCard(name, camera) {
  const card = document.createElement("div");
  card.className = "camera-card";

  const fps = camera.current_fps || 0;
  const statusColor = fps > 0 ? "#27ae60" : "#e74c3c";

  card.innerHTML = `
        <div class="camera-stream">
            <iframe src="${API_BASE}/cameras/${name}/stream" frameborder="0" title="${name}"></iframe>
        </div>
        <div class="camera-info">
            <h3>${camera.name || name}</h3>
            <div class="camera-detail">
                <span>Resolution:</span>
                <span>${camera.resolution[0]}x${camera.resolution[1]}</span>
            </div>
            <div class="camera-detail">
                <span>FPS:</span>
                <span style="color: ${statusColor}">${fps.toFixed(2)}</span>
            </div>
            <div class="camera-detail">
                <span>Status:</span>
                <span style="color: ${camera.is_running ? "#27ae60" : "#e74c3c"}">
                    ${camera.is_running ? "Active" : "Inactive"}
                </span>
            </div>
            <div class="camera-detail">
                <span>Frames:</span>
                <span>${formatNumber(camera.frame_count)}</span>
            </div>
        </div>
    `;

  return card;
}

// Load events
async function loadEvents(type = "", days = 1) {
  try {
    let url = `${API_BASE}/events?limit=100`;

    if (type) {
      url = `${API_BASE}/events/filter`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, days }),
      });
      const data = await response.json();
      renderEventsTable(data.events);
    } else {
      const response = await fetch(url);
      const data = await response.json();
      renderEventsTable(data.recent_events);
    }
  } catch (error) {
    console.error("Error loading events:", error);
  }
}

// Render events table
function renderEventsTable(events) {
  const tbody = document.querySelector("#events-table tbody");
  tbody.innerHTML = "";

  if (events.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="4" style="text-align: center; padding: 2rem;">No events found</td></tr>';
    return;
  }

  events.forEach((event) => {
    const row = document.createElement("tr");
    const date = new Date(event.timestamp);

    row.innerHTML = `
            <td>${date.toLocaleString()}</td>
            <td><span class="event-badge ${event.event_type}">${event.event_type}</span></td>
            <td>${event.camera_name}</td>
            <td>${JSON.stringify(event.details).substring(0, 50)}...</td>
        `;

    tbody.appendChild(row);
  });
}

// Filter events
function filterEvents() {
  const type = document.getElementById("event-filter-type").value;
  const days = document.getElementById("event-filter-days").value;
  loadEvents(type, days);
}

// Load alerts
async function loadAlerts() {
  try {
    const response = await fetch(`${API_BASE}/alerts?limit=20`);
    const data = await response.json();

    const alertsList = document.getElementById("alerts-list");
    alertsList.innerHTML = "";

    if (data.recent_alerts.length === 0) {
      alertsList.innerHTML = '<div class="empty-state"><p>No alerts</p></div>';
      return;
    }

    data.recent_alerts.forEach((alert) => {
      const item = createAlertItem(alert);
      alertsList.appendChild(item);
    });
  } catch (error) {
    console.error("Error loading alerts:", error);
  }
}

// Create alert item element
function createAlertItem(alert) {
  const item = document.createElement("div");
  item.className = `alert-item ${alert.severity}`;

  const date = new Date(alert.timestamp);

  item.innerHTML = `
        <div class="alert-content">
            <h4>${alert.alert_type.toUpperCase()}: ${alert.severity}</h4>
            <p>${alert.message}</p>
        </div>
        <div class="alert-time">${date.toLocaleString()}</div>
    `;

  return item;
}

// Load camera statistics
async function loadCameraStats() {
  try {
    const response = await fetch(`${API_BASE}/stats/cameras`);
    const stats = await response.json();

    const statsGrid = document.getElementById("camera-stats");
    statsGrid.innerHTML = "";

    for (const [name, stat] of Object.entries(stats)) {
      const card = createCameraStatCard(name, stat);
      statsGrid.appendChild(card);
    }
  } catch (error) {
    console.error("Error loading camera stats:", error);
  }
}

// Create camera stat card element
function createCameraStatCard(name, stat) {
  const card = document.createElement("div");
  card.className = "camera-stat-card";

  // Format uptime
  const uptime = Math.floor(stat.uptime_seconds);
  const hours = Math.floor(uptime / 3600);
  const minutes = Math.floor((uptime % 3600) / 60);

  card.innerHTML = `
        <h3>${name}</h3>
        <div class="camera-stat-detail">
            <span>Total Frames:</span>
            <span>${formatNumber(stat.total_frames)}</span>
        </div>
        <div class="camera-stat-detail">
            <span>Motion Events:</span>
            <span>${formatNumber(stat.motion_events)}</span>
        </div>
        <div class="camera-stat-detail">
            <span>Detections:</span>
            <span>${formatNumber(stat.total_detections)}</span>
        </div>
        <div class="camera-stat-detail">
            <span>Uptime:</span>
            <span>${hours}h ${minutes}m</span>
        </div>
    `;

  return card;
}

// Load statistics summary
async function loadStatistics() {
  try {
    const response = await fetch(`${API_BASE}/stats/summary`);
    const data = await response.json();

    // Update stats if needed
    return data;
  } catch (error) {
    console.error("Error loading statistics:", error);
  }
}

// System control functions
async function startSystem() {
  try {
    const response = await fetch(`${API_BASE}/control/start`, {
      method: "POST",
    });
    const data = await response.json();
    showNotification(data.message, "success");
    loadStatus();
  } catch (error) {
    console.error("Error starting system:", error);
    showNotification("Error starting system", "error");
  }
}

async function stopSystem() {
  try {
    const response = await fetch(`${API_BASE}/control/stop`, {
      method: "POST",
    });
    const data = await response.json();
    showNotification(data.message, "success");
    loadStatus();
  } catch (error) {
    console.error("Error stopping system:", error);
    showNotification("Error stopping system", "error");
  }
}

async function restartSystem() {
  try {
    const response = await fetch(`${API_BASE}/control/restart`, {
      method: "POST",
    });
    const data = await response.json();
    showNotification(data.message, "success");
    loadStatus();
  } catch (error) {
    console.error("Error restarting system:", error);
    showNotification("Error restarting system", "error");
  }
}

// Utility functions
function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num.toString();
}

function showNotification(message, type = "info") {
  // In a real app, you'd use a toast notification library
  console.log(`[${type.toUpperCase()}] ${message}`);
  alert(message);
}

// Camera Layout Management
function setupCameraLayout(layout) {
  applyLayout(layout);
  localStorage.setItem("cameraLayout", layout);
  updateLayoutButtons(layout);
}

function applyLayout(layout) {
  const camerasGrid = document.getElementById("cameras-grid");

  // Remove all layout classes
  camerasGrid.classList.remove("grid-1x1", "grid-1x2", "grid-2x2");

  // Add the selected layout class
  camerasGrid.classList.add(layout);
}

function updateLayoutButtons(layout) {
  const layoutBtns = document.querySelectorAll(".layout-btn");

  layoutBtns.forEach((btn) => {
    if (btn.getAttribute("data-layout") === layout) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
}

// Cleanup on page unload
window.addEventListener("beforeunload", function () {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval);
  }
});
