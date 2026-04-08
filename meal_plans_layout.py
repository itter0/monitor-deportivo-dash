"""Meal Plans Layout Function - to be integrated into app.py"""

def get_meal_plans_layout(username, full_name, _USER_DB, html, dbc, dcc, ALL, STYLES, current_search=""):
    """Generate meal plans management layout for patients."""
    user_data = _USER_DB.get(username, {})
    profile_data = user_data.get('profile', {})
    meal_plans_data = user_data.get('meal_plans', [])
    fights_data = user_data.get('fights', [])
    
    athlete_weight = profile_data.get('current_weight', 'N/A')
    weight_class = profile_data.get('weight_class', 'No definida')
    
    # Información de combates próximos
    fights_info = "Sin combates próximos"
    if fights_data:
        next_fight = fights_data[-1]  # Último combate agregado
        target_weight = next_fight.get('target_weight', 'N/A')
        fight_date = next_fight.get('date', 'N/A')
        fights_info = f"Próximo combate: {fight_date} | Target: {target_weight} kg"
    
    # Renderizar lista de planes
    meal_plans_html = []
    if meal_plans_data:
        for idx, plan in enumerate(meal_plans_data):
            weight_change_labels = {
                'gain': '⬆️ Ganancia de Masa',
                'cut': '⬇️ Corte de Peso',
                'maintain': '➡️ Mantenimiento',
                'none': '🤔 Sin Cambio'
            }
            weight_change = weight_change_labels.get(plan.get('weight_change'), 'N/A')
            
            meal_plans_html.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(plan.get('name', 'Plan sin nombre'), style={'color': '#00ff88', 'marginBottom': '10px'}),
                        html.P([
                            html.Strong("Tipo: "), weight_change,
                            html.Br(),
                            html.Strong("Objetivo: "), f"{plan.get('target_weight', 'N/A')} kg" if plan.get('target_weight') else "Sin objetivo",
                            html.Br(),
                            html.Strong("Duración: "), f"{plan.get('duration', 'N/A')} días",
                            html.Br(),
                            html.Strong("Creado: "), plan.get('created_date', 'N/A')[:10]
                        ], style={'fontSize': '0.9em', 'marginBottom': '10px'}),
                        dbc.Button("✏️ Editar", id={'type': 'edit-meal-plan-btn', 'index': idx}, 
                                  color='warning', size='sm', style={'marginRight': '5px'}),
                        dbc.Button("🗑️ Eliminar", id={'type': 'delete-meal-plan-btn', 'index': idx}, 
                                  color='danger', size='sm')
                    ])
                ], style={'marginBottom': '10px', 'backgroundColor': '#1a1a1a', 'border': '1px solid #333'})
            )
    else:
        meal_plans_html.append(
            html.Div("📭 No hay planes de comida guardados aún. ¡Crea uno ahora!",
                    style={'color': '#d9d9d9', 'textAlign': 'center', 'padding': '20px'})
        )
    
    from app import get_user_navbar
    
    return html.Div([
        get_user_navbar("🍽️", full_name.upper(), "PLANES DE COMIDA", current_search),
        
        html.Div([
            # INFORMACIÓN DEL ATLETA
            dbc.Card([
                dbc.CardHeader(html.Div([
                    html.Span("👤 ", style={'fontSize': '1.2em'}),
                    "Información del Atleta"
                ], style=STYLES['card_header_tactical']), style={'backgroundColor': '#000', 'border': '1px solid #333'}),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.P([html.Strong("⚖️ Peso Actual: "), 
                                   f"{athlete_weight} kg" if athlete_weight != 'N/A' else "No registrado"],
                                  style={'color': '#ffffff'}),
                            html.P([html.Strong("📊 Categoría de Peso: "), weight_class],
                                  style={'color': '#ffffff'}),
                        ], width=6),
                        dbc.Col([
                            html.P([html.Strong("🥊 Combates: "), fights_info],
                                  style={'color': '#00ff88'})
                        ], width=6)
                    ])
                ], style={'backgroundColor': '#1a1a1a'})
            ], style={'marginBottom': '20px', 'border': '1px solid #333'}),
            
            # CREAR NUEVO PLAN DE COMIDA
            dbc.Card([
                dbc.CardHeader(html.Div([
                    html.Span("➕ ", style={'fontSize': '1.2em'}),
                    "Crear Nuevo Plan de Comida"
                ], style=STYLES['card_header_tactical']), style={'backgroundColor': '#000', 'border': '1px solid #333'}),
                dbc.CardBody([
                    html.Label("Nombre del Plan", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                    dcc.Input(id='meal-plan-name', type='text', placeholder='Ej: Plan Pre-Combate Marzo', 
                             style={'width': '100%', 'marginBottom': '10px', 'padding': '8px', 'backgroundColor': '#2a2a2a', 'color': '#fff', 'border': '1px solid #444'}),
                    
                    dbc.Row([
                        dbc.Col([
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
                                style={'marginBottom': '10px'}
                            ),
                        ], width=6),
                        dbc.Col([
                            html.Label("Objetivo de Peso (kg)", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                            dcc.Input(id='meal-plan-target-weight', type='number', step=0.1, 
                                     placeholder='Ej: 75.5 (opcional)', 
                                     style={'width': '100%', 'marginBottom': '10px', 'padding': '8px', 'backgroundColor': '#2a2a2a', 'color': '#fff', 'border': '1px solid #444'}),
                        ], width=6)
                    ]),
                    
                    html.Label("Duración del Plan (días)", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                    dcc.Input(id='meal-plan-duration', type='number', min=1, max=365, value=30,
                             style={'width': '100%', 'marginBottom': '10px', 'padding': '8px', 'backgroundColor': '#2a2a2a', 'color': '#fff', 'border': '1px solid #444'}),
                    
                    html.Label("Descripción del Plan (Macros, Alimentos, Horarios)", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                    dcc.Textarea(id='meal-plan-description', placeholder='''Describe tu plan de comida detallado:
• Desayuno: ...
• Almuerzo: ...
• Merienda: ...
• Cena: ... 
• Macros diarios: Proteínas, carbohidratos, grasas (g)
• Suplementos: ...
• Hidratación: ...''', 
                                style={'width': '100%', 'height': '200px', 'marginBottom': '10px', 'padding': '8px', 'backgroundColor': '#2a2a2a', 'color': '#fff', 'border': '1px solid #444'}),
                    
                    html.Label("Notas Adicionales", style={'fontWeight': 'bold', 'color': '#ffffff', 'marginTop': '15px'}),
                    dcc.Textarea(id='meal-plan-notes', placeholder='Restricciones dietéticas, alergias, preferencias, consideraciones...',
                                style={'width': '100%', 'height': '100px', 'marginBottom': '10px', 'padding': '8px', 'backgroundColor': '#2a2a2a', 'color': '#fff', 'border': '1px solid #444'}),
                    
                    dbc.Button("📝 Guardar Plan", id='save-meal-plan-btn', n_clicks=0, color='success', className='w-100', size='lg'),
                    html.Div(id='meal-plan-feedback', style={'marginTop': '15px'})
                ], style={'backgroundColor': '#1a1a1a'})
            ], style={'marginBottom': '20px', 'border': '1px solid #333'}),
            
            # LISTA DE PLANES EXISTENTES
            dbc.Card([
                dbc.CardHeader(html.Div([
                    html.Span("📋 ", style={'fontSize': '1.2em'}),
                    "Planes de Comida Guardados"
                ], style=STYLES['card_header_tactical']), style={'backgroundColor': '#000', 'border': '1px solid #333'}),
                dbc.CardBody(meal_plans_html, style={'backgroundColor': '#1a1a1a'})
            ], style={'marginBottom': '20px', 'border': '1px solid #333'})
            
        ], style={'padding': '10px 24px', 'maxWidth': '1200px', 'margin': '0 auto'})
        
    ], style=STYLES['main_container'])
