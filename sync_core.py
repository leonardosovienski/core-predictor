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
    py -3.14 sync_core.py --write --target f1-predictor  # restringe a UM consumidor
    (--target aceita só o nome exato do diretório; sem ele, opera em todos como antes)

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
# congelado no SQLite nem o config pré-registrado.
#
# Auditoria hostil 2026-07-17 (rodada "tools/"): PARKED vazio deixou `--write` sem
# `--target` sincronizar TODOS os consumidores com vendor/predictor_core/, inclusive
# os 3 projetos históricos/protegidos (wc-predictor-v2, predictor-stocks,
# nba-predictor) — nenhum deles deveria receber commits automáticos de vendor.
# Repovoado para restaurar a garantia original de congelamento.
PARKED: set[str] = {"wc-predictor-v2", "predictor-stocks", "nba-predictor"}


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
    aggregate = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
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


def _diff_files(canon_files: dict, vendor_files: dict) -> list:
    """Divergências arquivo a arquivo (relatório do drift): faltantes no vendor,
    órfãos no vendor e conteúdo modificado."""
    out = []
    for rel in sorted(canon_files.keys() | vendor_files.keys()):
        if rel not in vendor_files:
            out.append(f"faltando: {rel}")
        elif rel not in canon_files:
            out.append(f"orfao:    {rel}")
        elif vendor_files[rel] != canon_files[rel]:
            out.append(f"difere:   {rel}")
    return out


def _select_consumers(target: str | None) -> list[Path] | None:
    """Filtra consumers() por nome exato de diretório quando `target` é dado.

    Retorna None (sem escrever nada) se `target` não casar com nenhum
    consumidor conhecido — correspondência parcial/ambígua nunca é aceita."""
    found = consumers()
    if target is None:
        return found
    matches = [d for d in found if d.name == target]
    if not matches:
        names = ", ".join(d.name for d in found) or "(nenhum)"
        print(f"erro: consumidor '{target}' não encontrado. Conhecidos: {names}")
        return None
    return matches


def cmd_check(target: str | None = None) -> int:
    canon = manifest(CANONICAL)
    print(f"canônico predictor_core/ — agregado {canon['aggregate']} ({len(canon['files'])} arquivos)")
    found = _select_consumers(target)
    if found is None:
        return 2
    if not found:
        print("  (nenhum consumidor com vendor/predictor_core/ ainda)")
        return 0
    drift = 0
    for d in found:
        vendor = d / "vendor" / "predictor_core"
        mpath = vendor / MANIFEST_NAME
        parked = _is_parked(d.name)
        flag = "  [PARKED]" if parked else ""
        # A verificação re-HASHEIA os bytes reais do vendor — confiar no agregado
        # gravado no manifest não detectaria adulteração pós-sync (editar um .py do
        # vendor sem tocar no CORE_MANIFEST.json passaria como "em sincronia").
        actual = manifest(vendor)
        stored = (json.loads(mpath.read_text(encoding="utf-8")).get("aggregate")
                  if mpath.exists() else None)
        # Domínio PARKED está deliberadamente congelado: drift nele é ESPERADO e
        # informativo, não falha (não conta no exit code). Só drift em consumidor
        # ATIVO reprova o --check.
        if actual["aggregate"] == canon["aggregate"]:
            if stored is None:
                print(f"  {d.name:<20} OK (conteúdo em sincronia; sem manifest — rode --write){flag}")
            else:
                print(f"  {d.name:<20} OK (em sincronia){flag}")
            continue
        # ASCII puro: o console cp1252 do Windows não encoda '≠'/'→' e quebraria aqui.
        if stored == canon["aggregate"]:
            # manifest jura sincronia, mas os bytes divergem: alguém editou o vendor
            # DEPOIS do sync — exatamente o cenário que esta salvaguarda existe p/ pegar.
            print(f"  {d.name:<20} ADULTERADO (manifest={stored} mas conteudo={actual['aggregate']}){flag}")
        else:
            print(f"  {d.name:<20} DRIFT (vendor={actual['aggregate']} != canonico={canon['aggregate']}) — rode --write{flag}")
        for line in _diff_files(canon["files"], actual["files"])[:10]:
            print(f"      {line}")
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


def _recover_vendor_swap(vendor: Path) -> tuple[Path, Path]:
    """Recupera um swap interrompido antes de iniciar um novo sync.

    O vendor final nunca é alterado durante a preparação: uma árvore irmã é
    completamente montada e validada antes da troca. Se o processo morrer entre
    os dois renames, a próxima execução restaura o backup conhecido.
    """
    staging = vendor.with_name(vendor.name + ".sync-staging")
    backup = vendor.with_name(vendor.name + ".sync-backup")
    if not vendor.exists() and backup.exists():
        backup.replace(vendor)
    if staging.exists():
        shutil.rmtree(staging)
    if vendor.exists() and backup.exists():
        shutil.rmtree(backup)
    return staging, backup


def _write_vendor_atomically(vendor: Path, files: list[Path], canon: dict,
                             source_version: str, stamp: str) -> None:
    """Publica uma nova árvore por staging e swap recuperável.

    Diretórios não têm replace-atômico portável entre Windows e POSIX. A
    garantia oferecida é: falha na preparação preserva o vendor e uma queda
    durante o swap é recuperada deterministicamente no próximo sync.
    """
    staging, backup = _recover_vendor_swap(vendor)
    for source in files:
        rel = source.relative_to(CANONICAL)
        dest_path = staging / rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest_path)
    out = {**canon, "synced_at": stamp, "source_version": source_version}
    manifest_path = staging / MANIFEST_NAME
    manifest_path.write_text(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True),
                             encoding="utf-8")
    # O staging já contém a árvore inteira; qualquer erro antes daqui deixa o
    # vendor anterior intacto. O backup permite recuperação determinística
    # caso a máquina caia entre os dois renames.
    vendor.replace(backup)
    try:
        # O destino foi movido para `backup`; `rename` evita o modo
        # REPLACE_EXISTING de Windows, que rejeita a troca de diretórios mesmo
        # quando o destino já não existe.
        staging.rename(vendor)
    except BaseException:
        if backup.exists() and not vendor.exists():
            backup.replace(vendor)
        raise
    shutil.rmtree(backup)


def cmd_write(target: str | None = None) -> int:
    canon = manifest(CANONICAL)
    selected = _select_consumers(target)
    if selected is None:
        return 2
    files = payload_files(CANONICAL)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_version = (CANONICAL / "VERSION").read_text(encoding="utf-8").strip().split("\n")[0]
    wrote = 0
    for d in selected:
        if _is_parked(d.name):
            print(f"  {d.name:<20} PULADO (PARKED — não se escreve em domínio congelado)")
            continue
        vendor = d / "vendor" / "predictor_core"
        _write_vendor_atomically(vendor, files, canon, source_version, stamp)
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
    ap.add_argument("--target", metavar="CONSUMER", default=None,
                    help="restringe --check/--write a um único consumidor "
                         "(nome exato de diretório; sem isso, opera em todos)")
    args = ap.parse_args()
    return cmd_check(args.target) if args.check else cmd_write(args.target)


if __name__ == "__main__":
    raise SystemExit(main())
