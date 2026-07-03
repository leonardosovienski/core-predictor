"""version — a fonte canônica guarda seu próprio carimbo de procedência
(<semver>-<tag>-<YYYYMMDD>). Espelha o teste que os vendados rodam downstream."""
import re

import predictor_core  # __init__.py da raiz expõe __version__


def test_version_has_provenance_stamp():
    v = predictor_core.__version__
    assert v, "__version__ vazio"
    assert re.match(r"^\d+\.\d+\.\d+-[a-z0-9]+-\d{8}$", v), \
        f"VERSION deve ser <semver>-<tag>-<YYYYMMDD>: {v!r}"
