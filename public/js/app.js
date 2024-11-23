const zoomOptions = {
    pan: {
        enabled: true,
        mode: 'x',
        // modifierKey: "alt",
    },
    zoom: {
        wheel: {
            enabled: true,
        },
        // drag: {
        //     enabled: true,
        // },
        pinch: {
            enabled: true
        },
        mode: 'x'
    }
};

function logSystem() {
    return {
        logs: [],
        stats: [],
        showModal: false,
        showStatsModal: false,
        selectedLog: {},
        selectedStat: {},
        page: 1,
        limit: 50,
        total: 0,
        searchQuery: '',
        searchTimeout: null,
        selectedDate: '',
        showConfirmModal: false,
        currentView: 'stats',
        statsPage: 1,
        statsLimit: 50,
        statsTotal: 0,
        chartInstances: {}, // 用于存储图表实例
        isInitialized: false,
        notification: {
            show: false,
            message: '',
            type: 'success', // 'success', 'error', or 'warning'
        },
        currentPointIndex: {},
        statsSearchQuery: '',
        statsSearchTimeout: null,

        init() {
            if (!this.isInitialized) {
                // 只加载 stats 数据
                this.fetchStats();
                this.isInitialized = true;
            }
            // 确保初始状态下模态框是关闭的
            this.showModal = false;
            this.showStatsModal = false;
            this.clearChartInstances();
        },

        debounceStatsSearch() {
            clearTimeout(this.statsSearchTimeout);
            this.statsSearchTimeout = setTimeout(() => {
                this.statsPage = 1;
                this.fetchStats();
            }, 300);
        },

        async fetchStats() {
            const response = await fetch(`/api/stats?page=${this.statsPage}&limit=${this.statsLimit}&search=${this.statsSearchQuery}`);
            const data = await response.json();
            this.stats = data.stats;
            this.statsTotal = data.total;
            this.statsPage = data.page;
            this.statsLimit = data.limit;
        },

        showLogDetails(log) {
            this.selectedLog = log;
            this.showModal = true;
        },

        showStatDetails(stat) {
            // if (this.showStatsModal) {
            //     // 如果模态框已经打开，只更新数据
            //     this.selectedStat = JSON.parse(JSON.stringify(stat));
            //     this.fetchStatDetails(stat.login_id);
            // } else {
            //     // 如果模态框未打开，打开模态框并加载数据
            //     this.selectedStat = JSON.parse(JSON.stringify(stat));
            //     this.showStatsModal = true;
            //     this.$nextTick(() => {
            //         this.fetchStatDetails(stat.login_id);
            //     });
            // }
            this.selectedStat = JSON.parse(JSON.stringify(stat));
            this.showStatsModal = true;
            this.$nextTick(() => {
                this.fetchStatDetails(stat.login_id);
            });
            this.updateClickedPointInfo("", "{}");
        },

        hideStatDetails() {
            this.showStatsModal = false;
            this.clearChartInstances();
        },

        async fetchStatDetails(loginID) {
            try {
                const response = await fetch(`/api/stats/details?login_id=${loginID}`);
                const data = await response.json();
                this.updateStatDetails(data);
            } catch (error) {
                console.error('Error fetching stat details:', error);
            }
        },

        updateStatDetails(data) {
            this.selectedStat = { ...this.selectedStat, ...data.statsRecord };
            this.$nextTick(() => {
                // 清除所有现有的图表实例
                this.clearChartInstances();
                // 重新渲染所有图表
                this.renderCharts(data.statsInfo);
            });
        },

        renderCharts(statsInfo) {
            if (!statsInfo || !Array.isArray(statsInfo) || statsInfo.length === 0) {
                console.warn('No stats info available to render charts');
                return;
            }

            const chartConfigs = [
                { id: 'fpsChart', label: 'FPS', dataKey: 'fps', color: 'rgba(75, 192, 192, 1)' },
                { 
                    id: 'memoryChart', 
                    label: 'Memory', 
                    dataKeys: ['total_mem', 'used_mem', 'mono_used_mem', 'mono_heap_mem'],
                    colors: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(153, 102, 255, 1)'
                    ]
                },
                { id: 'textureChart', label: 'Texture', dataKey: 'texture', color: 'rgba(255, 159, 64, 1)' },
                { id: 'meshChart', label: 'Mesh', dataKey: 'mesh', color: 'rgba(255, 99, 71, 1)' },
                { id: 'animationChart', label: 'Animation', dataKey: 'animation', color: 'rgba(50, 205, 50, 1)' },
                { id: 'audioChart', label: 'Audio', dataKey: 'audio', color: 'rgba(0, 191, 255, 1)' },
                { id: 'fontChart', label: 'Font', dataKey: 'font', color: 'rgba(255, 140, 0, 1)' },
                { id: 'textAssetChart', label: 'Text Asset', dataKey: 'text_asset', color: 'rgba(186, 85, 211, 1)' },
                { id: 'shaderChart', label: 'Shader', dataKey: 'shader', color: 'rgba(0, 128, 128, 1)' }
            ];

            chartConfigs.forEach(config => {
                const canvas = document.getElementById(config.id);
                if (!canvas) {
                    console.warn(`Canvas element with id ${config.id} not found`);
                    return;
                }

                const ctx = canvas.getContext('2d');

                if (config.id === 'memoryChart') {
                    // 特殊处理 memoryChart
                    const datasets = config.dataKeys.map((key, index) => ({
                        label: key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
                        data: statsInfo.map(info => ({
                            x: new Date(info.mtime).getTime(),
                            y: info[key]
                        })).filter(point => point.y !== undefined && point.y !== null),
                        borderColor: config.colors[index],
                        pointStyle: 'circle',
                        pointRadius: 5,
                        spanGaps: true,
                        showLine: true,
                        pointHoverRadius: 7,
                        pic: statsInfo.map(info => info.pic),
                        process: statsInfo.map(info => info.process)
                    }));

                    if (this.chartInstances[config.id]) {
                        // 更新现有图表
                        const chart = this.chartInstances[config.id];
                        chart.data.datasets = datasets;
                        chart.update();
                    } else {
                        // 创建新的图表实例
                        this.chartInstances[config.id] = new Chart(ctx, {
                            type: 'line',
                            data: { datasets },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                spanGaps: true,
                                showLine: true,
                                scales: {
                                    x: {
                                        type: 'time',
                                        time: {
                                            unit: 'second',
                                            displayFormats: {
                                                second: 'HH:mm:ss'
                                            }
                                        },
                                        ticks: {
                                            source: 'auto',
                                            maxRotation: 0,
                                            autoSkip: true,
                                            maxTicksLimit: 10
                                        }
                                    },
                                    y: {
                                        beginAtZero: true
                                    }
                                },
                                layout: {
                                    padding: {
                                        top: 20,
                                        right: 20,
                                        bottom: 20,
                                        left: 20
                                    }
                                },
                                onClick: (evt, elements) => {
                                    if (elements.length > 0) {
                                        const index = elements[0].index;
                                        const datasetIndex = elements[0].datasetIndex;
                                        const dataset = evt.chart.data.datasets[datasetIndex];
                                        const pic = dataset.pic[index];
                                        const process = dataset.process[index];
                                        this.updateClickedPointInfo(pic, process);
                                        
                                        // 更新当前选择的索引
                                        this.currentPointIndex[config.id] = index;
                                        
                                        // 高亮显示当前点
                                        evt.chart.setActiveElements([{
                                            datasetIndex: datasetIndex,
                                            index: index
                                        }]);
                                        evt.chart.update();
                                    }
                                },
                                plugins: {
                                    zoom: zoomOptions,
                                    title: {
                                        display: true,
                                        text: 'Memory Usage'
                                    },
                                    tooltip: {
                                        usePointStyle: true,
                                        callbacks: {
                                            title: function(context) {
                                                let date = new Date(context[0].parsed.x);
                                                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                                            }
                                        }
                                    }
                                },
                                onHover: (event, chartElement) => {
                                    if (event.native) {
                                        event.native.target.style.cursor = chartElement[0] ? 'pointer' : 'default';
                                    }
                                }
                            },
                            plugins: [ChartZoom]
                        });
                    }
                } else {
                    const chartData = statsInfo.map(info => ({
                        x: new Date(info.mtime).getTime(),
                        y: info[config.dataKey]
                    })).filter(point => point.y !== undefined && point.y !== null);

                    if (chartData.length === 0) {
                        console.warn(`No valid data for chart ${config.id}`);
                        return;
                    }

                    if (this.chartInstances[config.id]) {
                        // 更新现有图表
                        const chart = this.chartInstances[config.id];
                        chart.data.datasets[0].data = chartData;
                        chart.data.datasets[0].pic = statsInfo.map(info => info.pic);
                        chart.data.datasets[0].process = statsInfo.map(info => info.process);
                        chart.update();
                    } else {
                        // 创建新的图表实例
                        this.chartInstances[config.id] = new Chart(ctx, {
                            type: 'line',
                            data: {
                                datasets: [{
                                    label: config.label,
                                    data: chartData,
                                    borderColor: config.color,
                                    pointStyle: 'circle',
                                    pointRadius: 5,
                                    spanGaps: true,
                                    showLine: true,
                                    pointHoverRadius: 7,
                                    pic: statsInfo.map(info => info.pic),
                                    process: statsInfo.map(info => info.process)
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                spanGaps: true,
                                showLine: true,
                                scales: {
                                    x: {
                                        type: 'time',
                                        time: {
                                            unit: 'second',
                                            displayFormats: {
                                                second: 'HH:mm:ss'
                                            }
                                        },
                                        ticks: {
                                            source: 'auto',
                                            maxRotation: 0,
                                            autoSkip: true,
                                            maxTicksLimit: 10
                                        }
                                    },
                                    y: {
                                        beginAtZero: true
                                    }
                                },
                                layout: {
                                    padding: {
                                        top: 20,
                                        right: 20,
                                        bottom: 20,
                                        left: 20
                                    }
                                },
                                onClick: (evt, elements) => {
                                    if (elements.length > 0) {
                                        const index = elements[0].index;
                                        const datasetIndex = elements[0].datasetIndex;
                                        const dataset = evt.chart.data.datasets[datasetIndex];
                                        const pic = dataset.pic[index];
                                        const process = dataset.process[index];
                                        this.updateClickedPointInfo(pic, process);
                                        
                                        // 更��当前选择的索引
                                        this.currentPointIndex[config.id] = index;
                                        
                                        // 高亮显示当前点
                                        evt.chart.setActiveElements([{
                                            datasetIndex: datasetIndex,
                                            index: index
                                        }]);
                                        evt.chart.update();
                                    }
                                },
                                plugins: {
                                    zoom: zoomOptions,
                                    title: {
                                        display: true,
                                        text: config.label
                                    },
                                    tooltip: {
                                        usePointStyle: true,
                                        callbacks: {
                                            title: function(context) {
                                                let date = new Date(context[0].parsed.x);
                                                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                                            }
                                        }
                                    }
                                },
                                onHover: (event, chartElement) => {
                                    if (event.native) {
                                        event.native.target.style.cursor = chartElement[0] ? 'pointer' : 'default';
                                    }
                                }
                            },
                            plugins: [ChartZoom]
                        });
                    }
                }
            });

            // 清理不再需要的图表实例
            Object.keys(this.chartInstances).forEach(key => {
                if (!chartConfigs.some(config => config.id === key)) {
                    this.chartInstances[key].destroy();
                    delete this.chartInstances[key];
                }
            });

            // 删除不再需要的图表实例
            const memoryChartIds = ['totalMemChart', 'usedMemChart', 'monoUsedMemChart', 'monoHeapMemChart'];
            memoryChartIds.forEach(id => {
                if (this.chartInstances[id]) {
                    this.chartInstances[id].destroy();
                    delete this.chartInstances[id];
                }
            });
        },

        showEnlarged(imgSrc) {
            const enlargedContainer = document.getElementById('enlargedImageContainer');
            const enlargedImage = document.getElementById('enlargedImage');
            enlargedImage.src = imgSrc;
            enlargedContainer.classList.remove('hidden');
        },

        hideEnlarged() {
            const enlargedContainer = document.getElementById('enlargedImageContainer');
            setTimeout(() => {
                enlargedContainer.classList.add('hidden');
            }, 300);
        },

        formatProcess(process) {
            // 如果 process 是 JSON 格式，尝试解码
            if (typeof process === 'string') {
                try {
                    process = JSON.parse(process);
                } catch (e) {
                    // 如果解析失败，保持原样
                    return '解析执行统计数据的 JSON 失败：' + process;
                }
            }

            if (process == undefined || process == null || !Array.isArray(process)) return '';

            return process.map(item => {
                if (item == undefined || item == null) return '';

                var result = '[' + item['name'] + ']<br>';
                if (item['list'] != null && Array.isArray(item['list'])) {
                    return result + item['list'].map(subItem => {
                        return subItem.replace(/\\n/g, '<br>').replace(/ /g, '&nbsp;')
                    }).join('<br>');
                }
                return result.replace(/\\n/g, '<br>').replace(/ /g, '&nbsp;')
            }).join('<br><br>');
        },

        updateClickedPointInfo(pic, process) {
            const processElement = document.getElementById('processInfo');
            processElement.innerHTML = this.formatProcess(process);
            const screenshotElement = document.getElementById('screenshot');
            const picPath = pic.replace(/\\/g, '/');
            var picHTML = "";
            if (picPath != "") {
                picHTML = `
                <img src="${picPath}" alt="Stats Image" class="h-40 cursor-zoom-in stats-thumbnail" 
                     @mouseenter="showEnlarged('${picPath}')"
                     @mouseleave="hideEnlarged()">
                `;
            }
            screenshotElement.innerHTML = picHTML;
        },

        changePage(newPage) {
            if (newPage >= 1 && newPage <= Math.ceil(this.total / this.limit)) {
                this.page = newPage;
                this.fetchLogs();
            }
        },

        changeStatsPage(newPage) {
            if (newPage >= 1 && newPage <= Math.ceil(this.statsTotal / this.statsLimit)) {
                this.statsPage = newPage;
                this.fetchStats();
            }
        },

        // begin 日志接口

        debounceSearch() {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.page = 1;
                this.fetchLogs();
            }, 300);
        },

        async fetchLogs() {
            const response = await fetch(`/api/logs?page=${this.page}&limit=${this.limit}&search=${this.searchQuery}`);
            const data = await response.json();
            this.logs = data.logs;
            this.total = data.total;
            this.page = data.page;
            this.limit = data.limit;
        },

        async deleteLogsBefore() {
            if (!this.selectedDate) {
                this.showNotification('请先选择一个日期！', 'warning');
                return;
            }
            if (confirm('确定要删除选择日期前的日志数据吗？')) {
                try {
                    const response = await fetch(`/api/logs/before?date=${this.selectedDate}`, {
                        method: 'DELETE'
                    });
                    const result = await response.json();
                    if (response.ok && result.code === 0) {
                        this.showNotification(`成功删除 ${result.count} 条日志。`, 'success');
                        this.fetchLogs();
                    } else {
                        this.showNotification('删除日志失败: ' + result.error, 'error');
                    }
                } catch (error) {
                    this.showNotification('删除日志失败： ' + error.message, 'error');
                }
            }
        },

        deleteLog(id) {
            fetch(`/api/logs/${id}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(result => {
                    if (result.code === 0) {
                        this.showNotification('日志已成功删除', 'success');
                        this.fetchLogs();
                    } else {
                        this.showNotification('删除日志失败: ' + result.error, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    this.showNotification('删除日志时发生错误', 'error');
                });
        },

        formatStack(stack) {
            if (stack == undefined || stack == null) return '';
            return stack.replace(/\\n/g, '<br>').replace(/ /g, '&nbsp;');
        },

        viewLogs() {
            this.currentView = 'logs';
            if (this.logs.length === 0) {
                this.fetchLogs();
            }
        },

        // end 日志接口

        // begin 统计接口

        viewStats() {
            this.currentView = 'stats';
            if (this.stats.length === 0) {
                this.fetchStats();
            }
        },

        async deleteStatsBefore() {
            if (!this.selectedDate) {
                this.showNotification('请先选择一个日期！', 'warning');
                return;
            }
            if (confirm('确定要删除选择日期前的统计数据吗？')) {
                try {
                    const response = await fetch(`/api/stats/before?date=${this.selectedDate}`, {
                        method: 'DELETE'
                    });
                    const result = await response.json();
                    if (response.ok && result.code === 0) {
                        this.showNotification(`成功删除 ${result.count} 条记录。`, 'success');
                        this.fetchStats();
                    } else {
                        this.showNotification('删除统计数据失败: ' + result.error, 'error');
                    }
                } catch (error) {
                    this.showNotification('删除记录失败：' + error.message, 'error');
                }
            }
        },

        deleteStat(id) {
            if (confirm('确定要删除这条统计数据吗？')) {
                fetch(`/api/stats/${id}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(result => {
                        if (result.code === 0) {
                            this.showNotification('统计数据已成功删除', 'success');
                            this.fetchStats();
                        } else {
                            this.showNotification('删除统计数据失败: ' + result.error, 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        this.showNotification('删除统计数据时发生错误', 'error');
                    });
            }
        },

        clearChartInstances() {
            Object.values(this.chartInstances).forEach(chart => {
                if (chart) {
                    chart.destroy();
                }
            });
            this.chartInstances = {};
        },

        resetZoom(chartId) {
            const chart = this.chartInstances[chartId];
            if (chart) {
                chart.resetZoom();
            }
        },

        showNotification(message, type = 'success', duration = 3000) {
            this.notification.show = true;
            this.notification.message = message;
            this.notification.type = type;

            setTimeout(() => {
                this.notification.show = false;
            }, duration);
        },

        formatDate(dateString) {
            if (!dateString) return ''; // 处理空值
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return 'Invalid Date'; // 处理无效日期

            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');

            return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        },

        // end 统计接口

        showNextLog() {
            const currentIndex = this.logs.findIndex(log => log.id === this.selectedLog.id);
            if (currentIndex < this.logs.length - 1) {
                this.selectedLog = this.logs[currentIndex + 1];
            } else {
                if (this.page * this.limit < this.total) {
                    this.changePage(this.page + 1).then(() => {
                        this.selectedLog = this.logs[0];
                    });
                } else {
                    this.showNotification('已经是最后一条日志', 'warning');
                }
            }
        },

        showNextStat() {
            const currentIndex = this.stats.findIndex(stat => stat.id === this.selectedStat.id);
            if (currentIndex < this.stats.length - 1) {
                this.showStatDetails(this.stats[currentIndex + 1]);
            } else {
                if (this.statsPage * this.statsLimit < this.statsTotal) {
                    this.changeStatsPage(this.statsPage + 1).then(() => {
                        this.showStatDetails(this.stats[0]);
                    });
                } else {
                    this.showNotification('已经是最后一条统计数据', 'warning');
                }
            }
        },

        showPreviousLog() {
            const currentIndex = this.logs.findIndex(log => log.id === this.selectedLog.id);
            if (currentIndex > 0) {
                this.selectedLog = this.logs[currentIndex - 1];
            } else {
                if (this.page > 1) {
                    this.changePage(this.page - 1).then(() => {
                        this.selectedLog = this.logs[this.logs.length - 1];
                    });
                } else {
                    this.showNotification('已经是第一条日志', 'warning');
                }
            }
        },

        showPreviousStat() {
            const currentIndex = this.stats.findIndex(stat => stat.id === this.selectedStat.id);
            if (currentIndex > 0) {
                this.showStatDetails(this.stats[currentIndex - 1]);
            } else {
                if (this.statsPage > 1) {
                    this.changeStatsPage(this.statsPage - 1).then(() => {
                        this.showStatDetails(this.stats[this.stats.length - 1]);
                    });
                } else {
                    this.showNotification('已经是第一条统计数据', 'warning');
                }
            }
        },

        navigateChartPoint(direction, chartId) {
            const chart = this.chartInstances[chartId];
            if (!chart) return;

            const dataset = chart.data.datasets[0];
            if (!dataset || !dataset.data || dataset.data.length === 0) return;

            if (this.currentPointIndex[chartId] === undefined) {
                this.currentPointIndex[chartId] = 0;
            }

            let newIndex;
            if (direction === 'nextPoint') {
                newIndex = this.currentPointIndex[chartId] - 1;
                if (newIndex < 0) {
                    this.showNotification('已经是最后一个数据点', 'warning');
                    return;
                }
            } else {
                newIndex = this.currentPointIndex[chartId] + 1;
                if (newIndex >= dataset.data.length) {
                    this.showNotification('已经是第一个数据点', 'warning');
                    return;
                }
            }

            this.currentPointIndex[chartId] = newIndex;

            const point = dataset.data[this.currentPointIndex[chartId]];
            const pic = dataset.pic[this.currentPointIndex[chartId]];
            const process = dataset.process[this.currentPointIndex[chartId]];

            this.updateClickedPointInfo(pic, process);

            // 高亮显示当前点
            chart.setActiveElements([{
                datasetIndex: 0,
                index: this.currentPointIndex[chartId]
            }]);

            // 确保视图聚焦到选中的点
            chart.update();

            // 滚动到选中的点
            chart.scrollTo(point.x);
        },
    }
}