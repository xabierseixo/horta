from datetime import date

import horta.models  # noqa: F401
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoMedida
from horta.services.tratamentos_fito import cabe_no_formulario


def _tratamento() -> TratamentoFito:
    return TratamentoFito(horta_id=1, data_inicio=date(2026, 5, 1), data_fin=date(2026, 5, 1))


def test_un_cultivo_cabe_no_formulario():
    t = _tratamento()
    t.cultivos = [TratamentoCultivo(cultivo_id=1)]
    assert cabe_no_formulario(t)


def test_dous_cultivos_non_caben():
    t = _tratamento()
    t.cultivos = [TratamentoCultivo(cultivo_id=1), TratamentoCultivo(cultivo_id=2)]
    assert not cabe_no_formulario(t)


def test_con_medidas_non_cabe():
    t = _tratamento()
    t.medidas = [TratamentoMedida(tipo_medida="1")]
    assert not cabe_no_formulario(t)
