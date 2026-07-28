"""Coloca a raiz do core no sys.path para `import stats|net|obs|replay|settings|infra`
funcionar rodando o pytest da raiz do repositório (os módulos são planos na raiz —
vivem sob predictor_core/ só quando vendorizados nos consumidores)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT.parent)):   # ROOT → import plano; ROOT.parent → import predictor_core (pacote)
    if p not in sys.path:
        sys.path.insert(0, p)
