"""Tema visual «Caderno de campo» (ver o deseño).

As cores e os compoñentes defínense unha soa vez aquí, como variables e clases
CSS; as páxinas só usan os nomes das clases (`tarxeta`, `cifra`, `etiqueta-ok`...).
"""

from __future__ import annotations

from nicegui import ui

COR_PRIMARIA = "#2F7D4F"
COR_PRIMARIA_ESCURA = "#1F5C38"
COR_MENU = "#1F3A2B"
COR_FONDO = "#F4F6F3"
COR_TEXTO = "#1C2B22"
COR_ERRO = "#B3261E"
COR_AVISO = "#A15C00"

_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
      rel="stylesheet">
<style>
:root {
  --cor-primaria: #2F7D4F; --cor-primaria-escura: #1F5C38;
  --cor-menu: #1F3A2B; --cor-menu-texto: #DCE8DF; --cor-menu-suave: #A9C2B1;
  --cor-fondo: #F4F6F3; --cor-superficie: #FFFFFF; --cor-bordo: #E1E7E2;
  --cor-texto: #1C2B22; --cor-texto-suave: #5B6B60;
  --cor-ok-fondo: #E3F2E7; --cor-ok-texto: #1F5C38;
  --cor-aviso-fondo: #FFF4E0; --cor-aviso-texto: #6B4300; --cor-aviso-bordo: #F0C98A;
  --cor-erro: #B3261E;
}
body { font-family: Inter, system-ui, sans-serif; background: var(--cor-fondo);
       color: var(--cor-texto); font-size: 15px; }
.q-btn { text-transform: none; font-weight: 600; border-radius: 8px; min-height: 44px; }
.q-field__control { border-radius: 8px; }

/* Menú lateral */
.menu-lateral { background: var(--cor-menu) !important; color: var(--cor-menu-texto); }
.menu-marca { color: #FFFFFF !important; font-weight: 700; font-size: 20px;
              text-decoration: none; padding: 4px 8px 12px; display: flex; gap: 10px;
              align-items: center; }
.menu-grupo { font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
              color: var(--cor-menu-suave); padding: 14px 12px 4px; }
.menu-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px;
             border-radius: 8px; color: var(--cor-menu-texto) !important;
             text-decoration: none; font-size: 14px; min-height: 44px; }
.menu-boton { background: none; border: none; cursor: pointer; font: inherit; }
.menu-item:hover { background: rgba(255, 255, 255, .08); }
.menu-item.activo { background: var(--cor-primaria); color: #FFFFFF !important;
                    font-weight: 600; }
.menu-selector .q-field__control { background: #2A4A37; }
.menu-selector .q-field__native, .menu-selector .q-field__label,
.menu-selector .q-select__dropdown-icon { color: #FFFFFF !important; }
.menu-pe { border-top: 1px solid #3C5E4A; margin-top: 12px; padding-top: 12px; }
.cabeceira-mobil { background: var(--cor-menu) !important; }

/* Cabeceira de sección */
.migas { font-size: 13px; color: var(--cor-texto-suave); }
.titulo-seccion { font-size: 28px; font-weight: 700; letter-spacing: -0.01em;
                  line-height: 1.2; }

/* Compoñentes */
.tarxeta { background: var(--cor-superficie); border: 1px solid var(--cor-bordo);
           border-radius: 12px; padding: 16px 18px; box-shadow: none; }
.cifra-etiqueta { font-size: 13px; color: var(--cor-texto-suave); }
.cifra-valor { font-size: 28px; font-weight: 700; }
.etiqueta-ok, .etiqueta-aviso { display: inline-flex; padding: 3px 10px;
                                border-radius: 999px; font-size: 12px; font-weight: 600; }
.etiqueta-ok { background: var(--cor-ok-fondo); color: var(--cor-ok-texto); }
.etiqueta-aviso { background: var(--cor-aviso-fondo); color: var(--cor-aviso-texto); }
.aviso { background: var(--cor-aviso-fondo); border: 1px solid var(--cor-aviso-bordo);
         color: var(--cor-aviso-texto); border-radius: 10px; padding: 12px 16px;
         font-size: 14px; }
.taboa, .q-table__container { border-radius: 12px; border: 1px solid var(--cor-bordo);
                               box-shadow: none; }
.taboa thead th, .q-table thead th { color: var(--cor-texto-suave); font-size: 12px;
                                      font-weight: 600;
                  text-transform: uppercase; letter-spacing: .05em; }
.texto-suave { color: var(--cor-texto-suave); }
</style>
"""


def aplicar_tema() -> None:
    """Aplica cores, tipografía e clases CSS á páxina actual. Chamar unha vez por páxina."""
    ui.colors(
        primary=COR_PRIMARIA,
        secondary=COR_PRIMARIA_ESCURA,
        accent=COR_PRIMARIA,
        positive=COR_PRIMARIA,
        negative=COR_ERRO,
        warning=COR_AVISO,
        dark=COR_TEXTO,
    )
    ui.add_head_html(_CSS)
