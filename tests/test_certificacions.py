"""Probas do servizo de certificacións, autoavaliación e informes de auditoría (tarefa 182c)."""

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.certificacions import (
    actualizar_certificacion,
    actualizar_punto,
    avisos_certificacions,
    baixa_certificacion,
    borrar_punto,
    crear_certificacion,
    crear_punto,
    estado_certificacion,
    informe_auditoria,
    informe_auditoria_xlsx,
    listar_certificacions,
    listar_puntos,
)
from horta.services.documentos import crear_documento
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro


def _crear_usuario(session, email: str, rol: RolGlobal = RolGlobal.USUARIO) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=rol,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def _escenario(session):
    ana = _crear_usuario(session, "ana@example.com")
    pepe = _crear_usuario(session, "pepe@example.com")
    luis = _crear_usuario(session, "luis@example.com")
    alleo = _crear_usuario(session, "alleo@example.com")

    horta = crear_horta(session, ana, "Horta das Rías")
    engadir_membro(session, ana, horta.id, pepe, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)
    return ana, pepe, luis, alleo, horta


def test_globalgap_ggn_valido_e_non_valido(session):
    ana, _, _, _, horta = _escenario(session)

    # GGN válido de 13 díxitos
    cert = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="globalgap",
        numero="1234567890123",
        entidade="CertiCalidade",
    )
    assert cert.id is not None
    assert cert.numero == "1234567890123"

    # Sen número en GlobalGAP tamén se permite (se o hai, ten 13 díxitos)
    cert_sen_num = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="globalgap",
        numero=None,
    )
    assert cert_sen_num.id is not None

    # GGN con 12 díxitos: falla
    with pytest.raises(OperacionNonPermitidaError, match="13 díxitos"):
        crear_certificacion(
            session,
            ana,
            horta.id,
            esquema="globalgap",
            numero="123456789012",
        )

    # GGN con 14 díxitos: falla
    with pytest.raises(OperacionNonPermitidaError, match="13 díxitos"):
        crear_certificacion(
            session,
            ana,
            horta.id,
            esquema="globalgap",
            numero="12345678901234",
        )

    # GGN con letras: falla
    with pytest.raises(OperacionNonPermitidaError, match="13 díxitos"):
        crear_certificacion(
            session,
            ana,
            horta.id,
            esquema="globalgap",
            numero="123456789012A",
        )

    # Actualizar cun GGN non válido tamén falla
    with pytest.raises(OperacionNonPermitidaError, match="13 díxitos"):
        actualizar_certificacion(
            session,
            ana,
            cert,
            numero="curto",
        )


def test_dop_igp_e_outro_sen_nome_falla(session):
    ana, _, _, _, horta = _escenario(session)

    # dop_igp sen nome falla
    with pytest.raises(OperacionNonPermitidaError, match="O nome é obrigatorio"):
        crear_certificacion(
            session,
            ana,
            horta.id,
            esquema="dop_igp",
            nome=None,
        )

    with pytest.raises(OperacionNonPermitidaError, match="O nome é obrigatorio"):
        crear_certificacion(
            session,
            ana,
            horta.id,
            esquema="dop_igp",
            nome="   ",
        )

    # outro sen nome falla
    with pytest.raises(OperacionNonPermitidaError, match="O nome é obrigatorio"):
        crear_certificacion(
            session,
            ana,
            horta.id,
            esquema="outro",
            nome="",
        )

    # dop_igp con nome funciona
    cert_dop = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="dop_igp",
        nome="Pataca de Galicia",
    )
    assert cert_dop.nome == "Pataca de Galicia"

    # outro con nome funciona
    cert_outro = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="outro",
        nome="Selo Tradicional",
    )
    assert cert_outro.nome == "Selo Tradicional"

    # ecolóxica non require nome obrigatorio
    cert_eco = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="ecoloxica",
        nome=None,
    )
    assert cert_eco.nome is None

    # Actualizar dop_igp quitando o nome falla
    with pytest.raises(OperacionNonPermitidaError, match="O nome é obrigatorio"):
        actualizar_certificacion(
            session,
            ana,
            cert_dop,
            nome="",
        )


def test_datas_certificacion_e_baixa(session):
    ana, _, _, _, horta = _escenario(session)

    # data_fin anterior a data_inicio falla
    with pytest.raises(OperacionNonPermitidaError, match="data de fin"):
        crear_certificacion(
            session,
            ana,
            horta.id,
            esquema="ecoloxica",
            data_inicio=date(2026, 6, 1),
            data_fin=date(2026, 5, 31),
        )

    cert = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="ecoloxica",
        data_inicio=date(2026, 1, 1),
        data_fin=date(2026, 12, 31),
    )
    assert cert.activa is True

    baixa_certificacion(session, ana, cert)
    assert cert.activa is False

    # Listar só activas por defecto non inclúe a que está de baixa
    activas = listar_certificacions(session, ana, horta.id)
    assert cert.id not in [c.id for c in activas]

    # Non se pode modificar unha certificación dada de baixa
    with pytest.raises(OperacionNonPermitidaError, match="dada de baixa"):
        actualizar_certificacion(session, ana, cert, entidade="Nova Entidade")


def test_non_cumpre_sen_accion_falla(session):
    ana, _, _, _, horta = _escenario(session)
    cert = crear_certificacion(session, ana, horta.id, esquema="ecoloxica")

    # non_cumpre sen acción correctora falla
    with pytest.raises(OperacionNonPermitidaError, match="A acción correctora é obrigatoria"):
        crear_punto(
            session,
            ana,
            cert.id,
            data=date(2026, 6, 15),
            punto="FV 5.1.1",
            resultado="non_cumpre",
            accion_correctora=None,
        )

    with pytest.raises(OperacionNonPermitidaError, match="A acción correctora é obrigatoria"):
        crear_punto(
            session,
            ana,
            cert.id,
            data=date(2026, 6, 15),
            punto="FV 5.1.1",
            resultado="non_cumpre",
            accion_correctora="   ",
        )

    # non_cumpre con acción correctora funciona
    pto = crear_punto(
        session,
        ana,
        cert.id,
        data=date(2026, 6, 15),
        punto="FV 5.1.1",
        resultado="non_cumpre",
        evidencia="Falta rexistro de limpeza",
        accion_correctora="Crear e asinar rexistro de limpeza semanal",
    )
    assert pto.id is not None
    assert pto.resultado == "non_cumpre"
    assert pto.data_correccion is None

    # cumpre ou non_aplica sen acción correctora funciona
    pto_ok = crear_punto(
        session,
        ana,
        cert.id,
        data=date(2026, 6, 15),
        punto="FV 5.1.2",
        resultado="cumpre",
    )
    assert pto_ok.resultado == "cumpre"

    pto_na = crear_punto(
        session,
        ana,
        cert.id,
        data=date(2026, 6, 15),
        punto="FV 5.1.3",
        resultado="non_aplica",
    )
    assert pto_na.resultado == "non_aplica"

    # Actualizar punto a non_cumpre baleirando a acción correctora falla
    with pytest.raises(OperacionNonPermitidaError, match="A acción correctora é obrigatoria"):
        actualizar_punto(
            session,
            ana,
            pto_ok,
            resultado="non_cumpre",
            accion_correctora="",
        )

    # Borrar punto funciona
    borrar_punto(session, ana, pto_na)
    pts = listar_puntos(session, ana, cert.id)
    assert pto_na.id not in [p.id for p in pts]


def test_avisos_caducidade_e_correccions(session):
    ana, _, _, _, horta = _escenario(session)
    hoxe = date(2026, 7, 1)

    # 1. Selo caducado
    cert_caducado = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="demeter",
        data_inicio=date(2025, 1, 1),
        data_fin=hoxe - timedelta(days=5),
    )
    assert estado_certificacion(cert_caducado, hoxe) == "caducado"

    # 2. Selo que caduca nos próximos 60 días (por exemplo en 20 días)
    cert_pronto = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="leaf",
        data_inicio=date(2025, 7, 21),
        data_fin=hoxe + timedelta(days=20),
    )
    assert estado_certificacion(cert_pronto, hoxe) == "caduca_pronto"

    # 3. Selo vixente a máis de 60 días
    cert_vixente = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="ecoloxica",
        data_inicio=date(2026, 1, 1),
        data_fin=hoxe + timedelta(days=120),
    )
    assert estado_certificacion(cert_vixente, hoxe) == "vixente"

    # 4. Punto con non_cumpre sen corrección
    crear_punto(
        session,
        ana,
        cert_vixente.id,
        data=hoxe - timedelta(days=10),
        punto="PTO-10",
        resultado="non_cumpre",
        accion_correctora="Corrixir valado",
        data_correccion=None,
    )

    avisos = avisos_certificacions(session, ana, horta.id, hoxe=hoxe)
    # Debe haber aviso de caducado, aviso de caduca pronto e aviso de corrección pendente
    textos = " ".join(avisos)
    assert "caducou" in textos
    assert "caduca en 20 días" in textos
    assert "corrección pendente no punto PTO-10" in textos

    # Cando se engade a data de corrección, o aviso desaparece
    puntos = listar_puntos(session, ana, cert_vixente.id)
    actualizar_punto(session, ana, puntos[0], data_correccion=hoxe)

    avisos_despois = avisos_certificacions(session, ana, horta.id, hoxe=hoxe)
    textos_despois = " ".join(avisos_despois)
    assert "corrección pendente no punto PTO-10" not in textos_despois


def test_informe_auditoria_ten_todas_as_follas(session):
    ana, _, _, _, horta = _escenario(session)
    cert = crear_certificacion(
        session,
        ana,
        horta.id,
        esquema="ecoloxica",
        numero="ECO-123",
        entidade="CRAEGA",
        data_inicio=date(2026, 1, 1),
        data_fin=date(2026, 12, 31),
    )
    # Engadimos punto de autoavaliación
    crear_punto(
        session,
        ana,
        cert.id,
        data=date(2026, 4, 10),
        punto="ECOL 1.1",
        resultado="cumpre",
        evidencia="Certificado de sementes ecolóxicas",
    )
    # Engadimos un documento
    crear_documento(
        session,
        ana,
        horta.id,
        tipo="certificado_calidade",
        nome="Certificado CRAEGA 2026",
    )

    informe = informe_auditoria(session, ana, cert.id, ano=2026)

    follas_esperadas = [
        "Explotación e selo",
        "Autoavaliación",
        "Tratamentos",
        "Abonados",
        "Regas",
        "Colleitas e lotes",
        "Saídas de lotes",
        "Análises",
        "Documentos",
    ]
    for folla in follas_esperadas:
        assert folla in informe
        assert isinstance(informe[folla], list)
        assert len(informe[folla]) > 0

    # Comprobamos contido da autoavaliación
    folla_auto = informe["Autoavaliación"]
    assert any("ECOL 1.1" in row for row in folla_auto)

    # Comprobamos contido de documentos
    folla_docs = informe["Documentos"]
    assert any("Certificado CRAEGA 2026" in row for row in folla_docs)

    # Comprobamos xeración de bytes xlsx e apertura con openpyxl
    xlsx_bytes = informe_auditoria_xlsx(session, ana, cert.id, ano=2026)
    assert isinstance(xlsx_bytes, bytes)
    assert len(xlsx_bytes) > 0

    wb = load_workbook(BytesIO(xlsx_bytes))
    for folla in follas_esperadas:
        assert folla[:31] in wb.sheetnames


def test_permisos(session):
    ana, pepe, luis, alleo, horta = _escenario(session)

    # Admin e Editor poden crear certificacións
    cert_ana = crear_certificacion(session, ana, horta.id, esquema="ecoloxica")
    cert_pepe = crear_certificacion(session, pepe, horta.id, esquema="leaf")
    assert cert_ana.id is not None
    assert cert_pepe.id is not None

    # Lector non pode crear nin modificar certificacións
    with pytest.raises(PermisoDenegadoError):
        crear_certificacion(session, luis, horta.id, esquema="qs")

    with pytest.raises(PermisoDenegadoError):
        actualizar_certificacion(session, luis, cert_ana, entidade="Prohibido")

    with pytest.raises(PermisoDenegadoError):
        baixa_certificacion(session, luis, cert_ana)

    # Lector pode listar certificacións
    certs_luis = listar_certificacions(session, luis, horta.id)
    assert len(certs_luis) == 2

    # Admin e Editor poden crear puntos
    pto_ana = crear_punto(
        session,
        ana,
        cert_ana.id,
        data=date(2026, 5, 1),
        punto="1.1",
        resultado="cumpre",
    )
    pto_pepe = crear_punto(
        session,
        pepe,
        cert_ana.id,
        data=date(2026, 5, 2),
        punto="1.2",
        resultado="cumpre",
    )
    assert pto_ana.id is not None
    assert pto_pepe.id is not None

    # Lector non pode crear, actualizar nin borrar puntos
    with pytest.raises(PermisoDenegadoError):
        crear_punto(
            session,
            luis,
            cert_ana.id,
            data=date(2026, 5, 3),
            punto="1.3",
            resultado="cumpre",
        )

    with pytest.raises(PermisoDenegadoError):
        actualizar_punto(session, luis, pto_ana, punto="1.1b")

    with pytest.raises(PermisoDenegadoError):
        borrar_punto(session, luis, pto_ana)

    # Lector pode listar puntos e obter o informe de auditoría
    pts_luis = listar_puntos(session, luis, cert_ana.id)
    assert len(pts_luis) == 2

    inf_luis = informe_auditoria(session, luis, cert_ana.id, ano=2026)
    assert "Explotación e selo" in inf_luis

    # Usuario alleo non ten acceso a nada
    with pytest.raises(PermisoDenegadoError):
        listar_certificacions(session, alleo, horta.id)

    with pytest.raises(PermisoDenegadoError):
        crear_certificacion(session, alleo, horta.id, esquema="ecoloxica")

    with pytest.raises(PermisoDenegadoError):
        listar_puntos(session, alleo, cert_ana.id)

    with pytest.raises(PermisoDenegadoError):
        informe_auditoria(session, alleo, cert_ana.id, ano=2026)
