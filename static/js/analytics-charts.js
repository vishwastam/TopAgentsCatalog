// analytics-charts.js
// Reusable module for analytics dashboard charts (Chart.js required)

// Store chart instances for theme updates
const analyticsCharts = {};

function getThemeColors() {
  const styles = getComputedStyle(document.body);
  return {
    bg: styles.getPropertyValue('--bg-card').trim(),
    text: styles.getPropertyValue('--text-main').trim(),
    accent: styles.getPropertyValue('--accent').trim(),
    secondary: styles.getPropertyValue('--text-secondary').trim(),
  };
}

// Modern pastel/grey color palette
const pastelPalette = {
  blue: 'rgba(99, 179, 237, 0.7)',
  blueLine: 'rgba(99, 179, 237, 1)',
  green: 'rgba(144, 238, 174, 0.7)',
  greenLine: 'rgba(72, 201, 176, 1)',
  yellow: 'rgba(255, 221, 113, 0.7)',
  yellowLine: 'rgba(255, 221, 113, 1)',
  pink: 'rgba(255, 182, 193, 0.7)',
  pinkLine: 'rgba(255, 182, 193, 1)',
  purple: 'rgba(186, 143, 255, 0.7)',
  purpleLine: 'rgba(186, 143, 255, 1)',
  grey: 'rgba(180, 185, 196, 0.7)',
  greyLine: 'rgba(120, 124, 134, 1)',
};

// --- AI Code Metrics Chart ---
export function renderAiLinesChart(canvasId, data = null) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  const colors = getThemeColors();
  const chartData = data || {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    datasets: [
      {
        label: 'Lines Added',
        data: [120, 90, 150, 80, 130],
        borderColor: pastelPalette.blueLine,
        backgroundColor: pastelPalette.blue,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Lines Deleted',
        data: [30, 40, 20, 50, 35],
        borderColor: pastelPalette.greyLine,
        backgroundColor: pastelPalette.grey,
        fill: true,
        tension: 0.4
      }
    ]
  };
  if (analyticsCharts[canvasId]) analyticsCharts[canvasId].destroy();
  analyticsCharts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: {
      plugins: {
        legend: { labels: { color: colors.text } }
      },
      scales: {
        x: { ticks: { color: colors.text } },
        y: { ticks: { color: colors.text } }
      }
    }
  });
}

// --- Feature Usage Chart ---
export function renderFeatureUsageChart(canvasId, data = null) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  const colors = getThemeColors();
  const chartData = data || {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    datasets: [
      {
        label: 'Applies',
        data: [50, 60, 55, 70, 65],
        backgroundColor: pastelPalette.purple
      },
      {
        label: 'Accepts',
        data: [40, 45, 50, 60, 55],
        backgroundColor: pastelPalette.green
      },
      {
        label: 'Rejects',
        data: [10, 8, 12, 9, 11],
        backgroundColor: pastelPalette.grey
      }
    ]
  };
  if (analyticsCharts[canvasId]) analyticsCharts[canvasId].destroy();
  analyticsCharts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: chartData,
    options: {
      plugins: {
        legend: { labels: { color: colors.text } }
      },
      scales: {
        x: { stacked: true, ticks: { color: colors.text } },
        y: { stacked: true, ticks: { color: colors.text } }
      }
    }
  });
}

// --- Request Types Chart ---
export function renderRequestTypesChart(canvasId, data = null) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  const colors = getThemeColors();
  const chartData = data || {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    datasets: [
      {
        label: 'Edit Requests',
        data: [30, 35, 40, 38, 42],
        borderColor: pastelPalette.purpleLine,
        backgroundColor: pastelPalette.purple,
        fill: false,
        tension: 0.4
      },
      {
        label: 'Ask Requests',
        data: [20, 22, 18, 25, 23],
        borderColor: pastelPalette.greenLine,
        backgroundColor: pastelPalette.green,
        fill: false,
        tension: 0.4
      },
      {
        label: 'Agent Requests',
        data: [10, 12, 9, 11, 13],
        borderColor: pastelPalette.blueLine,
        backgroundColor: pastelPalette.blue,
        fill: false,
        tension: 0.4
      },
      {
        label: 'Cmd+K Usages',
        data: [5, 7, 6, 8, 7],
        borderColor: pastelPalette.greyLine,
        backgroundColor: pastelPalette.grey,
        fill: false,
        tension: 0.4
      }
    ]
  };
  if (analyticsCharts[canvasId]) analyticsCharts[canvasId].destroy();
  analyticsCharts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: {
      plugins: {
        legend: { labels: { color: colors.text } }
      },
      scales: {
        x: { ticks: { color: colors.text } },
        y: { ticks: { color: colors.text } }
      }
    }
  });
}

// --- Update all charts on theme change ---
export function updateAllAnalyticsCharts() {
  // Re-render all charts with current theme
  for (const [canvasId, chart] of Object.entries(analyticsCharts)) {
    if (chart.config.type === 'line' && canvasId === 'aiLinesChart') {
      renderAiLinesChart(canvasId);
    } else if (chart.config.type === 'bar') {
      renderFeatureUsageChart(canvasId);
    } else if (chart.config.type === 'line') {
      renderRequestTypesChart(canvasId);
    }
  }
} 