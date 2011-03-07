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

/**
 * A thermodynamics model defined by a set of discrete heat capacity data
 * points, along with a reference enthalpy and entropy.
 */
function ThermoGAModel(Tdata, Cpdata, H298, S298, Tmin, Tmax) {

    // The temperatures in K at which we have heat capacity data
    this.Tdata = (Tdata) ? Tdata : [];
    // The heat capacity in J/mol*K at each temperature
    this.Cpdata = (Cpdata) ? Cpdata : [];
    // The enthalpy at 298 K in J/mol
    this.H298 = (H298) ? H298 : 0.0;
    // The entropy at 298 K in J/mol*K
    this.S298 = (S298) ? S298 : 0.0;
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;

    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getHeatCapacity = function(T) {
        Cp = 0.0;
        if (T < this.Tdata[0])
            Cp = this.Cpdata[0];
        else if (T >= this.Tdata[this.Tdata.length-1])
            Cp = this.Cpdata[this.Cpdata.length-1];
        else {
            for (var i = 0; i < this.Tdata.length-1; i++) {
                var Tmin  = this.Tdata [i]; var Tmax  = this.Tdata [i+1];
                var Cpmin = this.Cpdata[i]; var Cpmax = this.Cpdata[i+1];
                if (Tmin <= T && T < Tmax)
                    Cp = (Cpmax - Cpmin) * ((T - Tmin) / (Tmax - Tmin)) + Cpmin;
            }
        }
        return Cp;
    }

    /**
     * Return the enthalpy in J/mol at the given temperature `T` in K.
     */
    this.getEnthalpy = function(T) {
        H = this.H298;
        for (var i = 0; i < this.Tdata.length-1; i++) {
            var Tmin  = this.Tdata [i]; var Tmax  = this.Tdata [i+1];
            var Cpmin = this.Cpdata[i]; var Cpmax = this.Cpdata[i+1];
            if (T > Tmin) {
                var slope = (Cpmax - Cpmin) / (Tmax - Tmin);
                var intercept = (Cpmin * Tmax - Cpmax * Tmin) / (Tmax - Tmin);
                if (T < Tmax) H += 0.5 * slope * (T*T - Tmin*Tmin) + intercept * (T - Tmin);
                else          H += 0.5 * slope * (Tmax*Tmax - Tmin*Tmin) + intercept * (Tmax - Tmin);
            }
        }
        if (T > this.Tdata[this.Tdata.length-1])
            H += this.Cpdata[this.Cpdata.length-1] * (T - this.Tdata[this.Tdata.length-1]);
        return H;
    }

    /**
     * Return the entropy in J/mol*K at the given temperature `T` in K.
     */
    this.getEntropy = function(T) {
        S = this.S298;
        for (var i = 0; i < this.Tdata.length-1; i++) {
            var Tmin  = this.Tdata [i]; var Tmax  = this.Tdata [i+1];
            var Cpmin = this.Cpdata[i]; var Cpmax = this.Cpdata[i+1];
            if (T > Tmin) {
                var slope = (Cpmax - Cpmin) / (Tmax - Tmin);
                var intercept = (Cpmin * Tmax - Cpmax * Tmin) / (Tmax - Tmin);
                if (T < Tmax) S += slope * (T - Tmin) + intercept * Math.log(T/Tmin);
                else          S += slope * (Tmax - Tmin) + intercept * Math.log(Tmax/Tmin);
            }
        }
        if (T > this.Tdata[this.Tdata.length-1])
            S += this.Cpdata[this.Cpdata.length-1] * Math.log(T / this.Tdata[this.Tdata.length-1]);
        return S;
    }

    /**
     * Return the Gibbs free energy in J/mol*K at the given temperature `T` in
     * K.
     */
    this.getFreeEnergy = function(T) {
        return this.getEnthalpy(T) - T * this.getEntropy(T);
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A thermodynamics model based on the Wilhoit polynomial model of heat
 * capacity.
 */
function WilhoitModel(cp0, cpInf, a0, a1, a2, a3, B, H0, S0, Tmin, Tmax) {

    // The heat capacity at zero temperature in J/mol*K
    this.cp0 = (cp0) ? cp0 : 0.0;
    // The heat capacity at infinite temperature in J/mol*K
    this.cpInf = (cpInf) ? cpInf : 0.0;
    // The Wilhoit zeroth-order polynomial coefficient
    this.a0 = (a0) ? a0 : 0.0;
    // The Wilhoit first-order polynomial coefficient
    this.a1 = (a1) ? a1 : 0.0;
    // The Wilhoit second-order polynomial coefficient
    this.a2 = (a2) ? a2 : 0.0;
    // The Wilhoit third-order polynomial coefficient
    this.a3 = (a3) ? a3 : 0.0;
    // The intermediate temperature in K
    this.B = (B) ? B : 0.0;
    // The enthalpy at zero temperature in J/mol
    this.H0 = (H0) ? H0 : 0.0;
    // The entropy at zero temperature in J/mol*K
    this.S0 = (S0) ? S0 : 0.0;
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;

    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getHeatCapacity = function(T) {
        var y = T / (T + this.B);
        return this.cp0 + (this.cpInf - this.cp0)*y*y*(1 + (y-1)*(this.a0 + y*(this.a1 + y*(this.a2 + y*this.a3))));
    }

    /**
     * Return the enthalpy in J/mol at the given temperature `T` in K.
     */
    this.getEnthalpy = function(T) {
        var y = T / (T + this.B);
        var y2 = y*y;
        var logBplust = Math.log(this.B + T);
        return this.H0 + this.cp0*T - (this.cpInf-this.cp0)*T*(y2*((3*this.a0 + this.a1 + this.a2 + this.a3)/6. + (4*this.a1 + this.a2 + this.a3)*y/12. + (5*this.a2 + this.a3)*y2/20. + this.a3*y2*y/5.) + (2 + this.a0 + this.a1 + this.a2 + this.a3)*( y/2. - 1 + (1/y-1)*logBplust));
    }

    /**
     * Return the entropy in J/mol*K at the given temperature `T` in K.
     */
    this.getEntropy = function(T) {
        var y = T / (T + this.B);
        var logt = Math.log(T);
        var logy = Math.log(y);
        return this.S0 + this.cpInf*logt-(this.cpInf-this.cp0)*(logy+y*(1+y*(this.a0/2+y*(this.a1/3 + y*(this.a2/4 + y*this.a3/5)))));
    }

    /**
     * Return the Gibbs free energy in J/mol*K at the given temperature `T` in
     * K.
     */
    this.getFreeEnergy = function(T) {
        return this.getEnthalpy(T) - T * this.getEntropy(T);
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A thermodynamics model based on the NASA polynomial model of heat
 * capacity.
 */
function NASAPolynomial(coeffs, Tmin, Tmax) {

    // The NASA polynomial coefficients
    this.coeffs = (coeffs) ? coeffs : [];
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;

    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getHeatCapacity = function(T) {
        return ((this.coeffs[0] / T + this.coeffs[1]) / T + this.coeffs[2] + T*(this.coeffs[3] + T*(this.coeffs[4] + T*(this.coeffs[5] + this.coeffs[6]*T)))) * 8.314472;
    }

    /**
     * Return the enthalpy in J/mol at the given temperature `T` in K.
     */
    this.getEnthalpy = function(T) {
        var T2 = T*T;
        var T4 = T2*T2;
        return ((-this.coeffs[0] / T + this.coeffs[1] * Math.log(T)) / T + this.coeffs[2] + this.coeffs[3]*T/2. + this.coeffs[4]*T2/3. + this.coeffs[5]*T2*T/4. + this.coeffs[6]*T4/5. + this.coeffs[7]/T) * 8.314472 * T;
    }

    /**
     * Return the entropy in J/mol*K at the given temperature `T` in K.
     */
    this.getEntropy = function(T) {
        var T2 = T*T;
        var T4 = T2*T2;
        return ((-this.coeffs[0] / T / 2. - this.coeffs[1]) / T + this.coeffs[2]*Math.log(T) + this.coeffs[3]*T + this.coeffs[4]*T2/2. + this.coeffs[5]*T2*T/3. + this.coeffs[6]*T4/4. + this.coeffs[8] ) * 8.314472;
    }

    /**
     * Return the Gibbs free energy in J/mol*K at the given temperature `T` in
     * K.
     */
    this.getFreeEnergy = function(T) {
        return this.getEnthalpy(T) - T * this.getEntropy(T);
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A thermodynamics model combining multiple NASA polynomials.
 */
function NASAModel(polynomials) {

    // The NASA polynomials
    this.polynomials = (polynomials) ? polynomials : [];

    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getHeatCapacity = function(T) {
        for (var j = 0; j < polynomials.length; j++) {
            if (polynomials[j].Tmin <= T && T <= polynomials[j].Tmax) {
                return polynomials[j].getHeatCapacity(T);
            }
        }
        return null;
    }

    /**
     * Return the enthalpy in J/mol at the given temperature `T` in K.
     */
    this.getEnthalpy = function(T) {
        for (var j = 0; j < polynomials.length; j++) {
            if (polynomials[j].Tmin <= T && T <= polynomials[j].Tmax) {
                return polynomials[j].getEnthalpy(T);
            }
        }
        return null;
    }

    /**
     * Return the entropy in J/mol*K at the given temperature `T` in K.
     */
    this.getEntropy = function(T) {
        for (var j = 0; j < polynomials.length; j++) {
            if (polynomials[j].Tmin <= T && T <= polynomials[j].Tmax) {
                return polynomials[j].getEntropy(T);
            }
        }
        return null;
    }

    /**
     * Return the Gibbs free energy in J/mol*K at the given temperature `T` in
     * K.
     */
    this.getFreeEnergy = function(T) {
        for (var j = 0; j < polynomials.length; j++) {
            if (polynomials[j].Tmin <= T && T <= polynomials[j].Tmax) {
                return polynomials[j].getFreeEnergy(T);
            }
        }
        return null;
    }
}

////////////////////////////////////////////////////////////////////////////////

function plotHeatCapacity(id, Cpseries) {

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
            title: { text: 'Temperature (K)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Heat capacity (J/mol*K)' }
        },
        legend: { enabled: legendEnabled },
        series: series,
        tooltip: {
            formatter: function() {
                return 'Cp(' + Highcharts.numberFormat(this.x, 0, '.', '') +' K) = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' J/mol*K';
            }
        }
    }
    
    var chartCp = new Highcharts.Chart(options);
}

function plotEnthalpy(id, Hseries) {

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
            title: { text: 'Temperature (K)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Enthalpy (kJ/mol)' }
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
                return 'H(' + Highcharts.numberFormat(this.x, 0, '.', '') + ' K) = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' kJ/mol';
            }
        }
    }

    var chartH = new Highcharts.Chart(options);
}

function plotEntropy(id, Sseries) {

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
            title: { text: 'Temperature (K)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Entropy (J/mol*K)' }
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
                return 'S(' + Highcharts.numberFormat(this.x, 0, '.', '') +' K) = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' J/mol*K';
            }
        }
    }

    var chartS = new Highcharts.Chart(options);
}

function plotFreeEnergy(id, Gseries) {

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
            title: { text: 'Temperature (K)' },
            min: 0
        },
        yAxis: {
            title: { text: 'Free energy (kJ/mol)' }
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
                return 'G(' + Highcharts.numberFormat(this.x, 0, '.', '') +' K) = ' + Highcharts.numberFormat(this.y, 2, '.', '') + ' kJ/mol';
            }
        }
    }

    var chartG = new Highcharts.Chart(options);
}