var Cpdata = new Array();
var Hdata = new Array();
var Sdata = new Array();
var Gdata = new Array();
for (var i = 0; i < Tlist.length; i++) {
    Cpdata.push([Tlist[i], Cplist[i]]);
    Hdata.push([Tlist[i], Hlist[i]]);
    Sdata.push([Tlist[i], Slist[i]]);
    Gdata.push([Tlist[i], Glist[i]]);
}

Cpseries.push(['{{ source }}', Cpdata]);
Hseries.push(['{{ source }}', Hdata]);
Sseries.push(['{{ source }}', Sdata]);
Gseries.push(['{{ source }}', Gdata]);

plotHeatCapacity = function(id, Cpseries) {

    series = [];
    for (var i = 0; i < Cpseries.length; i++)
        series.push({
            name: Cpseries[i][0],
            data: Cpseries[i][1]
        });
    var legendEnabled = (Cpseries.length > 1);
    
    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Heat capacity' },
        xAxis: {
            title: { text: 'Temperature (' + Tunits + ')' },
            min: 0
        },
        yAxis: {
            title: { text: 'Heat capacity (' + Cpunits + ')' }
        },
        legend: { enabled: legendEnabled },
        series: series,
        tooltip: {
            formatter: function() {
                if (legendEnabled == 0) {
                    return 'Cp(' + Highcharts.numberFormat(this.x, 0, '.', '') +' K) = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' J/mol*K';
                    } else {
                    return this.series.name + ': Cp(' + Highcharts.numberFormat(this.x, 0, '.', '') +' ' + Tunits + ') = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' ' + Cpunits + '';
                    }        
            }
        }
    }
    
    var chartCp = new Highcharts.Chart(options);
};

plotEnthalpy = function(id, Hseries) {

    series = [];
    for (var i = 0; i < Hseries.length; i++)
        series.push({
            name: Hseries[i][0],
            data: Hseries[i][1]
        });
    var legendEnabled = (Hseries.length > 1);

    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Enthalpy' },
        xAxis: {
            title: { text: 'Temperature (' + Tunits + ')' },
            min: 0
        },
        yAxis: {
            title: { text: 'Enthalpy (' + Hunits + ')' }
        },
        legend: { enabled: legendEnabled },
        series: series,
        plotOptions: {
            line: {
                marker: { enabled: false }
            }
        },
        tooltip: {
            formatter: function() {
                if (legendEnabled == 0) {
                    return 'H(' + Highcharts.numberFormat(this.x, 0, '.', '') + ' ' + Tunits + ') = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' ' + Hunits + '';
                    } else {
                    return this.series.name + ': H(' + Highcharts.numberFormat(this.x, 0, '.', '') + ' ' + Tunits + ') = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' ' + Hunits + '';
                    }
            }
        }
    }

    var chartH = new Highcharts.Chart(options);
};

plotEntropy = function(id, Sseries) {

    series = [];
    for (var i = 0; i < Sseries.length; i++)
        series.push({
            name: Sseries[i][0],
            data: Sseries[i][1]
        });
    var legendEnabled = (Sseries.length > 1);

    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Entropy' },
        xAxis: {
            title: { text: 'Temperature (' + Tunits + ')' },
            min: 0
        },
        yAxis: {
            title: { text: 'Entropy (' + Sunits + ')' }
        },
        legend: { enabled: legendEnabled },
        series: series,
        plotOptions: {
            line: {
                marker: { enabled: false }
            }
        },
        tooltip: {
            formatter: function() {
                    if (legendEnabled == 0) {
                    return 'S(' + Highcharts.numberFormat(this.x, 0, '.', '') +' ' + Tunits + ') = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' ' + Sunits + '';
                    } else {
                    return this.series.name + ': S(' + Highcharts.numberFormat(this.x, 0, '.', '') + ' ' + Tunits + ') = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' ' + Sunits + '';
                    }
            }
        }
    }

    var chartS = new Highcharts.Chart(options);
};

plotFreeEnergy = function(id, Gseries) {

    series = [];
    for (var i = 0; i < Gseries.length; i++)
        series.push({
            name: Gseries[i][0],
            data: Gseries[i][1]
        });
    var legendEnabled = (Gseries.length > 1);

    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Gibbs free energy' },
        xAxis: {
            title: { text: 'Temperature (' + Tunits + ')' },
            min: 0
        },
        yAxis: {
            title: { text: 'Free energy (' + Gunits + ')' }
        },
        legend: { enabled: legendEnabled },
        series: series,
        plotOptions: {
            line: {
                marker: { enabled: false }
            }
        },
        tooltip: {
            formatter: function() {
                if (legendEnabled == 0) {
                    return 'G(' + Highcharts.numberFormat(this.x, 0, '.', '') + ' ' + Tunits + ') = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' ' + Gunits + '';
                    } else {
                    return this.series.name + ': G(' + Highcharts.numberFormat(this.x, 0, '.', '') + ' ' + Tunits + ') = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' ' + Gunits + '';
                    }
            }
        }
    }

    var chartG = new Highcharts.Chart(options);
};
