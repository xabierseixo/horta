"""Probas do servizo de necesidades de rega (FAO-56)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from horta.models.cultivo import Cultivo
from horta.models.rega import Rega, RegaCultivo
from horta.models.tempo import EstacionMeteo, TempoDia
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta
from horta.services.necesidades_rega import (
    CoeficienteCultivo,
    auga_regada_mm,
    choiva_efectiva,
    coeficientes,
    kc_do_dia,
    necesidade_rega,
    necesidades_horta,
)
from horta.services.parcelas import crear_parcela


class FonteProba:
    """Fonte meteorolóxica de proba que non chame á rede."""

    def estacions(self):
        return []

    def dias(self, estacion_id, desde, ata):
        return []

    def predicion(self, concello_ine):
        return []

    def avisos(self, concello_ine):
        return []


@pytest.fixture(autouse=True)
def _cultivos_siex(session):
    """Os códigos do catálogo de cultivos que usan as probas (a táboa ten clave allea)."""
    from horta.models.catalogo import CatalogoVersion, CultivoSiex

    v = CatalogoVersion(catalogo="cultivo", nome_ficheiro="x", sha256="e" * 64, filas=5)
    session.add(v)
    session.flush()
    for codigo in (152, 155, 157, 197, 999999):
        session.add(CultivoSiex(codigo=codigo, nome_oficial=f"CULTIVO {codigo}", version_id=v.id))
    session.commit()


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


def _escenario(session):
    estacion = EstacionMeteo(
        id=10045,
        nome="Mabegondo",
        concello="Abegondo",
        lat=43.25,
        lon=-8.30,
        altitude=100.0,
    )
    session.add(estacion)
    session.flush()

    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta de Proba")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte", superficie=0.5)
    parcela.estacion_meteo_id = estacion.id
    session.commit()

    return ana, horta, parcela, estacion


def test_kc_do_dia():
    coef = CoeficienteCultivo(
        codigo_siex=197,
        nome="Tomate",
        cultivo_fao56="Tomato",
        kc_ini=0.6,
        kc_mid=1.15,
        kc_end=0.80,
        l_ini=30,
        l_dev=40,
        l_mid=45,
        l_late=30,
        nota="",
    )
    # Días negativos
    assert kc_do_dia(coef, -5) == 0.6
    # Inicio (dias < l_ini)
    assert kc_do_dia(coef, 0) == 0.6
    assert kc_do_dia(coef, 29) == 0.6
    # Metade do desenvolvemento: l_ini + l_dev / 2 = 30 + 20 = 50
    # kc_ini + (kc_mid - kc_ini) * 0.5 = 0.6 + 0.55 * 0.5 = 0.875
    assert kc_do_dia(coef, 50) == 0.875
    # Media: fin_dev = 70, fin_mid = 115
    assert kc_do_dia(coef, 70) == 1.15
    assert kc_do_dia(coef, 90) == 1.15
    # Metade da fase final: fin_mid + l_late / 2 = 115 + 15 = 130
    # kc_mid + (kc_end - kc_mid) * 0.5 = 1.15 + (0.80 - 1.15) * 0.5 = 0.975
    assert kc_do_dia(coef, 130) == 0.975
    # Despois do ciclo: fin_late = 145
    assert kc_do_dia(coef, 145) == 0.80
    assert kc_do_dia(coef, 200) == 0.80

    # Sen fases (sen l_*): devolve kc_mid
    coef_sen_fases = CoeficienteCultivo(
        codigo_siex=169,
        nome="Allo",
        cultivo_fao56="Garlic",
        kc_ini=0.7,
        kc_mid=1.00,
        kc_end=0.70,
        l_ini=None,
        l_dev=None,
        l_mid=None,
        l_late=None,
        nota="",
    )
    assert kc_do_dia(coef_sen_fases, 0) == 1.00
    assert kc_do_dia(coef_sen_fases, 50) == 1.00
    assert kc_do_dia(coef_sen_fases, 150) == 1.00


def test_coeficientes():
    todos = coeficientes()
    assert 197 in todos
    tomate = todos[197]
    assert tomate.nome == "Tomate"
    assert tomate.kc_mid == 1.15
    assert (tomate.l_ini, tomate.l_dev, tomate.l_mid, tomate.l_late) == (30, 40, 45, 30)


def test_choiva_efectiva():
    assert choiva_efectiva(None) == 0.0
    assert choiva_efectiva(0.0) == 0.0
    assert choiva_efectiva(-2.0) == 0.0
    assert choiva_efectiva(10.0) == 8.0
    assert choiva_efectiva(25.0) == 20.0


def test_auga_regada_mm_litros(session):
    ana, horta, parcela, _ = _escenario(session)
    cultivo = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        superficie_ha=0.01,
    )
    session.add(cultivo)
    session.commit()

    desde = date(2026, 7, 1)
    ata = date(2026, 7, 7)

    # Unha rega de 1000 L en 0,01 ha (100 m²) dá 10 l/m²
    r1 = Rega(
        horta_id=horta.id,
        data_inicio=date(2026, 7, 3),
        data_fin=date(2026, 7, 3),
        cantidade=1000.0,
        unidade="4",
        baixa=False,
        creado_por=ana.id,
    )
    r1.leiras = [RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.01)]
    session.add(r1)
    session.commit()

    assert auga_regada_mm(session, cultivo, desde, ata) == 10.0


def test_auga_regada_mm_en_m3(session):
    ana, horta, parcela, _ = _escenario(session)
    cultivo = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        superficie_ha=0.01,
    )
    session.add(cultivo)
    session.commit()

    desde = date(2026, 7, 1)
    ata = date(2026, 7, 7)

    # 1 m³ son 1000 L, en 0,01 ha dá 10 l/m²
    r1 = Rega(
        horta_id=horta.id,
        data_inicio=date(2026, 7, 3),
        data_fin=date(2026, 7, 3),
        cantidade=1.0,
        unidade="3",
        baixa=False,
        creado_por=ana.id,
    )
    r1.leiras = [RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.01)]
    session.add(r1)
    session.commit()

    assert auga_regada_mm(session, cultivo, desde, ata) == 10.0


def test_auga_regada_mm_repartida_duas_leiras(session):
    ana, horta, parcela, _ = _escenario(session)
    c1 = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        superficie_ha=0.01,
    )
    c2 = Cultivo(
        parcela_id=parcela.id,
        especie="Pemento",
        cultivo_siex_codigo=152,
        superficie_ha=0.01,
    )
    session.add_all([c1, c2])
    session.commit()

    desde = date(2026, 7, 1)
    ata = date(2026, 7, 7)

    # 1000 L repartida entre dúas leiras de 0,01 ha (suma 0,02 ha = 200 m²): 1000 / 200 = 5 l/m²
    r = Rega(
        horta_id=horta.id,
        data_inicio=date(2026, 7, 3),
        data_fin=date(2026, 7, 3),
        cantidade=1000.0,
        unidade="4",
        baixa=False,
        creado_por=ana.id,
    )
    r.leiras = [
        RegaCultivo(cultivo_id=c1.id, superficie_ha=0.01),
        RegaCultivo(cultivo_id=c2.id, superficie_ha=0.01),
    ]
    session.add(r)
    session.commit()

    assert auga_regada_mm(session, c1, desde, ata) == 5.0
    assert auga_regada_mm(session, c2, desde, ata) == 5.0


def test_auga_regada_mm_sen_superficie_non_conta(session):
    ana, horta, parcela, _ = _escenario(session)
    cultivo = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        superficie_ha=None,
    )
    session.add(cultivo)
    session.commit()

    desde = date(2026, 7, 1)
    ata = date(2026, 7, 7)

    # Rega sen superficie na leira nin no cultivo
    r = Rega(
        horta_id=horta.id,
        data_inicio=date(2026, 7, 3),
        data_fin=date(2026, 7, 3),
        cantidade=1000.0,
        unidade="4",
        baixa=False,
        creado_por=ana.id,
    )
    r.leiras = [RegaCultivo(cultivo_id=cultivo.id, superficie_ha=None)]
    session.add(r)
    session.commit()

    assert auga_regada_mm(session, cultivo, desde, ata) == 0.0


def test_auga_regada_mm_baixa_e_datas(session):
    ana, horta, parcela, _ = _escenario(session)
    cultivo = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        superficie_ha=0.01,
    )
    session.add(cultivo)
    session.commit()

    desde = date(2026, 7, 1)
    ata = date(2026, 7, 7)

    # Rega de baixa
    r_baixa = Rega(
        horta_id=horta.id,
        data_inicio=date(2026, 7, 3),
        data_fin=date(2026, 7, 3),
        cantidade=1000.0,
        unidade="4",
        baixa=True,
        creado_por=ana.id,
    )
    r_baixa.leiras = [RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.01)]

    # Rega fóra de datas
    r_fora = Rega(
        horta_id=horta.id,
        data_inicio=date(2026, 6, 25),
        data_fin=date(2026, 6, 25),
        cantidade=1000.0,
        unidade="4",
        baixa=False,
        creado_por=ana.id,
    )
    r_fora.leiras = [RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.01)]

    # Rega sen cantidade
    r_sen = Rega(
        horta_id=horta.id,
        data_inicio=date(2026, 7, 4),
        data_fin=date(2026, 7, 4),
        cantidade=None,
        unidade="4",
        baixa=False,
        creado_por=ana.id,
    )
    r_sen.leiras = [RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.01)]

    session.add_all([r_baixa, r_fora, r_sen])
    session.commit()

    assert auga_regada_mm(session, cultivo, desde, ata) == 0.0


def test_necesidade_rega_calculo_completo(session):
    ana, horta, parcela, estacion = _escenario(session)
    cultivo = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        data_inicio=date(2026, 7, 1),
        superficie_ha=0.01,
    )
    session.add(cultivo)
    session.commit()

    # Hoxe é 2026-07-08; período de 7 días: 2026-07-01 a 2026-07-07
    hoxe = date(2026, 7, 8)
    desde = date(2026, 7, 1)

    # Gardamos TempoDia para cada un dos 7 días.
    # Tomate ten kc_ini = 0.6 durante os primeiros 30 días.
    # Para os 7 días (días 0 a 6 dende inicio), kc_do_dia é sempre 0.6.
    # Cada día ten et0 = 5.0 mm -> ETc diaria = 0.6 * 5.0 = 3.0 mm.
    # ETc total dos 7 días = 7 * 3.0 = 21.0 mm.
    # O día 2026-07-02 chove 10.0 mm -> choiva efectiva = 8.0 mm (o resto 0 mm).
    for n in range(7):
        dia = desde + timedelta(days=n)
        choiva = 10.0 if dia == date(2026, 7, 2) else 0.0
        session.add(
            TempoDia(
                estacion_id=estacion.id,
                data=dia,
                et0=5.0,
                choiva=choiva,
                fonte="MeteoGalicia",
            )
        )

    # Engadimos unha rega o 2026-07-04 de 500 L en 0,01 ha (100 m²): 5.0 mm
    rega = Rega(
        horta_id=horta.id,
        data_inicio=date(2026, 7, 4),
        data_fin=date(2026, 7, 4),
        cantidade=500.0,
        unidade="4",
        baixa=False,
        creado_por=ana.id,
    )
    rega.leiras = [RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.01)]
    session.add(rega)
    session.commit()

    fonte = FonteProba()
    resultado = necesidade_rega(
        session,
        ana,
        cultivo.id,
        dias=7,
        hoxe=hoxe,
        fonte=fonte,
    )

    assert resultado.cultivo_id == cultivo.id
    assert resultado.estado == "ok"
    assert resultado.etc_mm == 21.0
    assert resultado.choiva_efectiva_mm == 8.0
    assert resultado.rega_mm == 5.0
    # falta_mm = max(0, 21.0 - 8.0 - 5.0) = 8.0
    assert resultado.falta_mm == 8.0
    # kc_actual é o Kc de onte (2026-07-07, día 6 desde sementeira -> 0.6)
    assert resultado.kc_actual == 0.6
    assert resultado.aproximado is False
    assert resultado.dias_con_datos == 7


def test_necesidade_rega_casos_especiais(session):
    ana, horta, parcela, estacion = _escenario(session)
    hoxe = date(2026, 7, 8)
    fonte = FonteProba()

    # 1. Secano
    c_secano = Cultivo(
        parcela_id=parcela.id,
        especie="Centeo",
        sistema_explotacion="S",
        cultivo_siex_codigo=197,
        data_inicio=date(2026, 7, 1),
    )
    session.add(c_secano)
    session.commit()
    res_secano = necesidade_rega(session, ana, c_secano.id, hoxe=hoxe, fonte=fonte)
    assert res_secano.estado == "secano"
    assert res_secano.falta_mm == 0.0

    # 2. Sen coeficiente
    c_sen_coef = Cultivo(
        parcela_id=parcela.id,
        especie="Descoñecido",
        cultivo_siex_codigo=999999,
        data_inicio=date(2026, 7, 1),
    )
    session.add(c_sen_coef)
    session.commit()
    res_sen_coef = necesidade_rega(session, ana, c_sen_coef.id, hoxe=hoxe, fonte=fonte)
    assert res_sen_coef.estado == "sen_coeficiente"

    # 3. Sen data de inicio
    c_sen_data = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        data_inicio=None,
    )
    session.add(c_sen_data)
    session.commit()
    res_sen_data = necesidade_rega(session, ana, c_sen_data.id, hoxe=hoxe, fonte=fonte)
    assert res_sen_data.estado == "sen_data_inicio"

    # 4. Sen estación na parcela
    p_sen_est = crear_parcela(session, ana, horta.id, "Parcela Sen Estación")
    c_sen_est = Cultivo(
        parcela_id=p_sen_est.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        data_inicio=date(2026, 7, 1),
    )
    session.add(c_sen_est)
    session.commit()
    res_sen_est = necesidade_rega(session, ana, c_sen_est.id, hoxe=hoxe, fonte=fonte)
    assert res_sen_est.estado == "sen_estacion"

    # 4 bis. Sen estación na parcela pero si na explotación: úsase a da explotación
    horta.estacion_meteo_id = estacion.id
    session.commit()
    res_horta = necesidade_rega(session, ana, c_sen_est.id, hoxe=hoxe, fonte=fonte)
    assert res_horta.estado != "sen_estacion"
    horta.estacion_meteo_id = None
    session.commit()

    # 5. Sen datos meteorolóxicos
    c_sen_datos = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        data_inicio=date(2026, 7, 1),
    )
    session.add(c_sen_datos)
    session.commit()
    res_sen_datos = necesidade_rega(
        session, ana, c_sen_datos.id, hoxe=date(2025, 1, 15), fonte=fonte
    )
    assert res_sen_datos.estado == "sen_datos"
    assert res_sen_datos.dias_con_datos == 0


def test_necesidade_rega_sen_permiso_falla(session):
    ana, horta, parcela, estacion = _escenario(session)
    cultivo = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        data_inicio=date(2026, 7, 1),
    )
    session.add(cultivo)
    session.commit()

    outro = _crear_usuario(session, "outro@example.com")
    with pytest.raises(PermisoDenegadoError):
        necesidade_rega(session, outro, cultivo.id)


def test_necesidades_horta(session):
    ana, horta, parcela, estacion = _escenario(session)
    hoxe = date(2026, 7, 8)
    desde = date(2026, 7, 1)

    for n in range(7):
        session.add(
            TempoDia(
                estacion_id=estacion.id,
                data=desde + timedelta(days=n),
                et0=5.0,
                choiva=0.0,
                fonte="MeteoGalicia",
            )
        )

    # Cultivo 1: Tomate (ok, falta auga)
    c1 = Cultivo(
        parcela_id=parcela.id,
        especie="Tomate",
        cultivo_siex_codigo=197,
        data_inicio=date(2026, 7, 1),
        superficie_ha=0.01,
    )
    # Cultivo 2: Leituga (ok, falta máis auga porque kc_ini = 0.7 > 0.6)
    c2 = Cultivo(
        parcela_id=parcela.id,
        especie="Leituga",
        cultivo_siex_codigo=155,
        data_inicio=date(2026, 7, 1),
        superficie_ha=0.01,
    )
    # Cultivo 3: Secano (estado="secano")
    c3 = Cultivo(
        parcela_id=parcela.id,
        especie="Centeo",
        sistema_explotacion="S",
        cultivo_siex_codigo=197,
        data_inicio=date(2026, 7, 1),
    )
    # Cultivo 4: Rematado (con data_fin -> non debe aparecer)
    c4 = Cultivo(
        parcela_id=parcela.id,
        especie="Cebola",
        cultivo_siex_codigo=157,
        data_inicio=date(2026, 5, 1),
        data_fin=date(2026, 7, 1),
    )
    session.add_all([c1, c2, c3, c4])
    session.commit()

    fonte = FonteProba()
    resultados = necesidades_horta(
        session, ana, horta.id, dias=7, hoxe=hoxe, fonte=fonte
    )

    ids_retornados = [r.cultivo_id for r in resultados]
    assert c4.id not in ids_retornados
    assert set(ids_retornados) == {c1.id, c2.id, c3.id}

    # Os "ok" van primeiro, ordenados por falta_mm de maior a menor
    # Leituga (c2): 7 * (0.7 * 5.0) = 24.5 mm
    # Tomate (c1): 7 * (0.6 * 5.0) = 21.0 mm
    # Secano (c3): falta_mm = 0.0, estado = "secano"
    assert resultados[0].cultivo_id == c2.id
    assert resultados[0].estado == "ok"
    assert resultados[0].falta_mm == 24.5

    assert resultados[1].cultivo_id == c1.id
    assert resultados[1].estado == "ok"
    assert resultados[1].falta_mm == 21.0

    assert resultados[2].cultivo_id == c3.id
    assert resultados[2].estado == "secano"

    # Sen permiso
    outro = _crear_usuario(session, "sen_rol@example.com")
    with pytest.raises(PermisoDenegadoError):
        necesidades_horta(session, outro, horta.id)
