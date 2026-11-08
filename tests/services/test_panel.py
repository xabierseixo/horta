"""Probas do servizo do panel de explotacións (paso 168)."""

from datetime import date

from horta.models.horta import RolHorta
from horta.models.outro_traballo import OutroTraballo
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.documentos import crear_documento
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.panel import resumo_explotacions
from horta.services.tarefas import crear_tarefa


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


def test_usuario_con_duas_explotacions(session):
    ana = _crear_usuario(session, "ana@example.com")
    dia = date(2026, 10, 22)

    # 1. Explotación profesional con documento caducado e tarefa atrasada
    horta_prof = crear_horta(
        session, ana, "Explotación Profesional", uso_profesional=True
    )
    crear_documento(
        session,
        ana,
        horta_prof.id,
        tipo="certificado_calidade",
        nome="Certificado CRAEGA",
        data_caducidade=date(2026, 1, 1),
    )
    crear_tarefa(
        session,
        ana,
        horta_prof.id,
        "Revisar cerramento",
        data_limite=date(2026, 1, 1),
    )

    # 2. Explotación de autoconsumo sen nada
    horta_auto = crear_horta(
        session, ana, "Horta Autoconsumo", uso_profesional=False
    )

    resumos = resumo_explotacions(session, ana, hoxe=dia)
    assert len(resumos) == 2

    # A profesional ten máis avisos (3 requisitos + 1 doc + 1 tarefa = 5), vai primeiro
    r_prof = resumos[0]
    assert r_prof.horta_id == horta_prof.id
    assert r_prof.nome == "Explotación Profesional"
    assert r_prof.rol == "admin"
    assert r_prof.uso_profesional is True
    assert r_prof.requisitos_pendentes == 3  # titular, REAGA, ROPO pendentes
    assert r_prof.documentos_aviso == 1
    assert r_prof.faltas_caderno == 0
    assert r_prof.tarefas_atrasadas == 1
    assert r_prof.avisos_cue == 0
    assert r_prof.total_avisos == 5

    # A de autoconsumo non ten avisos e vai de segunda
    r_auto = resumos[1]
    assert r_auto.horta_id == horta_auto.id
    assert r_auto.nome == "Horta Autoconsumo"
    assert r_auto.rol == "admin"
    assert r_auto.uso_profesional is False
    assert r_auto.requisitos_pendentes == 0
    assert r_auto.documentos_aviso == 0
    assert r_auto.faltas_caderno == 0
    assert r_auto.tarefas_atrasadas == 0
    assert r_auto.avisos_cue == 0
    assert r_auto.total_avisos == 0


def test_autoconsumo_requisitos_e_faltas_caderno_a_cero(session):
    ana = _crear_usuario(session, "ana@example.com")
    dia = date(2026, 10, 22)
    # Autoconsumo con animais: requisitos_en_regra pediría REGA, pero no panel vai a 0
    horta_auto = crear_horta(
        session, ana, "Autoconsumo Gando", uso_profesional=False
    )
    crear_animal(session, ana, horta_auto.id, "galiñas", date(2026, 1, 1), cantidade=4)

    resumos = resumo_explotacions(session, ana, hoxe=dia)
    assert len(resumos) == 1
    assert resumos[0].requisitos_pendentes == 0
    assert resumos[0].faltas_caderno == 0


def test_usuario_sen_explotacions_devolve_lista_baleira(session):
    ana = _crear_usuario(session, "ana@example.com")
    assert resumo_explotacions(session, ana) == []


def test_non_saen_explotacions_doutros_usuarios(session):
    ana = _crear_usuario(session, "ana@example.com")
    lois = _crear_usuario(session, "lois@example.com")
    horta = crear_horta(session, ana, "Horta de Ana")

    # Lois non é membro, devolve lista baleira
    assert resumo_explotacions(session, lois) == []

    # Se se engade como lector, xa sae co seu rol
    engadir_membro(session, ana, horta.id, lois, RolHorta.LECTOR)
    resumos = resumo_explotacions(session, lois)
    assert len(resumos) == 1
    assert resumos[0].horta_id == horta.id
    assert resumos[0].rol == "lector"


def test_orde_a_igualdade_de_avisos_por_nome(session):
    ana = _crear_usuario(session, "ana@example.com")
    crear_horta(session, ana, "Zeta")
    crear_horta(session, ana, "Alfa")

    resumos = resumo_explotacions(session, ana)
    assert [r.nome for r in resumos] == ["Alfa", "Zeta"]


def test_ultimo_traballo_feito_dentro_do_ano(session):
    ana = _crear_usuario(session, "ana@example.com")
    dia = date(2026, 10, 22)
    horta = crear_horta(session, ana, "Horta Con Traballos")

    # Traballo feito hai 30 días
    t_recente = OutroTraballo(
        horta_id=horta.id,
        descricion="Reparar valado",
        data_inicio=date(2026, 9, 22),
    )
    session.add(t_recente)
    session.commit()

    resumos = resumo_explotacions(session, ana, hoxe=dia)
    assert resumos[0].ultimo_traballo == date(2026, 9, 22)

    # Se o traballo é de hai máis de 365 días, non conta
    t_antigo = OutroTraballo(
        horta_id=horta.id,
        descricion="Traballo vello",
        data_inicio=date(2024, 1, 1),
    )
    session.add(t_antigo)
    session.delete(t_recente)
    session.commit()

    resumos2 = resumo_explotacions(session, ana, hoxe=dia)
    assert resumos2[0].ultimo_traballo is None
