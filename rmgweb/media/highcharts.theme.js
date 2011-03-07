// Construct the theme
Highcharts.theme = {
    chart: {
        animation: false,
        zoomType: "xy"
    },
	xAxis: {
        labels: {
            formatter: function() {
                return '' + Highcharts.numberFormat(this.value, 0, '.', '');
            }
        },
        lineWidth: 1,
        gridLineWidth: 0,
        tickWidth: 1,
        tickPosition: 'inside',
        minorTickPosition: 'inside',
        minorTickInterval: 'auto',
        minorTickWidth: 1,
        minorGridLineWidth: 0
    },
    yAxis: {
        labels: {
            formatter: function() {
                return '' + Highcharts.numberFormat(this.value, 0, '.', '');
            }
        },
        lineWidth: 1,
        gridLineWidth: 0,
        tickWidth: 1,
        tickPosition: 'inside',
        minorTickPosition: 'inside',
        minorTickInterval: 'auto',
        minorTickWidth: 1,
        minorGridLineWidth: 0
    },
    legend: { enabled: false },
    plotOptions: {
        line: {
            marker: { enabled: false }
        }
    },
    tooltip: {
        formatter: function() {
            return '' + Highcharts.numberFormat(this.x, 0, '.', '') +' K, ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' kJ/mol';
        }
    },
    credits: { enabled: false }
};

// Apply the theme
var highchartsOptions = Highcharts.setOptions(Highcharts.theme);
