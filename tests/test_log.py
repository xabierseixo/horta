from pathlib import Path

from horta.log import configurar_rexistro


def test_configurar_rexistro_crea_directorio_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    configurar_rexistro()

    assert (tmp_path / "logs").is_dir()


def test_configurar_rexistro_e_idempotente(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    configurar_rexistro()
    configurar_rexistro()  # non debe fallar nin duplicar

    # Non hai xeito directo de contar handlers de loguru dende fóra sen
    # tocar API interna, así que a proba real é que a segunda chamada
    # non levanta excepción e o directorio segue existindo.
    assert (tmp_path / "logs").is_dir()
