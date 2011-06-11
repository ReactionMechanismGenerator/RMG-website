{% ifequal kineticsParameters.format "KineticsData" %}
kineticsModel = new KineticsDataModel(
    [{% for T in kineticsModel.Tdata.values %}{{ T }}{% if not forloop.last %},{% endif %}{% endfor %}],
    [{% for k in kineticsModel.kdata.values %}{{ k }}{% if not forloop.last %},{% endif %}{% endfor %}]
    {% if kineticsModel.Tmin != None and kineticsModel.Tmax != None %}
    ,{{ kineticsModel.Tmin.value }},{{ kineticsModel.Tmax.value }}
    {% endif %}
);
{% endifequal %}

{% ifequal kineticsParameters.format "Arrhenius" %}
kineticsModel = new ArrheniusModel(
    {{ kineticsModel.A.value }},
    {{ kineticsModel.n.value }},
    {{ kineticsModel.Ea.value }},
    {{ kineticsModel.T0.value }}
    {% if kineticsModel.Tmin != None and kineticsModel.Tmax != None %}
    ,{{ kineticsModel.Tmin.value }},{{ kineticsModel.Tmax.value }}
    {% endif %}
);
{% endifequal %}

{% ifequal kineticsParameters.format "ArrheniusEP" %}
kineticsModel = new ArrheniusEPModel(
    {{ kineticsModel.A.value }},
    {{ kineticsModel.n.value }},
    {{ kineticsModel.alpha.value }},
    {{ kineticsModel.E0.value }}
    {% if kineticsModel.Tmin != None and kineticsModel.Tmax != None %}
    ,{{ kineticsModel.Tmin.value }},{{ kineticsModel.Tmax.value }}
    {% endif %}
);
{% endifequal %}

{% ifequal kineticsParameters.format "MultiArrhenius" %}
kineticsModel = new MultiArrheniusModel([
    {% for arrh in kineticsModel.arrheniusList %}
    new ArrheniusModel({{ arrh.A.value }}, {{ arrh.n.value }}, {{ arrh.Ea.value }}, {{ arrh.T0.value }}){% if not forloop.last %},{% endif %}
    {% endfor %}]
    {% if kineticsModel.Tmin != None and kineticsModel.Tmax != None %}
    ,{{ kineticsModel.Tmin.value }},{{ kineticsModel.Tmax.value }}
    {% endif %}
);
{% endifequal %}

{% ifequal kineticsParameters.format "PDepArrhenius" %}
kineticsModel = new PDepArrheniusModel(
    [{% for P in kineticsModel.pressures.values %}P{% if not forloop.last %},{% endif %}{% endfor %}],
    [
    {% for arrh in kineticsModel.arrhenius %}
        new ArrheniusModel({{ arrh.A.value }}, {{ arrh.n.value }}, {{ arrh.Ea.value }}, {{ arrh.T0.value }}){% if not forloop.last %},{% endif %}
    {% endfor %}]
    {% if kineticsModel.Tmin != None and kineticsModel.Tmax != None and kineticsModel.Pmin != None and kineticsModel.Pmax != None %}
    ,{{ kineticsModel.Tmin.value }},{{ kineticsModel.Tmax.value }},
    {{ kineticsModel.Pmin.value }},{{ kineticsModel.Pmax.value }}
    {% endif %}
);
{% endifequal %}

{% ifequal kineticsParameters.format "Chebyshev" %}
kineticsModel = new ChebyshevModel([
    {% for row in kineticsParameters.1 %}
        [{% for col in row %}{{ col }}{% if not forloop.last %},{% endif %}{% endfor %}],
    {% endfor %}]
    {% if kineticsModel.Tmin != None and kineticsModel.Tmax != None and kineticsModel.Pmin != None and kineticsModel.Pmax != None %}
    ,{{ kineticsModel.Tmin.value }},{{ kineticsModel.Tmax.value }},
    {{ kineticsModel.Pmin.value }},{{ kineticsModel.Pmax.value }}
    {% endif %}
);
{% endifequal %}

{% ifequal kineticsParameters.format "ThirdBody" %}
kineticsModel = new ThirdBodyModel(
    new ArrheniusModel({{ kineticsModel.arrheniusHigh.A.value }}, {{ kineticsModel.arrheniusHigh.n.value }}, {{ kineticsModel.arrheniusHigh.Ea.value }}, {{ kineticsModel.arrheniusHigh.T0.value }})
    {% if kineticsModel.Tmin != None and kineticsModel.Tmax != None and kineticsModel.Pmin != None and kineticsModel.Pmax != None %}
    ,{{ kineticsModel.Tmin.value }},{{ kineticsModel.Tmax.value }},
    {{ kineticsModel.Pmin.value }},{{ kineticsModel.Pmax.value }}
    {% endif %}
);
{% endifequal %}

{% ifequal kineticsParameters.format "Lindemann" %}
kineticsModel = new LindemannModel(
    new ArrheniusModel({{ kineticsModel.arrheniusHigh.A.value }}, {{ kineticsModel.arrheniusHigh.n.value }}, {{ kineticsModel.arrheniusHigh.Ea.value }}, {{ kineticsModel.arrheniusHigh.T0.value }}),
    new ArrheniusModel({{ kineticsModel.arrheniusLow.A.value }}, {{ kineticsModel.arrheniusLow.n.value }}, {{ kineticsModel.arrheniusLow.Ea.value }}, {{ kineticsModel.arrheniusLow.T0.value }})
    {% if kineticsModel.Tmin != None and kineticsModel.Tmax != None and kineticsModel.Pmin != None and kineticsModel.Pmax != None %}
    ,{{ kineticsModel.Tmin.value }},{{ kineticsModel.Tmax.value }},
    {{ kineticsModel.Pmin.value }},{{ kineticsModel.Pmax.value }}
    {% endif %}
);
{% endifequal %}

{% ifequal kineticsParameters.format "Troe" %}
kineticsModel = new TroeModel(
    new ArrheniusModel({{ kineticsModel.arrheniusHigh.A.value }}, {{ kineticsModel.arrheniusHigh.n.value }}, {{ kineticsModel.arrheniusHigh.Ea.value }}, {{ kineticsModel.arrheniusHigh.T0.value }}),
    new ArrheniusModel({{ kineticsModel.arrheniusLow.A.value }}, {{ kineticsModel.arrheniusLow.n.value }}, {{ kineticsModel.arrheniusLow.Ea.value }}, {{ kineticsModel.arrheniusLow.T0.value }}),
    {{ kineticsModel.alpha.value }},
    {{ kineticsModel.T3.value }},
    {{ kineticsModel.T1.value }}
    {% if kineticsModel.T2 != None %}, {{ kineticsModel.T2.value }}{% endif %}
    {% if kineticsModel.Tmin != None and kineticsModel.Tmax != None and kineticsModel.Pmin != None and kineticsModel.Pmax != None %}
    ,{{ kineticsModel.Tmin.value }},{{ kineticsModel.Tmax.value }},
    {{ kineticsModel.Pmin.value }},{{ kineticsModel.Pmax.value }}
    {% endif %}
);
{% endifequal %}
