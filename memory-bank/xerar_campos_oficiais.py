"""Xera docs/campos-oficiais-anexo-v.md: cada campo oficial do Anexo V e onde está en horta.

Uso (dende horta/): uv run python memory-bank/xerar_campos_oficiais.py > docs/campos-oficiais-anexo-v.md
Actualizar o dicionario CUBERTO cando unha tarefa engada campos.
"""
import openpyxl

ANEXO = "/home/xabier/dev/agrogandeiria/fitosanitarios/exploracion/siex/anexoV.xlsx"
CUBERTO: dict[tuple[str, str, int], str] = {}


def ok(folla: str, bloque: str, numeros: list[int], onde: str) -> None:
    for n in numeros:
        CUBERTO[(folla, bloque, n)] = onde


# REA 1 explotación
ok("REA", "1.-", [1], "horta.codigo_reaga (018)")
# REA 9 maquinaria
ok("REA", "9.-", [1], "maquina.num_roma (fase 1)")
# REA 12 superficies: DGC = parcela
ok("REA", "12.", [2, 3, 6, 7], "parcela.sigpac_*")
ok("REA", "12.", [1], "parcela.referencia_catastral (037)")
ok("REA", "12.", [4], "parcela.sigpac_agregado (037)")
ok("REA", "12.", [5], "parcela.sigpac_zona (037)")
ok("REA", "12.", [13], "parcela.rexime_tenencia (037)")
ok("REA", "12.", [14], "parcela.nif_arrendador (037)")
ok("REA", "12.", [16], "parcela.pequena_superficie (037)")
ok("REA", "12.", [19], "parcela.data_alta (037)")
ok("REA", "12.", [20], "parcela.data_baixa (037)")
ok("REA", "12.", [21], "parcela.causa_baixa (037)")
# REA 2 titular = persoa con e_titular (035); falta enderezo e tipo de agricultor/titular
ok("REA", "2.-", [1], "persoa.nif (e_titular, 035)")
ok("REA", "2.-", [2], "persoa.nome (e_titular, 035)")
ok("REA", "2.-", [3, 4], "persoa.apelidos (un só campo; separar ao exportar)")
ok("REA", "2.-", [5], "persoa.xenero (035)")
ok("REA", "2.-", [6], "persoa.data_nacemento (035)")
ok("REA", "2.-", [12], "persoa.telefono (035)")
ok("REA", "2.-", [13], "persoa.email (035)")
ok("REA", "12.", [8], "parcela.sigpac_subparcela (= recinto?) — revisar")
ok("REA", "12.", [15], "parcela.superficie (ha, 027)")
ok("REA", "12.", [18], "parcela.geometria (sen UI)")
ok("REA", "12.", [22], "cultivo.cultivo_siex_codigo")
ok("REA", "12.", [23], "cultivo.variedade_siex_id / variedade")
ok("REA", "12.", [24], "cultivo.actividade_agraria (029, por defecto 1 en 034)")
ok("REA", "12.", [25], "cultivo.data_inicio (029)")
ok("REA", "12.", [26, 32], "cultivo.data_fin (029)")
ok("REA", "12.", [27], "cultivo.sistema_explotacion (029)")
ok("REA", "12.", [31], "cultivo.causa_baixa (029)")
ok("REA", "12.", [34, 35], "cultivo.tipo_mvr / detalle_mvr (029; falta importar o catálogo composto)")
ok("REA", "12.", [36], "cultivo.empresa_semente (029; falta catálogo EMP_PRODUCTORA)")
ok("REA", "12.", [37], "cultivo.ropveg (029)")
ok("REA", "12.", [38], "cultivo.procedencia_material (029)")
ok("REA", "12.", [39], "cultivo.lote_material (029)")
ok("REA", "12.", [40], "cultivo.pasaporte_fitosanitario (029)")
ok("REA", "12.", [41], "cultivo.certificacion_ecoloxica (029)")
ok("REA", "12.", [42], "cultivo.producion_integrada (029)")
ok("REA", "12.", [43], "cultivo.destino (029)")
ok("REA", "12.", [44], "cultivo.sistema_cultivo (029)")
ok("REA", "12.", [45], "cultivo.sementeira_directa (029)")
ok("REA", "12.", [46], "cultivo.tipo_cobertura_solo (029)")
ok("REA", "12.", [47], "cultivo.num_arbores (029)")
ok("REA", "12.", [48], "cultivo.marco_plantacion (029)")
ok("REA", "12.", [49], "cultivo.num_castineiros/abeleiras/nogueiras/amendoeiras/outros (029)")
ok("REA", "12.", [50], "cultivo.ano_plantacion (029)")
ok("REA", "12.", [52], "cultivo.unidades_produtivas (029)")
ok("REA", "12.", [57], "cultivo.ciclos_ano × duracion_ciclo_dias (029) — revisar")
ok("REA", "12.", [62], "cultivo.variedade_siex_id")
ok("REA", "12.", [63], "parcela.uso_aproveitamento (texto; debería ser catálogo APROVECHAMIENTO)")
# CUE 6 sementeira/plantación = datos de sementeira do cultivo
ok("CUE", "6.-", [1], "cultivo.data_inicio (029)")
ok("CUE", "6.-", [2], "cultivo.data_fin_sementeira (029)")
ok("CUE", "6.-", [3], "cultivo.cultivo_siex_codigo")
ok("CUE", "6.-", [4], "cultivo.cantidade_semente_kg (029)")
ok("CUE", "6.-", [5], "cultivo.dose_sementeira_kg_ha (029)")
ok("CUE", "6.-", [7], "cultivo.material_tratado (029)")
ok("CUE", "6.-", [8], "cultivo.material_adquirido (029)")
ok("CUE", "6.-", [9], "cultivo.data_adquisicion_material (029)")
ok("CUE", "6.-", [10], "cultivo.lote_material (029)")
ok("CUE", "6.-", [11], "cultivo.superficie_ha (029)")
ok("CUE", "6.-", [12], "cultivo.sementeira_directa (029)")
ok("CUE", "6.-", [14], "cultivo.densidade_plantas_ha (029)")
ok("CUE", "6.-", [15], "cultivo.marco_plantacion (029)")
# CUE 8 tratamentos (fase 1): revisión campo a campo pendente
for n in range(1, 56):
    CUBERTO[("CUE", "8.-", n)] = "tratamento_fito e fillos (fase 1) — revisar campo a campo"
# CUE 11 colleita
ok("CUE", "11.-", [1], "colleita.data (029)")
ok("CUE", "11.-", [2], "colleita.data_fin (029)")
ok("CUE", "11.-", [3], "cultivo.cultivo_siex_codigo")
ok("CUE", "11.-", [4], "colleita.superficie_ha (029; por defecto a do cultivo)")
ok("CUE", "11.-", [5], "colleita.cantidade (029)")
ok("CUE", "11.-", [6], "colleita.unidade (029; traducir a UNIDADES_MEDIDA ao exportar)")
ok("CUE", "11.-", [7], "colleita.destino_colleita (DEST_COSECHA; só destino 22/23)")
ok("CUE", "11.-", [8], "colleita.destino_restos (029)")
ok("CUE", "11.-", [9], "colleita.obten_sementes (029)")
ok("CUE", "11.-", [10], "colleita.obten_plantas (029)")
ok("CUE", "11.-", [11], "colleita.sen_colleita_ambiental (029)")
ok("CUE", "11.-", [12], "colleita.restos_no_solo (029)")
ok("CUE", "11.-", [13, 14, 15, 16], "colleita.maquina_id → maquina (029; sen UI)")
ok("CUE", "11.-", [17], "colleita.num_repeticions (029; sen UI)")
ok("CUE", "11.-", [18], "colleita.duracion_h_ha (029; sen UI)")

wb = openpyxl.load_workbook(ANEXO)
print("# Campos oficiais (Anexo V SIEX) e onde están en horta\n")
print("Xerado con `memory-bank/xerar_campos_oficiais.py` dende o Anexo V oficial. **Fonte de "
      "verdade** para os campos (o código non o é, decisión do usuario 2026-10-23). Entre "
      "parénteses, a tarefa que o engade. **FALTA** = non está nin previsto.\n")
for folla in ("REA", "CUE"):
    print(f"## {folla}")
    bloque = None
    totais: dict[str, list[int]] = {}
    for r in list(wb[folla].iter_rows(values_only=True))[1:]:
        if not r or not r[2]:
            continue
        b = str(r[2]).strip()
        if b != bloque:
            bloque = b
            print(f"\n### {b}\n\n| Nº | Campo | Obrig. | En horta |\n|---|---|---|---|")
        clave = next((k for k in CUBERTO if k[0] == folla and b.startswith(k[1]) and k[2] == r[4]),
                     None)
        onde = CUBERTO[clave] if clave else "**FALTA**"
        ob = "si" if str(r[7]).startswith("Obligatorio") else "non"
        t = totais.setdefault(b, [0, 0, 0])
        t[0] += 1
        t[1] += ob == "si"
        t[2] += ob == "si" and onde == "**FALTA**"
        print(f"| {r[4] or ''} | {str(r[5]).strip().replace('|', '/')} | {ob} | {onde} |")
    print(f"\n### Resumo {folla}\n\n| Bloque | Campos | Obrigatorios | Obrigatorios que FALTAN |\n|---|---|---|---|")
    for b, (n, o, f) in totais.items():
        print(f"| {b} | {n} | {o} | {f} |")
    print()
