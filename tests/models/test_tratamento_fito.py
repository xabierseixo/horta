from datetime import date

from horta.models.tratamento_fito import (
    TratamentoCultivo,
    TratamentoFito,
    TratamentoProblema,
    TratamentoProduto,
)
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela


def test_tratamento_con_fillos_e_borrado_en_cascada_dos_fillos(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=1000.0)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    t = TratamentoFito(horta_id=horta.id, data_inicio=date(2026, 5, 1),
                       data_fin=date(2026, 5, 1))
    t.cultivos.append(TratamentoCultivo(cultivo_id=cultivo.id, superficie_ha=0.1))
    t.problemas.append(TratamentoProblema(tipo="enfermidade", codigo="10"))
    t.produtos.append(TratamentoProduto(tipo_produto="1", num_rexistro="ES-00001",
                                        nome_comercial="Cobre", dose=2.0, unidade="5"))
    session.add(t)
    session.commit()
    assert t.baixa is False
    t.produtos.clear()
    session.commit()
    assert session.query(TratamentoProduto).count() == 0
