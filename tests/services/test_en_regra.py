from datetime import date

from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.en_regra import requisitos_en_regra
from horta.services.hortas import actualizar_horta, crear_horta
from horta.services.persoas import crear_persoa


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def test_non_profesional_non_ten_requisitos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    assert requisitos_en_regra(session, ana, horta) == []


def test_profesional_sen_datos_ten_tres_pendentes(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    requisitos = requisitos_en_regra(session, ana, horta)
    assert [r.texto for r in requisitos] == [
        "NIF do titular",
        "Inscrición no REAGA",
        "Aplicador con carné ROPO en vigor",
    ]
    assert not any(r.cumprido for r in requisitos)


def test_profesional_completo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    actualizar_horta(
        session, ana, horta, titular_nif="12345678Z", codigo_reaga="ES150010000001"
    )
    crear_persoa(session, ana, horta.id, "Xan", e_aplicador=True, ropo_numero="1",
                 ropo_caducidade=date(2030, 1, 1))
    requisitos = requisitos_en_regra(session, ana, horta, hoxe=date(2026, 10, 22))
    assert all(r.cumprido for r in requisitos)


def test_con_animais_pide_rega(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=10)
    textos = [r.texto for r in requisitos_en_regra(session, ana, horta)]
    assert "Código REGA do gando" in textos
