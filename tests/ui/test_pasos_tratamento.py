"""Y3: o tratamento di todo o que falta en cada paso; Y4: dose da etiqueta en %."""

from horta.ui.pasos_tratamento import (
    cantidade_dende_porcentaxe,
    faltan_con_que,
    faltan_por_que,
    faltan_que_e_onde,
    faltan_quen,
)


def _produto(**campos):
    fila = {"nome": "Cobre", "num": "ES-1", "materia": "", "dose": "2", "unidade": "17",
            "total": False, "tipo_produto": "1"}
    fila.update(campos)
    return fila


def test_paso_1_di_as_dúas_cousas_xuntas():
    assert faltan_que_e_onde("", "", [{"cultivo_id": None}]) == [
        "as datas de inicio e fin", "polo menos un cultivo tratado"]
    assert faltan_que_e_onde("2026-05-01", "2026-05-01", [{"cultivo_id": 3}]) == []


def test_paso_2():
    assert len(faltan_por_que([{"codigo": None}], [])) == 2
    assert faltan_por_que([{"codigo": "7"}], ["1"]) == []


def test_paso_3_sen_nada():
    assert faltan_con_que([_produto(nome="", num="")], [{"tipo": None}]) == [
        "polo menos un produto ou unha medida non química"]


def test_paso_3_unha_medida_vale():
    assert faltan_con_que([], [{"tipo": "3"}]) == []


def test_paso_3_todo_o_que_falta_do_produto():
    faltan = faltan_con_que([_produto(dose="", unidade=None, num="", nome="Cobre")], [])
    assert faltan == ["a dose de Cobre", "a unidade de Cobre", "o nº de rexistro de Cobre"]


def test_paso_3_total_ou_por_hectarea():
    assert faltan_con_que([_produto(total=True, unidade="17")], []) == [
        "a cantidade total de Cobre en kg ou L"]
    assert faltan_con_que([_produto(unidade="4")], []) == [
        "a dose de Cobre en kg/ha ou L/ha (ou marca que é o total)"]
    assert faltan_con_que([_produto(total=True, unidade="4")], []) == []


def test_paso_4():
    assert faltan_quen(None) == ["quen aplicou o tratamento"]
    assert faltan_quen(5) == []


def test_dose_en_porcentaxe():
    assert cantidade_dende_porcentaxe(0.5, 16) == 0.08


def test_ordenar_problemas():
    """Primeiro os do cultivo; sen nomes repetidos, agás o escollido (Y5)."""
    from horta.ui.pasos_tratamento import ordenar_problemas

    opcions = {"1": "Fungi", "2": "Fungi", "3": "Fungi", "7": "Albugo spp.", "8": "Mildiu"}
    assert list(ordenar_problemas(opcions, {"8"}, None)) == ["8", "1", "7"]
    assert list(ordenar_problemas(opcions, set(), "3")) == ["1", "3", "7", "8"]
