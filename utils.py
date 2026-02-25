"""
Utilidades y funciones auxiliares para el sistema de rehabilitación
"""

from datetime import datetime
import numpy as np

def calculate_rehabilitation_score(patient_data):
    """
    Calcula una puntuación de rehabilitación basada en múltiples factores.
    """
    if not patient_data or not patient_data.get('questionnaires'):
        return {"score": 0, "level": "Sin datos", "factors": {}}
    
    # Asume que el historial está ordenado del más reciente al más antiguo
    recent_questionnaires = patient_data['questionnaires'][:5]  
    
    # Factores de evaluación (asumiendo que 'pain', 'mobility', etc. son mapeados)
    try:
        avg_pain = np.mean([q['pain'] for q in recent_questionnaires])
        avg_mobility = np.mean([q['mobility'] for q in recent_questionnaires])
        avg_fatigue = np.mean([q['fatigue'] for q in recent_questionnaires])
        avg_sleep = np.mean([q['sleep'] for q in recent_questionnaires])
    except:
         return {"score": 0, "level": "Error en datos", "factors": {}}
    
    # Cálculo del score (0-100)
    pain_score = max(0, 100 - (avg_pain * 10))
    mobility_score = avg_mobility * 10
    fatigue_score = max(0, 100 - (avg_fatigue * 10))
    
    sleep_score = 100 - abs(8 - avg_sleep) * 12.5
    sleep_score = max(0, min(100, sleep_score))
    
    # Ponderación
    total_score = (
        pain_score * 0.3 +
        mobility_score * 0.35 +
        fatigue_score * 0.2 +
        sleep_score * 0.15
    )
    
    # Clasificación
    if total_score >= 80:
        level = "Excelente progreso"
        color = "#2ebf7f"
    elif total_score >= 60:
        level = "Buen progreso"
        color = "#10b981"
    elif total_score >= 40:
        level = "Progreso moderado"
        color = "#f59e0b"
    elif total_score >= 20:
        level = "Progreso lento"
        color = "#ef4444"
    else:
        level = "Requiere atención"
        color = "#dc2626"
    
    return {
        "score": round(total_score, 1),
        "level": level,
        "color": color,
        "factors": {
            "pain": round(avg_pain, 1),
            "mobility": round(avg_mobility, 1),
            "fatigue": round(avg_fatigue, 1),
            "sleep": round(avg_sleep, 1)
        }
    }


def generate_exercise_recommendations(patient_data):
    """
    Genera recomendaciones de ejercicios basadas en el estado del paciente.
    """
    if not patient_data or not patient_data.get('questionnaires'):
        return []
    
    latest = patient_data['questionnaires'][0]
    pain = latest.get('pain', 5)
    mobility = latest.get('mobility', 5)
    
    recommendations = []
    
    # Ejercicios según nivel de dolor y movilidad
    if pain <= 3 and mobility >= 7:
        recommendations = [
            {
                "name": "Sentadillas asistidas",
                "reps": "3 × 15",
                "intensity": "Moderada",
                "notes": "Excelente progreso. Aumentar carga gradualmente."
            },
            {
                "name": "Estocadas controladas",
                "reps": "3 × 10 por pierna",
                "intensity": "Moderada-Alta",
                "notes": "Mantener alineación de rodilla sobre tobillo."
            },
            {
                "name": "Extensiones de rodilla con resistencia",
                "reps": "3 × 12",
                "intensity": "Moderada",
                "notes": "Usar banda elástica o peso ligero."
            }
        ]
    elif pain <= 5 and mobility >= 5:
        recommendations = [
            {
                "name": "Puente de glúteos",
                "reps": "3 × 12",
                "intensity": "Baja-Moderada",
                "notes": "Fortalecer cadena posterior sin impacto."
            },
            {
                "name": "Flexión de rodilla pasiva",
                "reps": "2 × 15",
                "intensity": "Baja",
                "notes": "Mejorar rango de movimiento."
            },
            {
                "name": "Elevación de pierna recta",
                "reps": "3 × 10",
                "intensity": "Baja",
                "notes": "Activación de cuádriceps."
            }
        ]
    else:
        recommendations = [
            {
                "name": "Movilizaciones pasivas",
                "reps": "2 × 10 minutos",
                "intensity": "Muy Baja",
                "notes": "Reducir rigidez sin dolor."
            },
            {
                "name": "Isométricos de cuádriceps",
                "reps": "10 × 10 segundos",
                "intensity": "Muy Baja",
                "notes": "Contracciones sin movimiento."
            },
            {
                "name": "Crioterapia",
                "reps": "3 × 15 minutos",
                "intensity": "N/A",
                "notes": "Reducir inflamación y dolor."
            }
        ]
    
    return recommendations


def format_date_spanish(date_string):
    """
    Formatea una fecha al español.
    """
    try:
        dt = datetime.fromisoformat(date_string)
        months = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        return f"{dt.day} de {months[dt.month]} de {dt.year}"
    except:
        return date_string


def get_risk_level(patient_data):
    """
    Evalúa el nivel de riesgo del paciente.
    """
    if not patient_data or not patient_data.get('questionnaires'):
        return {"level": "unknown", "message": "Sin datos suficientes", "color": "#6b7280", "recommendations": []}
    
    latest = patient_data['questionnaires'][0]
    pain = latest.get('pain', 5)
    mobility = latest.get('mobility', 5)
    fatigue = latest.get('fatigue', 5)
    
    # Evaluación de riesgos
    if pain >= 8 or mobility <= 2:
        return {
            "level": "high",
            "message": "⚠️ Riesgo alto - Requiere atención inmediata",
            "color": "#dc2626",
            "recommendations": [
                "Contactar al fisioterapeuta urgentemente",
                "Reducir actividad física",
                "Aplicar protocolos de manejo del dolor"
            ]
        }
    elif pain >= 6 or mobility <= 4 or fatigue >= 8:
        return {
            "level": "medium",
            "message": "⚡ Riesgo moderado - Monitoreo cercano",
            "color": "#f59e0b",
            "recommendations": [
                "Ajustar intensidad de ejercicios",
                "Aumentar frecuencia de evaluaciones",
                "Considerar terapias complementarias"
            ]
        }
    else:
        return {
            "level": "low",
            "message": "✅ Progreso normal - Continuar plan",
            "color": "#2ebf7f",
            "recommendations": [
                "Mantener rutina actual",
                "Progresar gradualmente",
                "Seguir indicaciones del fisioterapeuta"
            ]
        }