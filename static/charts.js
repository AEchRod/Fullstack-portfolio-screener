/* Draws the charts on the results page from the JSON that Flask embeds in #chart-data. */
(function () {
    'use strict';

    var dataEl = document.getElementById('chart-data');
    if (!dataEl || typeof Chart === 'undefined') return;

    var payload = JSON.parse(dataEl.textContent);
    var series = payload.series;
    var labels = payload.labels;
    var root = document.documentElement;
    var single = series.length === 1;

    var priceCanvas = document.getElementById('price-chart');
    var priceSubtitle = document.getElementById('price-subtitle');
    var modeInputs = document.querySelectorAll('input[name="price-mode"]');
    var volumeCanvases = document.querySelectorAll('.volume-chart');

    // several tickers start at different prices, so compare them as % change by default
    var mode = single ? 'price' : 'change';
    var hidden = series.map(function () { return false; });
    var priceChart = null;
    var volumeCharts = [];

    var FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.font.family = FONT;
    Chart.defaults.font.size = 12;

    /* ---------- formatting ---------- */

    var compact = new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 });
    var whole = new Intl.NumberFormat();

    function formatPrice(value) {
        if (value == null) return '—';
        var digits = Math.abs(value) >= 1 ? 2 : 4;
        return value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
    }

    function formatPercent(value, digits) {
        if (value == null) return '—';
        return (value > 0 ? '+' : '') + value.toFixed(digits == null ? 2 : digits) + '%';
    }

    // Labels are 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM' in the exchange's own time. Building them as
    // UTC and formatting in UTC keeps them from shifting into the viewer's timezone.
    function toDate(label) {
        var p = label.split(/[-T:]/).map(Number);
        return new Date(Date.UTC(p[0], p[1] - 1, p[2], p[3] || 0, p[4] || 0));
    }

    var dates = labels.map(toDate);
    var spanDays = (dates[dates.length - 1] - dates[0]) / 864e5;
    var oneDay = labels[0].slice(0, 10) === labels[labels.length - 1].slice(0, 10);
    var tickDate = new Intl.DateTimeFormat(undefined,
        payload.intraday && oneDay ? { hour: 'numeric', minute: '2-digit', timeZone: 'UTC' }
            : spanDays > 400 ? { month: 'short', year: 'numeric', timeZone: 'UTC' }
                : { month: 'short', day: 'numeric', timeZone: 'UTC' });
    var fullDate = new Intl.DateTimeFormat(undefined,
        payload.intraday ? { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }
            : { dateStyle: 'medium', timeZone: 'UTC' });

    /* ---------- colours ---------- */

    function tokens() {
        var css = getComputedStyle(root);
        function token(name) { return css.getPropertyValue(name).trim(); }
        return {
            surface: token('--surface-1'),
            text: token('--text-primary'),
            textSecondary: token('--text-secondary'),
            muted: token('--text-muted'),
            grid: token('--grid'),
            baseline: token('--baseline'),
            border: token('--border'),
            series: series.map(function (s, i) { return token('--series-' + (i + 1)); })
        };
    }

    function withAlpha(hex, alpha) {
        var n = parseInt(hex.slice(1), 16);
        return 'rgba(' + (n >> 16) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + alpha + ')';
    }

    /* ---------- plugins ---------- */

    // a vertical hairline at the hovered date, drawn behind the lines
    var crosshair = {
        id: 'crosshair',
        beforeDatasetsDraw: function (chart, args, options) {
            var active = chart.tooltip && chart.tooltip.getActiveElements();
            if (!active || !active.length) return;
            var x = Math.round(active[0].element.x) + 0.5;
            var ctx = chart.ctx;
            ctx.save();
            ctx.strokeStyle = options.color;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(x, chart.chartArea.top);
            ctx.lineTo(x, chart.chartArea.bottom);
            ctx.stroke();
            ctx.restore();
        }
    };

    // Each line ends in a dot with its ticker and latest value beside it. A label that would
    // overlap one already drawn is skipped; the legend and tooltip still name that line.
    var endLabels = {
        id: 'endLabels',
        afterDatasetsDraw: function (chart, args, options) {
            if (!options.enabled) return;
            var ends = [];
            chart.data.datasets.forEach(function (dataset, i) {
                if (!chart.isDatasetVisible(i)) return;
                for (var j = dataset.data.length - 1; j >= 0; j--) {
                    if (dataset.data[j] != null) {
                        var point = chart.getDatasetMeta(i).data[j];
                        ends.push({ x: point.x, y: point.y, color: dataset.borderColor,
                                    text: options.text(dataset, dataset.data[j]) });
                        return;
                    }
                }
            });
            ends.sort(function (a, b) { return a.y - b.y; });

            var ctx = chart.ctx;
            var placed = [];
            ctx.save();
            ctx.font = options.font;
            ctx.textBaseline = 'middle';
            ends.forEach(function (end) {
                ctx.beginPath();
                ctx.arc(end.x, end.y, 6, 0, 2 * Math.PI);
                ctx.fillStyle = options.surface;
                ctx.fill();
                ctx.beginPath();
                ctx.arc(end.x, end.y, 4, 0, 2 * Math.PI);
                ctx.fillStyle = end.color;
                ctx.fill();
                if (placed.some(function (y) { return Math.abs(y - end.y) < 16; })) return;
                placed.push(end.y);
                ctx.fillStyle = options.color;
                ctx.fillText(end.text, end.x + 10, end.y);
            });
            ctx.restore();
        }
    };

    /* ---------- shared options ---------- */

    function xAxis(t, maxTicks) {
        return {
            grid: { display: false },
            border: { color: t.baseline },
            ticks: {
                color: t.muted,
                maxRotation: 0,
                autoSkip: true,
                autoSkipPadding: 16,
                maxTicksLimit: maxTicks,
                callback: function (value) { return tickDate.format(dates[value]); }
            }
        };
    }

    function tooltip(t) {
        return {
            backgroundColor: t.surface,
            titleColor: t.text,
            bodyColor: t.text,
            borderColor: t.border,
            borderWidth: 1,
            cornerRadius: 6,
            padding: 10,
            boxPadding: 6,
            usePointStyle: true,
            titleFont: { weight: '600' },
            callbacks: {
                title: function (items) { return fullDate.format(dates[items[0].dataIndex]); }
            }
        };
    }

    /* ---------- price chart ---------- */

    function updateSubtitle() {
        var subject = single ? series[0].ticker + ' closing price' : 'Closing price';
        priceSubtitle.textContent = mode === 'change'
            ? subject + ', % change since ' + fullDate.format(dates[0])
            : subject;
    }

    function buildPriceChart(t) {
        var isChange = mode === 'change';
        var format = isChange ? function (v) { return formatPercent(v); } : formatPrice;
        var showEndLabels = series.length <= 4;
        var labelFont = '12px ' + FONT;

        function endText(dataset, value) { return dataset.label + ' ' + format(value); }

        var datasets = series.map(function (s, i) {
            var color = t.series[i];
            return {
                label: s.ticker,
                data: isChange ? s.change_pct : s.close,
                hidden: hidden[i],
                borderColor: color,
                backgroundColor: single ? withAlpha(color, 0.1) : color,
                // one ticker gets a light wash under its line
                fill: single ? (isChange ? 'origin' : 'start') : false,
                borderWidth: 2,
                borderJoinStyle: 'round',
                borderCapStyle: 'round',
                pointRadius: 0,
                pointHoverRadius: 4,
                pointHitRadius: 12,
                pointHoverBackgroundColor: color,
                pointHoverBorderColor: t.surface,
                pointHoverBorderWidth: 2,
                spanGaps: true
            };
        });

        // leave room on the right for the end labels
        var padRight = 8;
        if (showEndLabels) {
            var measure = document.createElement('canvas').getContext('2d');
            measure.font = labelFont;
            datasets.forEach(function (dataset) {
                var last = dataset.data.filter(function (v) { return v != null; }).pop();
                padRight = Math.max(padRight, measure.measureText(endText(dataset, last)).width + 18);
            });
        }

        var tip = tooltip(t);
        tip.filter = function (item) { return item.parsed.y != null; };
        tip.itemSort = function (a, b) { return b.parsed.y - a.parsed.y; };
        tip.callbacks.label = function (item) { return format(item.parsed.y) + '  ' + item.dataset.label; };
        tip.callbacks.labelPointStyle = function () { return { pointStyle: 'line', rotation: 0 }; };
        tip.callbacks.labelColor = function (item) {
            return { borderColor: item.dataset.borderColor, backgroundColor: item.dataset.borderColor, borderWidth: 2 };
        };

        return new Chart(priceCanvas, {
            type: 'line',
            data: { labels: labels, datasets: datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: { mode: 'index', intersect: false },
                layout: { padding: { top: 8, right: padRight } },
                scales: {
                    x: xAxis(t, 7),
                    y: {
                        border: { display: false },
                        grid: {
                            // in % change mode the 0% line is the starting price, so it is drawn darker
                            color: function (c) { return isChange && c.tick && c.tick.value === 0 ? t.baseline : t.grid; }
                        },
                        ticks: {
                            color: t.muted,
                            maxTicksLimit: 6,
                            callback: function (value) {
                                if (isChange) return formatPercent(value, Number.isInteger(value) ? 0 : 1);
                                return Math.abs(value) >= 10000 ? compact.format(value) : value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: !single,
                        position: 'top',
                        align: 'start',
                        labels: { color: t.textSecondary, usePointStyle: true, pointStyle: 'line', padding: 16 }
                    },
                    tooltip: tip,
                    crosshair: { color: t.baseline },
                    endLabels: { enabled: showEndLabels, font: labelFont, color: t.textSecondary, surface: t.surface, text: endText }
                }
            },
            plugins: [crosshair, endLabels]
        });
    }

    /* ---------- volume charts (one small chart per ticker) ---------- */

    function buildVolumeChart(canvas, t) {
        var i = Number(canvas.dataset.index);
        var color = t.series[i];

        var tip = tooltip(t);
        tip.displayColors = false;
        tip.callbacks.label = function (item) {
            return item.parsed.y == null ? 'No data' : whole.format(item.parsed.y) + ' shares';
        };

        return new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: series[i].ticker,
                    data: series[i].volume,
                    backgroundColor: color,
                    hoverBackgroundColor: withAlpha(color, 0.7),
                    borderRadius: 4,
                    borderSkipped: 'start',
                    maxBarThickness: 24,
                    categoryPercentage: 0.9,
                    barPercentage: 0.8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    x: xAxis(t, single ? 7 : 4),
                    y: {
                        beginAtZero: true,
                        border: { display: false },
                        grid: { color: t.grid },
                        ticks: { color: t.muted, maxTicksLimit: 4, callback: function (value) { return compact.format(value); } }
                    }
                },
                plugins: { legend: { display: false }, tooltip: tip }
            }
        });
    }

    /* ---------- drawing ---------- */

    function drawPriceChart(t) {
        if (priceChart) {
            // keep tickers hidden from the legend hidden when the chart is redrawn
            hidden = series.map(function (s, i) { return !priceChart.isDatasetVisible(i); });
            priceChart.destroy();
        }
        updateSubtitle();
        priceChart = buildPriceChart(t || tokens());
    }

    function drawAll() {
        var t = tokens();
        drawPriceChart(t);
        volumeCharts.forEach(function (chart) { chart.destroy(); });
        volumeCharts = Array.prototype.map.call(volumeCanvases, function (canvas) {
            return buildVolumeChart(canvas, t);
        });
    }

    modeInputs.forEach(function (input) {
        input.checked = input.value === mode;
        input.addEventListener('change', function () {
            mode = input.value;
            drawPriceChart();
        });
    });

    // redraw in the new colours when the page switches between light and dark
    new MutationObserver(drawAll).observe(root, { attributes: true, attributeFilter: ['data-bs-theme'] });

    drawAll();
})();
