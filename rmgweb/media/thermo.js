///////////////////////////////////////////////////////////////////////////////
//
//  thermo.js - Thermodynamic model classes and functions
//
//  Copyright (c) 2011 Prof. William H. Green (whgreen@mit.edu) and the
//  RMG Team (rmg_dev@mit.edu)
//
//  Permission is hereby granted, free of charge, to any person obtaining a
//  copy of this software and associated documentation files (the 'Software'),
//  to deal in the Software without restriction, including without limitation
//  the rights to use, copy, modify, merge, publish, distribute, sublicense,
//  and/or sell copies of the Software, and to permit persons to whom the
//  Software is furnished to do so, subject to the following conditions:
//
//  The above copyright notice and this permission notice shall be included in
//  all copies or substantial portions of the Software.
//
//  THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
//  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
//  DEALINGS IN THE SOFTWARE.
//
////////////////////////////////////////////////////////////////////////////////

function thermoGA_getHeatCapacity(T, Tdata, Cpdata, H298, S298) {
    Cp = 0.0;
    if (T < Tdata[0])
        Cp = Cpdata[0];
    else if (T >= Tdata[Tdata.length-1])
        Cp = Cpdata[Cpdata.length-1];
    else { 
        for (var i = 0; i < Tdata.length-1; i++) {
            var Tmin  = Tdata [i]; var Tmax  = Tdata [i+1];
            var Cpmin = Cpdata[i]; var Cpmax = Cpdata[i+1];
            if (Tmin <= T && T < Tmax)
                Cp = (Cpmax - Cpmin) * ((T - Tmin) / (Tmax - Tmin)) + Cpmin;
        }
    }
    return Cp;
}

function thermoGA_getEnthalpy(T, Tdata, Cpdata, H298, S298) {
    H = H298;
    for (var i = 0; i < Tdata.length-1; i++) {
        var Tmin  = Tdata [i]; var Tmax  = Tdata [i+1];
        var Cpmin = Cpdata[i]; var Cpmax = Cpdata[i+1];
        if (T > Tmin) {
            var slope = (Cpmax - Cpmin) / (Tmax - Tmin);
            var intercept = (Cpmin * Tmax - Cpmax * Tmin) / (Tmax - Tmin);
            if (T < Tmax) H += 0.5 * slope * (T*T - Tmin*Tmin) + intercept * (T - Tmin);
            else          H += 0.5 * slope * (Tmax*Tmax - Tmin*Tmin) + intercept * (Tmax - Tmin);
        }
    }
    if (T > Tdata[Tdata.length-1])
        H += Cpdata[Cpdata.length-1] * (T - Tdata[Tdata.length-1]);
    return H;
}

function thermoGA_getEntropy(T, Tdata, Cpdata, H298, S298) {
    S = S298;
    for (var i = 0; i < Tdata.length-1; i++) {
        var Tmin  = Tdata [i]; var Tmax  = Tdata [i+1];
        var Cpmin = Cpdata[i]; var Cpmax = Cpdata[i+1];
        if (T > Tmin) {
            var slope = (Cpmax - Cpmin) / (Tmax - Tmin);
            var intercept = (Cpmin * Tmax - Cpmax * Tmin) / (Tmax - Tmin);
            if (T < Tmax) S += slope * (T - Tmin) + intercept * Math.log(T/Tmin);
            else          S += slope * (Tmax - Tmin) + intercept * Math.log(Tmax/Tmin);
        }
    }
    if (T > Tdata[Tdata.length-1])
        S += Cpdata[Cpdata.length-1] * Math.log(T / Tdata[Tdata.length-1]);
    return S;
}

function wilhoit_getHeatCapacity(T, Cp0, CpInf, a0, a1, a2, a3, B, H0, S0) {
    var y = T / (T + B);
    return Cp0 + (CpInf - Cp0)*y*y*(1 + (y-1)*(a0 + y*(a1 + y*(a2 + y*a3))));
}

function wilhoit_getEnthalpy(T, Cp0, CpInf, a0, a1, a2, a3, B, H0, S0) {
    var y = T / (T + B);
    var y2 = y*y;
    var logBplust = Math.log(B + T);
    return H0 + Cp0*T - (CpInf-Cp0)*T*(y2*((3*a0 + a1 + a2 + a3)/6. + (4*a1 + a2 + a3)*y/12. + (5*a2 + a3)*y2/20. + a3*y2*y/5.) + (2 + a0 + a1 + a2 + a3)*( y/2. - 1 + (1/y-1)*logBplust)); 
}

function wilhoit_getEntropy(T, Cp0, CpInf, a0, a1, a2, a3, B, H0, S0) {
    var y = T / (T + B);
    var logt = Math.log(T);
    var logy = Math.log(y);
    return S0 + CpInf*logt-(CpInf-Cp0)*(logy+y*(1+y*(a0/2+y*(a1/3 + y*(a2/4 + y*a3/5)))));
}

function nasaPolynomial_getHeatCapacity(T, coeffs) {
    return ((coeffs[0] / T + coeffs[1]) / T + coeffs[2] + T*(coeffs[3] + T*(coeffs[4] + T*(coeffs[5] + coeffs[6]*T)))) * 8.314472;
}

function nasaPolynomial_getEnthalpy(T, coeffs) {
    var T2 = T*T;
    var T4 = T2*T2;
    return ((-coeffs[0] / T + coeffs[1] * Math.log(T)) / T + coeffs[2] + coeffs[3]*T/2. + coeffs[4]*T2/3. + coeffs[5]*T2*T/4. + coeffs[6]*T4/5. + coeffs[7]/T) * 8.314472 * T;
}

function nasaPolynomial_getEntropy(T, coeffs) {
    var T2 = T*T;
    var T4 = T2*T2;
    return ((-coeffs[0] / T / 2. - coeffs[1]) / T + coeffs[2]*Math.log(T) + coeffs[3]*T + coeffs[4]*T2/2. + coeffs[5]*T2*T/3. + coeffs[6]*T4/4. + coeffs[8] ) * 8.314472;
}

////////////////////////////////////////////////////////////////////////////////

function plotHeatCapacity(Tdata, Cpdata, id) {

    var data = new Array();
    for (var i = 0; i < Tdata.length; i++)
        data[i] = [Tdata[i], Cpdata[i]];
    
    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Heat capacity' },
        xAxis: {
            title: { text: 'Temperature (K)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Heat capacity (J/mol*K)' }
        },
        legend: { enabled: false },
        series: [{
            data: data
        }],
        tooltip: {
            formatter: function() {
                return 'Cp(' + Highcharts.numberFormat(this.x, 0, '.', '') +' K) = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' J/mol*K';
            }
        }
    }
    
    var chartCp = new Highcharts.Chart(options);
}

function plotEnthalpy(Tdata, Hdata, id) {

    var data = new Array();
    for (var i = 0; i < Tdata.length; i++)
        data[i] = [Tdata[i], Hdata[i] / 1000.];

    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Enthalpy' },
        xAxis: {
            title: { text: 'Temperature (K)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Enthalpy (kJ/mol)' }
        },
        legend: { enabled: false },
        series: [{
            data: data
        }],
        plotOptions: {
            line: {
                marker: { enabled: false }
            }
        },
        tooltip: {
            formatter: function() {
                return 'H(' + Highcharts.numberFormat(this.x, 0, '.', '') + ' K) = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' kJ/mol';
            }
        }
    }

    var chartH = new Highcharts.Chart(options);
}

function plotEntropy(Tdata, Sdata, id) {

    var data = new Array();
    for (var i = 0; i < Tdata.length; i++)
        data[i] = [Tdata[i], Sdata[i]];

    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Entropy' },
        xAxis: {
            title: { text: 'Temperature (K)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Entropy (J/mol*K)' }
        },
        legend: { enabled: false },
        series: [{
            data: data
        }],
        plotOptions: {
            line: {
                marker: { enabled: false }
            }
        },
        tooltip: {
            formatter: function() {
                return 'S(' + Highcharts.numberFormat(this.x, 0, '.', '') +' K) = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' J/mol*K';
            }
        }
    }

    var chartS = new Highcharts.Chart(options);
}

function plotFreeEnergy(Tdata, Gdata, id) {

    var data = new Array();
    for (var i = 0; i < Tdata.length; i++)
        data[i] = [Tdata[i], Gdata[i] / 1000.];

    options = {
        chart: {
            renderTo: id,
            defaultSeriesType: 'line'
        },
        title: { text: 'Gibbs free energy' },
        xAxis: {
            title: { text: 'Temperature (K)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Free energy (kJ/mol)' }
        },
        legend: { enabled: false },
        series: [{
            data: data
        }],
        plotOptions: {
            line: {
                marker: { enabled: false }
            }
        },
        tooltip: {
            formatter: function() {
                return 'G(' + Highcharts.numberFormat(this.x, 0, '.', '') +' K) = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' kJ/mol';
            }
        }
    }

    var chartG = new Highcharts.Chart(options);
}