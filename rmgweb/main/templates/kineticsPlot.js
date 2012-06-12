plotKinetics = function(id, kseries) {

    series = [];
    for (var i = 0; i < kseries.length; i++)
        series.push({
            name: kseries[i][0],
            data: kseries[i][1]
        });
    var legendEnabled = (kseries.length > 1);

    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Rate coefficient' },
        xAxis: {
            title: { text: '1000 / Temperature (1000/' + Tunits + ')' },
            min: 0,
            max: 4
        },
        yAxis: {
            title: { text: 'Rate coefficient (' + kunits + ')' },
            labels: {
                formatter: function() {
                    exponent = Math.floor(this.value);
                    mantissa = Math.pow(10, this.value) / Math.pow(10, exponent);
                    return '' + Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '');
                }
            }
        },
        legend: {
            enabled: legendEnabled,
            layout: 'vertical',
            labelFormatter: function() {
                return (this.index+1) + '. ' + this.name;
                }
        },
        series: series,
        tooltip: {
            formatter: function() {
                T = 1000.0/this.x;
                exponent = Math.floor(this.y);
                mantissa = Math.pow(10, this.y) / Math.pow(10, exponent);
                if (legendEnabled == 0) {
                    return  'k(' + Highcharts.numberFormat(T, 0, '.', '') + ' ' + Tunits + ') = ' +
                    Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '') + ' ' + kunits;
                    } else {
                    return  (this.series.index+1) +'. ' + this.series.name +': k(' + Highcharts.numberFormat(T, 0, '.', '') + ' ' + Tunits + ') = ' +
                    Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '') + ' ' + kunits;
                    }
            }
        }
    }

    return new Highcharts.Chart(options);
};
