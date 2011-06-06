{% ifequal thermoParameters.format "Group additivity" %}
thermoData = new ThermoGAModel(
    [{% for T in thermoModel.Tdata.values %}{{ T }}{% if not forloop.last %},{% endif %}{% endfor %}],
    [{% for Cp in thermoModel.Cpdata.values %}{{ Cp }}{% if not forloop.last %},{% endif %}{% endfor %}],
    {{ thermoModel.H298.value }},
    {{ thermoModel.S298.value }}
);
{% endifequal %}

{% ifequal thermoParameters.format "Wilhoit" %}
thermoData = new WilhoitModel(
    {{ thermoModel.cp0.value }},
    {{ thermoModel.cpInf.value }},
    {{ thermoModel.a0.value }},
    {{ thermoModel.a1.value }},
    {{ thermoModel.a2.value }},
    {{ thermoModel.a3.value }},
    {{ thermoModel.B.value }},
    {{ thermoModel.H0.value }},
    {{ thermoModel.S0.value }}
);
{% endifequal %}

{% ifequal thermoParameters.format "NASA" %}
thermoData = new NASAModel([
    {% for poly in thermoModel.polynomials %}
    new NASAPolynomial(
        [{{ poly.cm2 }},{{ poly.cm1 }},{{ poly.c0 }},{{ poly.c1 }},{{ poly.c2 }},{{ poly.c3 }},{{ poly.c4 }},{{ poly.c5 }},{{ poly.c6 }}],
        {{ poly.Tmin.value }},
        {{ poly.Tmax.value }}
    ),
{% endfor %}
]);
{% endifequal %}
