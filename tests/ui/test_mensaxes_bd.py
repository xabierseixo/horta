"""Mensaxes cando a base de datos rexeita un cambio (D2)."""

from sqlalchemy.exc import IntegrityError

from horta.ui.mensaxes_bd import mensaxe_integridade


def _erro(motivo):
    return IntegrityError("INSERT …", {}, Exception(motivo))


def test_algo_depende_disto():
    assert mensaxe_integridade(_erro("FOREIGN KEY constraint failed")) == (
        "Non se pode: hai outros datos que dependen disto")


def test_duplicado_sqlite_e_postgresql():
    assert mensaxe_integridade(_erro("UNIQUE constraint failed: parcela.nome")) == (
        "Xa existe un rexistro con eses datos")
    assert mensaxe_integridade(_erro("duplicate key value violates unique constraint")) == (
        "Xa existe un rexistro con eses datos")


def test_falta_un_dato():
    assert mensaxe_integridade(_erro("NOT NULL constraint failed: parcela.nome")) == (
        "Faltan datos ou algún non é válido")
