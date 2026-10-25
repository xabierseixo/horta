from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.tratamento_fito import (
    TratamentoAsesor,
    TratamentoCultivo,
    TratamentoFito,
    TratamentoProduto,
)
from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_persoa


def _filas(session, ana, horta):
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    return [[x for x in f if x not in (None, "")]
            for f in libro["3 Tratamentos"].iter_rows(values_only=True)]


def test_asesorados_e_semente_tratada(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2, data_inicio=date(2026, 3, 1),
                       material_tratado=True, cantidade_semente_kg=50,
                       semente_tratamento_produto="Monceren", semente_tratamento_num_rexistro="123")
    asesora = crear_persoa(session, ana, horta.id, "Lúa", e_asesor=True, ropo_numero="R-9")
    t = TratamentoFito(horta_id=horta.id, data_inicio=date(2026, 5, 2),
                       data_fin=date(2026, 5, 2))
    t.cultivos = [TratamentoCultivo(cultivo_id=cultivo.id, superficie_ha=0.2)]
    t.produtos = [TratamentoProduto(tipo_produto="1", nome_comercial="Cobre 50",
                                    num_rexistro="ES-1", dose=2, unidade="5")]
    t.asesor = TratamentoAsesor(persoa_id=asesora.id, data=date(2026, 5, 1))
    session.add(t)
    session.commit()

    filas = _filas(session, ana, horta)
    i = next(n for n, f in enumerate(filas) if f and str(f[0]).startswith("3.1 bis"))
    assert filas[i + 2][:3] == ["Pataca", 1, 0.2]
    assert "Cobre 50" in filas[i + 2] and "Lúa" in filas[i + 2] and "R-9" in filas[i + 2]
    j = next(n for n, f in enumerate(filas) if f == ["3.2 REXISTRO DE USO DE SEMENTE TRATADA"])
    assert filas[j + 1] == ["Aplica tratamento", "SI"]
    assert filas[j + 3] == ["01/03/2026", 1, "Pataca", 0.2, 50, "Monceren", "123"]
