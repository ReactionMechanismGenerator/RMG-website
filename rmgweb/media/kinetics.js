///////////////////////////////////////////////////////////////////////////////
//
//  kinetics.js - Kinetics model classes and functions
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
 * A kinetics model defined by a set of discrete rate coefficient data
 * points.
 */
function KineticsDataModel(Tdata, kdata, Tmin, Tmax) {

    // The temperatures in K at which we have kinetics data
    this.Tdata = (Tdata) ? Tdata : [];
    // The rate coefficient in SI units at each temperature
    this.kdata = (kdata) ? kdata : [];
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;

    /**
     * Return the rate coefficient in SI units at the given temperature `T` in K.
     */
    this.getRateCoefficient = function(T) {
        var k = 0.0;
        if (T < this.Tdata[0])
            k = this.kdata[0];
        else if (T >= this.Tdata[this.Tdata.length-1])
            k = this.kdata[this.kdata.length-1];
        else {
            // Interpolate on T^-1 and log k domain
            for (var i = 0; i < this.Tdata.length-1; i++) {
                var Tmin = this.Tdata[i]; var Tmax = this.Tdata[i+1];
                var kmin = this.kdata[i]; var kmax = this.kdata[i+1];
                if (Tmin <= T && T < Tmax)
                    k = Math.exp((Math.log(kmax) - Math.log(kmin)) * ((1.0/T - 1.0/Tmin) / (1.0/Tmax - 1.0/Tmin)) + Math.log(kmin));
            }
        }
        return k;
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A kinetics model based on the (modified) Arrhenius equation.
 */
function ArrheniusModel(A, n, Ea, T0, Tmin, Tmax) {

    // The Arrhenius preexponential factor in SI units (mol, m^3, s)
    this.A = (A) ? A : 0.0;
    // The Arrhenius temperature exponent
    this.n = (n) ? n : 0.0;
    // The Arrhenius activation energy in J/mol
    this.Ea = (Ea) ? Ea : 0.0;
    // The Arrhenius reference temperature in K
    this.T0 = (T0) ? T0 : 1.0;
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;

    /**
     * Return the rate coefficient in SI units at the given temperature `T` in K.
     */
    this.getRateCoefficient = function(T) {
        return this.A * Math.pow(T / this.T0, this.n) * Math.exp(-this.Ea / 8.314472 / T);
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A kinetics model based on the (modified) Arrhenius equation with
 * Evans-Polanyi correction to the activation energy.
 */
function ArrheniusEPModel(A, n, alpha, E0, Tmin, Tmax) {

    // The Arrhenius preexponential factor in SI units (mol, m^3, s)
    this.A = (A) ? A : 0.0;
    // The Arrhenius temperature exponent
    this.n = (n) ? n : 0.0;
    // The Evans-Polanyi slope
    this.alpha = (alpha) ? alpha : 0.0;
    // The Evans-Polanyi intercept (thermoneutral activation energy) in J/mol
    this.E0 = (E0) ? E0 : 0.0;
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;

    /**
     * Return the rate coefficient in SI units at the given temperature `T` in K.
     */
    this.getRateCoefficient = function(T, dHrxn) {
        return this.A * Math.pow(T, this.n) * Math.exp(-(this.E0 + this.alpha * dHrxn) / 8.314472 / T);
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A kinetics model based on a set of multiple Arrhenius equations. The
 * equations are summed to obtain the total rate.
 */
function MultiArrheniusModel(arrheniusList, Tmin, Tmax) {

    // A list of the Arrhenius equations to sum to obtain the rate
    this.arrheniusList = (arrheniusList) ? arrheniusList : [];
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;

    /**
     * Return the rate coefficient in SI units at the given temperature `T` in K.
     */
    this.getRateCoefficient = function(T) {
        var k = 0.0;
        for (var i = 0; i < this.arrheniusList.length; i++)
            k += this.arrheniusList[i].getRateCoefficient(T);
        return k;
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A kinetics model based on a set of multiple Arrhenius equations, each valid
 * at a different pressure.
 */
function PDepArrheniusModel(pressures, arrhenius, Tmin, Tmax, Pmin, Pmax) {

    // A list of the pressures in Pa for each Arrhenius equation
    this.pressures = (pressures) ? pressures : [];
    // A list of the Arrhenius equations at each pressure
    this.arrhenius = (arrhenius) ? arrhenius : [];
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;
    // The minimum valid pressure in Pa
    this.Pmin = (Pmin) ? Pmin : 0.0;
    // The maximum valid pressure in Pa
    this.Pmax = (Pmax) ? Pmax : 1.0e100;

    this.getAdjacentExpressions = function(P) {

        ilow = 0; ihigh = null; Plow = this.pressures[0]; Phigh = 0.0;
        for (var i = 1; i < this.pressures.length; i++) {
            if (this.pressures[i] <= P) {
                ilow = i; Plow = P;
            }
            if (this.pressures[i] <= P && ihigh == null) {
                ihigh = i; Phigh = P;
            }
        }

        return [Plow, Phigh, this.arrhenius[ilow], this.arrhenius[ihigh]];
    }

    /**
     * Return the rate coefficient in SI units at the given temperature `T` in K.
     */
    this.getRateCoefficient = function(T, P) {
        data = this.getAdjacentExpressions(P);
        Plow = data[0]; Phigh = data[1]; alow = data[2]; ahigh = data[3];
        var k = 0.0;
        if (Plow == Phigh) {
            k = alow.getRateCoefficient(T);
        } else {
            klow = alow.getRateCoefficient(T);
            khigh = ahigh.getRateCoefficient(T);
            k = Math.pow(10, (Math.log(P/Plow)/Math.LN10) / (Math.log(Phigh/Plow)/Math.LN10) * (Math.log(khigh/klow)/Math.LN10));
        }
        return k;
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A kinetics model based on a set of Chebyshev polynomials in temperature
 * and pressure.
 */
function ChebyshevModel(coeffs, Tmin, Tmax, Pmin, Pmax) {

    // A matrix of Chebyshev polynomial coefficients in temperature and pressure
    this.coeffs = (coeffs) ? coeffs : [];
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;
    // The minimum valid pressure in Pa
    this.Pmin = (Pmin) ? Pmin : 0.0;
    // The maximum valid pressure in Pa
    this.Pmax = (Pmax) ? Pmax : 1.0e100;

    this.getReducedTemperature = function(T) {
        return (2.0/T - 1.0/this.Tmin - 1.0/this.Tmax) / (1.0/this.Tmax - 1.0/this.Tmin);
    }

    this.getReducedPressure = function(P) {
        return (2.0*Math.log(P) - Math.log(this.Pmin) - Math.log(this.Pmax)) / (Math.log(this.Pmax) - Math.log(this.Pmin));
    }

    this.chebyshev = function(n, x) {
        if (n == 0)
            return 1;
        else if (n == 1)
            return x;
        else if (n == 2)
            return -1 + 2*x*x;
        else if (n == 3)
            return x * (-3 + 4*x*x);
        else if (n == 4)
            return 1 + x*x*(-8 + 8*x*x);
        else if (n == 5)
            return x * (5 + x*x*(-20 + 16*x*x));
        else if (n == 6)
            return -1 + x*x*(18 + x*x*(-48 + 32*x*x));
        else if (n == 7)
            return x * (-7 + x*x*(56 + x*x*(-112 + 64*x*x)));
        else if (n == 8)
            return 1 + x*x*(-32 + x*x*(160 + x*x*(-256 + 128*x*x)));
        else if (n == 9)
            return x * (9 + x*x*(-120 + x*x*(432 + x*x*(-576 + 256*x*x))));
        else
            return Math.cos(n * Math.acos(x));
    }

    /**
     * Return the rate coefficient in SI units at the given temperature `T` in K.
     */
    this.getRateCoefficient = function(T, P) {
        var k = 0.0;
        var Tred = this.getReducedTemperature(T);
        var Pred = this.getReducedPressure(P);
        for (var t = 0; t < this.coeffs.length; t++) {
            for (var p = 0; p < this.coeffs[t].length; p++)
                k += this.coeffs[t][p] * this.chebyshev(t, Tred) * this.chebyshev(p, Pred);
        }
        return Math.pow(10, k);
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A kinetics model based on a modified Arrhenius expression, which is
 * multiplied by the gas-phase total concentration [M] to get the total rate.
 */
function ThirdBodyModel(arrheniusHigh, Tmin, Tmax, Pmin, Pmax) {

    // The Arrhenius equation representing the high-pressure limit
    this.arrheniusHigh = (arrheniusHigh) ? arrheniusHigh : null;
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;
    // The minimum valid pressure in Pa
    this.Pmin = (Pmin) ? Pmin : 0.0;
    // The maximum valid pressure in Pa
    this.Pmax = (Pmax) ? Pmax : 1.0e100;

    /**
     * Return the rate coefficient in SI units at the given temperature `T` in K.
     */
    this.getRateCoefficient = function(T, P) {
        return this.arrheniusHigh.getRateCoefficient(T) * (P / 8.314472 / T);
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A kinetics model based on the Lindemann model for falloff.
 */
function LindemannModel(arrheniusHigh, arrheniusLow, Tmin, Tmax, Pmin, Pmax) {

    // The Arrhenius equation representing the high-pressure limit
    this.arrheniusHigh = (arrheniusHigh) ? arrheniusHigh : null;
    // The Arrhenius equation representing the low-pressure limit
    this.arrheniusLow = (arrheniusLow) ? arrheniusLow : null;
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;
    // The minimum valid pressure in Pa
    this.Pmin = (Pmin) ? Pmin : 0.0;
    // The maximum valid pressure in Pa
    this.Pmax = (Pmax) ? Pmax : 1.0e100;

    /**
     * Return the rate coefficient in SI units at the given temperature `T` in K.
     */
    this.getRateCoefficient = function(T, P) {
        var C = P / 8.314472 / T;
        var kinf = this.arrheniusHigh.getRateCoefficient(T);
        var k0 = this.arrheniusLow.getRateCoefficient(T);
        var Pr = k0 * C / kinf;
        var F = 1.0;
        return kinf * (Pr / (1 + Pr)) * F;
    }
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A kinetics model based on the Troe model for falloff.
 */
function TroeModel(arrheniusHigh, arrheniusLow, alpha, T3, T1, T2, Tmin, Tmax, Pmin, Pmax) {

    // The Arrhenius equation representing the high-pressure limit
    this.arrheniusHigh = (arrheniusHigh) ? arrheniusHigh : null;
    // The Arrhenius equation representing the low-pressure limit
    this.arrheniusLow = (arrheniusLow) ? arrheniusLow : null;
    // The Troe parameters
    this.alpha = (alpha) ? alpha : 0.0;
    this.T3 = (T3) ? T3 : 0.0;
    this.T1 = (T1) ? T1 : 0.0;
    this.T2 = (T2) ? T2 : 0.0;
    // The minimum valid temperature in K
    this.Tmin = (Tmin) ? Tmin : 0.0;
    // The maximum valid temperature in K
    this.Tmax = (Tmax) ? Tmax : 99999.9;
    // The minimum valid pressure in Pa
    this.Pmin = (Pmin) ? Pmin : 0.0;
    // The maximum valid pressure in Pa
    this.Pmax = (Pmax) ? Pmax : 1.0e100;

    /**
     * Return the rate coefficient in SI units at the given temperature `T` in K.
     */
    this.getRateCoefficient = function(T, P) {
        var C = P / 8.314472 / T;
        var kinf = this.arrheniusHigh.getRateCoefficient(T);
        var k0 = this.arrheniusLow.getRateCoefficient(T);
        var Pr = k0 * C / kinf;

        var Fcent = (1 - this.alpha) * Math.exp(-T / this.T3) + this.alpha * Math.exp(-T / this.T1);
        if (this.T2 != 1e100) Fcent += Math.exp(-this.T2 / T);
        var d = 0.14;
        var n = 0.75 - 1.27 * Math.log(Fcent) / Math.LN10;
        var c = -0.4 - 0.67 * Math.log(Fcent) / Math.LN10;
        var F = Math.pow(10.0, Math.log(Fcent)/Math.LN10/(1 + Math.pow((Math.log(Pr)/Math.LN10 + c)/(n - d * (Math.log(Pr)/Math.LN10)), 2)));

        return kinf * (Pr / (1 + Pr)) * F;
    }
}

////////////////////////////////////////////////////////////////////////////////

function plotKinetics(id, kseries) {
    
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
        title: { text: 'Rate coefficient (1 bar)' },
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
}
