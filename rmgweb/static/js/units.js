///////////////////////////////////////////////////////////////////////////////
//
//  units.js - Unit conversion functions
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
 * Convert temperature values to K from the specified units.
 */
function convertTemperatureFrom(value, units) {
    if (units == 'K')       return value;
    else if (units == 'C')  return value + 273.15;
    else if (units == 'F')  return (value + 459.67) / 1.8;
    else if (units == 'R')  return value / 1.8;
}

/**
 * Convert temperature values from K to the specified units.
 */
function convertTemperatureTo(value, units) {
    if (units == 'K')       return value;
    else if (units == 'C')  return value - 273.15;
    else if (units == 'F')  return value * 1.8 - 459.67;
    else if (units == 'R')  return value * 1.8;
}

/**
 * Convert pressure values from Pa to the specified units.
 */
function convertPressureTo(value, units) {
    if (units == 'bar')        return value / 1.0e5;
    else if (units == 'atm')   return value / 101325.;
    else if (units == 'Pa')    return value;
    else if (units == 'psi')   return value / 6894.757;
    else if (units == 'torr')  return value / 101325. / 760.0;
}

/**
 * Convert energy values from J/mol to the specified units.
 */
function convertEnergyTo(value, units) {
    if (units == 'kJ/mol')         return value / 1000.;
    else if (units == 'kcal/mol')  return value / 4184.;
    else if (units == 'J/mol')     return value;
    else if (units == 'cal/mol')   return value / 4.184;
    else if (units == 'cm^-1')     return value / 2.9979e10 * 6.626e-34 * 6.022e23;
}

/**
 * Convert heat capacity values from J/mol*K to the specified units.
 */
function convertHeatCapacityTo(value, units) {
    if (units == 'J/mol*K')         return value;
    else if (units == 'cal/mol*K')  return value / 4.184;
}
