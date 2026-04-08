# Helper function for meal plans layout
# This file contains the get_meal_plans_layout function to be imported into app.py

def get_meal_plans_layout_html(get_full_href, get_user_navbar, html, dbc, dcc, STYLES, COLORS, username, full_name, profile_data, current_search=""):
    """Generate meal plans management layout.
    
    Args:
        get_full_href: Function to create full href with session
        get_user_navbar: Function to create navbar
        html: Dash HTML components
        dbc: Dash Bootstrap components
        dcc: Dash Core components
        STYLES: Style dictionary
        COLORS: Color dictionary
        username: Current username
        full_name: User's full name
        profile_data: User profile data
        current_search: Current search/session query string
    """
    
    athlete_weight = profile_data.get('current_weight', 'N/A')
    weight_class = profile_data.get('weight_class', 'No definida')
    
    return html.Div([
        get_user_navbar("🍽️", full_name.upper(), "PLANES DE COMIDA", current_search),
        
        html.Div([
            # INFORMACIÓN DEL ATLETA
            html.Div([
                html.Div([
                    html.Span("👤 ", style={'fontSize': '1.2em'}),
                    "Información del Atleta"
                ], style=STYLES['card_header_tactical']),
                
                dbc.Row([
                    dbc.Col([
                        html.P([html.Strong("Peso Actual: "), f"{athlete_weight} kg" if athlete_weight != 'N/A' else "No registrado"]),
                        html.P([html.Strong("Categoría de Peso: "), weight_class]),
                    ], width=6),
                    dbc.Col([
                        html.Div(id='meal-plans-athlete-fights', children="Cargando combates...")
                    ], width=6)
                ])
            ], style=STYLES['card']),
            
            html.Hr(),
            
            # CREAR NUEVO PLAN DE COMIDA
            html.Div([
                html.Div([
                    html.Span("➕ ", style={'fontSize': '1.2em'}),
                    "Crear Nuevo Plan de Comida"
                ], style=STYLES['card_header_tactical']),
                
                html.Label("Nombre del Plan", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                dcc.Input(id='meal-plan-name', type='text', placeholder='Ej: Plan Pre-Combate Marzo', 
                         style={'width': '100%', 'marginBottom': '10px', 'padding': '8px'}),
                
                html.Label("Tipo de Cambio de Peso", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                dcc.Dropdown(
                    id='meal-plan-weight-change',
                    options=[
                        {'label': '⬆️ Subir de Peso (Ganancia de Masa)', 'value': 'gain'},
                        {'label': '⬇️ Bajar de Peso (Corte de Peso)', 'value': 'cut'},
                        {'label': '➡️ Mantener Peso (Mantenimiento)', 'value': 'maintain'},
                        {'label': '🤔 Sin Cambio (Nutrición General)', 'value': 'none'}
                    ],
                    value='none',
                    style={'marginBottom': '10px', 'color': 'black'}
                ),
                
                html.Label("Objetivo de Peso Deseado (kg)", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                dcc.Input(id='meal-plan-target-weight', type='number', step=0.1, 
                         placeholder='Ej: 75.5 (opcional)', style={'width': '100%', 'marginBottom': '10px', 'padding': '8px'}),
                
                html.Label("Duración del Plan (días)", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                dcc.Input(id='meal-plan-duration', type='number', min=1, max=365, value=30,
                         style={'width': '100%', 'marginBottom': '10px', 'padding': '8px'}),
                
                html.Label("Descripción del Plan (Macros, Alimentos, Horarios)", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                dcc.Textarea(id='meal-plan-description', placeholder='''Describe tu plan de comida detallado:
- Desayuno: ...
- Almuerzo: ...
- Merienda: ...
- Cena: ... 
- Macros diarios: Proteínas, carbohidratos, grasas
- Suplementos: ...''', 
                             style={'width': '100%', 'height': '200px', 'marginBottom': '10px', 'padding': '8px'}),
                
                html.Label("Notas Adicionales", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                dcc.Textarea(id='meal-plan-notes', placeholder='Restricciones dietéticas, alergias, preferencias, etc.',
                             style={'width': '100%', 'height': '100px', 'marginBottom': '10px', 'padding': '8px'}),
                
                dbc.Button("📝 Guardar Plan", id='save-meal-plan-btn', n_clicks=0, color='success', className='w-100', size='lg'),
                html.Div(id='meal-plan-feedback', style={'marginTop': '15px'})
            ], style=STYLES['card']),
            
            html.Hr(),
            
            # LISTA DE PLANES EXISTENTES
            html.Div([
                html.Div([
                    html.Span("📋 ", style={'fontSize': '1.2em'}),
                    "Planes de Comida Guardados"
                ], style=STYLES['card_header_tactical']),
                html.Div(id='meal-plans-list', children="Cargando planes...", style={'marginTop': '15px'})
            ], style=STYLES['card'])
            
        ], style={'padding': '10px 24px', 'maxWidth': '1200px', 'margin': '0 auto'})
        
    ], style=STYLES['main_container'])


# Placeholder for callback handlers - to be added in app.py
