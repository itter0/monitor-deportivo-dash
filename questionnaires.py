from dash import dcc, html
import sqlite3
from datetime import datetime, date


class QuestionnaireService:
    """Lógica de negocio de cuestionarios (recomendación, render y validación de envío)."""

    @staticmethod
    def get_recommended_questionnaires(health_status, injury_types, questionnaires_by_injury):
        if health_status == 'listo':
            return ['funcionalidad']

        if health_status == 'lesionado' and injury_types:
            if not isinstance(injury_types, list):
                injury_types = [injury_types]

            selected = []
            seen = set()
            for injury in injury_types:
                for q_id in questionnaires_by_injury.get(injury, []):
                    if q_id not in seen:
                        selected.append(q_id)
                        seen.add(q_id)
            return selected

        return ['funcionalidad']

    @staticmethod
    def can_submit_today(user_history, questionnaire_id):
        today_str = date.today().isoformat()
        already_done = any(
            q.get('questionnaire_id') == questionnaire_id and str(q.get('timestamp', '')).startswith(today_str)
            for q in (user_history or [])
        )
        return not already_done

    @staticmethod
    def build_questionnaire_component(questionnaire, component_prefix='questionnaire-input'):
        questions_content = []
        for i, question in enumerate(questionnaire['questions']):
            component_id = {'type': component_prefix, 'questionnaire': questionnaire['id'], 'index': question['id']}

            # Contenedor con contraste mejorado (tarjeta táctica)
            question_html = html.Div([
                html.Div([
                    html.Span(f"{i+1}", style={
                        'backgroundColor': '#3b82f6',
                        'color': 'white',
                        'padding': '2px 12px',
                        'borderRadius': '4px',
                        'marginRight': '15px',
                        'fontWeight': 'bold'
                    }),
                    html.Label(question['question'].upper(), style={
                        'color': '#f3f4f6',
                        'fontWeight': '600',
                        'letterSpacing': '0.5px',
                        'fontSize': '0.95rem',
                        'flex': '1'
                    }),
                ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '25px'}),
            ], style={
                'backgroundColor': '#0f172a',
                'padding': '25px',
                'borderRadius': '8px',
                'border': '1px solid #1e293b',
                'borderLeft': '5px solid #3b82f6',
                'marginBottom': '20px',
                'boxShadow': '0 10px 20px rgba(0,0,0,0.3)'
            })

            if question['type'] == 'slider':
                question_html.children.append(
                    html.Div([
                        dcc.Slider(
                            id=component_id,
                            min=question['min'],
                            max=question['max'],
                            step=question.get('step', 1),
                            value=question.get('min', 0),
                            marks={j: {'label': str(j), 'style': {'color': '#64748b', 'fontFamily': 'Oswald'}} for j in range(question['min'], question['max'] + 1)},
                            className='custom-tactical-slider',
                            updatemode='drag',
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'padding': '0 10px'})
                )
            elif question['type'] == 'radio':
                question_html.children.append(
                    dcc.RadioItems(
                        id=component_id,
                        options=question['options'],
                        value=question['options'][0]['value'] if question['options'] else None,
                        style={'marginTop': '10px'},
                        labelStyle={
                            'display': 'block', 
                            'marginBottom': '12px', 
                            'color': '#ffffff', 
                            'fontSize': '14px',
                            'cursor': 'pointer',
                            'padding': '8px 12px',
                            'backgroundColor': '#252525',
                            'borderRadius': '6px',
                            'transition': 'all 0.2s'
                        },
                        inputStyle={"marginRight": "12px", "transform": "scale(1.2)"},
                        className="custom-radio-group"
                    )
                )

            questions_content.append(question_html)

        return questions_content

    @staticmethod
    def extract_questionnaire_responses(questionnaire, questionnaire_id, input_ids, input_values):
        values_by_qid = {}
        if input_ids and input_values:
            for comp_id, comp_value in zip(input_ids, input_values):
                if not isinstance(comp_id, dict):
                    continue
                qid = comp_id.get('questionnaire')
                qindex = comp_id.get('index')
                if qid and qindex:
                    if qid not in values_by_qid:
                        values_by_qid[qid] = {}
                    values_by_qid[qid][qindex] = comp_value

        values_map = values_by_qid.get(questionnaire_id, {})
        question_ids = [q['id'] for q in questionnaire['questions']]
        missing = [q_id for q_id in question_ids if values_map.get(q_id) is None]

        if missing:
            return False, {}, missing

        responses = {q_id: values_map.get(q_id) for q_id in question_ids}
        return True, responses, []

    @staticmethod
    def build_submission_payload(questionnaire_id, questionnaire_title, responses):
        return {
            'questionnaire_id': questionnaire_id,
            'responses': responses,
            'timestamp': datetime.now().isoformat(),
            'questionnaire_title': questionnaire_title,
        }

# Layout de cuestionario
questionnaire_layout = html.Div([
    html.Label("Nivel de fatiga (1-10):", style={'color': '#ffffff'}),
    dcc.Slider(min=1, max=10, step=1, value=5, id="fatiga", marks={i: {'label': str(i), 'style': {'color': '#888'}} for i in range(1, 11)}, className='custom-tactical-slider'),

    html.Label("Horas de sueño:", style={'color': '#ffffff'}),
    dcc.Input(id="suenio", type="number", min=0, max=12, step=1, value=8, style={'backgroundColor': '#0b1220', 'color': '#ffffff', 'border': '1px solid #333', 'padding': '6px 8px', 'borderRadius': '6px'}),

    html.Label("Esfuerzo percibido (RPE, 1-10):", style={'color': '#ffffff'}),
    dcc.Slider(min=1, max=10, step=1, value=5, id="rpe", marks={i: {'label': str(i), 'style': {'color': '#888'}} for i in range(1, 11)}, className='custom-tactical-slider'),

    html.Br(),
    html.Button(
        '📤 FINALIZAR Y GUARDAR REGISTRO',
        id="submit-questionnaire",
        n_clicks=0,
        style={
            'backgroundColor': 'rgba(59, 130, 246, 0.1)',
            'borderColor': '#3b82f6',
            'color': '#3b82f6',
            'marginTop': '30px',
            'fontSize': '1rem',
            'padding': '15px',
            'borderRadius': '8px',
            'fontWeight': '700',
            'border': '1px solid #3b82f6',
            'cursor': 'pointer'
        }
    )
])

def save_questionnaire(fatiga, suenio, rpe):
    conn = sqlite3.connect("data/users.db")
    c = conn.cursor()
    c.execute("INSERT INTO questionnaires (user_id, fatiga, suenio, rpe) VALUES (?, ?, ?, ?)",
              (1, fatiga, suenio, rpe))  # por ahora asignamos user_id = 1 fijo
    conn.commit()
    conn.close()
