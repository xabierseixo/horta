"""Aviso do prazo de seguridade ao colleitar (Y1): sempre o tratamento que remata máis tarde."""

from datetime import date

from test_fito_consulta import _escenario

from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoProduto
from horta.services.fito_consulta import aviso_prazo_colleita


def _tratamento(session, horta, cultivo, dia):
    t = TratamentoFito(horta_id=horta.id, data_inicio=dia, data_fin=dia)
    t.cultivos = [TratamentoCultivo(cultivo_id=cultivo.id)]
    t.produtos = [TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-1",
                                    nome_comercial="MILDIUCIDA")]
    session.add(t)


def test_avisa_co_prazo_que_remata_mais_tarde(session):
    horta, cultivo = _escenario(session)
    _tratamento(session, horta, cultivo, date(2026, 5, 25))  # prazo ata o 08/06
    _tratamento(session, horta, cultivo, date(2026, 6, 1))   # prazo ata o 15/06
    session.commit()

    aviso = aviso_prazo_colleita(session, cultivo.id, date(2026, 6, 5))

    assert aviso and "15/06/2026" in aviso and "01/06/2026" in aviso
