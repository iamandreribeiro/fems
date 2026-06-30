"""PRNG com seed — reprodutível, no intervalo [0.85, 1.15], independente por carga."""

from fems.domain.simulation.prng import noise_series


def test_noise_no_intervalo():
    s = noise_series(20250101, 2025, 0, 5000)
    assert float(s.min()) >= 0.85
    assert float(s.max()) <= 1.15


def test_noise_reprodutivel():
    a = noise_series(123, 2025, 2, 200)
    b = noise_series(123, 2025, 2, 200)
    assert (a == b).all()


def test_noise_varia_por_seed():
    assert not (noise_series(1, 2025, 0, 200) == noise_series(2, 2025, 0, 200)).all()


def test_noise_varia_por_carga():
    assert not (noise_series(1, 2025, 0, 200) == noise_series(1, 2025, 1, 200)).all()


def test_noise_media_proxima_de_um():
    s = noise_series(20250101, 2025, 0, 100000)
    assert abs(float(s.mean()) - 1.0) < 0.01
