plotKinetics = function(id, kseries) {
    series = [];
    var identicalkUnits = true;
    
    for (var i = 0; i < kseries.length; i++) {
        series.push({
            name: kseries[i][0],
            data: kseries[i][1],
            index: i,
            events: {
                click: function() {
                    if (legendEnabled) this.hide();
                },
            },
            animation: false
        });
        
        if (kseries[i][2] !== kunits) {
        	identicalkUnits = false; } 
        }
        	
    if (identicalkUnits) {
		kunits = '(' + kunits + ')';
		}
	else {
     	kunits = '';
        }       
        
    var legendEnabled = (kseries.length > 1);
    
    if (legendEnabled) {
        series.push({
            name: "Average of selected rates",
            data: [],
            type: 'scatter',
            id: 'average'
        })
    }
    
    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line',
            events: {
                redraw: function() {
                    if (average_stale){
                        calculateAverage();
                    } else {
                        average_stale = true;
                    }
                }
            },
        },
        title: { text: 'Rate coefficient' },
        xAxis: {
            title: { text: '1000 / Temperature (1000/' + Tunits + ')' },
            min: 0,
            max: 4
        },
        yAxis: {
            title: { text: 'Rate coefficient ' + kunits },
            labels: {
                formatter: function() {
                    exponent = Math.floor(this.value);
                    mantissa = Math.pow(10, this.value) / Math.pow(10, exponent);
                    return '' + Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '');
                }
            },
        },
        legend: {
            enabled: legendEnabled,
            layout: 'vertical',
            labelFormatter: function() {
                return this.name;
            },
        },
        series: series,
        tooltip: {
            formatter: function() {
                T = 1000.0/this.x;
                exponent = Math.floor(this.y);
                mantissa = Math.pow(10, this.y) / Math.pow(10, exponent);
                if (!legendEnabled) {
                    return  'k(' + Highcharts.numberFormat(T, 0, '.', '') + ' ' + Tunits + ') = ' +
                    Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '') + ' ' + kseries[this.series.index][2];
                    } else {
                    return  this.series.name +': k(' + Highcharts.numberFormat(T, 0, '.', '') + ' ' + Tunits + ') = ' +
                    Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '') + ' ' + kseries[this.series.index][2];
                }
            },
        },
        plotOptions: {
            series: {
                animation: false
            },
        },
    }
    return new Highcharts.Chart(options);
};
