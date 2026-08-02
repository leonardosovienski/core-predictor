"""infra — WAL ligado, migração idempotente, config_hash determinístico."""

from predictor_core import infra


def test_connect_enables_wal_and_row_factory(tmp_path):
    conn = infra.connect(tmp_path / "t.db")
    assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    conn.execute("CREATE TABLE x(a)")
    conn.execute("INSERT INTO x VALUES(1)")
    row = conn.execute("SELECT a FROM x").fetchone()
    assert row["a"] == 1  # row_factory = sqlite3.Row (acesso por nome)
    conn.close()


def test_run_migrations_is_idempotent(tmp_path):
    conn = infra.connect(tmp_path / "m.db")
    migs = [("0001_init", "CREATE TABLE foo(id INTEGER);")]
    infra.run_migrations(conn, migs)
    infra.run_migrations(conn, migs)  # 2ª vez não pode reaplicar (tabela já existe)
    n = conn.execute("SELECT COUNT(*) FROM _migrations").fetchone()[0]
    assert n == 1
    conn.close()


def test_config_hash_deterministic_and_order_independent():
    a = infra.config_hash({"x": 1, "y": 2})
    b = infra.config_hash({"y": 2, "x": 1})  # ordem de chaves não importa
    assert a == b
    assert infra.config_hash({"x": 1, "y": 3}) != a  # valor diferente → hash diferente
