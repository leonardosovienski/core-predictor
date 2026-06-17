#!/usr/bin/env python3
"""sync_core — distribuidor canônico do predictor_core (fluxo UNIDIRECIONAL).

REGRA DE OURO: a verdade vive AQUI (predictor_core/). Este script LÊ os módulos
homologados deste diretório, calcula o hash de integridade, e ESCREVE (sobrescreve)
nas pastas vendor/predictor_core/ dos domínios consumidores.

Você nunca mais edita a matemática dentro do stocks ou do cripto: corrige AQUI, roda
o sync, e a correção propaga com integridade garantida — matando o "drift".

Uso (de qualquer diretório):
    py -3.12 sync_core.py --check     # relata o drift de cada consumidor (NÃO escreve)
    py -3.12 sync_core.py --write     # propaga o núcleo p/ os vendors (grava manifest)

Segurança:
  - SÓ escreve em domínios que JÁ têm vendor/predictor_core/ (consumidores opt-in).
  - NUNCA escreve em domínios PARKED (ex.: wc-predictor — dado irreproduzível da Copa).
  - Grava CORE_MANIFEST.json (hash por arquivo + agregado) em cada vendor: a assinatura
    que o --check confere depois.
"""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

CANONICAL = Path(__file__).resolve().parent     # predictor_core/  (a fonte da verdade)
WORKSPACE = CANONICAL.parent                     # raiz com os domínios lado a lado
MANIFEST_NAME = "CORE_MANIFEST.json"

# Tooling/artefatos do canônico — não fazem parte do payload distribuído:
_NOT_PAYLOAD = {"sync_core.py", MANIFEST_NAME, "README.md"}

# Domínios congelados: o sync se RECUSA a escrever neles (dado irreproduzível em jogo).
PARKED = {"wc-predictor"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_files(root: Path) -> list[Path]:
    """Arquivos do núcleo a distribuir: *.py + VERSION, menos o tooling."""
    out = []
    for p in sorted(root.iterdir()):
        if p.is_dir() or p.name in _NOT_PAYLOAD or p.name.startswith("."):
            continue
        if p.suffix == ".py" or p.name == "VERSION":
            out.append(p)
    return out


def manifest(root: Path) -> dict:
    files = {p.name: _sha256(p) for p in payload_files(root)}
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
        flag = "  [PARKED]" if d.name in PARKED else ""
        if not mpath.exists():
            print(f"  {d.name:<20} sem manifest (vendoring legado) — rode --write{flag}")
            drift += 1
            continue
        agg = json.loads(mpath.read_text(encoding="utf-8")).get("aggregate")
        if agg == canon["aggregate"]:
            print(f"  {d.name:<20} OK (em sincronia){flag}")
        else:
            print(f"  {d.name:<20} DRIFT (vendor={agg} ≠ canônico={canon['aggregate']}){flag}")
            drift += 1
    return 1 if drift else 0


def cmd_write() -> int:
    canon = manifest(CANONICAL)
    files = payload_files(CANONICAL)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_version = (CANONICAL / "VERSION").read_text(encoding="utf-8").strip()
    wrote = 0
    for d in consumers():
        if d.name in PARKED:
            print(f"  {d.name:<20} PULADO (PARKED — não se escreve em domínio congelado)")
            continue
        vendor = d / "vendor" / "predictor_core"
        for f in files:
            shutil.copy2(f, vendor / f.name)
        out = {**canon, "synced_at": stamp, "source_version": source_version}
        (vendor / MANIFEST_NAME).write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {d.name:<20} sincronizado ({len(files)} arquivos, agregado {canon['aggregate']})")
        wrote += 1
    parked = ", ".join(sorted(PARKED)) or "(nenhum)"
    print(f"\n{wrote} consumidor(es) sincronizado(s). Congelados não tocados: {parked}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Distribuidor canônico do predictor_core")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="relata drift, não escreve")
    g.add_argument("--write", action="store_true", help="propaga o núcleo para os vendors")
    args = ap.parse_args()
    return cmd_check() if args.check else cmd_write()


if __name__ == "__main__":
    raise SystemExit(main())
