plotKineticsVsP = function(id, kseries) {

    series = [];
    for (var i = 0; i < kseries.length; i++)
        series.push({
            name: kseries[i][0],
            data: kseries[i][1],
            events: {
                click: function(event) {
                    if (legendEnabled) this.hide();
                }
            }
        });
    var legendEnabled = (kseries.length > 1);

    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Rate coefficient' },
        xAxis: {
            title: { text: 'Pressure (' + Punits + ')' },
            labels: {
                formatter: function() {
                    exponent = Math.floor(this.value);
                    mantissa = Math.pow(10, this.value) / Math.pow(10, exponent);
                    return '' + Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent-5, 0, '.', '');
                }
            }
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
        legend: { enabled: legendEnabled },
        series: series,
        tooltip: {
            formatter: function() {
                exponentP = Math.floor(this.x);
                mantissaP = Math.pow(10, this.x) / Math.pow(10, exponentP);
                exponent = Math.floor(this.y);
                mantissa = Math.pow(10, this.y) / Math.pow(10, exponent);

                return 'k(' + Highcharts.numberFormat(mantissaP, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponentP-5, 0, '.', '') + ' ' + Punits + ') = ' +
                    Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '') + ' ' + kunits;
            }
        }
    }

    return new Highcharts.Chart(options);
};
