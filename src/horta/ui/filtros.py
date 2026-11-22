from __future__ import annotations


def filtrar_filas(
    filas: list[dict],
    texto: str,
    campos_busca: list[str],
    filtros_estruturados: dict[str, str | None] | None = None,
) -> list[dict]:
    """Filtra unha lista de filas por busca de texto (subcadea, sen distinguir
    maiúsculas/minúsculas) e por criterios estruturados de coincidencia exacta
    (p.ex. {"estado": "activa"}). Unha clave con valor None ou "" en
    filtros_estruturados non filtra por ese campo (sentinela "sen filtro")."""
    texto_normalizado = texto.casefold()
    filtros = {
        campo: valor for campo, valor in (filtros_estruturados or {}).items() if valor
    }

    def coincide(fila: dict) -> bool:
        if texto_normalizado and not any(
            texto_normalizado in str(fila.get(campo, "")).casefold() for campo in campos_busca
        ):
            return False
        return all(str(fila.get(campo)) == valor for campo, valor in filtros.items())

    return [fila for fila in filas if coincide(fila)]
