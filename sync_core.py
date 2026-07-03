#!/usr/bin/env python3
"""sync_core — distribuidor canônico do predictor_core (fluxo UNIDIRECIONAL).

REGRA DE OURO: a verdade vive AQUI (predictor_core/). Este script LÊ os módulos
homologados deste diretório (RECURSIVAMENTE, incluindo as subpastas kernel/,
measurement/, data/, testing/), calcula o hash de integridade por caminho relativo,
e ESCREVE (sobrescreve) nas pastas vendor/predictor_core/ dos domínios consumidores,
recriando a árvore de subdiretórios.

Você nunca mais edita a matemática dentro do stocks ou do cripto: corrige AQUI, roda
o sync, e a correção propaga com integridade garantida — matando o "drift".

Uso (de qualquer diretório):
    py -3.14 sync_core.py --check     # relata o drift de cada consumidor (NÃO escreve)
    py -3.14 sync_core.py --write     # propaga o núcleo p/ os vendors (grava manifest)

Payload distribuído = todos os *.py do pacote (recursivo) + VERSION. NÃO fazem parte
do payload (canônico-only): sync_core.py, CORE_MANIFEST.json, README.md, CHANGELOG.md,
e as pastas tests/, docs/, .github/ (tooling e documentação — sem consumidor de runtime).

Segurança:
  - SÓ escreve em domínios que JÁ têm vendor/predictor_core/ (consumidores opt-in).
  - NUNCA escreve em domínios PARKED (ex.: wc-predictor — dado irreproduzível da Copa).
  - Grava CORE_MANIFEST.json (hash por CAMINHO RELATIVO + agregado) em cada vendor.
"""
import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

CANONICAL = Path(__file__).resolve().parent     # predictor_core/  (a fonte da verdade)
WORKSPACE = CANONICAL.parent                     # raiz com os domínios lado a lado
MANIFEST_NAME = "CORE_MANIFEST.json"

# Arquivos de nível raiz que NÃO fazem parte do payload distribuído:
_NOT_PAYLOAD = {"sync_core.py", MANIFEST_NAME, "README.md", "CHANGELOG.md"}
# Diretórios canônico-only: tooling/doc/teste, não distribuídos aos vendors:
_EXCLUDE_DIRS = {".git", ".github", "__pycache__", ".pytest_cache", ".claude",
                 "tests", "docs"}

# Domínios congelados: o sync se RECUSA a escrever neles (dado irreproduzível em jogo).
# Onda 5 (2026-07-03): wc-predictor DESPARKADO — a coleta (ingest→matches.db) é
# independente da camada de análise; escrever vendor/ é aditivo e não toca o dado
# congelado no SQLite nem o config pré-registrado. A maquinaria permanece para PARKs
# futuros; hoje nenhum domínio está congelado.
PARKED: set[str] = set()


def _is_parked(name: str) -> bool:
    """Casa PARKED por prefixo: um rename de pasta (wc-predictor → wc-predictor-v2)
    NÃO pode reabrir silenciosamente a escrita num domínio congelado."""
    return any(name == p or name.startswith(p) for p in PARKED)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_files(root: Path) -> list[Path]:
    """Arquivos do núcleo a distribuir: *.py (recursivo) + VERSION, menos tooling/doc.

    Caminha a árvore inteira sob `root`, pulando os diretórios canônico-only
    (_EXCLUDE_DIRS) e os arquivos de raiz não-payload (_NOT_PAYLOAD)."""
    out = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in _EXCLUDE_DIRS for part in rel.parts):
            continue
        if len(rel.parts) == 1 and rel.name in _NOT_PAYLOAD:
            continue
        if p.suffix == ".py" or p.name == "VERSION":
            out.append(p)
    return out


def manifest(root: Path) -> dict:
    """Manifesto: {caminho_relativo_posix: sha256} + agregado determinístico."""
    files = {p.relative_to(root).as_posix(): _sha256(p) for p in payload_files(root)}
    aggregate = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16]
    return {"files": files, "aggregate": aggregate}


def consumers() -> list[Path]:
    """Domínios irmãos que JÁ consomem o core (têm vendor/predictor_core/)."""
    out = []
    for d in sorted(WORKSPACE.iterdir()):
        if d == CANONICAL or not d.is_dir():
            continue
        if (d / "vendor" / "predictor_core").is_dir():
            out.append(d)
    return out


def cmd_check() -> int:
    canon = manifest(CANONICAL)
    print(f"canônico predictor_core/ — agregado {canon['aggregate']} ({len(canon['files'])} arquivos)")
    found = consumers()
    if not found:
        print("  (nenhum consumidor com vendor/predictor_core/ ainda)")
        return 0
    drift = 0
    for d in found:
        mpath = d / "vendor" / "predictor_core" / MANIFEST_NAME
        parked = _is_parked(d.name)
        flag = "  [PARKED]" if parked else ""
        # Domínio PARKED está deliberadamente congelado: drift nele é ESPERADO e
        # informativo, não falha (não conta no exit code). Só drift em consumidor
        # ATIVO reprova o --check.
        if not mpath.exists():
            print(f"  {d.name:<20} sem manifest (vendoring legado) — rode --write{flag}")
            drift += 0 if parked else 1
            continue
        agg = json.loads(mpath.read_text(encoding="utf-8")).get("aggregate")
        if agg == canon["aggregate"]:
            print(f"  {d.name:<20} OK (em sincronia){flag}")
        else:
            # ASCII puro: o console cp1252 do Windows não encoda '≠'/'→' e quebraria aqui.
            print(f"  {d.name:<20} DRIFT (vendor={agg} != canonico={canon['aggregate']}){flag}")
            drift += 0 if parked else 1
    return 1 if drift else 0


def _prune_tree(vendor: Path, payload_rel: set) -> None:
    """Remove do vendor qualquer .py órfão (não mais no payload), o bytecode em cache
    e os subdiretórios que ficarem vazios — a árvore do vendor espelha EXATAMENTE a
    fonte (autoridade total: código customizado num domínio é deletado, não tolerado)."""
    for stale in vendor.rglob("*.py"):
        rel = stale.relative_to(vendor).as_posix()
        if rel not in payload_rel:
            stale.unlink()
            print(f"    prune: removido vendor/{rel} (não está mais no core)")
    for cache in vendor.rglob("__pycache__"):
        if cache.is_dir():
            shutil.rmtree(cache, ignore_errors=True)
    # remove subdiretórios vazios, de baixo para cima
    for d in sorted((p for p in vendor.rglob("*") if p.is_dir()),
                    key=lambda p: len(p.parts), reverse=True):
        try:
            if not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass


def cmd_write() -> int:
    canon = manifest(CANONICAL)
    files = payload_files(CANONICAL)
    payload_rel = {f.relative_to(CANONICAL).as_posix() for f in files}
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_version = (CANONICAL / "VERSION").read_text(encoding="utf-8").strip().split("\n")[0]
    wrote = 0
    for d in consumers():
        if _is_parked(d.name):
            print(f"  {d.name:<20} PULADO (PARKED — não se escreve em domínio congelado)")
            continue
        vendor = d / "vendor" / "predictor_core"
        for f in files:
            rel = f.relative_to(CANONICAL)
            target = vendor / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
        _prune_tree(vendor, payload_rel)
        out = {**canon, "synced_at": stamp, "source_version": source_version}
        (vendor / MANIFEST_NAME).write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {d.name:<20} sincronizado ({len(files)} arquivos, agregado {canon['aggregate']})")
        wrote += 1
    parked = ", ".join(sorted(PARKED)) or "(nenhum)"
    print(f"\n{wrote} consumidor(es) sincronizado(s). Congelados não tocados: {parked}")
    return 0


def main() -> int:
    # Console Windows é cp1252 e não encoda '—'/'≠' etc. — reconfigura para UTF-8
    # tolerante para o relatório nunca quebrar por causa de um glifo.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Distribuidor canônico do predictor_core")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="relata drift, não escreve")
    g.add_argument("--write", action="store_true", help="propaga o núcleo para os vendors")
    args = ap.parse_args()
    return cmd_check() if args.check else cmd_write()


if __name__ == "__main__":
    raise SystemExit(main())
