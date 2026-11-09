"""Eventos internos da app para avisar ás pantallas abertas sen ter que preguntar."""

from __future__ import annotations

from nicegui import Event

# Chegaron lecturas novas dun sensor (argumento: id do sensor)
lecturas_novas: Event[int] = Event()
