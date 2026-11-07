"""Probas para a ficha da persoa (datos_persoa)."""

from __future__ import annotations

from datetime import date

from horta.models.persoa import Persoa, TipoCarne
from horta.ui.ficha_persoa import datos_persoa


def _describir_proba(catalogo: str, codigo: str) -> str:
    return codigo


def test_datos_persoa_completa() -> None:
    """Unha persoa con todos os datos mostra as súas etiquetas e valores formatados."""
    persoa = Persoa(
        nome="Xiana",
        apelidos="López Gómez",
        nif="12345678Z",
        ropo_numero="12345678901234",
        ropo_tipo_carne=TipoCarne.cualificado,
        ropo_caducidade=date(2028, 5, 20),
        regfer_numero="REGFER-123",
        rega="ES123456789012",
        reaga="ES987654321098",
        nima="NIMA-001",
        ropveg="ROPVEG-002",
        rexistro_dixital="RD-003",
        num_asesoramento="ASESOR-004",
        enderezo="Rúa Maior 10",
        localidade="Compostela",
        codigo_postal="15701",
        provincia="A Coruña",
        pais="España",
    )
    datos = datos_persoa(persoa, _describir_proba)

    esperados = [
        ("Nome ou razón social", "Xiana"),
        ("Apelidos", "López Gómez"),
        ("NIF", "12345678Z"),
        ("Nº ROPO", "12345678901234"),
        ("Tipo de carné", "Cualificado"),
        ("Caducidade do carné", "20/05/2028"),
        ("Nº REGFER", "REGFER-123"),
        ("REGA (ES + 12 díxitos)", "ES123456789012"),
        ("REAGA", "ES987654321098"),
        ("NIMA", "NIMA-001"),
        ("Nº ROPVEG", "ROPVEG-002"),
        ("Nº de rexistro dixital de alimentos", "RD-003"),
        ("Nº de identificación da entidade de asesoramento", "ASESOR-004"),
        ("Enderezo", "Rúa Maior 10"),
        ("Localidade", "Compostela"),
        ("Código postal", "15701"),
        ("Provincia", "A Coruña"),
        ("País, se non é España", "España"),
    ]
    assert datos == esperados


def test_datos_persoa_so_nome() -> None:
    """Unha persoa só co nome devolve unicamente a parella de Nome ou razón social."""
    persoa = Persoa(nome="Xan")
    datos = datos_persoa(persoa, _describir_proba)

    assert datos == [("Nome ou razón social", "Xan")]
