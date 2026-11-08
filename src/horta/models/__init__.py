from horta.models.abonado import Abonado, AbonadoBoaPractica, AbonadoCultivo, Fertilizante
from horta.models.analise import Analise, AnaliseSubstancia, AnaliseTipo
from horta.models.animal import Animal, AnimalIdentificado
from horta.models.cartos import ApunteCartos
from horta.models.catalogo import (
    CatalogoValor,
    CatalogoVersion,
    CultivoSiex,
    NomeGalego,
    VariedadeLocal,
    VariedadeSiex,
)
from horta.models.categoria import Categoria
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.colleita import Colleita
from horta.models.comprobacion_catalogo import ComprobacionCatalogo
from horta.models.convite import Convite
from horta.models.cultivo import Cultivo
from horta.models.documento import Documento
from horta.models.envio_cue import EnvioCue, RexistroCue
from horta.models.fertilizante import FertilizanteSiex
from horta.models.fito_rexistro import (
    FitoMateria,
    FitoPonteAxente,
    FitoPonteCultivo,
    FitoProduto,
    FitoUso,
)
from horta.models.foto import Foto
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.instalacion import Instalacion
from horta.models.labor import Labor, LaborCultivo
from horta.models.legal import ConfiguracionLegal
from horta.models.lote import (
    Clasificacion,
    ClasificacionClase,
    Lote,
    LoteSaida,
    Mestura,
    MesturaOrixe,
    ProdutoVenda,
    Transformacion,
    TransformacionEntrada,
    TransformacionInsumo,
)
from horta.models.maquina import Maquina
from horta.models.movemento_animal import MovementoAnimal
from horta.models.observacion import LimiarPraga, ObservacionPraga
from horta.models.outro_traballo import OutroTraballo
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.pastoreo import Pastoreo, PastoreoAnimal, PastoreoLeira
from horta.models.persoa import Persoa, PersoaPapel, TipoCarne
from horta.models.plan_empresa import (
    PlanAno,
    PlanEmpresa,
    PlanFinanciamento,
    PlanInvestimento,
    PlanOferta,
)
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import EntradaProduto, Produto
from horta.models.recomendacion import Recomendacion
from horta.models.rega import Rega, RegaBoaPractica, RegaCultivo
from horta.models.tarefa import Tarefa
from horta.models.tempo import EstacionMeteo, TempoDia
from horta.models.tratamento_fito import (
    TratamentoAplicador,
    TratamentoAsesor,
    TratamentoCultivo,
    TratamentoFito,
    TratamentoMedida,
    TratamentoProblema,
    TratamentoProduto,
    TratamentoXustificacion,
)
from horta.models.tratamento_instalacion import TratamentoInstalacion
from horta.models.usuario import RolGlobal, Usuario
from horta.models.zona import ParcelaZona

__all__ = [
    "EnvioCue",
    "RexistroCue",
    "RolGlobal",
    "Usuario",
    "Horta",
    "HortaMembro",
    "RolHorta",
    "Parcela",
    "SecanoRegadio",
    "Animal",
    "CoidadoAnimal",
    "MovementoAnimal",
    "ProducionAnimal",
    "Produto",
    "Pastoreo",
    "PastoreoLeira",
    "PastoreoAnimal",
    "Cultivo",
    "Tarefa",
    "Colleita",
    "CatalogoVersion",
    "ComprobacionCatalogo",
    "CatalogoValor",
    "CultivoSiex",
    "VariedadeSiex",
    "FertilizanteSiex",
    "FitoProduto",
    "FitoMateria",
    "FitoUso",
    "FitoPonteCultivo",
    "FitoPonteAxente",
    "Fertilizante",
    "Abonado",
    "AbonadoCultivo",
    "AbonadoBoaPractica",
    "Rega",
    "RegaCultivo",
    "Labor",
    "LaborCultivo",
    "RegaBoaPractica",
    "Analise",
    "AnaliseTipo",
    "AnaliseSubstancia",
    "TratamentoInstalacion",
    "NomeGalego",
    "VariedadeLocal",
    "EntradaProduto",
    "Persoa",
    "PersoaPapel",
    "TipoCarne",
    "Lote",
    "LoteSaida",
    "ProdutoVenda",
    "Clasificacion",
    "ClasificacionClase",
    "Mestura",
    "MesturaOrixe",
    "Transformacion",
    "TransformacionEntrada",
    "TransformacionInsumo",
    "OutroTraballo",
    "Convite",
    "ApunteCartos",
    "Categoria",
    "ParcelaZona",
    "PlanEmpresa",
    "PlanInvestimento",
    "PlanOferta",
    "PlanFinanciamento",
    "PlanAno",
    "AnimalIdentificado",
    "Instalacion",
    "Foto",
    "EstacionMeteo",
    "TempoDia",
    "Maquina",
    "TratamentoFito",
    "TratamentoCultivo",
    "TratamentoProblema",
    "TratamentoXustificacion",
    "TratamentoProduto",
    "TratamentoMedida",
    "TratamentoAplicador",
    "TratamentoAsesor",
    "ConfiguracionLegal",
    "Documento",
    "Recomendacion",
    "LimiarPraga",
    "ObservacionPraga",
]
