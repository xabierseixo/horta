from horta.models.horta import Horta
from horta.models.tarefa import Tarefa


def test_crear_tarefa_con_valores_por_defecto(session):
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.flush()

    tarefa = Tarefa(horta_id=horta.id, descricion="Regar")
    session.add(tarefa)
    session.commit()

    atopada = session.query(Tarefa).filter_by(descricion="Regar").one()
    assert atopada.horta_id == horta.id
    assert atopada.estado == "pendente"
    assert atopada.prioridade == "media"
    assert atopada.parcela_id is None
    assert atopada.cultivo_id is None
    assert atopada.data is None
    assert atopada.data_limite is None
    assert atopada.data_feita is None
