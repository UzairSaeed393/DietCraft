document.addEventListener('DOMContentLoaded', function () {
    const root = document.getElementById('dashboard-root');
    if (!root) return;

    // parse data from data- attributes
    const labels = JSON.parse(root.dataset.weekLabels || '[]');
    const dailyCalories = JSON.parse(root.dataset.dailyCalories || '[]');
    const dailyProtein = JSON.parse(root.dataset.dailyProtein || '[]');
    const dailyExBurned = JSON.parse(root.dataset.dailyExBurned || '[]');
    const dailyExCompleted = JSON.parse(root.dataset.dailyExCompleted || '[]');

    const calorieProgress = parseInt(root.dataset.calorieProgress || '0', 10);
    const proteinProgress = parseInt(root.dataset.proteinProgress || '0', 10);
    const workoutProgress = parseInt(root.dataset.workoutProgress || '0', 10);

    // today's values and targets
    const calorieTarget = parseFloat(root.dataset.calorieTarget || '2000');
    const proteinTarget = parseFloat(root.dataset.proteinTarget || '80');
    const dailyWorkoutTarget = parseFloat(root.dataset.dailyWorkoutTarget || '1');
    const todayCalories = parseFloat(root.dataset.todayCalories || '0');
    const todayProtein = parseFloat(root.dataset.todayProtein || '0');
    const todayExBurned = parseFloat(root.dataset.todayExBurned || '0');
    const todayExCompleted = parseFloat(root.dataset.todayExCompleted || '0');

    // set today's progress bars (these show today's completion vs daily targets)
    const calBar = document.getElementById('calorie-progress');
    const protBar = document.getElementById('protein-progress');
    const workBar = document.getElementById('workout-progress');
    const calLabel = document.getElementById('calorie-label');
    const protLabel = document.getElementById('protein-label');
    const workLabel = document.getElementById('workout-label');

    const todayCalPct = Math.min(Math.round((calorieTarget ? (todayCalories / calorieTarget) * 100 : 0)), 100);
    const todayProtPct = Math.min(Math.round((proteinTarget ? (todayProtein / proteinTarget) * 100 : 0)), 100);
    const todayWorkPct = Math.min(Math.round((dailyWorkoutTarget ? (todayExCompleted / dailyWorkoutTarget) * 100 : 0)), 100);

    if (calBar) calBar.style.width = todayCalPct + '%';
    if (protBar) protBar.style.width = todayProtPct + '%';
    if (workBar) workBar.style.width = todayWorkPct + '%';

    if (calLabel) calLabel.textContent = `${Math.round(todayCalories)} / ${Math.round(calorieTarget)} kcal`;
    if (protLabel) protLabel.textContent = `${Math.round(todayProtein)} g / ${Math.round(proteinTarget)} g`;
    if (workLabel) workLabel.textContent = `${Math.round(todayExCompleted)} / ${Math.round(dailyWorkoutTarget)}`;

    // Chart setup (horizontal bars)
    const ctx = document.getElementById('weeklyChart');
    let chart = null;

    function buildChart(type) {
        if (!ctx) return;
        if (chart) chart.destroy();

        let dataset = [];
        let options = {
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } }
        };

        if (type === 'calories') {
            dataset = [{ label: 'Calories', data: dailyCalories, backgroundColor: 'rgba(255,159,28,0.95)', borderRadius: 6 }];
            // draw end-of-bar pill labels with numeric kcal
            options.plugins = options.plugins || {};
            options.plugins.afterDatasetsDraw = function (chartInstance) {
                const ctx = chartInstance.ctx;
                const meta = chartInstance.getDatasetMeta(0);
                const values = dailyCalories || [];
                const pillBg = getComputedStyle(document.documentElement).getPropertyValue('--bg1') || 'rgb(148,215,237)';
                ctx.save();
                ctx.font = '12px ' + (getComputedStyle(document.documentElement).getPropertyValue('--font1') || 'sans-serif');
                ctx.textBaseline = 'middle';

                function roundRect(ctx, x, y, w, h, r) {
                    const minSize = Math.min(w, h);
                    if (r > minSize / 2) r = minSize / 2;
                    ctx.beginPath();
                    ctx.moveTo(x + r, y);
                    ctx.arcTo(x + w, y, x + w, y + h, r);
                    ctx.arcTo(x + w, y + h, x, y + h, r);
                    ctx.arcTo(x, y + h, x, y, r);
                    ctx.arcTo(x, y, x + w, y, r);
                    ctx.closePath();
                }

                const textColor = getComputedStyle(document.documentElement).getPropertyValue('--darktext') || '#0A2633';
                for (let i = 0; i < meta.data.length; i++) {
                    const bar = meta.data[i];
                    const val = values[i] || 0;
                    if (!val) continue;
                    const text = `${Math.round(val)} kcal`;
                    const padding = 8;
                    const textWidth = ctx.measureText(text).width;
                    const rectW = textWidth + padding * 2;
                    const rectH = 22;
                    const x = bar.x + 10;
                    const y = bar.y - rectH / 2;

                    ctx.fillStyle = pillBg;
                    roundRect(ctx, x, y, rectW, rectH, rectH / 2);
                    ctx.fill();

                    ctx.fillStyle = textColor.trim();
                    ctx.fillText(text, x + padding, y + rectH / 2);
                }
                ctx.restore();
            };
        } else if (type === 'protein') {
            dataset = [{ label: 'Protein', data: dailyProtein, backgroundColor: 'rgba(255,159,28,0.95)', borderRadius: 6 }];
            // draw end-of-bar pill labels with numeric g
            options.plugins = options.plugins || {};
            options.plugins.afterDatasetsDraw = function (chartInstance) {
                const ctx = chartInstance.ctx;
                const meta = chartInstance.getDatasetMeta(0);
                const values = dailyProtein || [];
                const pillBg = getComputedStyle(document.documentElement).getPropertyValue('--bg1') || 'rgb(148,215,237)';
                ctx.save();
                ctx.font = '12px ' + (getComputedStyle(document.documentElement).getPropertyValue('--font1') || 'sans-serif');
                ctx.textBaseline = 'middle';

                function roundRect(ctx, x, y, w, h, r) {
                    const minSize = Math.min(w, h);
                    if (r > minSize / 2) r = minSize / 2;
                    ctx.beginPath();
                    ctx.moveTo(x + r, y);
                    ctx.arcTo(x + w, y, x + w, y + h, r);
                    ctx.arcTo(x + w, y + h, x, y + h, r);
                    ctx.arcTo(x, y + h, x, y, r);
                    ctx.arcTo(x, y, x + w, y, r);
                    ctx.closePath();
                }

                const textColor = getComputedStyle(document.documentElement).getPropertyValue('--darktext') || '#0A2633';
                for (let i = 0; i < meta.data.length; i++) {
                    const bar = meta.data[i];
                    const val = values[i] || 0;
                    if (!val) continue;
                    const text = `${Math.round(val)} g`;
                    const padding = 8;
                    const textWidth = ctx.measureText(text).width;
                    const rectW = textWidth + padding * 2;
                    const rectH = 22;
                    const x = bar.x + 10;
                    const y = bar.y - rectH / 2;

                    ctx.fillStyle = pillBg;
                    roundRect(ctx, x, y, rectW, rectH, rectH / 2);
                    ctx.fill();

                    ctx.fillStyle = textColor.trim();
                    ctx.fillText(text, x + padding, y + rectH / 2);
                }
                ctx.restore();
            };
        } else if (type === 'exercises') {
            // exercises view focuses on counts (completed per day)
            dataset = [{ label: 'Exercises Completed', data: dailyExCompleted, backgroundColor: 'rgba(255,159,28,0.95)', borderRadius: 6 }];
            options.scales.x = { beginAtZero: true, stacked: false };

            // draw small pill labels showing completed out of daily total (e.g. 2/4)
            options.plugins = options.plugins || {};
            options.plugins.afterDatasetsDraw = function (chartInstance) {
                const ctx = chartInstance.ctx;
                const meta = chartInstance.getDatasetMeta(0);
                const completed = dailyExCompleted || [];
                const pillBg = getComputedStyle(document.documentElement).getPropertyValue('--btn2') || 'rgb(30,60,85)';
                const dailyTotal = typeof dailyWorkoutTarget === 'number' ? dailyWorkoutTarget : parseFloat(root.dataset.dailyWorkoutTarget || '4');
                ctx.save();
                ctx.font = '12px ' + (getComputedStyle(document.documentElement).getPropertyValue('--font1') || 'sans-serif');
                ctx.textBaseline = 'middle';

                function roundRect(ctx, x, y, w, h, r) {
                    const minSize = Math.min(w, h);
                    if (r > minSize / 2) r = minSize / 2;
                    ctx.beginPath();
                    ctx.moveTo(x + r, y);
                    ctx.arcTo(x + w, y, x + w, y + h, r);
                    ctx.arcTo(x + w, y + h, x, y + h, r);
                    ctx.arcTo(x, y + h, x, y, r);
                    ctx.arcTo(x, y, x + w, y, r);
                    ctx.closePath();
                }

                for (let i = 0; i < meta.data.length; i++) {
                    const bar = meta.data[i];
                    const count = completed[i] || 0;
                    if (count === 0) continue; // skip zeros
                    const text = `${count}/${dailyTotal}`;
                    const padding = 8;
                    const textWidth = ctx.measureText(text).width;
                    const rectW = textWidth + padding * 2;
                    const rectH = 22;
                    const x = bar.x + 10;
                    const y = bar.y - rectH / 2;

                    ctx.fillStyle = pillBg;
                    roundRect(ctx, x, y, rectW, rectH, rectH / 2);
                    ctx.fill();

                    ctx.fillStyle = '#fff';
                    ctx.fillText(text, x + padding, y + rectH / 2);
                }
                ctx.restore();
            };
        }

        chart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: { labels: labels, datasets: dataset },
            options: options
        });
    }

    // buttons
    const btnCal = document.getElementById('btn-calories');
    const btnProt = document.getElementById('btn-protein');
    const btnEx = document.getElementById('btn-exercises');
    const btns = [btnCal, btnProt, btnEx];

    function setActive(btn) {
        btns.forEach(b => b && b.classList.remove('active'));
        if (btn) btn.classList.add('active');
    }

    if (btnCal) btnCal.addEventListener('click', function () { buildChart('calories'); setActive(btnCal); });
    if (btnProt) btnProt.addEventListener('click', function () { buildChart('protein'); setActive(btnProt); });
    if (btnEx) btnEx.addEventListener('click', function () { buildChart('exercises'); setActive(btnEx); });

    // initial view
    if (dailyCalories && dailyCalories.some(v => v > 0)) {
        buildChart('calories');
        setActive(btnCal);
    } else if (dailyProtein && dailyProtein.some(v => v > 0)) {
        buildChart('protein');
        setActive(btnProt);
    } else if (dailyExCompleted && dailyExCompleted.some(v => v > 0)) {
        buildChart('exercises');
        setActive(btnEx);
    } else {
        // no data: leave chart empty and show placeholder message
        const wrapper = document.getElementById('chart-wrapper');
        if (wrapper) wrapper.innerHTML = '<div style="padding:30px;color:var(--darktext)">No data available for this week. Log meals or mark exercises done to populate the chart.</div>';
    }

});
