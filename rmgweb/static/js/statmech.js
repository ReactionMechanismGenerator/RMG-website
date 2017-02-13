///////////////////////////////////////////////////////////////////////////////
//
//  statmech.js - Statistical mechanical model classes and functions
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
 * Compute the modified Bessel function of the first kind at zeroth-order for
 * the given argument x.
 * 
 * Taken from http://www.mhtlab.uwaterloo.ca/old/courses/me3532/js/bessel.html 
 */
function besseli0(x) {
	var ax,ans,y;
	ax=Math.abs(x);
	if (ax < 3.75) {
		y=x/3.75;
		y*=y;
		ans=1.0+y*(3.5156229+y*(3.0899424+y*(1.2067492+y*(0.2659732+y*(0.360768e-1+y*0.45813e-2)))));
	} else {
		y=3.75/ax;
		ans=(Math.exp(ax)/Math.sqrt(ax))*(0.39894228+y*(0.1328592e-1+y*(0.225319e-2+y*(-0.157565e-2+y*(0.916281e-2+y*(-0.2057706e-1+y*(0.2635537e-1+y*(-0.1647633e-1+y*0.392377e-2))))))));
	}
	return ans;
}
 
/** 
 * Compute the modified Bessel function of the first kind at first-order for
 * the given argument x.
 * 
 * Taken from http://www.mhtlab.uwaterloo.ca/old/courses/me3532/js/bessel.html 
 */
function besseli1(x) {
	var ax,ans,y;
	ax=Math.abs(x);
	if (ax<3.75) {
		y=x/3.75;
		y*=y;
		ans=ax*(0.5+y*(0.87890594+y*(0.51498869+y*(0.15084934+y*(0.2658733e-1+y*(0.301532e-2+y*0.32411e-3))))));
	} else {
		y=3.75/ax;
		ans=0.2282967e-1+y*(-0.2895312e-1+y*(0.1787654e-1-y*0.420059e-2));
		ans=0.39894228+y*(-0.3988024e-1+y*(-0.362018e-2+y*(0.163801e-2+y*(-0.1031555e-1+y*ans))));
		ans*=(Math.exp(ax)/Math.sqrt(ax));
	}
	return x < 0.0 ? -ans : ans;
}

/**
 * Return the value of the complete elliptic integral of the first kind for
 * the given argument m.
 */
function cellipk(m) {
    // Compute arithmetic-geometric mean of 1 - m and 1 + m
    var A = 1;
    var G = Math.sqrt((1-m) * (1+m));
    while (Math.abs(A - G) > 1.0e-6) {
        A0 = A; G0 = G;
        A = 0.5 * (A0 + G0);
        G = Math.sqrt(A0 * G0);
    }
    // Use the arithmetic-geometric mean to compute the integral
    return Math.PI / 2 / A;
}

/**
 * Convolve the two densities of states rho1 and rho2 -- each evaluated at the
 * given energies Elist -- into a single array. The units of the parameters do 
 * not matter so long as they are consistent.
 */
function convolve(rho1, rho2, Elist) {
    
    var rho = new Array();
    var size = Elist.length;
    var r, s;
    for (r = 0; r < size; r++) {
        rho[r] = 0.0;
    }
    
    var found1 = false;
    var found2 = false;
    if (rho1.length == size) {
        for (r = 0; r < size; r++) {
            if (rho1[r] > 0) {
                found1 = true;
                break;
            }
        }
    }
    if (rho2.length == size) {
        for (r = 0; r < size; r++) {
            if (rho2[r] > 0) {
                found2 = true;
                break;
            }
        }
    }
    
    if (found1 && found2) {
        var dE = Elist[1] - Elist[0];
        for (r = 0; r < size; r++) {
            for (s = 0; s <= r; s++) {
                rho[r] += rho2[r-s] * rho1[r] * dE;
            }
        }
    }
    else if (found1 && !found2) {
        for (r = 0; r < size; r++) {
            rho[r] = rho1[r];
        }
    }
    else if (!found1 && found2) {
        for (r = 0; r < size; r++) {
            rho[r] = rho2[r];
        }
    }
    
    return rho;
}

////////////////////////////////////////////////////////////////////////////////

/**
 * A statistical mechanical model of 3D translational motion.
 */
function Translation(mass) {
    
    // The mass of the molecule in kg/mol
    this.mass = (mass) ? mass : 0.0;
    
    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getHeatCapacity = function(T) {
        return 1.5 * 8.314472;
    }

    /**
     * Return the enthalpy in J/mol at the given temperature `T` in K.
     */
    this.getEnthalpy = function(T) {
        return 1.5 * 8.314472 * T;
    }

    /**
     * Return the entropy in J/mol*K at the given temperature `T` in K.
     */
    this.getEntropy = function(T) {
        return Math.log(this.getPartitionFunction(T) + 1.5) * 8.314472;
    }
    
    /**
     * Return the partition function at the given temperature `T` in K.
     */
    this.getPartitionFunction = function(T) {
        var qt = Math.pow(((2 * Math.PI * this.mass / 6.022e23) / (6.626e-34 * 6.626e-34)), 1.5) / 101325.;
        return qt * Math.pow((1.381e-23 * T), 2.5);
    }
    
    /**
     * Return the density of states in mol/J at the given energies `Elist` in 
     * J/mol.
     */
    this.getDensityOfStates = function(Elist) {
        var rho = new Array();
        var qt = Math.pow(((2 * Math.PI * this.mass / 6.022e23) / (6.626e-34 * 6.626e-34)), 1.5) / 101325.;
        for (var r = 0; r < Elist.length; r++) {
            rho[r] = qt * Math.pow(Elist[r], 1.5) / (Math.sqrt(Math.pi) * 0.75) / 6.022e23;
        }
        return rho;
    }
    
}

/**
 * A statistical mechanical model of a (linear or nonlinear) rigid rotor.
 */
function RigidRotor(linear, inertia, symmetry) {
    
    // true if the molecule is linear, false if nonlinear
    this.linear = (linear) ? linear : false;
    // The external moments of inertia in kg*m^2
    this.inertia = (inertia) ? inertia : [];
    // The external symmetry number
    this.symmetry = (symmetry) ? symmetry : 1;
    
    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getHeatCapacity = function(T) {
        if (this.linear)
            return 8.314472;
        else
            return 1.5 * 8.314472;
    }

    /**
     * Return the enthalpy in J/mol at the given temperature `T` in K.
     */
    this.getEnthalpy = function(T) {
        if (this.linear)
            return 8.314472 * T;
        else
            return 1.5 * 8.314472 * T;
    }

    /**
     * Return the entropy in J/mol*K at the given temperature `T` in K.
     */
    this.getEntropy = function(T) {
        if (this.linear)
            return Math.log(this.getPartitionFunction(T) + 1.0) * 8.314472;
        else
            return Math.log(this.getPartitionFunction(T) + 1.5) * 8.314472;
    }
    
    /**
     * Return the partition function at the given temperature `T` in K.
     */
    this.getPartitionFunction = function(T) {
        var theta;
        var inertia;
        if (this.linear) {
            inertia = this.inertia[0];
            theta = 6.626e-34 * 6.626e-34 / (8 * Math.PI * Math.PI * inertia * 1.381e-23);
            return T / theta / this.symmetry;
        }
        else {
            theta = 1.0;
            for (var n = 0; n < this.inertia.length; n++) {
                inertia = this.inertia[n];
                theta = theta * 6.626e-34 * 6.626e-34 / (8 * Math.PI * Math.PI * inertia * 1.381e-23);
            }
            return Math.sqrt(Math.PI * Math.pow(T, this.inertia.length) / theta) / this.symmetry;
        }
    }
    
    /**
     * Return the density of states in mol/J at the given energies `Elist` in 
     * J/mol.
     */
    this.getDensityOfStates = function(Elist) {
        var rho = new Array();
        var inertia;
        var theta;
        for (var r = 0; r < Elist.length; r++) {
            if (this.linear) {
                inertia = this.inertia[0];
                theta = 6.626e-34 * 6.626e-34 / (8 * Math.PI * Math.PI * inertia * 1.381e-23);
                rho[r] = 1.0 / theta / this.symmetry;
            }
            else {
                theta = 1.0;
                for (var n = 0; n < this.inertia.length; n++) {
                    inertia = this.inertia[n];
                    theta = theta * 6.626e-34 * 6.626e-34 / (8 * Math.PI * Math.PI * inertia * 1.381e-23);
                }
                rho[r] = 2 * Math.sqrt(Elist[r] / theta) / this.symmetry;                
            }
        }
        return rho;
    }
    
}

/**
 * A statistical mechanical model of a set of one-dimensional harmonic
 * oscillators.
 */
function HarmonicOscillator(frequencies) {
    
    // The vibrational frequencies in cm^-1
    this.frequencies = (frequencies) ? frequencies : [];
    
    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getHeatCapacity = function(T) {
        var Cv = 0.0;
        for (var n = 0; n < this.frequencies.length; n++) {
            x = this.frequencies[n] / (0.695039 * T); // kB = 0.695039 cm^-1/K
            exp_x = Math.exp(x);
            one_minus_exp_x = 1.0 - exp_x;
            Cv = Cv + x * x * exp_x / one_minus_exp_x / one_minus_exp_x;
        }
        return Cv * 8.314472;
    }

    /**
     * Return the enthalpy in J/mol at the given temperature `T` in K.
     */
    this.getEnthalpy = function(T) {
        var H = 0.0;
        for (var n = 0; n < this.frequencies.length; n++) {
            x = this.frequencies[n] / (0.695039 * T); // kB = 0.695039 cm^-1/K
            exp_x = Math.exp(x);
            H = H + x / (exp_x - 1);
        }
        return H * 8.314472 * T;
    }

    /**
     * Return the entropy in J/mol*K at the given temperature `T` in K.
     */
    this.getEntropy = function(T) {
        var S = Math.log(this.getPartitionFunction(T));
        for (var n = 0; n < this.frequencies.length; n++) {
            x = this.frequencies[n] / (0.695039 * T); // kB = 0.695039 cm^-1/K
            exp_x = Math.exp(x);
            S = S + x / (exp_x - 1);
        }
        return S * 8.314472;
    }
    
    /**
     * Return the partition function at the given temperature `T` in K.
     */
    this.getPartitionFunction = function(T) {
        var Q = 1.0;
        for (var n = 0; n < this.frequencies.length; n++) {
            x = this.frequencies[n] / (0.695039 * T); // kB = 0.695039 cm^-1/K
            Q = Q / (1 - Math.exp(-x));
        }
        return Q;
    }
    
    /**
     * Return the density of states in mol/J at the given energies `Elist` in 
     * J/mol.
     */
    this.getDensityOfStates = function(Elist, rho0) {
        var rho = new Array();
        var dE = Elist[1] - Elist[0];
        var nE = Elist.length;
        var r, n;
        
        for (r = 0; r < nE; r++) {
            rho[r] = rho0[r];
        }
        
        for (n = 0; n < this.frequencies.length; n++) {
            dr = Math.round(this.frequencies[n] * 6.626e-34 * 2.9979e10 * 6.022e23 / dE);
            for (r = dr; r < nE; r++) {
                rho[r] = rho[r] + rho[r-dr];
            }
        }
        return rho;
    }
    
}

/**
 * A statistical mechanical model of a single one-dimensional hindered internal
 * rotor.
 */
function HinderedRotor(inertia, symmetry, barrier, fourierA, fourierB) {
    
    // The reduced moment of inertia in kg*m^2 for this torsion
    this.inertia = (inertia) ? inertia : 0.0;
    // The internal symmetry number for this torsion
    this.symmetry = (symmetry) ? symmetry : 1;
    // The barrier height in J/mol
    this.barrier = (barrier) ? barrier : 0.0;
    // The Fourier series coefficients for cosine
    this.fourierA = (fourierA) ? fourierA : [];
    // The Fourier series coefficients for sine
    this.fourierB = (fourierB) ? fourierB : [];
    // The solution energies to the 1D Schrodinger equation for the Fourier series potential
    this.energies = [];
    
    /**
     * Return true if the Fourier series potential is being used or false if
     * not.
     */
    this.isFourier = function() {
        return (this.fourierA.length > 0 && this.fourierB.length > 0);
    }
    
    /**
     * Return true if the simple cosine potential is being used or false if
     * not.
     */
    this.isCosine = function() {
        return (this.barrier > 0);
    }
    
    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getFrequency = function() {
        var V0 = 0.0;
        if (this.isFourier()) {
            V0 = -Math.sum(this.fourierA);
        } else {
            V0 = this.barrier;
        }
        return this.symmetry / 2.0 / Math.PI * Math.sqrt(V0 / 6.022e23 / 2 / this.inertia) / (2.9979e10);
    }
    
    /**
     * Return the values of the hindered rotor potential V(phi) in J/mol at the 
     * angles `phi` in radians.
     */ 
    this.getPotential = function(phi) {
        var V = 0.0;
        if (this.isFourier()) {
            for (var k = 0; k < this.fourierA.length; k++)
                V = V + this.fourierA[k] * Math.cos((k+1) * phi) + this.fourierB[k] * Math.sin((k+1) * phi);
            V = V - Math.sum(this.fourierA);
        }
        else {
            V = 0.5 * this.barrier * (1 - Math.cos(this.symmetry * phi));
        }
        return V;
    }
    
    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getHeatCapacity = function(T) {
        var Cv = 0.0;
        if (this.isFourier()) {
            var e_kT = new Array();
            var E_e_kT = new Array();
            var E_E_e_kT = new Array();
            for (var s = 0; s < this.energies.length; s++) {
                E = this.energies[s];
                e_kT[s] = Math.exp(-E / 8.314472 / T);
                E_e_kT[s] = E * e_kT[s];
                E_E_e_kT[s] = E * E_e_kT[s];
            }
            Cv = (Math.sum(E_E_e_kT) * Math.sum(e_kT) - Math.pow(Math.sum(E_e_kT), 2)) / (8.314472*T*T * Math.pow(Math.sum(e_kT), 2));
            
        } else {
            var frequency = this.getFrequency() * 2.9979e10;
            var x = 6.626e-34 * frequency / (1.381e-23 * T);
            var z = 0.5 * this.barrier / (8.314472 * T);
            var exp_x = Math.exp(x);
            var one_minus_exp_x = 1.0 - exp_x;
            BB = besseli1(z) / besseli0(z);
            Cv = (x * x * exp_x / one_minus_exp_x / one_minus_exp_x - 0.5 + z * (z - BB - z * BB * BB)) * 8.314472;
        }
        return Cv;
    }

    /**
     * Return the enthalpy in J/mol at the given temperature `T` in K.
     */
    this.getEnthalpy = function(T) {
        var H = 0.0;
        if (this.isFourier()) {
            var e_kT = new Array();
            var E_e_kT = new Array();
            for (var s = 0; s < this.energies.length; s++) {
                E = this.energies[s];
                e_kT[s] = Math.exp(-E / 8.314472 / T);
                E_e_kT[s] = E * e_kT[s];
            }
            H = Math.sum(E_e_kT) / Math.sum(e_kT);            
        } else {
            var Tlow = T * 0.999;
            var Thigh = T * 1.001;
            H = (T *
                (Math.log(this.getPartitionFunction(Thigh)) -
                Math.log(this.getPartitionFunction(Tlow))) /
                (Thigh - Tlow)) * 8.314472 * T;
        }
        return H;
    }
    
    /**
     * Return the entropy in J/mol*K at the given temperature `T` in K.
     */
    this.getEntropy = function(T) {
        var S = 8.314472 * Math.log(this.getPartitionFunction(T));
        if (this.isFourier()) {
            var e_kT = new Array();
            var E_e_kT = new Array();
            for (var s = 0; s < this.energies.length; s++) {
                E = this.energies[s];
                e_kT[s] = Math.exp(-E / 8.314472 / T);
                E_e_kT[s] = E * e_kT[s];
            }
            S = S + Math.sum(E_e_kT) / (T * Math.sum(e_kT));            
        } else {
            var Tlow = T * 0.999;
            var Thigh = T * 1.001;
            S = (Math.log(this.getPartitionFunction(Thigh)) + 
                T * (Math.log(this.getPartitionFunction(Thigh)) -
                Math.log(this.getPartitionFunction(Tlow))) /
                (Thigh - Tlow)) * 8.314472;
        }
        return S;
    }
    
    /**
     * Return the partition function at the given temperature `T` in K.
     */
    this.getPartitionFunction = function(T) {
        var Q = 1.0;
        if (this.isFourier()) {
            var e_kT = new Array();
            for (var s = 0; s < this.energies.length; s++) {
                E = this.energies[s];
                e_kT[s] = Math.exp(-E / 8.314472 / T);
            }
            Q = Math.sum(e_kT) / this.symmetry;    
        } else {
            var frequency = this.getFrequency() * 2.9979e10;
            var x = 6.626e-34 * frequency / (1.381e-23 * T);
            var z = 0.5 * this.barrier / (8.314472 * T);
            BB = besseli1(z) / besseli0(z);
            Q = x / (1 - Math.exp(-x)) * Math.sqrt(2 * Math.PI * this.inertia * 1.381e-23 * T / 6.626e-34 / 6.626e-34) * (2 * Math.PI / this.symmetry) * Math.exp(-z) * besseli0(z);
        }
        return Q;
    }
    
    /**
     * Return the density of states in mol/J at the given energies `Elist` in 
     * J/mol.
     */
    this.getDensityOfStates = function(Elist) {
        var rho = new Array();
        for (var r = 0; r < Elist.length; r++) {
            rho[r] = 0.0;
            if (this.isFourier()) {
            
            } else {
                var q1f = Math.sqrt(8 * Math.PI * Math.PI * Math.PI * this.inertia / 6.626e-34 / 6.626e-34 / 6.022e23) / this.symmetry;
                var V0 = this.barrier;
                var pre = 2.0 * q1f / Math.sqrt(Math.PI * Math.PI * Math.PI * V0);
                if (Elist[r] / V0 < 1)
                    rho[r] = pre * cellipk(Elist[r] / V0);
                else if (Elist[r] / V0 > 1)
                    rho[r] = pre * Math.sqrt(V0 / Elist[r]) * cellipk(V0 / Elist[r]);
            } 
        }
        return rho;
    }
    
}

/**
 * A statistical mechanical model that collects various molecular degrees of
 * freedom.
 */
function StatesModel(modes, spinMultiplicity) {
    
    // The molecular degrees of freedom
    this.modes = (modes) ? modes : [];
    // The spin multiplicity of the electronic ground state
    this.spinMultiplicity = (spinMultiplicity) ? spinMultiplicity : 1;
    
    /**
     * Return the heat capacity in J/mol*K at the given temperature `T` in K.
     */
    this.getHeatCapacity = function(T) {
        var Cp = 8.314472;
        for (var n = 0; n < this.modes.length; n++) {
            Cp += this.modes[n].getHeatCapacity(T);
        }
        return Cp;
    }

    /**
     * Return the enthalpy in J/mol at the given temperature `T` in K.
     */
    this.getEnthalpy = function(T) {
        var H = 8.314472 * T;
        for (var n = 0; n < this.modes.length; n++) {
            H += this.modes[n].getEnthalpy(T);
        }
        return H;
    }

    /**
     * Return the entropy in J/mol*K at the given temperature `T` in K.
     */
    this.getEntropy = function(T) {
        var S = 0.0;
        for (var n = 0; n < this.modes.length; n++) {
            S += this.modes[n].getEntropy(T);
        }
        return S;
    }
    
    this.useActiveKRotor = function() {
        for (var n = 0; n < this.modes.length; n++) {
            if (this.modes[n] instanceof Translation || this.modes[n] instanceof RigidRotor)
                return false;
        }
        return true;
    }
    
    /**
     * Return the partition function at the given temperature `T` in K.
     */
    this.getPartitionFunction = function(T) {
        var Q = 1.0;
        
        // Include an (arbitrary) active K-rotor if necessary
        if (this.useActiveKRotor()) {
            var Trot = 1.0 / 8.314472 / Math.PI;
            Q = Q * Math.sqrt(T / Trot);
        }
        
        // Include all other modes
        for (var n = 0; n < this.modes.length; n++) {
            Q = Q * this.modes[n].getPartitionFunction(T);
        }
        
        return Q * this.spinMultiplicity;
    }
    
    /**
     * Return the density of states in mol/J at the given energies `Elist` in 
     * J/mol.
     */
    this.getDensityOfStates = function(Elist) {
        
        var rho = new Array();
        var rho0;
        for (var r = 0; r < Elist.length; r++)
            rho[r] = 0.0;
        
        // Include an (arbitrary) active K-rotor if necessary
        if (this.useActiveKRotor()) {
            rho0 = new Array();
            for (var r = 0; r < Elist.length; r++) {
                if (Elist[r] > 0)
                    rho0[r] = 1.0 / Math.sqrt(1.0 * Elist[r]);
            }
            rho = convolve(rho, rho0, Elist);
        }
        
        // Include other non-vibrational modes
        for (var n = 0; n < this.modes.length; n++) {
            if (!(this.modes[n] instanceof HarmonicOscillator)) {
                rho0 = this.modes[n].getDensityOfStates(Elist);
                rho = convolve(rho, rho0, Elist);
            }
        }
        
        // Include vibrational modes
        for (var n = 0; n < this.modes.length; n++) {
            if (this.modes[n] instanceof HarmonicOscillator) {
                rho = this.modes[n].getDensityOfStates(Elist, rho);
            }
        }
        
        return rho;
    }
    
}

////////////////////////////////////////////////////////////////////////////////

function plotPartitionFunction(id, Qseries) {

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
}

function plotDensityOfStates(id, rhoseries) {

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
            title: { text: 'Energy (kJ/mol)' },
            min: 0
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
}

function plotHinderedRotorPotential(id, Vseries) {

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
            min: 0,
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
}

