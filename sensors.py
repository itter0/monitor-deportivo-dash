import pandas as pd
import numpy as np
from scipy.signal import find_peaks

def calculate_bpm(rr_intervals):
    """
    Calcula la frecuencia cardíaca (BPM) a partir de los intervalos R-R.
    
    Args:
        rr_intervals: Array de intervalos R-R en segundos.
        
    Returns:
        BPM (latidos por minuto).
    """
    if len(rr_intervals) > 0:
        # BPM = 60 segundos / intervalo R-R promedio (en segundos)
        return 60 / np.mean(rr_intervals)
    return 0

def load_ecg_and_compute_bpm(filepath):
    df = pd.read_csv(filepath)
    t = df["Time"].values
    ecg = df["ECG"].values

    # Normalización básica
    ecg = ecg - np.mean(ecg)

    # Detección de picos (R-peaks)
    # distance=50 asumiendo una frecuencia de muestreo que da un período mínimo
    # de 50 muestras entre latidos. prominence=0.5 es un umbral de altura relativa.
    peaks, _ = find_peaks(ecg, distance=50, prominence=0.5)

    # LÍNEA 16 CORREGIDA: Cálculo de los intervalos R-R en segundos
    rr_intervals = np.diff(t[peaks])
    
    bpm = calculate_bpm(rr_intervals)

    return t, ecg, bpm

"""
Utilidades y funciones auxiliares para el sistema de rehabilitación
"""

import plotly.graph_objs as go
from datetime import datetime, timedelta
# import numpy as np # Ya importado arriba

def create_progress_chart(patient_data):
    """
    Crea un gráfico de progreso de movilidad y dolor del paciente.
    
    Args:
        patient_data: Diccionario con datos del paciente
        
    Returns:
        Figura de Plotly
    """
    if not patient_data or not patient_data.get('questionnaires'):
        return go.Figure().add_annotation(
            text="Sin datos suficientes",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6b7280")
        )
    
    questionnaires = patient_data['questionnaires'][::-1]  # Invertir para orden cronológico
    
    dates = [q['timestamp'][:10] for q in questionnaires]
    pain_levels = [q['pain'] for q in questionnaires]
    mobility_scores = [q['mobility'] for q in questionnaires]
    
    fig = go.Figure()
    
    # Línea de dolor
    fig.add_trace(go.Scatter(
        x=dates,
        y=pain_levels,
        mode='lines+markers',
        name='Nivel de dolor',
        line=dict(color='#ef4444', width=3),
        marker=dict(size=8)
    ))
    
    # Línea de movilidad
    fig.add_trace(go.Scatter(
        x=dates,
        y=mobility_scores,
        mode='lines+markers',
        name='Movilidad',
        line=dict(color='#2ebf7f', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Evolución del Paciente",
        xaxis_title="Fecha",
        yaxis_title="Puntuación (0-10)",
        hovermode='x unified',
        plot_bgcolor='#f6f8fb',
        paper_bgcolor='white',
        font=dict(family="Inter, sans-serif"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    fig.update_yaxis(range=[0, 10], dtick=2)
    
    return fig


def create_bpm_chart(ecg_data):
    """
    Crea un gráfico de evolución de BPM del paciente.
    
    Args:
        ecg_data: Lista de diccionarios con datos ECG
        
    Returns:
        Figura de Plotly
    """
    if not ecg_data:
        return go.Figure().add_annotation(
            text="Sin registros ECG",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6b7280")
        )
    
    ecg_data_sorted = sorted(ecg_data, key=lambda x: x['timestamp'])
    
    dates = [d['timestamp'][:16] for d in ecg_data_sorted]
    bpm_values = [d['bpm'] for d in ecg_data_sorted]
    quality_scores = [d['quality'] for d in ecg_data_sorted]
    
    fig = go.Figure()
    
    # Gráfico de barras de BPM con color según calidad
    colors = ['#2ebf7f' if q >= 70 else '#f59e0b' if q >= 50 else '#ef4444' 
              for q in quality_scores]
    
    fig.add_trace(go.Bar(
        x=dates,
        y=bpm_values,
        name='BPM',
        marker=dict(color=colors),
        text=[f"{bpm:.0f} BPM<br>Calidad: {q}%" for bpm, q in zip(bpm_values, quality_scores)],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>BPM: %{y:.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Frecuencia Cardíaca en Sesiones",
        xaxis_title="Fecha de sesión",
        yaxis_title="BPM",
        plot_bgcolor='#f6f8fb',
        paper_bgcolor='white',
        font=dict(family="Inter, sans-serif"),
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=80)
    )
    
    fig.update_xaxis(tickangle=-45)
    
    return fig


def create_ecg_signal_plot(time_array, ecg_signal, bpm):
    """
    Crea un gráfico de la señal ECG.
    
    Args:
        time_array: Array de tiempos
        ecg_signal: Array de señal ECG
        bpm: Frecuencia cardíaca en BPM
        
    Returns:
        Figura de Plotly
    """
    if time_array is None or ecg_signal is None:
        return go.Figure().add_annotation(
            text="No hay señal ECG disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6b7280")
        )
    
    # Mostrar solo los primeros 10 segundos para visualización clara
    mask = time_array <= 10
    t_plot = time_array[mask]
    ecg_plot = ecg_signal[mask]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=t_plot,
        y=ecg_plot,
        mode='lines',
        name='ECG',
        line=dict(color='#1e88e5', width=1.5)
    ))
    
    fig.update_layout(
        title=f"Señal ECG - {bpm:.0f} BPM",
        xaxis_title="Tiempo (s)",
        yaxis_title="Amplitud (normalizada)",
        plot_bgcolor='#f6f8fb',
        paper_bgcolor='white',
        font=dict(family="Inter, sans-serif"),
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode='x'
    )
    
    return fig


def calculate_rehabilitation_score(patient_data):
    """
    Calcula una puntuación de rehabilitación basada en múltiples factores.
    
    Args:
        patient_data: Diccionario con datos del paciente
        
    Returns:
        dict con score y desglose
    """
    if not patient_data or not patient_data.get('questionnaires'):
        return {"score": 0, "level": "Sin datos", "factors": {}}
    
    recent_questionnaires = patient_data['questionnaires'][:5]  # Últimos 5
    
    # Factores de evaluación
    avg_pain = np.mean([q['pain'] for q in recent_questionnaires])
    avg_mobility = np.mean([q['mobility'] for q in recent_questionnaires])
    avg_fatigue = np.mean([q['fatigue'] for q in recent_questionnaires])
    avg_sleep = np.mean([q['sleep'] for q in recent_questionnaires])
    
    # Cálculo del score (0-100)
    # Menor dolor = mejor score
    pain_score = max(0, 100 - (avg_pain * 10))
    
    # Mayor movilidad = mejor score
    mobility_score = avg_mobility * 10
    
    # Menor fatiga = mejor score
    fatigue_score = max(0, 100 - (avg_fatigue * 10))
    
    # Sueño óptimo entre 7-9 horas
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
    
    Args:
        patient_data: Diccionario con datos del paciente
        
    Returns:
        Lista de ejercicios recomendados
    """
    if not patient_data or not patient_data.get('questionnaires'):
        return []
    
    latest = patient_data['questionnaires'][0]
    pain = latest['pain']
    mobility = latest['mobility']
    
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
    
    Args:
        date_string: Fecha en formato ISO
        
    Returns:
        Fecha formateada en español
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
    
    Args:
        patient_data: Diccionario con datos del paciente
        
    Returns:
        dict con nivel de riesgo y recomendaciones
    """
    if not patient_data or not patient_data.get('questionnaires'):
        return {"level": "unknown", "message": "Sin datos suficientes", "color": "#6b7280"}
    
    latest = patient_data['questionnaires'][0]
    pain = latest['pain']
    mobility = latest['mobility']
    fatigue = latest['fatigue']
    
    # Evaluación de riesgos
    if pain >= 8 or mobility <= 2:
        return {
            "level": "high",
            "message": "⚠ Riesgo alto - Requiere atención inmediata",
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