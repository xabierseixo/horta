"""Probas do servizo de documentos e certificacións (paso N2)."""

from datetime import date, timedelta

import pytest

from horta.models.documento import Documento
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.documentos import (
    actualizar_documento,
    crear_documento,
    dar_de_baixa_documento,
    documentos_con_aviso,
    estado_documento,
    extension,
    ficheiro_do_documento,
    gardar_ficheiro,
    listar_documentos,
)
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela

PDF_MINIMO = b"%PDF-1.4 contido de proba"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20
JPG = b"\xff\xd8\xff\xe0" + b"0" * 20
WEBP = b"RIFF" + b"0000" + b"WEBP" + b"0" * 20


@pytest.fixture(autouse=True)
def cartafol(tmp_path, monkeypatch):
    monkeypatch.setenv("HORTA_DOCUMENTOS_DIR", str(tmp_path))
    return tmp_path


def _usuario(session, nome):
    usuario = Usuario(
        nome=nome,
        email=f"{nome}@example.com",
        password_hash="x",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def _escenario(session):
    ana = _usuario(session, "ana")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    return ana, horta, parcela


def test_crear_documento_correcto(session):
    ana, horta, parcela = _escenario(session)
    doc = crear_documento(
        session,
        ana,
        horta.id,
        tipo="certificado_calidade",
        nome="Certificado CRAEGA",
        emisor="CRAEGA",
        numero="GA-2026-001",
        data_emision=date(2026, 1, 1),
        data_caducidade=date(2027, 1, 1),
        que="parcela",
        ref_id=parcela.id,
        notas="Certificación anual",
    )
    assert doc.id is not None
    assert doc.horta_id == horta.id
    assert doc.tipo == "certificado_calidade"
    assert doc.nome == "Certificado CRAEGA"
    assert doc.emisor == "CRAEGA"
    assert doc.numero == "GA-2026-001"
    assert doc.data_emision == date(2026, 1, 1)
    assert doc.data_caducidade == date(2027, 1, 1)
    assert doc.que == "parcela"
    assert doc.ref_id == parcela.id
    assert doc.notas == "Certificación anual"
    assert doc.baixa is False
    assert doc.creado_por == ana.id

    # Crear sen referencia (á explotación enteira)
    doc_global = crear_documento(
        session,
        ana,
        horta.id,
        tipo="seguro",
        nome="Seguro da explotación",
    )
    assert doc_global.que is None
    assert doc_global.ref_id is None


def test_crear_documento_validacions(session):
    ana, horta, parcela = _escenario(session)

    # Tipo descoñecido
    with pytest.raises(ValueError):
        crear_documento(session, ana, horta.id, tipo="desconhecido", nome="Doc")

    # Nome baleiro
    with pytest.raises(OperacionNonPermitidaError):
        crear_documento(session, ana, horta.id, tipo="seguro", nome="")
    with pytest.raises(OperacionNonPermitidaError):
        crear_documento(session, ana, horta.id, tipo="seguro", nome="   ")

    # Caducidade antes da emisión
    with pytest.raises(OperacionNonPermitidaError):
        crear_documento(
            session,
            ana,
            horta.id,
            tipo="seguro",
            nome="Seguro",
            data_emision=date(2026, 5, 10),
            data_caducidade=date(2026, 5, 9),
        )

    # Referencia doutra horta
    outra_horta = crear_horta(session, ana, "Outra Horta")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta"):
        crear_documento(
            session,
            ana,
            outra_horta.id,
            tipo="seguro",
            nome="Seguro",
            que="parcela",
            ref_id=parcela.id,
        )

    # Referencia con modelo non admitido
    with pytest.raises(OperacionNonPermitidaError, match="non é desta"):
        crear_documento(
            session,
            ana,
            horta.id,
            tipo="seguro",
            nome="Seguro",
            que="inventado",
            ref_id=1,
        )

    # Referencia inexistente
    with pytest.raises(OperacionNonPermitidaError, match="non é desta"):
        crear_documento(
            session,
            ana,
            horta.id,
            tipo="seguro",
            nome="Seguro",
            que="parcela",
            ref_id=999999,
        )


def test_lector_non_pode_crear(session):
    ana, horta, _ = _escenario(session)
    luis = _usuario(session, "luis")
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        crear_documento(
            session,
            luis,
            horta.id,
            tipo="seguro",
            nome="Documento lector",
        )


def test_gardar_ficheiro_e_recuperar(session, cartafol):
    ana, horta, _ = _escenario(session)
    luis, xan = _usuario(session, "luis"), _usuario(session, "xan")
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)

    doc = crear_documento(session, ana, horta.id, tipo="seguro", nome="Póliza")
    gardar_ficheiro(session, ana, doc, PDF_MINIMO, "poliza.pdf")

    assert doc.ficheiro.endswith(".pdf")
    assert doc.nome_orixinal == "poliza.pdf"
    assert (cartafol / str(horta.id) / doc.ficheiro).read_bytes() == PDF_MINIMO

    ruta = ficheiro_do_documento(session, ana, doc.id)
    assert ruta == cartafol / str(horta.id) / doc.ficheiro

    # O lector pode consultar o ficheiro
    assert ficheiro_do_documento(session, luis, doc.id) == ruta

    # O lector non pode gardar ficheiro
    with pytest.raises(PermisoDenegadoError):
        gardar_ficheiro(session, luis, doc, PDF_MINIMO)

    # Quen non é da explotación non ten acceso
    with pytest.raises(PermisoDenegadoError):
        ficheiro_do_documento(session, xan, doc.id)


def test_gardar_ficheiro_validacions(session):
    ana, horta, _ = _escenario(session)
    doc = crear_documento(session, ana, horta.id, tipo="seguro", nome="Póliza")

    # Ficheiro de texto (non admitido)
    with pytest.raises(OperacionNonPermitidaError, match="Só se admiten PDF ou imaxes"):
        gardar_ficheiro(session, ana, doc, b"Ola mundo texto", "nota.txt")

    # Máis de 20 MB
    grando = b"%PDF" + b"0" * (20 * 1024 * 1024 + 1)
    with pytest.raises(OperacionNonPermitidaError, match="20 MB"):
        gardar_ficheiro(session, ana, doc, grando)

    # Ficheiro do documento sen ficheiro adxunto
    doc_sen = crear_documento(session, ana, horta.id, tipo="contrato", nome="Contrato verbal")
    with pytest.raises(OperacionNonPermitidaError):
        ficheiro_do_documento(session, ana, doc_sen.id)

    # Documento inexistente
    with pytest.raises(OperacionNonPermitidaError):
        ficheiro_do_documento(session, ana, 999999)


def test_gardar_ficheiro_imaxes(session, cartafol):
    ana, horta, _ = _escenario(session)
    for contido, ext_esperada in ((JPG, ".jpg"), (PNG, ".png"), (WEBP, ".webp")):
        doc = crear_documento(session, ana, horta.id, tipo="outro", nome=f"Foto {ext_esperada}")
        gardar_ficheiro(session, ana, doc, contido, f"imaxe{ext_esperada}")
        assert doc.ficheiro.endswith(ext_esperada)
        assert (cartafol / str(horta.id) / doc.ficheiro).read_bytes() == contido


def test_estado_documento():
    hoxe = date(2026, 11, 8)

    # Caducado (anterior a hoxe)
    d_cad = Documento(data_caducidade=date(2026, 11, 7))
    assert estado_documento(d_cad, hoxe) == "caducado"

    # Caduca hoxe
    d_hoxe = Documento(data_caducidade=date(2026, 11, 8))
    assert estado_documento(d_hoxe, hoxe) == "caduca_pronto"

    # Caduca en 30 días
    d_30 = Documento(data_caducidade=hoxe + timedelta(days=30))
    assert estado_documento(d_30, hoxe) == "caduca_pronto"

    # Caduca en 31 días
    d_31 = Documento(data_caducidade=hoxe + timedelta(days=31))
    assert estado_documento(d_31, hoxe) == "vixente"

    # Sen data de caducidade
    d_sen = Documento(data_caducidade=None)
    assert estado_documento(d_sen, hoxe) == "vixente"


def test_listar_documentos_orde_filtro_e_baixa(session):
    ana, horta, parcela = _escenario(session)

    doc_20 = crear_documento(
        session,
        ana,
        horta.id,
        tipo="autorizacion",
        nome="Doc 20 nov",
        data_caducidade=date(2026, 11, 20),
        que="parcela",
        ref_id=parcela.id,
    )
    doc_10 = crear_documento(
        session,
        ana,
        horta.id,
        tipo="autorizacion",
        nome="Doc 10 nov",
        data_caducidade=date(2026, 11, 10),
        que="parcela",
        ref_id=parcela.id,
    )
    doc_sen_b = crear_documento(
        session,
        ana,
        horta.id,
        tipo="autorizacion",
        nome="Doc Sen Data B",
        data_caducidade=None,
        que="parcela",
        ref_id=parcela.id,
    )
    doc_sen_a = crear_documento(
        session,
        ana,
        horta.id,
        tipo="autorizacion",
        nome="Doc Sen Data A",
        data_caducidade=None,
    )
    doc_baixa = crear_documento(
        session,
        ana,
        horta.id,
        tipo="autorizacion",
        nome="Doc Baixa",
        data_caducidade=date(2026, 11, 5),
    )

    dar_de_baixa_documento(session, ana, doc_baixa)
    assert doc_baixa.baixa is True

    todos = listar_documentos(session, ana, horta.id)
    assert doc_baixa not in todos
    # Orde: caducan antes primeiro, os sen data ao final e despois por nome
    assert todos == [doc_10, doc_20, doc_sen_a, doc_sen_b]

    # Filtro por cousa
    da_parcela = listar_documentos(session, ana, horta.id, que="parcela", ref_id=parcela.id)
    assert da_parcela == [doc_10, doc_20, doc_sen_b]
    assert doc_sen_a not in da_parcela


def test_documentos_con_aviso(session):
    ana, horta, _ = _escenario(session)
    hoxe = date(2026, 11, 8)

    doc_caducado = crear_documento(
        session,
        ana,
        horta.id,
        tipo="inspeccion",
        nome="ITEAF caducada",
        data_caducidade=date(2026, 11, 1),
    )
    doc_pronto = crear_documento(
        session,
        ana,
        horta.id,
        tipo="seguro",
        nome="Seguro a caducar",
        data_caducidade=date(2026, 11, 20),
    )
    doc_vixente = crear_documento(
        session,
        ana,
        horta.id,
        tipo="autorizacion",
        nome="Autorización longa",
        data_caducidade=date(2027, 6, 1),
    )
    doc_sen_data = crear_documento(
        session,
        ana,
        horta.id,
        tipo="contrato",
        nome="Contrato indefinido",
        data_caducidade=None,
    )
    doc_baixa = crear_documento(
        session,
        ana,
        horta.id,
        tipo="inspeccion",
        nome="Inspección antiga dada de baixa",
        data_caducidade=date(2026, 11, 2),
    )
    dar_de_baixa_documento(session, ana, doc_baixa)

    avisos = documentos_con_aviso(session, ana, horta.id, hoxe=hoxe)
    assert avisos == [doc_caducado, doc_pronto]
    assert doc_vixente not in avisos
    assert doc_sen_data not in avisos
    assert doc_baixa not in avisos


def test_actualizar_documento(session):
    ana, horta, parcela = _escenario(session)
    luis = _usuario(session, "luis")
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)

    doc = crear_documento(
        session,
        ana,
        horta.id,
        tipo="seguro",
        nome="Póliza 2026",
        data_emision=date(2026, 1, 1),
        data_caducidade=date(2026, 12, 31),
    )

    actualizar_documento(
        session,
        ana,
        doc,
        nome="Póliza renovada 2026",
        emisor="Mapfre",
        numero="MAP-99",
        data_caducidade=date(2027, 1, 15),
        que="parcela",
        ref_id=parcela.id,
        notas="Ampliación de coberturas",
    )
    assert doc.nome == "Póliza renovada 2026"
    assert doc.emisor == "Mapfre"
    assert doc.numero == "MAP-99"
    assert doc.data_caducidade == date(2027, 1, 15)
    assert doc.que == "parcela"
    assert doc.ref_id == parcela.id
    assert doc.notas == "Ampliación de coberturas"

    # Erro en campo non editable
    with pytest.raises(ValueError):
        actualizar_documento(session, ana, doc, id=999)

    # Erro en tipo descoñecido
    with pytest.raises(ValueError):
        actualizar_documento(session, ana, doc, tipo="desconhecido")

    # Erro en nome baleiro
    with pytest.raises(OperacionNonPermitidaError):
        actualizar_documento(session, ana, doc, nome="   ")

    # Erro en caducidade anterior a emisión
    with pytest.raises(OperacionNonPermitidaError):
        actualizar_documento(session, ana, doc, data_caducidade=date(2025, 1, 1))

    # Lector non pode actualizar
    with pytest.raises(PermisoDenegadoError):
        actualizar_documento(session, luis, doc, nome="Intento")


def test_extension():
    assert extension(PDF_MINIMO) == "pdf"
    assert extension(PNG) == "png"
    assert extension(JPG) == "jpg"
    assert extension(WEBP) == "webp"
    assert extension(b"calquera contido de texto") is None
