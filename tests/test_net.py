"""net — classificação transitório vs não-transitório (sem rede). Cota diária e 404
NÃO se reententam; 5xx/429 e marcadores de mensagem sim."""

from predictor_core import net


class _HttpError(Exception):
    def __init__(self, msg="", status_code=None):
        super().__init__(msg)
        self.status_code = status_code


def test_transient_status_codes():
    assert net.is_transient(_HttpError(status_code=503))
    assert net.is_transient(_HttpError(status_code=429))
    assert not net.is_transient(_HttpError(status_code=404))


def test_daily_quota_is_not_transient():
    # mesmo sendo 429-like na mensagem, "per day" = esperar o reset, não reententar
    assert not net.is_transient(_HttpError("Quota exceeded: requests per day"))


def test_message_markers_transient():
    assert net.is_transient(Exception("Service temporarily unavailable"))
    assert net.is_transient(Exception("RESOURCE_EXHAUSTED: overloaded"))
    assert not net.is_transient(Exception("invalid api key"))


def test_status_of_extracts_code():
    assert net._status_of(_HttpError(status_code=500)) == 500
    assert net._status_of(Exception("sem código")) is None
