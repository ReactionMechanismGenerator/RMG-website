statesData = new StatesModel();

{% for mode in statesModel.modes %}

{% if mode.inertia and mode.symmetry and not mode.barrier and not mode.fourier %}
{% if mode.linear %}
mode = new RigidRotor(
    true,
    [{{ mode.inertia.value }}],
    {{ mode.symmetry }}
);
{% else %}
mode = new RigidRotor(
    false,
    [{% for inertia in mode.inertia.values %}{{ inertia }}{% if not forloop.last %},{% endif %}{% endfor %}],
    {{ mode.symmetry }}
);
{% endif %}
statesData.modes.push(mode);
{% endif %}

{% if mode.frequencies %}
mode = new HarmonicOscillator(
    [{% for freq in mode.frequencies.values %}{{ freq }}{% if not forloop.last %},{% endif %}{% endfor %}]
);
statesData.modes.push(mode);
{% endif %}

{% if mode.inertia and mode.symmetry and mode.barrier %}
mode = new HinderedRotor(
    {{ mode.inertia.value }},
    {{ mode.symmetry }},
    {{ mode.barrier.value }},
    [],
    []
);
statesData.modes.push(mode);
{% endif %}
{% if mode.inertia and mode.symmetry and mode.fourier %}
mode = new HinderedRotor(
    {{ mode.inertia.value }},
    {{ mode.symmetry }},
    0.0,
    mode.fourier.0,
    mode.fourier.1
);
statesData.modes.push(mode);
{% endif %}

{% endfor %}

