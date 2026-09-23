from nicegui import ui

# Título
ui.label('🌱 A miña horta').classes('text-3xl font-bold')

ui.separator()

# Datos básicos
with ui.card():
    ui.label('Estado da horta').classes('text-xl font-bold')

    ui.label('Parcelas: 3')
    ui.label('Cultivos activos: 7')
    ui.label('Tarefas pendentes: 4')

# Cultivos
with ui.card():
    ui.label('Cultivos').classes('text-xl font-bold')

    ui.table(
        columns=[
            {'name': 'cultivo', 'label': 'Cultivo', 'field': 'cultivo'},
            {'name': 'parcela', 'label': 'Parcela', 'field': 'parcela'},
            {'name': 'estado', 'label': 'Estado', 'field': 'estado'},
        ],
        rows=[
            {'cultivo': 'Tomate', 'parcela': 'Parcela 1', 'estado': 'En crecemento'},
            {'cultivo': 'Faba', 'parcela': 'Parcela 2', 'estado': 'En crecemento'},
            {'cultivo': 'Repolos', 'parcela': 'Parcela 3', 'estado': 'Plantado'},
        ],
    )

# Nova tarefa
with ui.card():
    ui.label('Nova tarefa').classes('text-xl font-bold')

    tarefa = ui.input('Que hai que facer?')

    ui.button(
        'Engadir tarefa',
        on_click=lambda: ui.notify(
            f'Tarefa engadida: {tarefa.value}'
        ),
    )

ui.run(port=8081)
