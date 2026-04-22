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
            question_html = html.Div([
                html.H6(f"{i+1}. {question['question']}", style={'marginBottom': '10px', 'fontWeight': 'bold', 'color': '#ffffff'}),
            ])

            component_id = {'type': component_prefix, 'questionnaire': questionnaire['id'], 'index': question['id']}

            if question['type'] == 'slider':
                question_html.children.append(
                    dcc.Slider(
                        id=component_id,
                        min=question['min'],
                        max=question['max'],
                        step=question.get('step', 1),
                        value=question.get('min', 0),
                        marks=question.get('marks', {j: str(j) for j in range(question['min'], question['max'] + 1, max(1, (question['max'] - question['min']) // 5))}),
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                )
            elif question['type'] == 'radio':
                question_html.children.append(
                    dcc.RadioItems(
                        id=component_id,
                        options=question['options'],
                        value=question['options'][0]['value'] if question['options'] else None,
                        style={'marginBottom': '15px'},
                        labelStyle={'display': 'block', 'marginBottom': '10px', 'color': '#ffffff', 'fontWeight': '500'}
                    )
                )

            questions_content.append(question_html)
            questions_content.append(html.Hr())

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
    html.Label("Nivel de fatiga (1-10):"),
    dcc.Slider(1, 10, 1, value=5, id="fatiga"),

    html.Label("Horas de sueño:"),
    dcc.Input(id="suenio", type="number", min=0, max=12, step=1, value=8),

    html.Label("Esfuerzo percibido (RPE, 1-10):"),
    dcc.Slider(1, 10, 1, value=5, id="rpe"),

    html.Br(),
    html.Button("Enviar", id="submit-questionnaire", n_clicks=0)
])

def save_questionnaire(fatiga, suenio, rpe):
    conn = sqlite3.connect("data/users.db")
    c = conn.cursor()
    c.execute("INSERT INTO questionnaires (user_id, fatiga, suenio, rpe) VALUES (?, ?, ?, ?)",
              (1, fatiga, suenio, rpe))  # por ahora asignamos user_id = 1 fijo
    conn.commit()
    conn.close()
