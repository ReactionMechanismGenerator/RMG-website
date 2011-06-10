var Tlist = {{ statesParameters.data.Tdata }};
var Qlist = {{ statesParameters.data.Qdata }};
var Elist = {{ statesParameters.data.Edata }};
var rholist = {{ statesParameters.data.rhodata }};
var philist = {{ statesParameters.data.phidata }};
var Vlist = {{ statesParameters.data.Vdata }};

var Qdata = new Array();
for (var i = 0; i < Tlist.length; i++) {
    Qdata.push([Tlist[i], Math.log(Qlist[i]) / Math.LN10]);
}
Qseries.push(['{{ source }}', Qdata]);

var rhodata = new Array();
for (var i = 0; i < Elist.length; i++) {
    if (rholist[i] > 0)
        rhodata.push([Elist[i]/1000., Math.log(rholist[i]) / Math.LN10]);
}
rhoseries.push(['{{ source }}', rhodata]);

for (var j = 0; j < Vlist.length; j++) {
    var Vdata = new Array();
    for (var i = 0; i < philist.length; i++) {
        Vdata.push([philist[i], Vlist[j][i] / 1000.]);
    }
    Vseries.push(['Rotor #' + (j+1), Vdata]);
}

plotPartitionFunction = function(id, Qseries) {

    series = [];
    for (var i = 0; i < Qseries.length; i++)
        series.push({
            name: Qseries[i][0],
            data: Qseries[i][1]
        });
    var legendEnabled = (Qseries.length > 1);
    
    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Partition function' },
        xAxis: {
            title: { text: 'Temperature (K)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Partition function' },
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
                T = this.x; 
                exponent = Math.floor(this.y);
                mantissa = Math.pow(10, this.y) / Math.pow(10, exponent);
                
                return 'Q(' + Highcharts.numberFormat(T, 0, '.', '') +' K) = ' +
                    Highcharts.numberFormat(mantissa, 1, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '');
            }
        }
    }
    
    var chartQ = new Highcharts.Chart(options);
};

plotDensityOfStates = function(id, rhoseries) {

    series = [];
    for (var i = 0; i < rhoseries.length; i++)
        series.push({
            name: rhoseries[i][0],
            data: rhoseries[i][1]
        });
    var legendEnabled = (rhoseries.length > 1);
    
    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Density of states' },
        xAxis: {
            title: { text: 'Energy (kJ/mol)' }
        },
        yAxis: {
            title: { text: 'Density of states (mol/J)' },
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
                E = this.x; 
                exponent = Math.floor(this.y);
                mantissa = Math.pow(10, this.y) / Math.pow(10, exponent);
                
                return 'rho(' + Highcharts.numberFormat(E, 2, '.', '') +' kJ/mol) = ' +
                    Highcharts.numberFormat(mantissa, 2, '.', '') + '*10^' + Highcharts.numberFormat(exponent, 0, '.', '') + ' mol/J';
            }
        }
    }
    
    var chartRho = new Highcharts.Chart(options);
};

plotHinderedRotorPotential = function(id, Vseries) {

    series = [];
    for (var i = 0; i < Vseries.length; i++)
        series.push({
            name: Vseries[i][0],
            data: Vseries[i][1]
        });
    var legendEnabled = (Vseries.length > 1);
    
    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Hindered rotor potentials' },
        xAxis: {
            title: { text: 'Angle (rad)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Potential (kJ/mol)' }
        },
        legend: { enabled: legendEnabled },
        series: series,
        tooltip: {
            formatter: function() {
                return 'V(' + Highcharts.numberFormat(this.x, 2, '.', '') +') = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' kJ/mol';
            }
        }
    }
    
    var chartRho = new Highcharts.Chart(options);
};
