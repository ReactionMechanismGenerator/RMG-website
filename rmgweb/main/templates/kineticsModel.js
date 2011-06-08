var Tlist = {{ kineticsParameters.data.Tdata }};
var Plist = {{ kineticsParameters.data.Pdata }};
var klist = {{ kineticsParameters.data.kdata }};

var kdata;
if (Plist.length > 0) {
    for (var j = 0; j < Plist.length; j++) {
        kdata = new Array();
        for (var i = 0; i < Tlist.length; i++) {
            kdata.push([1000./Tlist[i], Math.log(klist[j][i]) / Math.LN10]);
        }
        kseries.push([(Plist[j]/1e5) + ' bar', kdata]);
    }
}
else {
    kdata = new Array();
    for (var i = 0; i < Tlist.length; i++) {
        kdata.push([1000./Tlist[i], Math.log(klist[i]) / Math.LN10]);
    }
    kseries.push(['{{ source }}', kdata]);
}

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
            title: { text: '1000 / Temperature (1000/K)' },
            min: 0,
            max: 4
        },
        yAxis: {
            title: { text: 'Rate coefficient (SI units)' },
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
                T = 1000.0/this.x; 
                exponent = Math.floor(this.y);
                mantissa = Math.pow(10, this.y) / Math.pow(10, exponent);
                
                return 'k(' + Highcharts.numberFormat(T, 0, '.', '') +' K) = ' +
                    Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '');
            }
        }
    }

    var chartk = new Highcharts.Chart(options);
};
