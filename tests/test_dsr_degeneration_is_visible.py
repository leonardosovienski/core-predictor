"""O DSR não degenera em silêncio: quando não desconta, ele diz que não desconta.

Auditoria adversarial 2026-09-05, achado 2 (core-predictor#20). `E[max SR]` é
`sqrt(V[SR])` vezes um fator que cresce com N — o número de tentativas entra
apenas dentro desse fator, MULTIPLICADO pela raiz da variância entre tentativas.
E `V[SR]` é estimado só com as tentativas que registraram sharpe numérico.

Consequência medida no registro real do consumidor: 3 de 29 tentativas com
sharpe, e as três variantes do mesmo experimento OU2.5 walk-forward — a
subamostra menos diversa possível. Mesma série de retornos, mesmo `n_trials=29`,
o DSR passava no gate de 0,95; com uma variância realista entre tentativas,
reprovava. Com menos de duas tentativas registrando sharpe, `V[SR]` não existe,
`sr0` vira 0 e o "Deflated" Sharpe é PSR puro — enquanto o retorno seguia
anunciando `n_trials`.

A fórmula está certa (Bailey & López de Prado, 2014) e não foi tocada. O que
muda aqui é que o resultado passa a carregar o próprio diagnóstico.
"""

from __future__ import annotations

import math
import random

import pytest

from predictor_core import DeflationNotEstimableError, deflated_sharpe_ratio

# Sharpe por-período modesto: PSR sensível, não saturado em 1.0.
_RETORNOS = [0.001 + 0.01 * math.sin(i / 2.0) for i in range(150)]


def test_sem_sharpe_nenhum_a_degeneracao_e_declarada():
    """O caso limite: 29 tentativas, nenhuma com sharpe — desconto zero."""
    r = deflated_sharpe_ratio(_RETORNOS, [None] * 29)

    assert r["n_trials"] == 29, "o N continua sendo reportado"
    assert r["n_sharpes"] == 0
    assert r["sr0"] == 0.0
    assert r["sr0_estimable"] is False
    assert r["deflation_applied"] is False, (
        "sr0 == 0 significa PSR puro; quem lê precisa conseguir ver isso"
    )
    assert r["sharpe_coverage"] == 0.0


def test_uma_so_tentativa_com_sharpe_ainda_nao_estima_variancia():
    """Variância entre tentativas precisa de duas observações, não de uma."""
    r = deflated_sharpe_ratio(_RETORNOS, [0.1] + [None] * 28)
    assert r["n_sharpes"] == 1
    assert r["sr0_estimable"] is False
    assert r["deflation_applied"] is False


def test_com_variancia_estimavel_o_desconto_acontece_e_e_declarado():
    r = deflated_sharpe_ratio(_RETORNOS, [0.05, 0.20, -0.10, 0.30] + [None] * 25)
    assert r["n_sharpes"] == 4
    assert r["sr0_estimable"] is True
    assert r["deflation_applied"] is True
    assert r["sr0"] > 0.0


def test_cobertura_expoe_a_fracao_do_registro_que_sustenta_o_desconto():
    """3 de 29 é o número real do consumidor em 2026-09-05."""
    r = deflated_sharpe_ratio(_RETORNOS, [0.0722, 0.1043, 0.0911] + [None] * 26)
    assert r["n_trials"] == 29
    assert r["n_sharpes"] == 3
    assert r["sharpe_coverage"] == pytest.approx(3 / 29)
    assert r["deflation_applied"] is True, "descontou, mas com V[SR] de 10% do registro"


def test_strict_recusa_devolver_numero_que_parece_descontado():
    """Para gate de promoção: melhor erro do que número enganoso."""
    with pytest.raises(DeflationNotEstimableError, match="não estimável"):
        deflated_sharpe_ratio(_RETORNOS, [None] * 29, strict=True)


def test_strict_nao_atrapalha_quando_o_desconto_e_estimavel():
    r = deflated_sharpe_ratio(_RETORNOS, [0.05, 0.20, -0.10], strict=True)
    assert r["sr0_estimable"] is True


def test_registro_vazio_nao_divide_por_zero():
    r = deflated_sharpe_ratio(_RETORNOS, [])
    assert r["n_trials"] == 0
    assert r["sharpe_coverage"] == 0.0
    assert r["deflation_applied"] is False


def test_os_numeros_publicados_nao_mudaram():
    """A correção é de visibilidade: dsr e sr0 seguem idênticos aos de antes.

    Recalcular vereditos já publicados seria mudar o passado; o que faltava era
    conseguir enxergar quando o desconto não aconteceu.
    """
    sharpes = [0.0722, 0.1043, 0.0911] + [None] * 26
    r = deflated_sharpe_ratio(_RETORNOS, sharpes)

    # Reprodução literal do cálculo anterior à correção.
    from statistics import variance

    from predictor_core.measurement.stats import probabilistic_sharpe_ratio
    from predictor_core.measurement.trials import expected_max_sharpe

    finite = [s for s in sharpes if s is not None and math.isfinite(s)]
    sr0_antigo = expected_max_sharpe(len(sharpes), variance(finite))
    assert r["sr0"] == sr0_antigo
    assert r["dsr"] == probabilistic_sharpe_ratio(_RETORNOS, benchmark_sharpe=sr0_antigo)


def test_a_sensibilidade_do_desconto_a_diversidade_das_tentativas():
    """O mecanismo do achado 2, fixado como regressão.

    Mesmo N, mesma série: quanto mais parecidas entre si as tentativas
    registradas, menor o desconto. Uma subamostra homogênea produz um DSR
    otimista sem que nada no resultado antigo denunciasse isso.
    """
    random.seed(1)
    retornos = [random.gauss(0.02, 0.35) for _ in range(400)]

    homogeneas = deflated_sharpe_ratio(retornos, [0.0722, 0.1043, 0.0911] + [None] * 26)
    diversas = deflated_sharpe_ratio(retornos, [random.gauss(0.0, 0.10) for _ in range(29)])

    assert homogeneas["n_trials"] == diversas["n_trials"] == 29
    assert homogeneas["sr0"] < diversas["sr0"]
    assert homogeneas["dsr"] > diversas["dsr"], (
        "o mesmo N produz vereditos opostos conforme V[SR]; por isso "
        "n_sharpes e sharpe_coverage precisam ser visíveis"
    )
