"""circuit_breaker — a máquina de estados unificada (API da dpl E da v3).

Porta os 7 comportamentos do antigo test_v3_circuit_breaker (state/can_attempt/
data_quality_score) e valida o alias allow() e o relógio injetável usados pela dpl.
"""
from predictor_core.data.circuit_breaker import CircuitBreaker


def test_inicia_fechado_e_saudavel():
    cb = CircuitBreaker("t")
    assert cb.state == CircuitBreaker.CLOSED
    assert cb.data_quality_score == 1.0
    assert cb.can_attempt() is True and cb.allow() is True


def test_falhas_abaixo_do_limiar_seguem_fechado():
    cb = CircuitBreaker("t", failure_threshold=3)
    cb.record_failure(); cb.record_failure()
    assert cb.state == CircuitBreaker.CLOSED and cb.can_attempt() is True


def test_atinge_limiar_abre():
    cb = CircuitBreaker("t", failure_threshold=3, reset_timeout=999)
    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitBreaker.OPEN
    assert cb.data_quality_score == 0.0
    assert cb.can_attempt() is False          # dentro do timeout, bloqueia


def test_apos_timeout_vai_para_half_open():
    cb = CircuitBreaker("t", failure_threshold=1, reset_timeout=0.0)
    cb.record_failure()
    assert cb.state == CircuitBreaker.OPEN    # state NÃO auto-transiciona na leitura
    assert cb.can_attempt() is True           # reset=0 → transita OPEN→HALF_OPEN
    assert cb.state == CircuitBreaker.HALF_OPEN
    assert cb.data_quality_score == 0.5


def test_sucesso_em_half_open_fecha_e_zera():
    cb = CircuitBreaker("t", failure_threshold=1, reset_timeout=0.0)
    cb.record_failure(); cb.can_attempt(); cb.record_success()
    assert cb.state == CircuitBreaker.CLOSED and cb.data_quality_score == 1.0
    cb2 = CircuitBreaker("t2", failure_threshold=2, reset_timeout=0.0)
    cb2.record_failure(); cb2.record_success(); cb2.record_failure()  # 1/2, não 2/2
    assert cb2.state == CircuitBreaker.CLOSED


def test_falha_em_half_open_reabre():
    cb = CircuitBreaker("t", failure_threshold=1, reset_timeout=0.0)
    cb.record_failure(); cb.can_attempt(); cb.record_failure()
    assert cb.state == CircuitBreaker.OPEN and cb.data_quality_score == 0.0


def test_relogio_injetavel_controla_timeout():
    now = [1000.0]
    cb = CircuitBreaker("t", failure_threshold=1, reset_timeout=30.0, clock=lambda: now[0])
    cb.record_failure()
    assert cb.allow() is False                # 0s decorridos
    now[0] += 31.0
    assert cb.allow() is True                 # passou o timeout → HALF_OPEN
    assert cb.state == CircuitBreaker.HALF_OPEN


def test_half_open_libera_uma_sonda_por_vez():
    """Regressão: HALF_OPEN liberava sondas ilimitadas — N chamadas concorrentes
    bombardeariam a fonte convalescente de uma vez."""
    now = [0.0]
    cb = CircuitBreaker("t", failure_threshold=1, reset_timeout=10.0, clock=lambda: now[0])
    cb.record_failure()
    now[0] = 11.0
    assert cb.can_attempt() is True     # a sonda
    assert cb.can_attempt() is False    # em voo: bloqueia
    assert cb.can_attempt() is False
    cb.record_failure()                 # sonda falhou → reabre
    assert cb.state == CircuitBreaker.OPEN
    now[0] = 22.0
    assert cb.can_attempt() is True     # novo ciclo, nova sonda única
    assert cb.can_attempt() is False
    cb.record_success()                 # sonda passou → fecha e destrava
    assert cb.state == CircuitBreaker.CLOSED
    assert cb.can_attempt() is True and cb.can_attempt() is True
