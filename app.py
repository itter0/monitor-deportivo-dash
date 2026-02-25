import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import json
import pandas as pd
import numpy as np
from urllib.parse import urlparse, parse_qs, urlencode
import os
import re 
import subprocess
import signal
import threading
import csv  
import time 

# --------------------------------------------------------------------------
# --- INICIALIZACIÓN DE DUMMIES PARA BASE DE DATOS Y SENSORES ---
# --------------------------------------------------------------------------

STREAM_FILE = "data/sensor_data_stream.csv" # Mueve el stream a la carpeta data
# Asegúrate de que la carpeta existe antes de que el simulador empiece
if not os.path.exists('data'):
    os.makedirs('data')

# Archivo de persistencia de la base de datos (CRÍTICO)
DB_FILE = 'rehabidesk_db.json'

# Base de datos DUMMY (Diccionario simple) - Ahora globalmente mutable
_USER_DB = {}
_APPOINTMENTS_DB = []
_PATIENT_INFO_DB = {}
_QUESTIONNAIRE_HISTORY_DB = {}
_EXERCISE_HISTORY_DB = {}

# Funciones dummy de SENSORS (Asegurando que load_ecg_and_compute_bpm existe)
try:
    from sensors import load_ecg_and_compute_bpm
except ImportError:
    # Definición dummy para evitar que el script falle si sensors.py no tenga la función
    def load_ecg_and_compute_bpm(filepath):
        fs = 200 # Frecuencia de muestreo
        t = np.linspace(0, 10, int(10*fs), endpoint=False)
        
        if "stress" in filepath:
            bpm = 105.0
            # Simulación de taquicardia/esfuerzo
            ecg = 0.5 * np.sin(2 * np.pi * 1.5 * t) + 0.9 * np.exp(-((t - 0.2) ** 2) / 0.005) * np.sin(2 * np.pi * 7 * t)
        else:
            bpm = 75.0
            # Simulación de ritmo normal
            ecg = 0.5 * np.sin(2 * np.pi * 1.0 * t) 
            ecg += 0.8 * np.exp(-((t - 0.2) ** 2) / 0.01) * np.sin(2 * np.pi * 5 * t) 
            ecg += 0.3 * np.exp(-((t - 0.6) ** 2) / 0.05) 
            
        return t, ecg, bpm

class DummyDB:
    def __init__(self):
        # 1. Intenta cargar los datos del disco
        loaded = self.load_data()
        
        # 2. Si no se cargó nada, inicializa la DB con usuarios de prueba y guarda
        if not loaded:
            self.add_user("dr.garcia","1234","medico","Dr. Ángel García", initial_save=False)
            self.add_user("paciente.torn","1234","paciente","Torn Benson", initial_save=False)
            self.add_user("paciente.nuevo","1234","paciente","Paciente Nuevo", initial_save=False) # Paciente sin asignar
            
            self.save_user_profile("paciente.torn", {
                'email': 'paciente.torn@mail.com', 
                'phone': '666-000-001', 
                'address': 'C/ Falsa 123', 
                'dni': 'X0000000A', 
                'birth_date': '1995-10-20',
                'emergency_contact': 'Familiar Torn', 
                'emergency_phone': '666-111-111', 
                'blood_type': 'O+',
                'allergies': 'Penicilina',
                'current_medications': 'Ibuprofeno 600mg',
                'medical_conditions': 'Osteoartritis leve'
            }, initial_save=False)
            
            # Perfil médico (solo para evitar que sea None)
            self.save_user_profile("dr.garcia", {
                'email': 'dr.garcia@mail.com', 
                'phone': '910-000-000', 
                'address': 'Hospital Central', 
                'dni': 'Y0000000B', 
                'birth_date': '1980-05-15',
                'emergency_contact': 'Esposa', 
                'emergency_phone': '910-111-111', 
            }, initial_save=False)

            self.save_user_profile("paciente.nuevo", {
                'email': 'nuevo@mail.com', 
                'phone': '666-000-002', 
                'dni': 'Z0000000C', 
            }, initial_save=False)
            
            self.add_patient(username="paciente.torn", diagnosis="Rodilla Derecha", doctor_user="dr.garcia", physio_user=None, initial_save=False)
            # paciente.nuevo NO se añade a _PATIENT_INFO_DB para simular no asignado inicialmente

            # Datos de prueba para gráficas (se mantiene)
            today = datetime.now()
            if not _QUESTIONNAIRE_HISTORY_DB.get("paciente.torn"):
                _QUESTIONNAIRE_HISTORY_DB["paciente.torn"] = [
                    {'questionnaire_title': 'Dolor Rodilla', 'questionnaire_id': 'dolor_rodilla', 'timestamp': (today - timedelta(days=10)).isoformat(), 'responses': {'q1': 7, 'q2': 5, 'q3': 'moderado'}},
                    {'questionnaire_title': 'Dolor Rodilla', 'questionnaire_id': 'dolor_rodilla', 'timestamp': (today - timedelta(days=3)).isoformat(), 'responses': {'q1': 5, 'q2': 3, 'q3': 'leve'}}
                ]
            if not _EXERCISE_HISTORY_DB.get("paciente.torn"):
                _EXERCISE_HISTORY_DB["paciente.torn"] = [
                    {'exercise_id': 'ext_rodilla', 'exercise_name': 'Extensión de Rodilla', 'timestamp': (today - timedelta(days=9)).isoformat(), 'duration_seconds': 120, 'sets': 3, 'reps': 10},
                    {'exercise_id': 'flex_rodilla', 'exercise_name': 'Flexión de Rodilla', 'timestamp': (today - timedelta(days=2)).isoformat(), 'duration_seconds': 180, 'sets': 3, 'reps': 12}
                ]
            
            # Citas de prueba, asegurando que el ID sea único y compatible con el formato 'appt-XXX'
            now = datetime.now()
            _APPOINTMENTS_DB.extend([
                {
                    'id': 'appt-1',
                    'datetime': (now + timedelta(days=5)).isoformat(),
                    'patient_username': 'paciente.torn',
                    'professional_username': 'dr.garcia',
                    'professional_name': 'Dr. Ángel García',
                    'hospital': 'Hospital Central',
                    'office': 'Consultorio 201',
                    'comments': 'Revisión post-quirúrgica y ajuste de plan de rehabilitación.',
                    'status': 'scheduled',
                    'doctor_notes': ''
                },
                {
                    'id': 'appt-2',
                    'datetime': (now + timedelta(days=15)).isoformat(),
                    'patient_username': 'paciente.torn',
                    'professional_username': 'dr.garcia',
                    'professional_name': 'Dr. Ángel García',
                    'hospital': 'Clínica Periférica',
                    'office': 'Sala 3',
                    'comments': 'Seguimiento de terapia.',
                    'status': 'confirmed',
                    'doctor_notes': ''
                }
            ])
            
            self.save_data()
            print("DEBUG: Usuarios de prueba inicializados y guardados en JSON.")

    def init_db(self):
        print(f"DEBUG: Dummy DB inicializada. Persistencia: {DB_FILE}. Usuarios: {len(_USER_DB)}")

    # --- MÉTODOS DE PERSISTENCIA ---
    def save_data(self):
        """Guarda la base de datos completa en el archivo JSON."""
        data = {
            'users': _USER_DB,
            'appointments': _APPOINTMENTS_DB,
            'patient_info': _PATIENT_INFO_DB,
            'questionnaire_history': _QUESTIONNAIRE_HISTORY_DB,
            'exercise_history': _EXERCISE_HISTORY_DB,
        }
        try:
            with open(DB_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"ERROR: No se pudo guardar la DB en {DB_FILE}: {e}")

    def load_data(self):
        """Carga la base de datos desde el archivo JSON."""
        global _USER_DB, _APPOINTMENTS_DB, _PATIENT_INFO_DB, _QUESTIONNAIRE_HISTORY_DB, _EXERCISE_HISTORY_DB
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f:
                    data = json.load(f)
                    _USER_DB = data.get('users', {})
                    _APPOINTMENTS_DB = data.get('appointments', [])
                    _PATIENT_INFO_DB = data.get('patient_info', {})
                    _QUESTIONNAIRE_HISTORY_DB = data.get('questionnaire_history', {})
                    _EXERCISE_HISTORY_DB = data.get('exercise_history', {})
                print(f"DEBUG: Datos cargados desde {DB_FILE}. Usuarios: {len(_USER_DB)}")
                return True
            except (json.JSONDecodeError, IOError, EOFError) as e:
                print(f"ADVERTENCIA: Archivo {DB_FILE} corrupto o vacío ({e}). Se inicializará DB vacía.")
                return False
        return False

    # --- MÉTODOS DE LA DB (MODIFICADOS PARA PERSISTENCIA) ---
    
    def add_user(self, username, password, role, full_name, initial_save=True):
        if username in _USER_DB:
            print(f"ADVERTENCIA: Intento de añadir usuario {username} que ya existe.")
            return
            
        _USER_DB[username] = {'password': password, 'role': role, 'full_name': full_name, 'member_since': datetime.now().isoformat()}
        if initial_save: self.save_data()
        print(f"DEBUG: Usuario {username} ({role}) añadido.")

    def authenticate_user(self, username, password):
        user = _USER_DB.get(username)
        if user and user['password'] == password:
            return user
        return None

    def add_patient(self, username, diagnosis, doctor_user, physio_user, initial_save=True):
        # CORRECCIÓN: Si el paciente ya existe en _PATIENT_INFO_DB, lo actualiza (útil para la asociación)
        current_info = _PATIENT_INFO_DB.get(username, {})
        current_info.update({
            'diagnosis': diagnosis, 
            'doctor_user': doctor_user, 
            'physio_user': physio_user, 
            'full_name': _USER_DB.get(username, {}).get('full_name')
        })
        _PATIENT_INFO_DB[username] = current_info

        if initial_save: self.save_data()
        print(f"DEBUG: Info de paciente {username} añadida/actualizada.")

    # NUEVO MÉTODO AÑADIDO: Eliminar la asociación del paciente con el doctor
    def disassociate_patient(self, patient_username):
        """Elimina la asociación del paciente con el doctor (lo quita de _PATIENT_INFO_DB)."""
        global _PATIENT_INFO_DB
        if patient_username in _PATIENT_INFO_DB:
            del _PATIENT_INFO_DB[patient_username]
            self.save_data() # Persistencia
            print(f"DEBUG: Paciente {patient_username} desasociado (removido de _PATIENT_INFO_DB).")
            return True
        print(f"ADVERTENCIA: Paciente {patient_username} no encontrado en _PATIENT_INFO_DB para desasociar.")
        return False


    # NUEVO MÉTODO: Obtener pacientes que el doctor puede asociar
    def get_unassigned_patients_or_unassigned_to_doctor(self, doctor_username):
        """Devuelve todos los usuarios que son pacientes y que no están asignados 
        a ningún médico o no están asignados al médico actual."""
        unassigned_patients = []
        
        for user_name, user_data in _USER_DB.items():
            if user_data.get('role') == 'paciente':
                patient_info = _PATIENT_INFO_DB.get(user_name)
                
                # Criterio de inclusión:
                # 1. No está en _PATIENT_INFO_DB (paciente nuevo sin asignar diagnóstico/doctor)
                # 2. Está en _PATIENT_INFO_DB, pero no tiene doctor o el doctor no es el actual
                if (patient_info is None or 
                    patient_info.get('doctor_user') is None or 
                    patient_info.get('doctor_user') != doctor_username):
                    
                    # Incluimos información básica para el desplegable
                    unassigned_patients.append({
                        'username': user_name, 
                        'full_name': user_data.get('full_name'),
                        'is_unassigned': patient_info is None or patient_info.get('doctor_user') is None
                    })

        # Para que el doctor.garcia tenga siempre a 'paciente.torn' visible si ya está asociado
        # (Esto es útil si la DB de prueba no es perfecta, pero no es estrictamente necesario si la lógica de arriba funciona)
        # Por simplicidad en la UI, el desplegable mostrará solo los NO ASIGNADOS/NO ASIGNADOS AL DOCTOR.
        
        return unassigned_patients

    def get_all_patients_for_doctor(self, doctor_username):
        # NOTA: Devuelve pacientes que el doctor TIENE asignados.
        assigned_patients = [
            {'username': k, 'full_name': v['full_name']}
            for k, v in _PATIENT_INFO_DB.items()
            if v.get('doctor_user') == doctor_username
        ] 
        # Si no hay pacientes, usa un dummy de prueba si el doctor es dr.garcia
        if not assigned_patients and doctor_username == 'dr.garcia':
             return [{'username': 'paciente.torn', 'full_name': 'Torn Benson'}]
        return assigned_patients

    def save_user_profile(self, username, profile_data, initial_save=True):
        if username in _USER_DB:
            # Asegurar que 'profile' exista antes de actualizar
            if 'profile' not in _USER_DB[username]:
                 _USER_DB[username]['profile'] = {}
            
            # --- CORRECCIÓN CRÍTICA PARA ACTUALIZAR EL NOMBRE COMPLETO ---
            if 'full_name' in profile_data:
                 _USER_DB[username]['full_name'] = profile_data.pop('full_name')

            _USER_DB[username]['profile'].update(profile_data)
            if initial_save: self.save_data()
            print(f"DEBUG: Perfil de {username} guardado.")
        else:
            print(f"ADVERTENCIA: No se puede guardar perfil. Usuario {username} no encontrado.")

    def schedule_appointment(self, data):
        # Asegurarse de que el ID es un string único
        data['id'] = 'appt-' + str(len(_APPOINTMENTS_DB) + 1)
        # Asignar estado inicial a "scheduled"
        data['status'] = data.get('status', 'scheduled') 
        _APPOINTMENTS_DB.append(data)
        self.save_data() # Persistencia
        print(f"DEBUG: Cita {data['id']} agendada.")

    def get_doctor_appointments(self, doctor_username):
        real_apps = [app for app in _APPOINTMENTS_DB if app.get('professional_username') == doctor_username]
        # Si no hay citas reales y es el doctor de prueba, devolver citas de prueba
        if not real_apps and doctor_username == 'dr.garcia':
             return [
                 {
                     'id': 'appt-001',
                     'datetime': (datetime.now() + timedelta(days=7)).isoformat(),
                     'patient_username': 'paciente.torn',
                     'professional_name': 'Dr. Ángel García',
                     'hospital': 'Hospital Central',
                     'office': 'Consultorio 201',
                     'comments': 'Revisión post-quirúrgica y ajuste de plan de rehabilitación.',
                     'status': 'scheduled',
                     'doctor_notes': ''
                 }
             ]
        return real_apps

    def get_patient_appointments(self, patient_username):
        real_apps = [app for app in _APPOINTMENTS_DB if app.get('patient_username') == patient_username]
        if real_apps: return real_apps
        
        # Citas de ejemplo para el paciente si la DB está vacía o sin datos específicos
        now = datetime.now()
        return [
             {
                 'id': 'appt-001',
                 'datetime': (now - timedelta(days=1)).isoformat(),
                 'patient_username': patient_username,
                 'professional_name': 'Dr. Ángel García',
                 'hospital': 'Hospital Central',
                 'office': 'Consultorio 201',
                 'comments': 'Revisión pasada.',
                 'status': 'attended',
                 'doctor_notes': 'El paciente mostró una mejoría notable en la movilidad de la rodilla.'
             },
             {
                 'id': 'appt-002',
                 'datetime': (now + timedelta(days=7)).isoformat(),
                 'patient_username': patient_username,
                 'professional_name': 'Dr. Ángel García',
                 'hospital': 'Hospital Central',
                 'office': 'Consultorio 201',
                 'comments': 'Revisión post-quirúrgica y ajuste de plan de rehabilitación.',
                 'status': 'scheduled', # Pendiente de confirmación del paciente
                 'doctor_notes': ''
             },
             {
                 'id': 'appt-003',
                 'datetime': (now + timedelta(days=14)).isoformat(),
                 'patient_username': patient_username,
                 'professional_name': 'Dr. Ángel García',
                 'hospital': 'Hospital Central',
                 'office': 'Consultorio 202',
                 'comments': 'Seguimiento de terapia.',
                 'status': 'confirmed', # Ya confirmada por el paciente
                 'doctor_notes': ''
             }
           ]

    def get_appointment_by_id(self, appointment_id):
        # Buscar en la lista de citas (citas reales + citas de prueba si las hubiera)
        all_apps = _APPOINTMENTS_DB
        
        # Añadir citas de prueba si no existen citas reales y el ID es uno de prueba
        if not _APPOINTMENTS_DB and (appointment_id == 'appt-001' or appointment_id == 'appt-002' or appointment_id == 'appt-003'):
             all_apps = self.get_patient_appointments('paciente.torn') 

        appt = next((a for a in all_apps if a.get('id') == appointment_id), None)
        
        if appt:
            return appt
            
        # Fallback de datos simulados si la cita no se encuentra (solo para no romper la app si el ID es un dummy antiguo)
        if appointment_id.startswith('appt-'):
             return {
                 'id': appointment_id,
                 'datetime': (datetime.now() + timedelta(days=10, hours=10)).isoformat(),
                 'patient_username': 'paciente.torn',
                 'professional_name': 'Dr. Ángel García',
                 'hospital': 'Hospital Central',
                 'office': 'Consultorio 201',
                 'comments': 'Cita de seguimiento',
                 'status': 'confirmed',
                 'doctor_notes': ''
             }
        return None

    def update_appointment(self, appointment_id, updated_data):
        for appt in _APPOINTMENTS_DB:
            if appt['id'] == appointment_id:
                appt.update(updated_data)
                self.save_data() # Persistencia
                print(f"DEBUG: Cita {appointment_id} actualizada.")
                return
        print(f"ADVERTENCIA: Cita {appointment_id} no encontrada para actualizar.")

    def delete_appointment(self, appointment_id):
        global _APPOINTMENTS_DB
        initial_len = len(_APPOINTMENTS_DB)
        _APPOINTMENTS_DB = [appt for appt in _APPOINTMENTS_DB if appt['id'] != appointment_id]
        if len(_APPOINTMENTS_DB) < initial_len:
            self.save_data() # Persistencia
            print(f"DEBUG: Cita {appointment_id} eliminada.")
            return True
        print(f"ADVERTENCIA: Cita {appointment_id} no encontrada para eliminar.")
        return False

    def get_rodillo_exercises(self):
        return KNEE_EXERCISES

    def record_completed_exercise(self, username, exercise_id, exercise_data):
        if username not in _EXERCISE_HISTORY_DB:
            _EXERCISE_HISTORY_DB[username] = []
        _EXERCISE_HISTORY_DB[username].append(exercise_data)
        self.save_data() # Persistencia
        print(f"DEBUG: Ejercicio {exercise_id} registrado para {username}.")

    def save_specialized_questionnaire(self, username, questionnaire_data):
        if username not in _QUESTIONNAIRE_HISTORY_DB:
            _QUESTIONNAIRE_HISTORY_DB[username] = []
        _QUESTIONNAIRE_HISTORY_DB[username].append(questionnaire_data)
        self.save_data() # Persistencia
        print(f"DEBUG: Cuestionario {questionnaire_data['questionnaire_id']} guardado para {username}.")

    def get_complete_user_data(self, username):
        basic_info = _USER_DB.get(username, {})
        profile = basic_info.get('profile', {})
        patient_info = _PATIENT_INFO_DB.get(username, {})
        
        # Recuperar datos existentes
        questionnaires = _QUESTIONNAIRE_HISTORY_DB.get(username, [])
        exercises = _EXERCISE_HISTORY_DB.get(username, [])
        appointments = [app for app in _APPOINTMENTS_DB if app.get('patient_username') == username]

        # --- CORRECCIÓN --- 
        # Generar datos de simulación para CUALQUIER paciente si no tiene historial.
        # Eliminamos la restricción "if username == 'paciente.torn'"
        
        if not questionnaires and not exercises: 
            today = datetime.now()
            
            # Generar cuestionarios dummy si está vacío
            if not questionnaires:
                questionnaires = [
                    {'questionnaire_title': 'Dolor Rodilla', 'questionnaire_id': 'dolor_rodilla', 'timestamp': (today - timedelta(days=10)).isoformat(), 'responses': {'q1': 7, 'q2': 5, 'q3': 'moderado'}},
                    {'questionnaire_title': 'Dolor Rodilla', 'questionnaire_id': 'dolor_rodilla', 'timestamp': (today - timedelta(days=3)).isoformat(), 'responses': {'q1': 5, 'q2': 3, 'q3': 'leve'}}
                ]
                # Guardamos en la variable global para que persista en esta sesión
                _QUESTIONNAIRE_HISTORY_DB[username] = questionnaires

            # Generar ejercicios dummy si está vacío
            if not exercises:
                exercises = [
                    {'exercise_id': 'ext_rodilla', 'exercise_name': 'Extensión de Rodilla', 'timestamp': (today - timedelta(days=9)).isoformat(), 'duration_seconds': 120, 'sets': 3, 'reps': 10},
                    {'exercise_id': 'flex_rodilla', 'exercise_name': 'Flexión de Rodilla', 'timestamp': (today - timedelta(days=2)).isoformat(), 'duration_seconds': 180, 'sets': 3, 'reps': 12}
                ]
                _EXERCISE_HISTORY_DB[username] = exercises

            # Generar citas dummy si está vacío
            if not appointments:
                appointments = self.get_patient_appointments(username)

        return {
            'basic_info': {'full_name': basic_info.get('full_name', 'N/A'), 'role': basic_info.get('role', 'N/A'), 'member_since': datetime.fromisoformat(basic_info.get('member_since', datetime.now().isoformat())).strftime('%d/%m/%Y')},
            'profile': profile,
            'patient_info': patient_info,
            'questionnaires': questionnaires,
            'exercises': exercises,
            'appointments': appointments
        }

db = DummyDB()
# --------------------------------------------------------------------------
# --- FIN DE DUMMIES ---
# --------------------------------------------------------------------------

# Inicializar base de datos
try:
    db.init_db()
except Exception:
    pass

# Crear aplicación Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

server = app.server

# Estilos y constantes (Se mantienen)
COLORS = {
    'primary': '#1e88e5',
    'secondary': '#2ebf7f',
    'background': '#f6f8fb',
    'card': '#ffffff',
    'text': '#0f172a',
    'muted': '#6b7280'
}
STYLES = {
    'login_container': {
        'maxWidth': '420px','margin': '80px auto','padding': '32px','background': 'white',
        'borderRadius': '16px','boxShadow': '0 10px 30px rgba(2,6,23,0.08)'
    },
    'navbar': {
        'background': 'linear-gradient(135deg, #1e88e5, #2ebf7f)','padding': '16px 24px','color': 'white',
        'borderRadius': '0 0 12px 12px','marginBottom': '24px','boxShadow': '0 4px 12px rgba(30,136,229,0.15)',
        'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'
    },
    'card': {
        'background': COLORS['card'],'borderRadius': '12px','padding': '20px',
        'boxShadow': '0 6px 18px rgba(17,24,39,0.06)','marginBottom': '20px'
    }
}
REHAB_STYLES = {
    'label': {
        'fontWeight': '600',
        'marginBottom': '8px'
    }
}

# REPERTORIO DE EJERCICIOS PARA RODILLA (Se mantienen)
KNEE_EXERCISES = [
      {
          'id': 'ext_rodilla',
          'title': 'Extensión de Rodilla',
          'description': 'Sentado en una silla, extienda completamente la rodilla y mantenga la posición por 5 segundos.',
          'reps': 10,
          'sets': 3,
          'rest_sec': 30,
          'difficulty': 'Principiante',
          'weight': 'Sin peso / 2-5kg',
          'images': ['https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300&h=200&fit=crop'],
          'video_url': 'https://www.youtube.com/embed/example1',
          'muscles': ['Cuádriceps'],
          'instructions': [
              "Siéntese en una silla con la espalda recta y pies apoyados en el suelo",
              "Extienda completamente una pierna hasta que quede recta",
              "Mantenga la posición durante 5 segundos contrayendo el cuádriceps",
              "Baje la pierna lentamente controlando el movimiento",
              "Repita con la otra pierna según las series indicadas"
          ],
          'benefits': "Fortalece el cuádriceps, mejora la estabilidad de la rodilla"
      },
    {
          'id': 'flex_rodilla',
          'title': 'Flexión de Rodilla',
          'description': 'Acostado boca abajo, flexione la rodilla llevando el talón hacia el glúteo.',
          'reps': 12,
          'sets': 3,
          'rest_sec': 30,
          'difficulty': 'Principiante',
          'weight': 'Sin peso / banda elástica',
          'images': ['https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=300&h=200&fit=crop'],
          'video_url': 'https://www.youtube.com/embed/example2',
          'muscles': ['Isquiotibiales'],
          'instructions': [
              "Acuéstese boca abajo en una superficie cómoda",
              "Flexione la rodilla llevando el talón hacia el glúteo",
              "Mantenga la posición durante 3 segundos sintiendo la contracción",
              "Baje la pierna lentamente",
              "Repita con la otra pierna"
          ],
          'benefits': "Fortalece isquiotibiales, mejora flexibilidad"
      },
]

# CUESTIONARIOS ESPECIALIZADOS PARA PACIENTES (Se mantienen)
QUESTIONNAIRES = {
    'dolor_rodilla': {
        'id': 'dolor_rodilla',
        'title': '📋 Cuestionario de Dolor de Rodilla',
        'description': 'Evalúa el nivel de dolor y funcionalidad de la rodilla',
        'questions': [
            {
                'id': 'q1',
                'question': '¿Cómo calificaría su dolor de rodilla en reposo? (0 = sin dolor, 10 = dolor máximo)',
                'type': 'slider',
                'min': 0,
                'max': 10,
                'step': 1
            },
            {
                'id': 'q2',
                'question': '¿Cómo calificaría su dolor de rodilla al caminar? (0 = sin dolor, 10 = dolor máximo)', # Añadido texto
                'type': 'slider',
                'min': 0,
                'max': 10,
                'step': 1
            },
            {
                'id': 'q3',
                'question': '¿El dolor le limita para subir y bajar escaleras?',
                'type': 'radio',
                'options': [
                    {'label': ' Sí, mucho', 'value': 'mucho'},
                    {'label': ' Sí, moderadamente', 'value': 'moderado'},
                    {'label': ' Sí, un poco', 'value': 'poco'},
                    {'label': ' No me limita', 'value': 'nada'}
                ]
            },
            
        ]
    },
    'funcionalidad': {
        'id': 'funcionalidad',
        'title': '📊 Cuestionario de Funcionalidad',
        'description': 'Evalúa la capacidad para realizar actividades diarias',
        'questions': [
            {
                'id': 'q1',
                'question': '¿Puede caminar sin ayuda?',
                'type': 'radio',
                'options': [
                    {'label': ' Sí, sin dificultad', 'value': 'sin_dificultad'},
                    {'label': ' No, necesito ayuda', 'value': 'necesita_ayuda'}
                ]
            },
            {
                'id': 'q2',
                'question': '¿Puede permanecer de pie durante 30 minutos?',
                'type': 'radio',
                'options': [
                    {'label': ' Sí, sin problemas', 'value': 'sin_problemas'},
                    {'label': ' No, duele demasiado', 'value': 'dolor_severo'}
                ]
            },
        ]
    },
}

# --- FUNCIONES AUXILIARES PARA GRÁFICAS ---
def create_questionnaire_plot(questionnaires):
    """Genera dos gráficas independientes para Dolor en Reposo y al Caminar"""
    # Si no hay datos, devolvemos dos gráficas vacías con un mensaje
    if not questionnaires:
        empty = go.Figure().add_annotation(
            text="Sin datos registrados", xref="paper", yref="paper", 
            x=0.5, y=0.5, showarrow=False
        ).update_layout(height=320, template="plotly_white")
        return empty, empty

    data_q1, data_q2 = [], []
    
    for q in questionnaires:
        try:
            ts = datetime.fromisoformat(q['timestamp'])
            # Filtramos solo el cuestionario de dolor de rodilla
            if q.get('questionnaire_id') == 'dolor_rodilla':
                # Pregunta 1: Reposo
                if 'q1' in q['responses']: 
                    data_q1.append({'timestamp': ts, 'Valor': float(q['responses']['q1'])})
                # Pregunta 2: Caminar
                if 'q2' in q['responses']: 
                    data_q2.append({'timestamp': ts, 'Valor': float(q['responses']['q2'])})
        except (ValueError, TypeError): 
            continue

    # Función interna para dar formato consistente a ambas gráficas
    def format_fig(data, title, line_color):
        if not data:
            return go.Figure().add_annotation(text="Pregunta sin respuestas").update_layout(height=320)
        
        df = pd.DataFrame(data).sort_values('timestamp')
        fig = px.line(df, x='timestamp', y='Valor', markers=True, title=title)
        
        # Estética médica
        fig.update_traces(line=dict(width=3, color=line_color), marker=dict(size=8))
        fig.update_layout(
            yaxis=dict(range=[-0.5, 10.5], dtick=1, gridcolor="#f0f0f0"),
            xaxis=dict(gridcolor="#f0f0f0"),
            height=320,
            margin=dict(l=40, r=20, t=60, b=40),
            template="plotly_white",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    # Retornamos la TUPLA de dos figuras
    fig_reposo = format_fig(data_q1, '🔴 Dolor en Reposo', '#ef4444')
    fig_caminar = format_fig(data_q2, '🟠 Dolor al Caminar', '#f59e0b')

    return fig_reposo, fig_caminar

def create_exercise_plot(exercises):
    if not exercises:
        return go.Figure().add_annotation(
            text="No hay registros de ejercicios para graficar.",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font={'color': COLORS['muted']}
        ).update_layout(height=300, margin=dict(t=50, b=50))

    df = pd.DataFrame(exercises)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['duration_seconds'] = pd.to_numeric(df['duration_seconds'], errors='coerce').fillna(0)

    df_pivot = df.groupby(['exercise_name', 'timestamp'])['duration_seconds'].sum().reset_index()

    fig = px.bar(df_pivot, x='timestamp', y='duration_seconds', color='exercise_name',
                      title='Duración de Ejercicios Completados (Segundos)',
                      color_discrete_sequence=px.colors.qualitative.Vivid)

    fig.update_layout(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['card'],
        font_color=COLORS['text'],
        margin=dict(t=50, b=50, l=50, r=20),
        xaxis_title="Fecha de Ejecución",
        yaxis_title="Duración (segundos)",
        barmode='stack',
        height=400
    )

    return fig

# Función auxiliar para crear la figura inicial del ECG (NUEVA)
def create_initial_ecg_figure(filepath="data/ecg_example.csv"):
    """Crea la figura inicial del ECG sin errores"""
    try:
        t, ecg, bpm = load_ecg_and_compute_bpm(filepath)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=t, 
            y=ecg, 
            mode="lines", 
            line=dict(color="green", width=2),
            name="ECG"
        ))
        
        fig.update_layout(
            title="✅ Señal ECG de Ritmo Normal",
            xaxis_title="Tiempo (s)",
            yaxis_title="Amplitud (mV)",
            plot_bgcolor=COLORS['background'],
            paper_bgcolor=COLORS['card'],
            font_color=COLORS['text'],
            height=350,
            margin=dict(l=40,r=20,t=50,b=40),
            template="plotly_white",
            showlegend=False
        )
        
        bpm_text = f"❤️ Frecuencia cardíaca promedio: {bpm:.1f} BPM"
        
    except Exception as e:
        print(f"Error en create_initial_ecg_figure: {e}")
        # Figura de placeholder
        fig = go.Figure()
        fig.add_annotation(
            text="Cargando datos de ECG...",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font={'color': COLORS['muted'], 'size': 14}
        )
        fig.update_layout(
            title="Monitorización ECG",
            xaxis_title="Tiempo (s)",
            yaxis_title="Amplitud (mV)",
            height=350,
            template="plotly_white"
        )
        bpm_text = "⏳ Esperando datos..."
    
    return fig, bpm_text


# --- MODALES (Se mantienen) ---

def get_exercise_execution_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("💪 Ejecución con Biofeedback")),
            dbc.ModalBody([
                html.Div(id="exercise-execution-content"),
                html.Hr(),
                # Cambiamos width de 6 a 12 para que estén una debajo de otra
                dbc.Row([
                dbc.Col([
                    html.H5("❤️ ECG (Frecuencia Cardíaca)", className="text-center"),
                    dcc.Graph(id='live-ecg-graph', config={'displayModeBar': False}, style={'height': '300px'}),
                    html.Div(id='ecg-status-msg', className="text-center fw-bold")
                ], width=12, className="mb-4"),
                dbc.Col([
                    html.H5("📐 IMU (Ángulo de Rodilla)", className="text-center"),
                    dcc.Graph(id='live-imu-graph', config={'displayModeBar': False}, style={'height': '300px'}),
                    html.Div(id='imu-status-msg', className="text-center fw-bold")
                ], width=12),
            ]),
            ]),
            dbc.ModalFooter([
                dbc.Button("✅ Terminar", id="finish-exercise-btn", n_clicks=0, color="success"),
                dbc.Button("❌ Cancelar", id="cancel-exercise-btn", n_clicks=0, color="danger")
            ]),
        ],
        id="exercise-execution-modal",
        is_open=False,
        size="lg" # "lg" es mejor para apilado vertical que "xl"
    )

def get_exercise_survey_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("📊 Cuestionario Post-Ejercicio")),
            dbc.ModalBody([
                html.Div(id="exercise-survey-content")
            ]),
            dbc.ModalFooter([
                dbc.Button("📤 Enviar Respuestas", id="submit-exercise-survey", n_clicks=0,
                           style={'background': COLORS['secondary'], 'border': 'none'}),
            ]),
        ],
        id="exercise-survey-modal",
        is_open=False,
        size="lg"
    )

def get_schedule_appointment_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("📅 Agendar Nueva Cita")),
            dbc.ModalBody([
                html.Label("👤 Seleccionar Paciente"),
                dcc.Dropdown(id='appointment-patient-select', options=[], placeholder="Selecciona un paciente..."),

                html.Label("📅 Fecha", style={'marginTop': '15px'}),
                dcc.DatePickerSingle(id='appointment-date', date=datetime.now().date()),

                html.Label("⏰ Hora", style={'marginTop': '15px'}),
                dcc.Dropdown(id='appointment-time', options=[
                    {'label': f'{h:02d}:00', 'value': f'{h:02d}:00'} for h in range(8, 20)
                ], placeholder="Selecciona hora..."),

                html.Label("🏥 Hospital", style={'marginTop': '15px'}),
                dcc.Input(id='appointment-hospital', type='text', placeholder='Nombre del hospital', style={'width': '100%'}),

                html.Label("🚪 Consultorio", style={'marginTop': '15px'}),
                dcc.Input(id='appointment-office', type='text', placeholder='Número de consultorio', style={'width': '100%'}),

                html.Label("📝 Comentarios", style={'marginTop': '15px'}),
                dcc.Textarea(id='appointment-comments', placeholder='Comentarios adicionales...', style={'width': '100%', 'height': '80px'})
            ]),
            dbc.ModalFooter([
                dbc.Button("✅ Confirmar Cita", id="confirm-appointment-btn", color="primary"),
                dbc.Button("❌ Cancelar", id="cancel-appointment-btn", color="secondary"),
            ]),
        ],
        id="schedule-appointment-modal",
        is_open=False,
        size="lg"
    )

def get_edit_appointment_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("✏️ Modificar Cita")),
            dbc.ModalBody(html.P("La edición de citas se ha deshabilitado para el doctor, por favor cancele y re-agende si es necesario.", className="alert alert-warning")),
            dbc.ModalFooter([
                dbc.Button("❌ Cerrar", id="cancel-edit-appt-btn", color="secondary"), 
            ]),
        ],
        id="edit-appointment-modal",
        is_open=False,
        size="lg"
    )

def get_edit_profile_modal():
    """Modal para editar la información de perfil y médica del usuario."""
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("✏️ Actualizar Mi Perfil")),
            dbc.ModalBody(id="edit-profile-modal-content"), # Contenido cargado por callback
            dbc.ModalFooter([
                html.Div(id='edit-profile-feedback'), # Feedback local de guardado
                dbc.Button("✅ Guardar Cambios", id="save-profile-btn", color="primary", className="me-2"),
                dbc.Button("❌ Cancelar", id="cancel-profile-btn", color="secondary"),
            ]),
        ],
        id="edit-profile-modal",
        is_open=False,
        size="lg"
    )


# --- LAYOUTS ---
def get_login_layout():
    return html.Div([
        html.Div([
            html.H2("🏥 RehabiDesk", style={'textAlign': 'center', 'color': COLORS['primary'], 'marginBottom': '8px'}),
            html.P("Sistema de Rehabilitación Integral", style={'textAlign': 'center', 'color': COLORS['muted'], 'marginBottom': '32px'}),
            
            html.Label("👤 Usuario", style={'fontWeight': '600', 'marginBottom': '8px'}),
            # 1. Corrección texto cortado: boxSizing
            dcc.Input(id='login-username', type='text', placeholder='Ingresa tu usuario (ej: dr.garcia)', 
                      style={'width': '100%', 'padding': '12px', 'boxSizing': 'border-box', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '16px'}),
            
            html.Label("🔒 Contraseña", style={'fontWeight': '600', 'marginBottom': '8px'}),
            
            # 2. Corrección del ojo: Contenedor Flex para alinear Input + Botón
            html.Div([
                dcc.Input(id="login-password", type="password", placeholder="Ingresa tu contraseña",
                          style={'flex': '1', 'padding': '12px', 'boxSizing': 'border-box', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px 0 0 8px', 'outline': 'none'}),
                html.Button("👁️", id="password-eye", n_clicks=0, 
                            style={'padding': '0 15px', 'background': 'white', 'border': f'1px solid {COLORS["muted"]}', 'borderLeft': 'none', 'borderRadius': '0 8px 8px 0', 'cursor': 'pointer', 'fontSize': '20px', 'display': 'flex', 'alignItems': 'center'})
            ], style={'display': 'flex', 'width': '100%', 'marginBottom': '24px'}),
            
            html.Label("🎭 Rol", style={'fontWeight': '600', 'marginBottom': '8px'}),
            dcc.Dropdown(
                id='login-role',
                options=[
                    {'label': '👨‍⚕️ Médico', 'value': 'medico'},
                    {'label': '🧑‍🦽 Paciente', 'value': 'paciente'}
                ],
                placeholder='Selecciona tu rol',
                style={'marginBottom': '24px'}
            ),
            
            html.Button('🚀 Iniciar Sesión', id='login-button', n_clicks=0,
                        style={'width': '100%', 'padding': '12px', 'background': COLORS['primary'], 'color': 'white', 
                               'border': 'none', 'borderRadius': '8px', 'cursor': 'pointer', 'fontWeight': '600', 'marginBottom': '16px'}),
            
            html.Div(id='login-feedback'),
            
            html.Hr(style={'margin': '24px 0'}),
            
            html.P("¿No tienes cuenta?", style={'textAlign': 'center', 'color': COLORS['muted']}),
            dcc.Link('📝 Regístrate aquí', href='/register', 
                     style={'textAlign': 'center', 'display': 'block', 'color': COLORS['secondary'], 'textDecoration': 'none', 'fontWeight': '600'})
        ], style=STYLES['login_container'])
    ], style={'background': COLORS['background'], 'minHeight': '100vh', 'padding': '20px'})



def get_register_layout():
    return html.Div([
        html.Div([
            html.H2("📝 Registro Completo", style={'textAlign': 'center', 'color': COLORS['primary'], 'marginBottom': '8px'}),
            html.P("Crea tu cuenta en RehabiDesk - Completa tu información médica", style={'textAlign': 'center', 'color': COLORS['muted'], 'marginBottom': '32px'}),
            
            html.H4("👤 Información de Cuenta", style={'color': COLORS['primary'], 'marginBottom': '16px', 'borderBottom': f'2px solid {COLORS["primary"]}', 'paddingBottom': '8px'}),
            
            html.Label("👤 Nombre Completo *", style=REHAB_STYLES['label']),
            dcc.Input(id='register-fullname', type='text', placeholder='Ingresa tu nombre completo', 
                      style={'width': '100%', 'padding': '12px', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '16px'}),
            
            html.Label("👤 Usuario *", style=REHAB_STYLES['label']),
            dcc.Input(id='register-username', type='text', placeholder='Crea un nombre de usuario', 
                      style={'width': '100%', 'padding': '12px', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '16px'}),
            
            html.Label("🔒 Contraseña *", style=REHAB_STYLES['label']),
            dcc.Input(id='register-password', type='password', placeholder='Crea una contraseña segura', 
                      style={'width': '100%', 'padding': '12px', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '16px'}),
            
            html.Label("🎭 Rol *", style=REHAB_STYLES['label']),
            dcc.Dropdown(
                id='register-role',
                options=[
                    {'label': '👨‍⚕️ Médico', 'value': 'medico'},
                    {'label': '🧑‍🦽 Paciente', 'value': 'paciente'}
                ],
                placeholder='Selecciona tu rol',
                style={'marginBottom': '24px'}
            ),
            
            html.H4("📋 Información Personal", style={'color': COLORS['primary'], 'marginBottom': '16px', 'borderBottom': f'2px solid {COLORS["primary"]}', 'paddingBottom': '8px', 'marginTop': '32px'}),
            
            html.Label("📧 Email *", style=REHAB_STYLES['label']),
            dcc.Input(id='register-email', type='email', placeholder='tu.email@ejemplo.com', 
                      style={'width': '100%', 'padding': '12px', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '16px'}),
            
            html.Label("📞 Teléfono *", style=REHAB_STYLES['label']),
            dcc.Input(id='register-phone', type='tel', placeholder='+34 600 000 000 (Formato: +XX XXX XXX XXX)', 
                      style={'width': '100%', 'padding': '12px', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '16px'}),
            
            html.Label("🏠 Dirección", style=REHAB_STYLES['label']),
            dcc.Input(id='register-address', type='text', placeholder='Calle, número, ciudad, código postal', 
                      style={'width': '100%', 'padding': '12px', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '16px'}),
            
            html.Label("🆔 DNI/NIE *", style=REHAB_STYLES['label']),
            dcc.Input(id='register-dni', type='text', placeholder='12345678X o Y0000000A', 
                      style={'width': '100%', 'padding': '12px', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '16px'}),
            
            html.Label("🎂 Fecha de Nacimiento *", style=REHAB_STYLES['label']),
            dcc.DatePickerSingle(
                id='register-birthdate',
                min_date_allowed=datetime(1900, 1, 1),
                max_date_allowed=datetime.today(),
                initial_visible_month=datetime(1990, 1, 1),
                style={'width': '100%', 'marginBottom': '16px'}
            ),
            
            html.Div(id='medical-info-section', children=[
                html.H4("🏥 Información Médica", style={'color': COLORS['primary'], 'marginBottom': '16px', 'borderBottom': f'2px solid {COLORS["primary"]}', 'paddingBottom': '8px', 'marginTop': '32px'}),
                
                html.Label("🩸 Tipo de Sangre", style=REHAB_STYLES['label']),
                dcc.Dropdown(
                    id='register-blood-type',
                    options=[
                        {'label': 'A+', 'value': 'A+'},
                        {'label': 'A-', 'value': 'A-'},
                        {'label': 'B+', 'value': 'B+'},
                        {'label': 'B-', 'value': 'B-'},
                        {'label': 'AB+', 'value': 'AB+'},
                        {'label': 'AB-', 'value': 'AB-'},
                        {'label': 'O+', 'value': 'O+'},
                        {'label': 'O-', 'value': 'O-'}
                    ],
                    placeholder='Selecciona tu tipo de sangre',
                    style={'marginBottom': '16px'}
                ),
                
                html.Label("⚠️ Alergias", style=REHAB_STYLES['label']),
                dcc.Textarea(id='register-allergies', placeholder='Lista de alergias conocidas (medicamentos, alimentos, etc.)', 
                              style={'width': '100%', 'height': '80px', 'borderRadius': '8px', 'padding': '12px', 'marginBottom': '16px'}),
                
                html.Label("💊 Medicamentos Actuales", style=REHAB_STYLES['label']),
                dcc.Textarea(id='register-medications', placeholder='Medicamentos que tomas actualmente', 
                              style={'width': '100%', 'height': '80px', 'borderRadius': '8px', 'padding': '12px', 'marginBottom': '16px'}),
                
                html.Label("📋 Condiciones Médicas", style=REHAB_STYLES['label']),
                dcc.Textarea(id='register-conditions', placeholder='Enfermedades crónicas o condiciones médicas relevantes', 
                              style={'width': '100%', 'height': '80px', 'borderRadius': '8px', 'padding': '12px', 'marginBottom': '16px'}),
            ]),
            
            html.H4("🚨 Contacto de Emergencia", style={'color': COLORS['primary'], 'marginBottom': '16px', 'borderBottom': f'2px solid {COLORS["primary"]}', 'paddingBottom': '8px', 'marginTop': '32px'}),
            
            html.Label("👤 Nombre del Contacto *", style=REHAB_STYLES['label']),
            dcc.Input(id='register-emergency-contact', type='text', placeholder='Nombre completo del contacto de emergencia', 
                      style={'width': '100%', 'padding': '12px', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '16px'}),
            
            html.Label("📞 Teléfono del Contacto *", style=REHAB_STYLES['label']),
            dcc.Input(id='register-emergency-phone', type='tel', placeholder='+34 600 000 000 (Formato: +XX XXX XXX XXX)', 
                      style={'width': '100%', 'padding': '12px', 'border': f'1px solid {COLORS["muted"]}', 'borderRadius': '8px', 'marginBottom': '32px'}),
            
            html.Button('✅ Registrar Cuenta Completa', id='register-button', n_clicks=0,
                        style={'width': '100%', 'padding': '14px', 'background': COLORS['secondary'], 'color': 'white', 
                               'border': 'none', 'borderRadius': '10px', 'cursor': 'pointer', 'fontWeight': '600', 'marginBottom': '16px', 'fontSize': '16px'}),
            
            html.Div(id='register-feedback'),
            
            html.Hr(style={'margin': '24px 0'}),
            
            html.P("¿Ya tienes cuenta?", style={'textAlign': 'center', 'color': COLORS['muted']}),
            dcc.Link('🚀 Inicia sesión aquí', href='/login', 
                     style={'textAlign': 'center', 'display': 'block', 'color': COLORS['primary'], 'textDecoration': 'none', 'fontWeight': '600'})
        ], style=STYLES['login_container'])
    ], style={'background': COLORS['background'], 'minHeight': '100vh', 'padding': '20px'})

# --- NAV BAR ---
def get_user_navbar(role_symbol, full_name, role_name, current_search=""): 
    
    def get_full_href(path):
        if not path or path.startswith('http'):
            return path
        path_no_search = urlparse(path).path
        return f"{path_no_search}{current_search}"
    
    user_menu_items = [
        dbc.DropdownMenuItem("👤 Ver Mis Datos", id="nav-my-data-btn", n_clicks=0, href=get_full_href("/my-data")),
    ]
    
    if 'medico' in role_name.lower():
        is_doctor_dashboard = role_name.lower() == 'panel médico'

        if not is_doctor_dashboard:
            user_menu_items.extend([
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("🔬 Datos del Paciente", id="nav-patient-viewer-btn", n_clicks=0, href=get_full_href("/patient-data-viewer")),
                # Usamos un ID único para el botón del menú desplegable para evitar conflictos.
                dbc.DropdownMenuItem("📅 Agendar Cita", id="schedule-appointment-btn-modal-trigger", n_clicks=0),
                dbc.DropdownMenuItem("📅 Ver Citas", id="nav-view-appointments-btn", n_clicks=0, href=get_full_href("/view-appointments")),
            ])
    
    if 'paciente' in role_name.lower():
        user_menu_items.extend([
            dbc.DropdownMenuItem("📊 Ver Cuestionarios", id="nav-my-questionnaires-btn", n_clicks=0, href=get_full_href("/my-questionnaires")),
            dbc.DropdownMenuItem("📅 Ver Citas", id="nav-view-patient-appointments-btn", n_clicks=0, href=get_full_href("/view-patient-appointments"))
        ])

    user_menu_items.append(dbc.DropdownMenuItem("🚪 Cerrar Sesión", id="logout-button", style={'color': 'red'}))
    
    user_menu = dbc.DropdownMenu(
        user_menu_items,
        label=f"Hola, {full_name.split()[0]}",
        color="light",
        className="me-1",
        nav=True,
        style={'fontWeight':'600'}
    )
    
    return html.Div([
        html.Div([
            html.H3(f"{role_symbol} {full_name}", style={'color':'white', 'margin': '0'}),
            html.P(role_name, style={'color':'white','opacity':'0.9', 'margin': '0'})
        ]),
        user_menu
    ], style=STYLES['navbar'])

# --- DASHBOARDS ---

def get_patient_dashboard(username, full_name, current_search=""): 
    initial_ecg_fig, initial_bpm_text = create_initial_ecg_figure()
    
    try:
        patient_data = db.get_complete_user_data(username) or {}
        exercises = db.get_rodillo_exercises() or KNEE_EXERCISES
    except Exception:
        patient_data = {}
        exercises = KNEE_EXERCISES
    
    questionnaires_data = patient_data.get('questionnaires', [])
    exercises_data = patient_data.get('exercises', [])
    
    # --- CAMBIO CLAVE: create_questionnaire_plot ahora devuelve dos figuras ---
    fig_q1, fig_q2 = create_questionnaire_plot(questionnaires_data)
    exercise_fig = create_exercise_plot(exercises_data)

    # Tarjeta de citas pendientes
    appointments_card = html.Div([
        html.H4("📅 Mis Citas Pendientes", style={'color':COLORS['primary'], 'marginBottom': '15px'}),
        html.Div(id='patient-appointments-list') 
    ], style=STYLES['card'])

    # Grid de ejercicios
    exercise_grid = html.Div([
        html.H4('💪 Ejercicios de Rodilla', style={'color':COLORS['primary'], 'marginBottom': '20px'}),
        html.P("Selecciona un ejercicio para comenzar:", style={'color': COLORS['muted'], 'marginBottom': '20px'}),
        html.Div(
            [
                html.Div([
                    html.Img(
                        src=ex['images'][0],
                        style={
                            'width': '100%',
                            'height': '150px',
                            'objectFit': 'cover',
                            'borderRadius': '8px',
                            'marginBottom': '10px',
                            'cursor': 'pointer'
                        },
                        id={'type': 'exercise-image', 'index': ex['id']}
                    ),
                    html.H6(ex['title'], style={'marginBottom': '5px', 'color': COLORS['text']}),
                    html.P(f"💪 {ex['difficulty']}", style={'color': COLORS['muted'], 'fontSize': '0.8em', 'marginBottom': '5px'}),
                    html.P(f"📊 {ex['sets']} series × {ex['reps']} repes", style={'color': COLORS['muted'], 'fontSize': '0.8em', 'marginBottom': '10px'}),
                    html.Button(
                        '▶️ Iniciar Ejercicio',
                        id={'type': 'start-exercise-btn', 'index': ex['id']},
                        n_clicks=0,
                        style={
                            'width': '100%',
                            'padding': '8px',
                            'background': COLORS['primary'],
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '6px',
                            'cursor': 'pointer',
                            'fontSize': '0.9em'
                        }
                    )
                ], style={
                    'background': 'white',
                    'padding': '15px',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'textAlign': 'center',
                    'transition': 'transform 0.2s',
                    ':hover': {
                        'transform': 'translateY(-2px)'
                    }
                }) for ex in exercises
            ],
            style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(auto-fill, minmax(250px, 1fr))',
                'gap': '20px',
                'marginBottom': '20px'
            }
        )
    ], style=STYLES['card'])

    return html.Div([
        get_user_navbar("🧑‍🦽", full_name, "Panel Paciente", current_search), 

        html.Div([
            # Columna izquierda: Cuestionarios y Citas
            html.Div([
                html.Div([
                    html.H4("📝 Cuestionarios Especializados", style={'color':COLORS['primary'], 'marginBottom': '15px'}),
                    html.P("Complete estos cuestionarios para evaluar su progreso:", style={'color': COLORS['muted'], 'marginBottom': '15px'}),
                    dcc.Dropdown(
                        id='questionnaire-select',
                        options=[
                            {'label': QUESTIONNAIRES['dolor_rodilla']['title'], 'value': 'dolor_rodilla'},
                            {'label': QUESTIONNAIRES['funcionalidad']['title'], 'value': 'funcionalidad'},
                        ],
                        placeholder='Seleccione un cuestionario...',
                        style={'marginBottom': '15px'}
                    ),
                    html.Div(id='selected-questionnaire-content'),
                    html.Div(id='questionnaire-submission-feedback', style={'marginTop': '15px'})
                ], style=STYLES['card']),

                appointments_card,
            ], style={'flex': 1, 'minWidth': '320px'}),

            # Columna derecha: Gráficas y Ejercicios
            html.Div([
                # --- NUEVA TARJETA DE EVOLUCIÓN DEL DOLOR (Doble Gráfica) ---
                html.Div([
                    html.H4("📈 Evolución del Dolor", style={'color':COLORS['primary'], 'marginBottom': '15px'}),
                    dbc.Row([
                        dbc.Col(dcc.Graph(id="questionnaire-q1-graph", figure=fig_q1, config={'displayModeBar': False}), width=12, lg=6),
                        dbc.Col(dcc.Graph(id="questionnaire-q2-graph", figure=fig_q2, config={'displayModeBar': False}), width=12, lg=6),
                    ]),
                ], style=STYLES['card']),

                html.Div([
                    html.H4("📊 Progreso de Ejecución de Ejercicios", style={'color':COLORS['primary'], 'marginBottom': '15px'}),
                    dcc.Graph(id="exercise-history-graph", figure=exercise_fig),
                ], style=STYLES['card']),
                
                html.Div([
                    html.H4("❤️ Monitorización ECG en Tiempo Real", style={'color':COLORS['primary'], 'marginBottom': '15px'}),
                    dcc.Graph(id="ecg-graph", config={'displayModeBar': False}),
                    html.Div(id="bpm-output", className="mt-2 fw-bold", style={'color': COLORS['secondary']}),
                ], style=STYLES['card']),

                exercise_grid,
            ], style={'flex': 2, 'minWidth': '400px'})
        ], style={'display': 'flex', 'gap': '20px', 'padding': '24px', 'flexWrap': 'wrap', 'alignItems': 'flex-start'}),

        dcc.Store(id='current-patient-username', data=username),
        dcc.Store(id='available-exercises', data=exercises),
        dcc.Store(id='current-exercise-id', data=None),
        dcc.Store(id='exercise-start-time', data=None),
        get_exercise_execution_modal(),
        get_exercise_survey_modal(),
    ])

def get_doctor_dashboard(username, full_name, current_search=""): 
    
    # NUEVA ESTRUCTURA PARA ASOCIAR PACIENTES
    patient_management_card = html.Div([
        html.H4("👥 Asociación de Pacientes", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
        
        html.H5("🔗 Asociar Paciente Existente", style={'marginBottom': '15px'}),
        html.P("Selecciona un paciente no asignado o reasigna uno a tu cargo:", style={'color': COLORS['muted'], 'fontSize': '0.9em'}),
        
        html.Label("👤 Seleccionar Paciente"),
        dcc.Dropdown(
            id='unassigned-patient-select',
            placeholder='Buscar paciente por nombre o usuario...',
            options=[], # Se llena por callback
            style={'width': '100%', 'marginBottom': '10px'}
        ),
        
        html.Label("🏥 Diagnóstico (Si es paciente nuevo)"),
        dcc.Input(id='patient-diagnosis-input', type='text', placeholder='Diagnóstico inicial (ej: Lesión de rodilla)', 
                  style={'width': '100%', 'marginBottom': '10px'}),
        
        html.Button('✅ Asociar Paciente', id='associate-patient-button', n_clicks=0, 
                        style={'width': '100%', 'padding': '10px', 'background': COLORS['secondary'], 'color': 'white', 'border': 'none', 'borderRadius': '6px', 'marginTop': '15px'}),
        
        html.Div(id='associate-patient-feedback', style={'marginTop': '15px'})
    ], style=STYLES['card'])
    
    # NUEVA ESTRUCTURA PARA ELIMINAR/DESASOCIAR PACIENTES
    disassociate_patient_card = html.Div([
        html.H4("🗑️ Desasociar/Eliminar Paciente", style={'color': 'red', 'marginBottom': '20px'}),
        
        html.P("Selecciona un paciente para removerlo de tu lista de pacientes asignados. El paciente seguirá existiendo, pero ya no estará bajo tu supervisión.", style={'color': COLORS['muted'], 'fontSize': '0.9em'}),
        
        html.Label("👤 Seleccionar Paciente Asignado"),
        dcc.Dropdown(
            id='assigned-patient-select-disassociate',
            placeholder='Buscar paciente asignado por nombre o usuario...',
            options=[], # Se llena por callback
            style={'width': '100%', 'marginBottom': '15px'}
        ),
        
        dbc.Button('🗑️ Eliminar Paciente Asignado', id='disassociate-patient-button', n_clicks=0, 
                             color='danger', style={'width': '100%', 'padding': '10px', 'borderRadius': '6px', 'marginTop': '10px'}),
        
        html.Div(id='disassociate-patient-feedback', style={'marginTop': '15px'})
    ], style=STYLES['card'])

    
    doctor_navigation_card = html.Div([
        html.H4("⚡ Navegación Rápida", style={'color': COLORS['primary'], 'marginBottom': '20px', 'textAlign': 'center'}),
        dbc.Row([
            dbc.Col(
                dbc.Button("🔬 Visor de Pacientes", id="nav-patient-viewer-btn",
           href=f"/patient-data-viewer{current_search}", color="primary", className="w-100", size="lg")
            ),
            dbc.Col(
                dbc.Button("📅 Ver Citas", id="nav-view-appointments-btn", # Cambiar dash- por nav-
           href=f"/view-appointments{current_search}", color="info", className="w-100", size="lg")
            ),
            dbc.Col(
                # Este botón usa n_clicks para abrir un modal. Debe tener un Input fantasma.
                dbc.Button("➕ Agendar Cita", id="schedule-appointment-btn", n_clicks=0, color="success", className="w-100", size="lg"),
                width=12, lg=4, style={'marginBottom': '15px'}
            ),
        ], className="mb-4"),
        # NUEVO DIV PARA FEEDBACK DE AGENDAMIENTO DE CITA
        html.Div(id='appointment-schedule-feedback', style={'marginBottom': '15px'}),
        html.P("Utiliza el visor para ver el historial y progreso de tus pacientes.", style={'color': COLORS['muted'], 'textAlign': 'center', 'marginTop': '10px'})
    ], style=STYLES['card'])

    return html.Div([
        get_user_navbar("👨‍⚕️", full_name, "Panel Médico", current_search), 
        
        html.Div([
            dbc.Row([
                dbc.Col([
                    doctor_navigation_card, 
                    
                    patient_management_card, # Nuevo/Modificado panel de gestión
                    
                ], width=12, lg=6, className="mx-auto"), 
                
                # NUEVA COLUMNA PARA ELIMINACIÓN
                dbc.Col([
                    disassociate_patient_card,
                ], width=12, lg=6, className="mx-auto"),
                
            ], className="g-4"),
        ], className="g-4", style={'padding': '24px'}),
        
        dcc.Store(id='current-user-data', data={'username': username, 'full_name': full_name, 'role': 'medico'}),
        get_schedule_appointment_modal(),
        # IMPORTANTE: Se incluye el modal de edición/eliminación solo en get_view_appointments_layout
    ])

def get_user_data_layout(username, full_name, role, current_search=""): 
    try:
        user_data = db.get_complete_user_data(username)
    except Exception as e:
        print(f"Error cargando datos de usuario dummy: {e}")
        user_data = {
            'basic_info': {'full_name': full_name, 'role': role, 'member_since': datetime.now().strftime('%d/%m/%Y')},
            'profile': {'email': 'test@example.com', 'phone': '666-000-000', 'dni': '12345678X', 'birth_date': '1980-01-01', 'emergency_contact': 'Familiar', 'emergency_phone': '666-111-111'},
            'patient_info': {'diagnosis': 'Lesión de ligamento cruzado anterior'},
            'questionnaires': [{'questionnaire_title': 'Dolor Rodilla', 'timestamp': '2023-11-20T10:00:00', 'responses': {'q1': 8, 'q2': 5, 'q3': 'moderado'}}]
        }
    
    return html.Div([
        get_user_navbar("👤", full_name, f"Mis Datos - {role.capitalize()}", current_search), 
        
        html.Div([
            dbc.Row([
                dbc.Col(
                    dbc.Button("← Volver al Dashboard", id="nav-dashboard-btn", href=f"/{current_search}", color="primary", className="me-3"),
                    width="auto"
                ),
                dbc.Col(
                    # BOTÓN DE ACTIVACIÓN DEL MODAL
                    dbc.Button("✏️ Actualizar Datos", id="open-edit-profile-modal-btn", n_clicks=0, color="warning"),
                    width="auto"
                ),
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.H4("📋 Información Personal", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
                        
                        dbc.Row([
                            dbc.Col([
                                html.P([html.Strong("👤 Nombre: "), user_data.get('basic_info', {}).get('full_name', full_name)]),
                                html.P([html.Strong("🎭 Rol: "), user_data.get('basic_info', {}).get('role', role)]),
                                html.P([html.Strong("📧 Email: "), user_data.get('profile', {}).get('email', 'No especificado')]),
                                html.P([html.Strong("📞 Teléfono: "), user_data.get('profile', {}).get('phone', 'No especificado')]),
                            ], width=6),
                            dbc.Col([
                                html.P([html.Strong("🆔 DNI: "), user_data.get('profile', {}).get('dni', 'No especificado')]),
                                html.P([html.Strong("🎂 Fecha Nacimiento: "), user_data.get('profile', {}).get('birth_date', 'No especificado')]),
                                html.P([html.Strong("🏠 Dirección: "), user_data.get('profile', {}).get('address', 'No especificado')]),
                                html.P([html.Strong("📅 Miembro desde: "), user_data.get('basic_info', {}).get('member_since', 'No disponible')]),
                            ], width=6)
                        ])
                    ], style=STYLES['card']),
                    
                    html.Div([
                        html.H4("🏥 Información Médica", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
                        
                        dbc.Row([
                            dbc.Col([
                                html.P([html.Strong("📝 Diagnóstico: "), user_data.get('patient_info', {}).get('diagnosis', 'No especificado')]),
                                html.P([html.Strong("👨‍⚕️ Médico: "), user_data.get('patient_info', {}).get('doctor_user', 'No asignado')]),
                                html.P([html.Strong("🩸 Tipo de Sangre: "), user_data.get('profile', {}).get('blood_type', 'No especificado')]),
                            ], width=6),
                            dbc.Col([
                                html.P([html.Strong("⚠️ Alergias: "), user_data.get('profile', {}).get('allergies', 'Ninguna especificada')]),
                                html.P([html.Strong("💊 Medicamentos: "), user_data.get('profile', {}).get('current_medications', 'Ninguno especificado')]),
                                html.P([html.Strong("📋 Condiciones: "), user_data.get('profile', {}).get('medical_conditions', 'Ninguna especificada')]),
                            ], width=6)
                        ])
                    ], style=STYLES['card']) if role == 'paciente' else None,
                    
                    html.Div([
                        html.H4("🚨 Contacto de Emergencia", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
                        
                        html.P([html.Strong("👤 Contacto: "), user_data.get('profile', {}).get('emergency_contact', 'No especificado')]),
                        html.P([html.Strong("📞 Teléfono: "), user_data.get('profile', {}).get('emergency_phone', 'No especificado')]),
                    ], style=STYLES['card']),
                    
                ], style={'flex': 1, 'minWidth': '400px'}),
                
                html.Div([
                    # Historial de cuestionarios
                    html.Div([
                        html.H4("📊 Historial de Cuestionarios", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
                        
                        html.Div([
                            html.Div([
                                html.H5(f"📋 {q.get('questionnaire_title', 'Cuestionario')}", 
                                                style={'color': COLORS['primary'], 'marginBottom': '8px', 'fontSize': '16px'}),
                                html.P(f"🕒 {q.get('timestamp', 'Fecha no disponible')}", 
                                                style={'color': COLORS['muted'], 'fontSize': '14px', 'marginBottom': '10px'}),
                                
                                html.Ul([
                                    html.Li([
                                        html.Strong(f"{key.replace('_', ' ').title()}: "),
                                        html.Span(str(value))
                                    ], style={'marginBottom': '4px', 'fontSize': '13px', 'color': COLORS['text']})
                                    for key, value in q.get('responses', {}).items()
                                ], style={'paddingLeft': '20px'}),
                                
                                html.Hr(style={'margin': '15px 0'})
                            ]) for q in user_data.get('questionnaires', [])[:10]
                        ]) if user_data.get('questionnaires') else html.P("📭 No hay cuestionarios completados.", 
                                                                    style={'textAlign': 'center', 'color': COLORS['muted'], 'padding': '20px'})
                    ], style=STYLES['card']),

                    # Historial de ejercicios
                    html.Div([
                        html.H4("💪 Historial de Ejercicios", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
                        
                        html.Div([
                            html.Div([
                                html.P([
                                    html.Strong(f"Ejercicio: "),
                                    html.Span(ex.get('exercise_name', ex['exercise_id'])),
                                    html.Br(),
                                    html.Strong(f"Fecha: "),
                                    html.Span(ex['timestamp']),
                                    html.Br(),
                                    html.Strong(f"Series: "),
                                    html.Span(f"{ex.get('sets', 'N/A')} × {ex.get('reps', 'N/A')} repeticiones"),
                                    html.Br(),
                                    html.Strong(f"Duración: "),
                                    html.Span(f"{ex['duration_seconds']} segundos" if ex['duration_seconds'] else "No registrada")
                                ], style={'marginBottom': '15px', 'padding': '10px', 'background': '#f8f9fa', 'borderRadius': '8px'})
                            ]) for ex in user_data.get('exercises', [])[:5]
                        ]) if user_data.get('exercises') else html.P("📭 No hay ejercicios registrados.", 
                                                                    style={'textAlign': 'center', 'color': COLORS['muted'], 'padding': '20px'})
                    ], style=STYLES['card']),
                    
                ], style={'flex': 1, 'minWidth': '500px'}) if role == 'paciente' else None,
                
            ], style={'display': 'flex', 'gap': '20px', 'padding': '24px', 'flexWrap': 'wrap', 'alignItems': 'flex-start'}),
            
            dcc.Store(id='user-complete-data', data=user_data)
        ]),
        
        get_edit_profile_modal() # Añadir el modal de edición
    ])

# FUNCIÓN AÑADIDA: Historial de Cuestionarios
def get_questionnaire_history_layout(username, full_name, current_search=""): 
    try:
        user_data = db.get_complete_user_data(username)
        questionnaires = user_data.get('questionnaires', [])
        questionnaires.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    except Exception as e:
        print(f"Error cargando historial de cuestionarios: {e}")
        questionnaires = []
    
    return html.Div([
        get_user_navbar("🧑‍🦽", full_name, "Mis Cuestionarios", current_search), 
        
        html.Div([
            dbc.Button("← Volver al Dashboard", id="nav-dashboard-btn-2", href=f"/{current_search}", color="primary", 
                       style={'marginBottom': '20px'}),
            
            html.Div([
                html.H4("📊 Historial Completo de Cuestionarios", 
                        style={'color': COLORS['primary'], 'marginBottom': '20px'}),
                
                html.Div([
                    html.Div([
                        html.H5(f"📋 {q.get('questionnaire_title', 'Cuestionario')}", 
                                       style={'color': COLORS['primary'], 'marginBottom': '10px'}),
                        html.P(f"🕒 {q.get('timestamp', 'Fecha no disponible')}", 
                                        style={'color': COLORS['muted'], 'marginBottom': '15px'}),
                        
                        html.Ul([
                            html.Li([
                                html.Strong(f"{key.replace('_', ' ').title()}: "),
                                html.Span(str(value))
                            ], style={'marginBottom': '8px'})
                            for key, value in q.get('responses', {}).items()
                        ], style={'paddingLeft': '20px'}),
                        
                        html.Hr(style={'margin': '20px 0'})
                    ], style=STYLES['card']) for q in questionnaires
                ]) if questionnaires else html.P("📭 No hay cuestionarios completados.", 
                                                 style={'textAlign': 'center', 'color': COLORS['muted'], 'padding': '40px'})
            ], style={'padding': '24px'})
        ])
    ])

# FUNCIÓN NUEVA: Vista de Citas para el Paciente (con categorías y acciones)
def get_view_appointments_layout_patient(username, full_name, current_search=""):
    """Layout para que el paciente vea sus citas categorizadas (Pendientes, Próximas, Anteriores)"""
    
    try:
        appointments = db.get_patient_appointments(username)
    except Exception:
        appointments = []
        
    now = datetime.now()
    
    # 1. Citas Pendientes de Confirmación (Estado: scheduled, fecha futura)
    pending_apps = [
        app for app in appointments
        if datetime.fromisoformat(app['datetime']) > now and app.get('status', 'scheduled') == 'scheduled'
    ]
    pending_apps.sort(key=lambda x: x['datetime'])

    # 2. Próximas Citas (Estado: confirmed, fecha futura)
    upcoming_apps = [
        app for app in appointments
        if datetime.fromisoformat(app['datetime']) > now and app.get('status', 'scheduled') == 'confirmed'
    ]
    upcoming_apps.sort(key=lambda x: x['datetime'])

    # 3. Citas Anteriores (Fecha pasada o Cancelada/Atendida, fecha pasada o cualquier estado finalizado)
    past_apps_all = [
        app for app in appointments
        if datetime.fromisoformat(app['datetime']) <= now or app.get('status') in ['cancelled', 'attended']
    ]
    
    # Aseguramos que las citas canceladas o atendidas con fecha futura no aparezcan aquí
    # Se considera 'anterior' si la fecha es pasada O si el estado es final (cancelada/atendida)
    # Excluimos las citas canceladas que ya están contadas en past_apps
    past_apps = [app for app in past_apps_all if datetime.fromisoformat(app['datetime']) <= now or app.get('status') == 'cancelled']
    
    # Eliminar duplicados si una cita cancelada también tenía fecha pasada (redundante)
    unique_past_apps = {app['id']: app for app in past_apps}.values()
    past_apps = sorted(list(unique_past_apps), key=lambda x: x['datetime'], reverse=True)


    def build_appointment_card(app, category):
        appt_dt = datetime.fromisoformat(app['datetime'])
        
        actions = []
        if category == 'pending':
            actions = [
                dbc.Button("✅ Confirmar Cita", id={'type': 'confirm-appt-patient-btn', 'index': app['id']}, color="success", size="sm", className="me-2"),
                dbc.Button("❌ Cancelar Cita", id={'type': 'cancel-appt-patient-btn', 'index': app['id']}, color="danger", size="sm"),
            ]
        elif category == 'upcoming':
            actions = [
                dbc.Button("❌ Cancelar Cita", id={'type': 'cancel-appt-patient-btn', 'index': app['id']}, color="warning", size="sm"),
            ]
        
        status_text = app.get('status', 'Finalizada').capitalize()
        status_color = 'success' if app.get('status') in ['confirmed', 'attended'] else ('danger' if app.get('status') == 'cancelled' else 'warning')
        
        # Mostrar notas del doctor solo en citas pasadas
        doctor_notes = app.get('doctor_notes', 'No hay notas registradas.')
        notes_display = html.Div()
        if category == 'past':
            notes_display = html.Div([
                html.P([html.Strong("Notas del Médico: "), html.Span(doctor_notes)]),
                html.P([html.Strong("Estado: "), html.Span(status_text, className=f"text-{status_color}")])
            ], className="mt-3 p-2 border rounded bg-light")

        return dbc.Card(
            dbc.CardBody([
                html.H5(f"Consulta con {app['professional_name']}", className="card-title text-primary"),
                html.P(f"📅 Fecha y Hora: {appt_dt.strftime('%d/%m/%Y %H:%M')}", className="card-text"),
                html.P(f"🏥 Lugar: {app['hospital']} - {app['office']}", className="card-text"),
                html.P(f"📝 Comentarios: {app['comments']}", className="card-text text-muted"),
                notes_display,
                html.Div(actions, className="mt-3")
            ]),
            className="mb-3"
        )
    
    return html.Div([
        get_user_navbar("🧑‍🦽", full_name, "Mis Citas", current_search),
        
        html.Div([
            dbc.Button("← Volver al Dashboard", id="nav-dashboard-btn-patient-appt", href=f"/{current_search}", color="primary", style={'marginBottom': '20px'}),
            
            # --- Citas Pendientes de Confirmación ---
            html.Div([
                html.H4("🚨 Citas Pendientes de Confirmación", style={'color': COLORS['primary'], 'marginBottom': '15px'}),
                html.Div(
                    [build_appointment_card(app, 'pending') for app in pending_apps]
                ) if pending_apps else html.P("✅ No tienes citas pendientes de acción.", className="p-3 bg-light rounded text-muted")
            ], style=STYLES['card']),

            # --- Próximas Citas Confirmadas ---
            html.Div([
                html.H4("✅ Próximas Citas", style={'color': COLORS['primary'], 'marginBottom': '15px'}),
                html.Div(
                    [build_appointment_card(app, 'upcoming') for app in upcoming_apps]
                ) if upcoming_apps else html.P("📅 No hay citas confirmadas próximas.", className="p-3 bg-light rounded text-muted")
            ], style=STYLES['card']),

            # --- Citas Anteriores (Historial) ---
            html.Div([
                html.H4("📜 Citas Anteriores", style={'color': COLORS['primary'], 'marginBottom': '15px'}),
                html.Div(
                    [build_appointment_card(app, 'past') for app in past_apps]
                ) if past_apps else html.P("📭 No hay historial de citas.", className="p-3 bg-light rounded text-muted")
            ], style=STYLES['card']),
            
            html.Div(id='patient-appt-action-feedback', className="mt-3") # Feedback de acciones
            
        ], style={'padding': '24px'})
    ])

# FUNCIÓN AÑADIDA: Visor de Datos de Pacientes (MODIFICADA para incluir gráficos)
def get_patient_data_viewer_layout(username, full_name, current_search=""): 
    """Layout del visor de datos de pacientes para médicos con alertas"""
    initial_ecg_fig, initial_bpm_text = create_initial_ecg_figure()
    
    return html.Div([
        get_user_navbar("👨‍⚕️", full_name, "Visor de Pacientes", current_search), 
        
        html.Div([
            dbc.Button("← Volver al Dashboard", id="nav-dashboard-btn-3", href=f"/{current_search}", color="primary", 
                        style={'marginBottom': '20px'}),
            
            html.Div(id='health-alert-container', className="mb-3"),
            
            html.Div([
                html.H4("🔬 Visor de Datos de Pacientes", 
                        style={'color': COLORS['primary'], 'marginBottom': '20px'}),
                
                html.Label("👤 Seleccionar Paciente", style={'fontWeight': '600', 'marginBottom': '10px'}),
                dcc.Dropdown(
                    id='doctor-patient-select',
                    placeholder='Buscar paciente...',
                    style={'marginBottom': '20px'}
                ),

                # --- BOTÓN DE EXPORTACIÓN CORREGIDO ---
                html.Div([
                    dbc.Button([
                        html.I(className="bi bi-download me-2"), "📥 Exportar Historial (CSV)"
                    ], id="btn-export-csv", color="success", className="mb-3", n_clicks=0),
                    dcc.Download(id="download-dataframe-csv"),
                ]),
                # ---------------------------------------
                
                html.Div(id='doctor-patient-display'),
                
                html.Div(id="doctor-ecg-container", style={'display': 'none'}, children=[
                    html.Div([
                        html.H4("❤️ Monitorización ECG", style={'color':COLORS['primary'], 'marginBottom': '15px'}),
                        dcc.Graph(id="doctor-ecg-graph", figure=initial_ecg_fig), 
                        html.Div(id="doctor-bpm-output", children=initial_bpm_text, className="mt-2 fw-bold", style={'color': COLORS['secondary']}),
                    ], style=STYLES['card'])
                ]),
                dcc.Store(id='doctor-selected-patient-username', data=None)

            ], style=STYLES['card'])
        ], style={'padding': '24px'})
    ])

# FUNCIÓN AUXILIAR MEJORADA: Construir Tabla de Citas (Soporta rol Médico y Paciente)
def build_appointments_table(username, role):
    """Construye la tabla de citas para un usuario (Médico o Paciente) sin columnas de acciones para el médico."""
    try:
        if role == 'medico':
            appointments = db.get_doctor_appointments(username)
        elif role == 'paciente':
            appointments = db.get_patient_appointments(username)
        else:
            appointments = []
            
        appointments.sort(key=lambda x: x['datetime'], reverse=True)
        
        if not appointments:
            return html.P("📭 No hay citas programadas.", 
                          style={'textAlign': 'center', 'color': COLORS['muted'], 'padding': '40px'})
        
        # Diccionario para mapear estados a texto y colores visibles
        STATUS_MAP = {
            'scheduled': {'text': 'Pendiente', 'color': 'warning'},
            'confirmed': {'text': 'Confirmada', 'color': 'success'},
            'cancelled': {'text': 'Cancelada', 'color': 'danger'},
            'attended': {'text': 'Atendida', 'color': 'primary'},
            'default': {'text': 'Desconocido', 'color': 'muted'}
        }
        
        table_rows = []
        for app in appointments:
            # Manejar errores de parseo de fecha por si acaso
            try:
                appointment_datetime = datetime.fromisoformat(app['datetime'])
            except ValueError:
                appointment_datetime = datetime.now() 
            
            patient_cell = html.Td(app['patient_username']) if role == 'medico' else html.Td(app['professional_name'])
            
            # Obtener estado
            status_info = STATUS_MAP.get(app.get('status', 'default'), STATUS_MAP['default'])
            status_badge = html.Span(status_info['text'], className=f"badge bg-{status_info['color']}")
            
            # --- LÓGICA DE ACCIONES (ELIMINADA PARA ROL 'medico') ---
            actions_header_cell = None
            actions_data_cell = None
            
            # No se añade actions_data_cell para cumplir con la solicitud

            row_content = [
                html.Td(appointment_datetime.strftime('%d/%m/%Y')),
                html.Td(appointment_datetime.strftime('%H:%M')),
                patient_cell,
                html.Td(f"{app['hospital']} - {app['office']}"),
                html.Td(app['comments'][:50] + '...' if len(app.get('comments', '')) > 50 else app.get('comments', '')),
                html.Td(status_badge) # El estado siempre se muestra como badge
            ]
            
            # Solo añadir acciones si se definieron
            if actions_data_cell:
                row_content.append(actions_data_cell)

            table_rows.append(html.Tr(row_content))
        
        header = [html.Th("Fecha"), html.Th("Hora")]
        if role == 'medico':
            # Se eliminan las columnas de "Acciones" (que irían al final)
            header.extend([html.Th("Paciente"), html.Th("Lugar"), html.Th("Comentarios"), html.Th("Estado")])
        elif role == 'paciente':
             header.extend([html.Th("Profesional"), html.Th("Lugar"), html.Th("Comentarios"), html.Th("Estado")])
             if actions_header_cell:
                 header.append(actions_header_cell)
        
        return dbc.Table([
            html.Thead(html.Tr(header)),
            html.Tbody(table_rows)
        ], striped=True, hover=True)
        
    except Exception as e:
        return html.P(f"❌ Error al cargar citas: {str(e)}", style={'color': 'red'})

# FUNCIÓN MEJORADA: Ver Citas (soporta Médico y Paciente)
def get_view_appointments_layout(username, full_name, role, current_search=""): 
    """Layout para ver todas las citas programadas"""
    role_symbol = "👨‍⚕️" if role == 'medico' else "🧑‍🦽"
    
    return html.Div([
        get_user_navbar(role_symbol, full_name, "Gestión de Citas", current_search), 
        
        html.Div([
            dbc.Button("← Volver al Dashboard", id="nav-dashboard-btn-4", href=f"/{current_search}", color="primary", 
                       style={'marginBottom': '20px'}),
            
            html.Div([
                html.H4("📅 Historial de Citas", 
                        style={'color': COLORS['primary'], 'marginBottom': '20px'}),
                
                # Este div se actualizará dinámicamente con el callback de recarga
                html.Div(id='appointments-table-container', children=build_appointments_table(username, role))
            ], style=STYLES['card'])
        ], style={'padding': '24px'}),
        
        get_edit_appointment_modal(), # Mantenemos el modal para evitar problemas de componente inexistente en el layout global, aunque esté vacío.
    ])


# ---------- Layout principal MEJORADO con Divs Fantasma y Stores de control ----------
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # --- Almacenamiento Global (Stores) ---
    dcc.Store(id='user-session-state', data={}),
    dcc.Store(id='reload-trigger', data=0),
    dcc.Store(id='appointments-reload-trigger', data=0),
    dcc.Store(id='current-patient-username', data=None),
    dcc.Store(id='available-exercises', data=[]),
    dcc.Store(id='current-exercise-id', data=None),
    dcc.Store(id='exercise-start-time', data=None),
    dcc.Store(id='current-user-data', data={}),
    dcc.Store(id='doctor-selected-patient-username', data=None),
    dcc.Store(id='profile-user-role', data=None), # ID reclamado en logs
    dcc.Store(id='user-complete-data', data={}),

    # --- Intervalos ---
    dcc.Interval(id='exercise-timer-interval', interval=1000, disabled=True),
    dcc.Interval(id='sensor-interval', interval=500, n_intervals=0),
    dcc.Interval(id='patient-appointments-refresh-interval', interval=30000, disabled=True),

    # --- Modales Globales ---
    # Los modales deben estar en el layout raíz para ser accesibles siempre
    get_exercise_execution_modal(),
    get_exercise_survey_modal(),
    get_schedule_appointment_modal(),
    get_edit_appointment_modal(),
    get_edit_profile_modal(),

    # --- CONTENEDOR FANTASMA (Invisible) ---nav-view-patient-appointments-btn
# --- CONTENEDOR FANTASMA (Invisible) ---
    html.Div([
        # Botones de navegación 
        html.Button(id='nav-dashboard-btn'),    
        html.Button(id='nav-dashboard-btn-2'),
        html.Button(id='nav-dashboard-btn-3'),
        html.Button(id='nav-dashboard-btn-4'),
        html.Button(id='health-alert-container'),
        html.Button(id='nav-dashboard-btn-patient-appt'),
        html.Button(id='nav-patient-viewer-btn'),
        html.Button(id='nav-view-appointments-btn'),
        html.Button(id='nav-view-patient-appointments-btn'),
        html.Button(id='nav-my-data-btn'),
        html.Button(id='nav-my-questionnaires-btn'),
        html.Button(id='logout-button'),
        
        # Citas y Gestión
        html.Button(id='dash-view-appointments-btn'),
        html.Button(id='schedule-appointment-btn'),
        html.Div(id='schedule-appointment-btn-modal-trigger'),
        html.Div(id='appointment-schedule-feedback'),
        html.Div(id='patient-appt-action-feedback'),
        
        # Formulario de Perfil 
        dcc.Input(id='edit-fullname'),
        dcc.Input(id='edit-email'),
        dcc.Input(id='edit-phone'),
        dcc.Input(id='edit-address'),
        dcc.Input(id='edit-dni'),
        dcc.DatePickerSingle(id='edit-birthdate'),
        dcc.Input(id='edit-emergency-contact'),
        dcc.Input(id='edit-emergency-phone'),
        dcc.Dropdown(id='edit-blood-type'),
        dcc.Textarea(id='edit-allergies'),
        dcc.Textarea(id='edit-medications'),
        dcc.Textarea(id='edit-conditions'),
        html.Button(id='open-edit-profile-modal-btn'),
        html.Button(id='save-profile-btn'),
        html.Button(id='cancel-profile-btn'),
        
        # Salidas de datos y Gráficos
        html.Div(id='bpm-output'),
        html.Div(id='doctor-bpm-output'),
        html.Div(id='ecg-status-msg'),
        html.Div(id='imu-status-msg'),
        dcc.Graph(id='ecg-graph'),
        dcc.Graph(id='doctor-ecg-graph'),
        dcc.Graph(id='questionnaire-q1-graph'),
        dcc.Graph(id='questionnaire-q2-graph'),
        dcc.Graph(id='exercise-history-graph'),
        dcc.Graph(id='live-ecg-graph'),
        dcc.Graph(id='live-imu-graph'),
        
        # Contenedores de layouts dinámicos
        html.Div(id='appointments-table-container'),
        html.Div(id='patient-appointments-list'),
        html.Div(id='doctor-patient-display'),
        html.Div(id='doctor-ecg-container'),
        html.Div(id='selected-questionnaire-content'),
        html.Div(id='questionnaire-submission-feedback'),
        html.Div(id='exercise-execution-content'),
        html.Div(id='exercise-survey-content'),
        html.Div(id='exercise-timer'),
        
        # Selectores
        dcc.Dropdown(id='doctor-patient-select'),
        dcc.Dropdown(id='questionnaire-select'),
        dcc.Dropdown(id='unassigned-patient-select'),
        dcc.Dropdown(id='assigned-patient-select-disassociate'),
        
        # Otros
        html.Button(id='load-ecg-stress-btn'),
        html.Button(id='doctor-load-ecg-stress-btn'),
        html.Button(id='associate-patient-button'),
        html.Button(id='disassociate-patient-button'),
        html.Button(id='finish-exercise-btn'),
        html.Button(id='cancel-exercise-btn'),
        html.Button(id='submit-exercise-survey'),
        
    ], style={'display': 'none'}), # Mantiene todo el bloque invisible

    # --- Contenido Dinámico Real ---

    html.Div(id='page-content'),
])

# NUEVO CALLBACK: Actualiza el gráfico de ECG en el Visor del Médico
# NUEVO CALLBACK: Actualiza el gráfico de ECG en el Visor del Médico
@app.callback(
    [Output("ecg-graph", "figure"),
     Output("bpm-output", "children")],
    [Input('sensor-interval', 'n_intervals')],
    [State('url', 'pathname')]
)
def update_main_dashboard_auto(n, pathname):
    # Solo actualizar si el usuario está en el Dashboard y el archivo existe
    if pathname != '/' or not os.path.exists(STREAM_FILE):
        return dash.no_update, dash.no_update
    
    try:
        # 1. Leer los últimos datos del stream
        df = pd.read_csv(STREAM_FILE).tail(50)
        if df.empty:
            return dash.no_update, dash.no_update

        y_data = df['ecg'].tolist()
        
        # 2. Detectar estado de alerta (rojo si hay arritmia)
        is_warning = (df['status_ecg'] == 'RED_FLAG_ARRHYTHMIA').any()
        line_color = "#ef4444" if is_warning else "#2ebf7f" # Rojo vs Verde esmeralda
        
        # 3. Crear la gráfica Scatter
        fig = go.Figure(go.Scatter(
            x=list(range(len(y_data))), 
            y=y_data, 
            mode="lines", 
            line=dict(color=line_color, width=2.5),
            fill='none',
            hoverinfo='none'
        ))

        # 4. RIGIDEZ ABSOLUTA DEL LAYOUT (Formato ECG Profesional)
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=50, r=20, t=40, b=40),
            height=350,
            xaxis=dict(
                range=[0, 49], 
                fixedrange=True, # Evita zoom accidental
                showgrid=True,
                gridcolor="#f0f0f0"
            ),
            yaxis=dict(
                range=[-1.0, 2.0], # Rango FIJO: La onda no moverá el cuadro
                fixedrange=True,
                dtick=0.5,
                tickformat=".1f", # Mantiene el ancho del eje constante
                gridcolor="#f0f0f0",
                zeroline=True,
                zerolinecolor="#e5e7eb"
            ),
            showlegend=False,
            title={
                'text': "⚠️ Alerta: Arritmia Detectada" if is_warning else "✅ Ritmo Cardíaco Normal",
                'font': {'color': line_color}
            }
        )

        # 5. Cálculo de BPM (Lógica simplificada para el dashboard)
        bpm = 75 + (max(y_data) * 5)
        return fig, f"❤️ Frecuencia Cardíaca: {bpm:.1f} BPM"

    except Exception as e:
        print(f"Error en callback de ECG: {e}")
        return dash.no_update, dash.no_update
    
    # Callback para actualizar el estado de salud y alertas en el visor del médico
@app.callback(
    [Output('health-alert-container', 'children'),
     Output('doctor-ecg-graph', 'figure', allow_duplicate=True)],
    [Input('sensor-interval', 'n_intervals')],
    [State('doctor-selected-patient-username', 'data')],
    prevent_initial_call=True
)
def monitor_patient_health(n, selected_patient):
    if not selected_patient or not os.path.exists(STREAM_FILE):
        return dash.no_update, dash.no_update

    try:
        # Leer los últimos 100 registros para análisis de tendencias
        df = pd.read_csv(STREAM_FILE).tail(100)
        
        alerts = []
        # 1. Detectar Arritmia (Datos del ECG)
        if (df['status_ecg'] == 'RED_FLAG_ARRHYTHMIA').any():
            alerts.append(dbc.Alert(
                [html.I(className="bi bi-exclamation-triangle-fill me-2"),
                 f"⚠️ ALERTA CRÍTICA: Arritmia detectada en el paciente {selected_patient}"],
                color="danger", className="d-flex align-items-center animate__animated animate__pulse animate__infinite"
            ))

        # 2. Detectar Fatiga o Movimiento Anómalo (Datos del IMU)
        if (df['status_imu'] == 'RED_FLAG_FATIGUE').any():
            alerts.append(dbc.Alert(
                [html.I(className="bi bi-info-circle-fill me-2"),
                 "Aviso: El paciente muestra signos de fatiga muscular o pérdida de rango de movimiento."],
                color="warning"
            ))

        # 3. Actualizar Gráfico con colores de alerta
        line_color = "red" if (df['status_ecg'] == 'RED_FLAG_ARRHYTHMIA').any() else "green"
        fig = go.Figure(go.Scatter(x=df['timestamp'], y=df['ecg'], line=dict(color=line_color)))
        fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20), height=300)

        return alerts, fig

    except Exception as e:
        print(f"Error en monitorización: {e}")
        return dash.no_update, dash.no_update



# --- CALLBACK DE RECARGA DE GRÁFICAS Y CITAS ---
@app.callback(
    [Output('questionnaire-q1-graph', 'figure', allow_duplicate=True),
     Output('questionnaire-q2-graph', 'figure', allow_duplicate=True),
     Output('exercise-history-graph', 'figure', allow_duplicate=True)],
    Input('reload-trigger', 'data'),
    State('current-patient-username', 'data'),
    prevent_initial_call=True
)
def reload_progress_graphs(trigger, username):
    if trigger is not None and username:
        try:
            patient_data = db.get_complete_user_data(username) or {}
            questionnaires_data = patient_data.get('questionnaires', [])
            exercises_data = patient_data.get('exercises', [])
            
            # Ahora desempaquetamos las dos figuras correctamente
            fig_q1, fig_q2 = create_questionnaire_plot(questionnaires_data)
            exercise_fig = create_exercise_plot(exercises_data)
            
            return fig_q1, fig_q2, exercise_fig
        except Exception as e:
            print(f"Error al recargar gráficas: {e}")
            return dash.no_update, dash.no_update, dash.no_update
    return dash.no_update, dash.no_update, dash.no_update

# NUEVO CALLBACK: Refresca la lista de citas pendientes del paciente (cada 30s)
@app.callback(
    Output('patient-appointments-list', 'children'),
    Input('patient-appointments-refresh-interval', 'n_intervals'),
    State('current-patient-username', 'data')
)
def refresh_patient_appointments_list(n_intervals, username):
    if not username:
        return html.P("Inicia sesión para ver tus citas.", style={'textAlign': 'center', 'color': COLORS['muted'], 'padding': '20px'})

    try:
        appointments = db.get_patient_appointments(username)
        current_time = datetime.now()
        upcoming_appointments = [
            app for app in appointments 
            if datetime.fromisoformat(app['datetime']) > current_time and app.get('status', 'scheduled') in ['scheduled', 'confirmed']
        ]
        upcoming_appointments.sort(key=lambda x: x['datetime'])
        
        content = html.Ul([
            html.Li([
                html.Strong(f"{app['professional_name']} - "),
                html.Span(f"{datetime.fromisoformat(app['datetime']).strftime('%d/%m/%Y %H:%M')}"),
                html.Br(),
                html.Span(f"🏥 {app['hospital']} - {app['office']} ({app.get('status', 'Scheduled').capitalize()})", style={'fontSize': '0.9em', 'color': COLORS['muted']}),
                html.Br(),
                html.Span(f"📝 {app['comments']}", style={'fontSize': '0.9em', 'color': COLORS['muted']})
            ], style={'marginBottom': '10px', 'padding': '10px', 'background': '#f8f9fa', 'borderRadius': '5px'})
            for app in upcoming_appointments[:5]
        ], style={'paddingLeft': '20px'})
        
        if not upcoming_appointments:
             return html.P("📭 No tienes citas pendientes", style={'textAlign': 'center', 'color': COLORS['muted'], 'padding': '20px'})
        
        return content
        
    except Exception as e:
        print(f"Error al recargar citas del paciente: {e}")
        return html.P(f"Error: {e}", style={'color': 'red'})


# NUEVO CALLBACK: Recarga la tabla de citas del médico/paciente cuando el trigger cambia
@app.callback(
    Output('appointments-table-container', 'children', allow_duplicate=True),
    Input('appointments-reload-trigger', 'data'),
    [State('user-session-state', 'data'),
     State('url', 'pathname')], 
    prevent_initial_call=True
)
def reload_appointments_table_on_trigger(trigger_value, user_data, pathname):
    # Solo recarga si estamos en la vista de citas del médico
    if pathname == '/view-appointments' and user_data.get('username') and user_data.get('role') == 'medico':
        return build_appointments_table(user_data['username'], user_data['role'])
    # Si estamos en la vista de citas del paciente, forzamos la recarga de esa vista
    if pathname == '/view-patient-appointments' and user_data.get('username') and user_data.get('role') == 'paciente':
         # Simplemente actualizamos el layout de citas del paciente si se confirma/cancela una cita
         return dash.no_update 
    return dash.no_update

# NUEVO CALLBACK: Habilita/Deshabilita el intervalo de refresco de citas
@app.callback(
    Output('patient-appointments-refresh-interval', 'disabled'),
    Input('url', 'pathname'),
    State('user-session-state', 'data')
)
def control_patient_refresh_interval(pathname, user_data):
    # Solo si estamos en el Dashboard raíz (/) Y el usuario es 'paciente'
    is_patient_dashboard = pathname == '/' and user_data.get('role') == 'paciente'
    
    # Si es el dashboard del paciente, deshabilitado = False (está activo)
    # En cualquier otro caso, deshabilitado = True (está inactivo)
    return not is_patient_dashboard


# --- RESTO DE CALLBACKS ---

# Callback para mostrar/ocultar sección médica según el rol (Se mantiene)
@app.callback(
    Output('medical-info-section', 'style'),
    Input('register-role', 'value')
)
def toggle_medical_section(role):
    if role == 'paciente':
        return {'display': 'block'}
    return {'display': 'none'}

# Callback: Mostrar contenido del cuestionario seleccionado (Se mantiene)
@app.callback(
    Output('selected-questionnaire-content', 'children'),
    Input('questionnaire-select', 'value')
)
def display_questionnaire(selected_questionnaire):
    if not selected_questionnaire:
        return html.P("Selecciona un cuestionario para comenzar.", style={'color': COLORS['muted']})
    
    questionnaire = QUESTIONNAIRES.get(selected_questionnaire)
    if not questionnaire:
        return html.P("Cuestionario no encontrado.", style={'color': 'red'})
    
    questions_content = []
    for i, question in enumerate(questionnaire['questions']):
        question_html = html.Div([
            html.H6(f"{i+1}. {question['question']}", style={'marginBottom': '10px', 'fontWeight': 'bold'}),
        ])
        
        component_id = {'type': f'q-{questionnaire["id"]}-input', 'index': question['id']}

        if question['type'] == 'slider':
            question_html.children.append(
                dcc.Slider(
                    id=component_id,
                    min=question['min'],
                    max=question['max'],
                    step=question.get('step', 1),
                    value=question.get('min', 0),
                    marks=question.get('marks', {i: str(i) for i in range(question['min'], question['max']+1, max(1, (question['max']-question['min'])//5))}),
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
                    labelStyle={'display': 'block', 'marginBottom': '10px'} 
                )
            )
            
        questions_content.append(question_html)
        questions_content.append(html.Hr())
    
    questions_content.append(
        html.Button(
            '📤 Enviar Cuestionario',
            id={'type': 'submit-questionnaire', 'index': selected_questionnaire},
            n_clicks=0,
            style={
                'width': '100%',
                'padding': '12px',
                'background': COLORS['primary'],
                'color': 'white',
                'border': 'none',
                'borderRadius': '8px',
                'cursor': 'pointer',
                'fontWeight': '600',
                'marginTop': '15px'
            }
        )
    )
    
    return html.Div([
        html.H5(questionnaire['title'], style={'color': COLORS['primary'], 'marginBottom': '10px'}),
        html.P(questionnaire['description'], style={'color': COLORS['muted'], 'marginBottom': '20px'}),
        *questions_content
    ])

# Callback: Enviar cuestionario especializado (Recarga gráfica)
@app.callback(
    [Output('questionnaire-submission-feedback', 'children'),
     Output('reload-trigger', 'data', allow_duplicate=True)],
    Input({'type': 'submit-questionnaire', 'index': dash.ALL}, 'n_clicks'),
    [State('questionnaire-select', 'value'),
     State('current-patient-username', 'data'),
     State('questionnaire-select', 'options'),
     State({'type': 'q-dolor_rodilla-input', 'index': dash.ALL}, 'value'),
     State({'type': 'q-funcionalidad-input', 'index': dash.ALL}, 'value'),
     State('reload-trigger', 'data')],
    prevent_initial_call=True
)
def submit_specialized_questionnaire(n_clicks, questionnaire_id, username, options, dolor_rodilla_vals, funcionalidad_vals, reload_trigger):
    ctx = callback_context
    if not ctx.triggered or not n_clicks or n_clicks[0] == 0:
        return dash.no_update, dash.no_update
    
    if not questionnaire_id:
        return html.Div("❌ Error: No se ha seleccionado cuestionario", style={'color': 'red'}), dash.no_update
    
    try:
        responses = {}
        questionnaire = QUESTIONNAIRES.get(questionnaire_id)
        
        if questionnaire_id == 'dolor_rodilla':
            # Aseguramos que los valores que llegan de ALL no sean dash.no_update
            values = [v for v in dolor_rodilla_vals if v is not dash.no_update and v is not None]
        elif questionnaire_id == 'funcionalidad':
            values = [v for v in funcionalidad_vals if v is not dash.no_update and v is not None]
        else:
            values = []

        if questionnaire:
            question_ids = [q['id'] for q in questionnaire['questions']]
            
            # Validación de cantidad de respuestas
            if len(values) != len(question_ids):
                 return html.Div(f"⚠️ Error: Faltan {len(question_ids) - len(values)} respuestas en el cuestionario activo.", style={'color': 'orange'}), dash.no_update

            for q_id, value in zip(question_ids, values):
                 responses[q_id] = value

        
        questionnaire_data = {
            'questionnaire_id': questionnaire_id,
            'responses': responses,
            'timestamp': datetime.now().isoformat(),
            'questionnaire_title': questionnaire['title']
        }
        
        db.save_specialized_questionnaire(username, questionnaire_data)
        
        new_trigger = reload_trigger + 1 if reload_trigger is not None else 1
        return html.Div("✅ Cuestionario enviado correctamente. Gráficas actualizadas.", style={'color': 'green'}), new_trigger
        
    except Exception as e:
        return html.Div(f"❌ Error al enviar cuestionario: {str(e)}", style={'color': 'red'}), dash.no_update

# Callback: Iniciar ejercicio (abrir modal) (Se mantiene)
@app.callback(
    [Output('exercise-execution-modal', 'is_open'),
     Output('exercise-execution-content', 'children'),
     Output('current-exercise-id', 'data'),
     Output('exercise-start-time', 'data'),
     Output('exercise-timer-interval', 'disabled')], 
    [Input({'type': 'start-exercise-btn', 'index': dash.ALL}, 'n_clicks'),
     Input({'type': 'exercise-image', 'index': dash.ALL}, 'n_clicks')],
    [State('available-exercises', 'data')],
    prevent_initial_call=True
)
def start_exercise(start_clicks, image_clicks, exercises):
    ctx = callback_context
    if not ctx.triggered or not ctx.triggered[0]['value']:
        return False, html.Div(), None, None, True 
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        exercise_id = json.loads(trigger_id)['index']
    except:
        return False, html.Div(), None, None, True 
    
    exercise = next((ex for ex in exercises if ex['id'] == exercise_id), None)
    if not exercise:
        return False, html.Div(), None, None, True 
    
    execution_content = html.Div([
        html.Div([
            html.Img(
                src=exercise['images'][0],
                style={
                    'width': '100%',
                    'maxHeight': '200px',
                    'objectFit': 'cover',
                    'borderRadius': '8px',
                    'marginBottom': '20px'
                }
            ),
            html.H4(exercise['title'], style={'color': COLORS['primary'], 'marginBottom': '10px'}),
            html.P(exercise['description'], style={'color': COLORS['muted'], 'marginBottom': '20px'})
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H6("📊 Series y Repeticiones", style={'color': COLORS['primary']}),
                    html.P(f"🔢 Series: {exercise['sets']}"),
                    html.P(f"🔄 Repeticiones: {exercise['reps']}"),
                    html.P(f"⏱️ Descanso: {exercise['rest_sec']} segundos")
                ], style={'padding': '15px', 'background': '#f8f9fa', 'borderRadius': '8px'})
            ], width=6),
            dbc.Col([
                html.Div([
                    html.H6("💪 Peso y Dificultad", style={'color': COLORS['primary']}),
                    html.P(f"🏋️ Peso: {exercise['weight']}"),
                    html.P(f"📈 Dificultad: {exercise['difficulty']}"),
                    html.P(f"🎯 Músculos: {', '.join(exercise['muscles'])}")
                ], style={'padding': '15px', 'background': '#f8f9fa', 'borderRadius': '8px'})
            ], width=6)
        ], style={'marginBottom': '20px'}),
        
        html.Div([
            html.H5("📝 Instrucciones Detalladas", style={'color': COLORS['primary'], 'marginBottom': '15px'}),
            html.Ol([
                html.Li(instruction, style={'marginBottom': '10px', 'lineHeight': '1.5', 'padding': '5px'}) 
                for instruction in exercise.get('instructions', [])
            ], style={'paddingLeft': '20px'}),
            
            html.H6("✨ Beneficios:", style={'color': COLORS['secondary'], 'marginTop': '15px'}),
            html.P(exercise.get('benefits', ''), style={'color': COLORS['muted'], 'fontStyle': 'italic'})
        ]),
        
        html.Div([
            html.H6("⏰ Tiempo de ejercicio:", style={'color': COLORS['primary'], 'marginBottom': '10px'}),
            html.Div(id='exercise-timer', style={
                'fontSize': '24px',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'color': COLORS['secondary'],
                'padding': '10px',
                'border': f'2px solid {COLORS["secondary"]}',
                'borderRadius': '8px'
            })
        ], style={'marginTop': '20px', 'textAlign': 'center'})
    ])
    
    return True, execution_content, exercise_id, datetime.now().isoformat(), False

# Callback: Terminar ejercicio y mostrar cuestionario (Recarga gráfica)
@app.callback(
    [Output('exercise-execution-modal', 'is_open', allow_duplicate=True),
     Output('exercise-survey-modal', 'is_open'),
     Output('exercise-survey-content', 'children'),
     Output('exercise-timer-interval', 'disabled', allow_duplicate=True),
     Output('reload-trigger', 'data', allow_duplicate=True)],
    Input('finish-exercise-btn', 'n_clicks'),
    [State('current-exercise-id', 'data'),
     State('exercise-start-time', 'data'),
     State('available-exercises', 'data'),
     State('current-patient-username', 'data'),
     State('reload-trigger', 'data')],
    prevent_initial_call=True
)
def finish_exercise_and_show_survey(n_clicks, exercise_id, start_time, exercises, username, reload_trigger):
    if not n_clicks or n_clicks == 0:
        return dash.no_update, False, html.Div(), dash.no_update, dash.no_update
    
    end_time = datetime.now()
    start_time_obj = datetime.fromisoformat(start_time) if start_time else end_time
    duration_seconds = int((end_time - start_time_obj).total_seconds())
    
    exercise = next((ex for ex in exercises if ex['id'] == exercise_id), None) if exercise_id else None
    
    survey_content = html.Div([
        html.H4("📊 Datos del Ejercicio Completado", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
        
        html.Div([
            html.H5("Ejercicio completado:", style={'marginBottom': '10px'}),
            html.P(f"💪 {exercise['title'] if exercise else 'Ejercicio no especificado'}", style={'fontWeight': 'bold'}),
            html.P(f"⏱️ Duración: {duration_seconds} segundos"),
            html.P(f"📅 Fecha: {end_time.strftime('%d/%m/%Y %H:%M')}")
        ], style={
            'background': '#f8f9fa',
            'padding': '15px',
            'borderRadius': '8px',
            'marginBottom': '20px'
        }),
        
        html.H5("Esta información ha sido guardada y estará disponible para tu médico.", 
                 style={'color': COLORS['secondary'], 'textAlign': 'center', 'padding': '20px'}),
        
        html.Div([
            html.P("Tu médico revisará tu progreso en la próxima cita.", 
                          style={'textAlign': 'center', 'color': COLORS['muted']})
        ], style={'marginTop': '20px'})
    ])
    
    new_trigger = dash.no_update
    if exercise_id and start_time and username:
        exercise_data = {
            'exercise_id': exercise_id,
            'start_time': start_time,
            'end_time': end_time.isoformat(),
            'duration_seconds': duration_seconds,
            'exercise_name': exercise['title'] if exercise else 'Desconocido',
            'completed': True,
            'timestamp': end_time.isoformat(),
            'sets': exercise.get('sets', 'N/A') if exercise else 'N/A',
            'reps': exercise.get('reps', 'N/A') if exercise else 'N/A'
        }
        
        try:
            db.record_completed_exercise(username, exercise_id, exercise_data)
            new_trigger = reload_trigger + 1 if reload_trigger is not None else 1
        except Exception as e:
            print(f"Error saving exercise: {e}")
            pass 
    
    return False, True, survey_content, True, new_trigger

# Callback: Cerrar cuestionario de ejercicio (Se mantiene)
@app.callback(
    Output('exercise-survey-modal', 'is_open', allow_duplicate=True),
    Input('submit-exercise-survey', 'n_clicks'),
    prevent_initial_call=True
)
def close_exercise_survey(n_clicks):
    if n_clicks and n_clicks > 0:
        return False
    return dash.no_update

# Callback: Cancelar ejercicio (Se mantiene)
@app.callback(
    [Output('exercise-execution-modal', 'is_open', allow_duplicate=True),
     Output('current-exercise-id', 'data', allow_duplicate=True),
     Output('exercise-start-time', 'data', allow_duplicate=True),
     Output('exercise-timer-interval', 'disabled', allow_duplicate=True)], 
    Input('cancel-exercise-btn', 'n_clicks'),
    prevent_initial_call=True
)
def cancel_exercise(n_clicks):
    if n_clicks and n_clicks > 0:
        return False, None, None, True
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Callback: Actualizar temporizador (Se mantiene)
@app.callback(
    Output('exercise-timer', 'children'),
    Input('exercise-timer-interval', 'n_intervals'),
    [State('current-exercise-id', 'data'),
     State('exercise-start-time', 'data')]
)
def update_exercise_timer(n_intervals, exercise_id, start_time): 
    if exercise_id and start_time:
        start_time_obj = datetime.fromisoformat(start_time)
        duration = datetime.now() - start_time_obj
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        return f"{minutes:02d}:{seconds:02d}"
    return "00:00"

# Callback: Agendar cita (abrir modal) (CORREGIDO: Usa el ID global)
@app.callback(
    Output('schedule-appointment-modal', 'is_open'),
    [Input('schedule-appointment-btn', 'n_clicks'), 
     Input('schedule-appointment-btn-modal-trigger', 'n_clicks'), 
     Input('cancel-appointment-btn', 'n_clicks'),
     Input('confirm-appointment-btn', 'n_clicks')],
    [State('schedule-appointment-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_appointment_modal(n_open_dash, n_open_nav_trigger, n_cancel, n_confirm, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return is_open
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id in ['schedule-appointment-btn', 'schedule-appointment-btn-modal-trigger']:
        # Se disparó por un botón de abrir, verificar que no sea un clic None
        if ctx.triggered[0]['value'] and ctx.triggered[0]['value'] > 0:
             return True
    
    if trigger_id == 'cancel-appointment-btn' and n_cancel and n_cancel > 0:
        return False
    if trigger_id == 'confirm-appointment-btn' and n_confirm and n_confirm > 0:
        return False
    
    return is_open

# Callback: Cargar pacientes en el dropdown de citas (CORREGIDO: Usa el ID global)
@app.callback(
    Output('appointment-patient-select', 'options'),
    [Input('schedule-appointment-btn', 'n_clicks'), Input('schedule-appointment-btn-modal-trigger', 'n_clicks')], 
    State('current-user-data', 'data'),
    prevent_initial_call=True
)
def load_patients_for_appointment(n_clicks_dash, n_clicks_nav_trigger, user_data):
    # Se activará con cualquier clic, pero solo si es médico
    if user_data.get('role') != 'medico':
        return []

    try:
        patients = db.get_all_patients_for_doctor(user_data['username'])
        
        return [
            {'label': f"👤 {p['full_name']} ({p['username']})", 'value': p['username']}
            for p in patients
        ]
    except Exception as e:
        print(f"Error cargando pacientes para cita: {e}")
        return []

# Callback: Confirmar y guardar cita (Implementa validaciones de obligatoriedad y tiempo)
@app.callback(
    [Output('appointment-patient-select', 'value', allow_duplicate=True),
     Output('appointment-date', 'date', allow_duplicate=True),
     Output('appointment-time', 'value', allow_duplicate=True),
     Output('appointment-hospital', 'value', allow_duplicate=True),
     Output('appointment-office', 'value', allow_duplicate=True),
     Output('appointment-comments', 'value', allow_duplicate=True),
     Output('appointment-schedule-feedback', 'children', allow_duplicate=True), 
     Output('appointments-reload-trigger', 'data', allow_duplicate=True), 
     Output('patient-appointments-refresh-interval', 'n_intervals', allow_duplicate=True)],
    Input('confirm-appointment-btn', 'n_clicks'),
    [State('appointment-patient-select', 'value'),
     State('appointment-date', 'date'),
     State('appointment-time', 'value'),
     State('appointment-hospital', 'value'),
     State('appointment-office', 'value'),
     State('appointment-comments', 'value'),
     State('current-user-data', 'data'),
     State('appointments-reload-trigger', 'data'),
     State('patient-appointments-refresh-interval', 'n_intervals')],
    prevent_initial_call=True
)
def schedule_appointment(n_clicks, patient_username, date, time, hospital, office, comments, user_data, reload_trigger, patient_n_intervals):
    if not n_clicks or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # --- 1. Validación de campos obligatorios (todos excepto 'Comentarios') ---
    if not patient_username or not date or not time or not hospital or not office:
        feedback = html.Div("⚠️ Faltan campos obligatorios para crear la cita (excepto Comentarios).", style={'color': 'red'})
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, feedback, reload_trigger, dash.no_update

    try:
        # Combinar fecha y hora para la validación de tiempo
        appointment_datetime_str = f"{date} {time}"
        
        # Intentar parsear la fecha y hora
        try:
            appointment_dt = datetime.strptime(appointment_datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
             feedback = html.Div("❌ Error: Formato de fecha/hora inválido.", style={'color': 'red'})
             return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, feedback, reload_trigger, dash.no_update
        
        # --- 2. Validación de tiempo (debe ser futuro) ---
        now = datetime.now()
        if appointment_dt <= now:
            feedback = html.Div("❌ Error: No se puede crear una cita para un día u hora anterior a la actual.", style={'color': 'red'})
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, feedback, reload_trigger, dash.no_update
            
        # Si la validación pasa, convertir a formato ISO para guardar
        appointment_datetime = appointment_dt.isoformat()
        
        appointment_data = {
            'patient_username': patient_username,
            'professional_username': user_data['username'],
            'professional_name': user_data['full_name'],
            'professional_role': user_data['role'],
            'datetime': appointment_datetime,
            'hospital': hospital,
            'office': office,
            'comments': comments or '',
            'status': 'scheduled', # Estado inicial: Pendiente de confirmación del paciente
            'created_at': datetime.now().isoformat()
        }

        db.schedule_appointment(appointment_data)
        
        feedback = html.Div(f"✅ Cita para {patient_username} creada correctamente. Pendiente de confirmación del paciente.", style={'color': 'green'})
        new_reload_trigger = reload_trigger + 1 if reload_trigger is not None else 1
        # No forzamos el n_intervals del paciente, ya que lo hace el callback de abajo
        
        # Limpiamos campos y actualizamos triggers
        return None, datetime.now().date(), None, "", "", "", feedback, new_reload_trigger, dash.no_update
        
    except Exception as e:
        print(f"Error scheduling appointment: {e}")
        feedback = html.Div(f"❌ Error al crear la cita: {e}", style={'color': 'red'})
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, feedback, reload_trigger, dash.no_update

# NUEVOS CALLBACKS: Acciones del Paciente (Confirmar/Cancelar)
@app.callback(
    [Output('appointments-reload-trigger', 'data', allow_duplicate=True),
     Output('patient-appt-action-feedback', 'children')],
    [Input({'type': 'confirm-appt-patient-btn', 'index': dash.ALL}, 'n_clicks'),
     Input({'type': 'cancel-appt-patient-btn', 'index': dash.ALL}, 'n_clicks')],
    State('appointments-reload-trigger', 'data'),
    prevent_initial_call=True
)
def handle_patient_appointment_actions(confirm_clicks, cancel_clicks, reload_trigger):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    trigger = ctx.triggered[0]
    # Asegúrate de que el clic no sea None antes de intentar cargar json.loads
    if trigger['value'] is None or trigger['value'] == 0:
            return dash.no_update, dash.no_update
            
    trigger_id = json.loads(trigger['prop_id'].split('.')[0])
    appointment_id = trigger_id['index']
    action_type = trigger_id['type']

    try:
        new_status = None
        feedback_msg = ""
        
        if 'confirm-appt-patient-btn' in action_type:
            new_status = 'confirmed'
            feedback_msg = f"✅ Cita {appointment_id} confirmada con éxito. ¡Aparecerá en Próximas Citas!"
            
        elif 'cancel-appt-patient-btn' in action_type:
            # Si el paciente cancela, el estado final es 'cancelled'
            new_status = 'cancelled'
            feedback_msg = f"❌ Cita {appointment_id} cancelada. Historial actualizado."
            
        
        db.update_appointment(appointment_id, {'status': new_status, 'patient_notes': 'Acción del paciente: Cambio de estado.'})

        
        # Forzar el re-renderizado de la vista de citas (ya que no es un output directo)
        new_reload_trigger = reload_trigger + 1 if reload_trigger is not None else 1
        return new_reload_trigger, html.Div(feedback_msg, className="alert alert-success")

    except Exception as e:
        print(f"Error handling patient appointment action: {e}")
        return dash.no_update, html.Div(f"❌ Error al procesar la acción: {e}", className="alert alert-danger")


# --- CALLBACKS DE EDICIÓN DE PERFIL (CORREGIDOS) ---

# Callback 1: Abrir Modal de Edición de Perfil y precargar datos
@app.callback(
    [Output('edit-profile-modal', 'is_open'),
     Output('edit-profile-modal-content', 'children'),
     Output('edit-profile-feedback', 'children')],
    Input('open-edit-profile-modal-btn', 'n_clicks'),
    [State('user-session-state', 'data'),
     State('edit-profile-modal', 'is_open')],
    prevent_initial_call=True
)
def open_edit_profile_modal(n_clicks, user_session, is_open):
    if not n_clicks or n_clicks == 0:
        return is_open, dash.no_update, dash.no_update
    
    if is_open:
        return False, html.Div(), html.Div()
    
    username = user_session['username']
    role = user_session['role']
    user_data = db.get_complete_user_data(username)
    profile = user_data.get('profile', {})
    
    # Define el formulario para médico o paciente (el layout es el mismo, solo varía la sección médica)
    form_content = html.Div([
        # --- Información Personal ---
        html.H4("📋 Información Personal", style={'color': COLORS['primary'], 'marginBottom': '16px'}),
        
        html.Label("👤 Nombre Completo"),
        # CORRECCIÓN: Asegurar que el nombre completo sea el del basic_info (que se guarda correctamente)
        dcc.Input(id='edit-fullname', type='text', value=user_data['basic_info']['full_name'], style={'width': '100%', 'marginBottom': '10px'}),
        
        html.Label("📧 Email *"),
        dcc.Input(id='edit-email', type='email', value=profile.get('email', ''), required=True, style={'width': '100%', 'marginBottom': '10px'}),
        
        html.Label("📞 Teléfono *"),
        dcc.Input(id='edit-phone', type='tel', value=profile.get('phone', ''), required=True, style={'width': '100%', 'marginBottom': '10px'}),
        
        html.Label("🏠 Dirección"),
        dcc.Input(id='edit-address', type='text', value=profile.get('address', ''), style={'width': '100%', 'marginBottom': '10px'}),
        
        html.Label("🆔 DNI/NIE *"),
        dcc.Input(id='edit-dni', type='text', value=profile.get('dni', ''), required=True, style={'width': '100%', 'marginBottom': '10px'}),
        
        html.Label("🎂 Fecha de Nacimiento *"),
        dcc.DatePickerSingle(
            id='edit-birthdate',
            date=profile.get('birth_date'), 
            max_date_allowed=datetime.today(),
            style={'width': '100%', 'marginBottom': '20px'}
        ),
        
        # --- Información Médica (Solo para paciente) ---
        html.Div(id='edit-medical-info-section', children=[
            html.H4("🏥 Información Médica", style={'color': COLORS['primary'], 'marginBottom': '16px', 'marginTop': '20px'}),
            
            html.Label("🩸 Tipo de Sangre"),
            dcc.Dropdown(
                id='edit-blood-type',
                options=[{'label': b, 'value': b} for b in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']],
                value=profile.get('blood_type'),
                style={'marginBottom': '10px'}
            ),
            
            html.Label("⚠️ Alergias"),
            dcc.Textarea(id='edit-allergies', value=profile.get('allergies', ''), style={'width': '100%', 'height': '60px', 'marginBottom': '10px'}),
            
            html.Label("💊 Medicamentos Actuales"),
            dcc.Textarea(id='edit-medications', value=profile.get('current_medications', ''), style={'width': '100%', 'height': '60px', 'marginBottom': '10px'}),
            
            html.Label("📋 Condiciones Médicas"),
            dcc.Textarea(id='edit-conditions', value=profile.get('medical_conditions', ''), style={'width': '100%', 'height': '60px', 'marginBottom': '20px'}),
        ]) if role == 'paciente' else None, # CORRECCIÓN: Solo renderiza la sección médica para pacientes
        
        # --- Contacto de Emergencia ---
        html.H4("🚨 Contacto de Emergencia", style={'color': COLORS['primary'], 'marginBottom': '16px', 'marginTop': '20px'}),
        
        html.Label("👤 Nombre del Contacto *"),
        dcc.Input(id='edit-emergency-contact', type='text', value=profile.get('emergency_contact', ''), required=True, style={'width': '100%', 'marginBottom': '10px'}),
        
        html.Label("📞 Teléfono del Contacto *"),
        dcc.Input(id='edit-emergency-phone', type='tel', value=profile.get('emergency_phone', ''), required=True, style={'width': '100%', 'marginBottom': '10px'}),

        dcc.Store(id='profile-user-role', data=role) # Usar dcc.Store para el rol
    ])
    
    return True, form_content, html.Div() # Abrir modal y precargar

# Callback 2: Guardar los datos actualizados
@app.callback(
    [Output('edit-profile-modal', 'is_open', allow_duplicate=True),
     Output('edit-profile-feedback', 'children', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)], # Forzar re-render de /my-data
    Input('save-profile-btn', 'n_clicks'),
    [State('user-session-state', 'data'),
      State('edit-fullname', 'value'),
      State('edit-email', 'value'),
      State('edit-phone', 'value'),
      State('edit-address', 'value'),
      State('edit-dni', 'value'),
      State('edit-birthdate', 'date'),
      State('edit-emergency-contact', 'value'),
      State('edit-emergency-phone', 'value'),
      # Los siguientes States solo existirán si role == 'paciente' (si el componente se renderiza)
      State('edit-blood-type', 'value'), 
      State('edit-allergies', 'value'), 
      State('edit-medications', 'value'), 
      State('edit-conditions', 'value'), 
      State('profile-user-role', 'data')], # Rol guardado en el Store
    prevent_initial_call=True
)
def save_profile_changes(n_clicks, user_session, fullname, email, phone, address, dni, birthdate, emergency_contact, emergency_phone, blood_type, allergies, medications, conditions, role):
    if not n_clicks or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update

    # Validación mínima de campos requeridos
    if not all([email, phone, dni, birthdate, emergency_contact, emergency_phone, fullname]): # CORRECCIÓN: Añadir fullname a la validación
        return dash.no_update, html.Div("⚠️ Completa todos los campos obligatorios marcados con *.", style={'color': 'red'}), dash.no_update

    username = user_session['username']
    
    try:
        # 1. Crear/Actualizar datos de perfil (incluyendo el nombre completo en el diccionario)
        profile_data = {
            'full_name': fullname, # Pasa el nombre para actualizar la clave principal
            'email': email,
            'phone': phone,
            'address': address,
            'dni': dni,
            'birth_date': birthdate,
            'emergency_contact': emergency_contact,
            'emergency_phone': emergency_phone,
        }

        # 2. Añadir datos médicos si es paciente
        if role == 'paciente':
            # Solo si el rol es 'paciente', intentará leer los States de los campos médicos
            profile_data.update({
                'blood_type': blood_type,
                'allergies': allergies,
                'current_medications': medications,
                'medical_conditions': conditions
            })
        
        # CORRECCIÓN: La función db.save_user_profile se modificó para manejar la actualización de full_name
        db.save_user_profile(username, profile_data) 
        
        feedback = html.Div("✅ Perfil actualizado correctamente.", style={'color': 'green'})
        
        # Forzar el cierre del modal y la recarga de la página de datos
        return False, feedback, '/my-data'
        
    except Exception as e:
        print(f"Error guardando perfil: {e}")
        feedback = html.Div(f"❌ Error al guardar: {str(e)}", style={'color': 'red'})
        return dash.no_update, feedback, dash.no_update

# Callback 3: Cerrar Modal de Edición
@app.callback(
    [Output('edit-profile-modal', 'is_open', allow_duplicate=True),
     Output('edit-profile-feedback', 'children', allow_duplicate=True)],
    Input('cancel-profile-btn', 'n_clicks'),
    prevent_initial_call=True
)
def close_edit_profile_modal(n_clicks):
    if n_clicks:
        return False, html.Div()
    return dash.no_update, dash.no_update


# Callback de navegación principal (Se mantiene)
@app.callback(
    [Output('page-content','children'), 
     Output('user-session-state', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    Input('url','pathname'), 
    State('url', 'search'), 
    State('user-session-state', 'data'),
    prevent_initial_call='initial_duplicate'
)
def display_page(pathname, search, current_session):
    
    query_params = parse_qs(urlparse(search).query)
    username_url = query_params.get('user', [None])[0]
    role_url = query_params.get('role', [None])[0]
    
    user_session = {}
    if username_url and role_url:
        user_data = _USER_DB.get(username_url)
        if user_data and user_data['role'] == role_url:
            user_session = {'username': username_url, 'role': role_url, 'full_name': user_data.get('full_name')}
    
    if user_session and user_session.get('username'):
        username = user_session['username']
        role = user_session['role']
        full_name = user_session['full_name']
        
        session_search = f"?{urlencode({'user': username, 'role': role})}"
        updated_session = user_session
        
        if pathname == '/my-data':
            return get_user_data_layout(username, full_name, role, session_search), updated_session, dash.no_update 
        
        if pathname == '/my-questionnaires' and role == 'paciente':
            return get_questionnaire_history_layout(username, full_name, session_search), updated_session, dash.no_update 
        
        # NUEVO: VISTA DE CITAS DEL PACIENTE
        if pathname == '/view-patient-appointments' and role == 'paciente':
            return get_view_appointments_layout_patient(username, full_name, session_search), updated_session, dash.no_update 
        
        if pathname == '/patient-data-viewer' and role == 'medico':
            return get_patient_data_viewer_layout(username, full_name, session_search), updated_session, dash.no_update 
            
        if pathname == '/view-appointments':
            # Incluir el modal de edición de citas aquí para que siempre exista en esta vista.
            return get_view_appointments_layout(username, full_name, role, session_search), updated_session, dash.no_update 
            
        if pathname in ['/', '/login', '/register']:
            if role == 'medico':
                return get_doctor_dashboard(username, full_name, session_search), updated_session, dash.no_update 
            elif role == 'paciente':
                return get_patient_dashboard(username, full_name, session_search), updated_session, dash.no_update 
    
    if pathname == '/register':
        return get_register_layout(), {}, dash.no_update
    
    return get_login_layout(), {}, dash.no_update

# Callback: Login (Se mantiene)
# Callback: Login (Se mantiene)
@app.callback(
    [Output('page-content','children', allow_duplicate=True),
     Output('login-feedback','children'),
     Output('url', 'pathname', allow_duplicate=True),
     Output('url', 'search', allow_duplicate=True)],
    Input('login-button','n_clicks'),
    [State('login-username','value'),
     State('login-password','value'),
     State('login-role','value')],
    prevent_initial_call=True
)
def login(n_clicks, username, password, role):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, html.Div("⚠️ Haz clic en el botón para iniciar sesión", style={'color':'orange'}), dash.no_update, dash.no_update
    
    if not username or not password or not role:
        return dash.no_update, html.Div("⚠️ Completa todos los campos", style={'color':'red'}), dash.no_update, dash.no_update
        
    user_data = db.authenticate_user(username, password)
    if not user_data or user_data['role'] != role:
        return dash.no_update, html.Div("❌ Credenciales incorrectas", style={'color':'red'}), dash.no_update, dash.no_update
        
    session_params = urlencode({'user': username, 'role': role})
    return dash.no_update, "", "/", f"?{session_params}"

# Callback: Mostrar/Ocultar contraseña (Ojo)
@app.callback(
    Output("login-password", "type"),
    Output("password-eye", "children"),
    Input("password-eye", "n_clicks"),
    State("login-password", "type"),
    prevent_initial_call=True
)
def toggle_password(n_clicks, current_type):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, dash.no_update
    if current_type == "password":
        return "text", "🙈"
    return "password", "👁️"

def login(n_clicks, username, password, role):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, html.Div("⚠️ Haz clic en el botón para iniciar sesión", style={'color':'orange'}), dash.no_update, dash.no_update
        
    if not username or not password or not role:
        return dash.no_update, html.Div("⚠️ Completa todos los campos", style={'color':'red'}), dash.no_update, dash.no_update
    
    user_data = db.authenticate_user(username, password)
    if not user_data or user_data['role'] != role:
        return dash.no_update, html.Div("❌ Credenciales incorrectas", style={'color':'red'}), dash.no_update, dash.no_update
    
    session_params = urlencode({'user': username, 'role': role})
    
    return dash.no_update, "", "/", f"?{session_params}"

# Callback: Navegación de Botones/Enlaces Internos (CORREGIDO)
# Callback: Navegación de Botones/Enlaces Internos (CORREGIDO DE FORMA SEGURA)
@app.callback(
    Output('url', 'search', allow_duplicate=True),
    Input('url', 'pathname'), # <- ¡El gran cambio! Solo escuchamos si la ruta cambia
    [State('user-session-state', 'data'),
     State('url', 'search')],
    prevent_initial_call=True
)
def handle_internal_navigation(pathname, user_data, current_search):
    # Si no hay sesión activa o estamos cerrando sesión, no hacemos nada
    if not user_data or not user_data.get('username') or pathname in ['/login', '/register']:
        return dash.no_update

    # Generamos los parámetros de búsqueda con los datos del usuario
    session_params = urlencode({'user': user_data['username'], 'role': user_data['role']})
    new_search = f"?{session_params}"
    
    # Si la URL perdió la información del usuario en el clic, se la volvemos a inyectar
    if new_search != current_search:
        return new_search
            
    return dash.no_update
# Callback: Registro (VALIDACIONES DE FORMATO APLICADAS)
@app.callback(
    Output('register-feedback','children'), 
    Input('register-button','n_clicks'),
    [State('register-username','value'), 
     State('register-password','value'), 
     State('register-role','value'), 
     State('register-fullname','value'),
     State('register-email','value'),
     State('register-phone','value'),
     State('register-address','value'),
     State('register-dni','value'),
     State('register-birthdate','date'),
     State('register-blood-type','value'),
     State('register-allergies','value'),
     State('register-medications','value'),
     State('register-conditions','value'),
     State('register-emergency-contact','value'),
     State('register-emergency-phone','value')],
    prevent_initial_call=True
)
def register_user_complete(n_clicks, username, password, role, fullname, email, phone, address, dni, birthdate, blood_type, allergies, medications, conditions, emergency_contact, emergency_phone):
    if n_clicks is None or n_clicks == 0:
        return html.Div("⚠️ Haz clic en el botón para registrar", style={'color':'orange'})
        
    required_fields = [username, password, role, fullname, email, phone, dni, birthdate, emergency_contact, emergency_phone]
    if not all(required_fields):
        return html.Div("⚠️ Completa todos los campos obligatorios (*)", style={'color':'red'})
    
    # ------------------ VALIDACIONES DE FORMATO ------------------
    # 1. Email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return html.Div("❌ Error de formato: El email no es válido.", style={'color':'red'})
        
    # 2. DNI/NIE (8 dígitos + 1 letra o X/Y/Z + 7 dígitos + 1 letra, opcionalmente con guiones/espacios)
    dni_pattern = re.compile(r"^[XYZ]?\d{7,8}[A-Z]$", re.IGNORECASE)
    if not dni_pattern.match(dni.strip().replace('-', '').replace(' ', '')):
        return html.Div("❌ Error de formato: DNI/NIE debe ser 8 números + letra (ej: 12345678X o Y0000000A).", style={'color':'red'})

    # 3. Teléfono (Permite formatos internacionales comunes: +XX XXX XXX XXX o 9-12 dígitos)
    phone_pattern = re.compile(r"^\+?\s?(\d{1,3})?\s?(\d{2,4}\s?){2,5}\d{1,4}$")
    if not phone_pattern.match(phone.strip()) or not phone_pattern.match(emergency_phone.strip()):
            return html.Div("❌ Error de formato: Teléfono debe tener 9-12 dígitos, opcionalmente con prefijo + y espacios.", style={'color':'red'})
        
    # ------------------ FIN VALIDACIONES DE FORMATO ------------------

    if _USER_DB.get(username): 
        return html.Div("❌ El usuario ya existe", style={'color':'red'})
    
    try:
        db.add_user(username, password, role, fullname)
        
        profile_data = {
            'email': email,
            'phone': phone,
            'address': address,
            'dni': dni,
            'birth_date': birthdate,
            'emergency_contact': emergency_contact,
            'emergency_phone': emergency_phone,
            'blood_type': blood_type,
            'allergies': allergies,
            'current_medications': medications,
            'medical_conditions': conditions
        }
        
        db.save_user_profile(username, profile_data)
        
        return html.Div("✅ Usuario registrado correctamente con toda la información. Ahora puedes iniciar sesión.", style={'color':'green'})
    except Exception as e:
        return html.Div(f"❌ Error: {str(e)}", style={'color':'red'})

# Callback: Cargar pacientes no asignados para el dropdown del médico (NUEVO)
@app.callback(
    Output('unassigned-patient-select', 'options'),
    [Input('url', 'pathname'),
     Input('associate-patient-button', 'n_clicks')], # Recargar tras asociar
    State('current-user-data', 'data')
)
def load_unassigned_patients_for_doctor(pathname, n_clicks_associate, user_data):
    if pathname == '/' and user_data.get('role') == 'medico':
        try:
            doctor_username = user_data['username']
            patients = db.get_unassigned_patients_or_unassigned_to_doctor(doctor_username)
            
            return [
                {'label': f"👤 {p['full_name']} ({p['username']}) - {'No asignado' if p['is_unassigned'] else 'Reasignar'}", 'value': p['username']}
                for p in patients
            ]
        except Exception as e:
            print(f"Error cargando pacientes para asociación: {e}")
            return [{'label': f"Error: {e}", 'value': 'error', 'disabled': True}]
    return []


# Callback: Asociar Paciente al Médico (REEMPLAZA AÑADIR PACIENTE)
@app.callback(
    [Output('associate-patient-feedback','children'), 
     Output('unassigned-patient-select','value'), 
     Output('patient-diagnosis-input','value')],
    Input('associate-patient-button','n_clicks'),
    [State('current-user-data','data'), 
     State('unassigned-patient-select','value'), 
     State('patient-diagnosis-input','value')],
    prevent_initial_call=True
)
def associate_patient_to_doctor(n_clicks, user_data, patient_username, diagnosis):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update
        
    if not patient_username:
        return html.Div("⚠️ Selecciona un paciente para asociar.", style={'color':'red'}), dash.no_update, dash.no_update
    
    if not diagnosis:
        # CORRECCIÓN: Si el paciente ya está en _PATIENT_INFO_DB con diagnóstico, no pedimos uno nuevo
        patient_info = _PATIENT_INFO_DB.get(patient_username, {})
        if not patient_info.get('diagnosis'):
             return html.Div("⚠️ Ingresa el diagnóstico inicial del paciente.", style={'color':'red'}), dash.no_update, dash.no_update

    current_user = user_data['username']
    
    try:
        # Si el paciente existe en _USER_DB (que debería si está en el dropdown)
        patient_full_name = _USER_DB.get(patient_username, {}).get('full_name', 'N/A')
        
        # 1. Asociar el paciente al médico (usa el método add_patient, que actualiza o crea)
        db.add_patient(
            username=patient_username, 
            diagnosis=diagnosis or _PATIENT_INFO_DB.get(patient_username, {}).get('diagnosis', 'No especificado'), # Usa diagnóstico existente si no se proporciona uno nuevo
            doctor_user=current_user, 
            physio_user=None # Dejar physio en None
        )
        
        feedback = html.Div(f"✅ Paciente {patient_full_name} asociado/reasignado a tu cargo.", style={'color':'green'})
        return feedback, None, "" # Limpiar campos y feedback
        
    except Exception as e:
        return html.Div(f"❌ Error al asociar paciente: {e}", style={'color':'red'}), dash.no_update, dash.no_update

# Callback: Cerrar Sesión (Se mantiene)
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('url', 'search', allow_duplicate=True),
     Output('user-session-state', 'data', allow_duplicate=True)],
    Input('logout-button','n_clicks'),
    prevent_initial_call=True
)
def logout(n_clicks):
    if n_clicks and n_clicks > 0:
        return '/login', '', {} 
    return dash.no_update, dash.no_update, dash.no_update

# Callback: Cargar pacientes en el dropdown del Visor de Pacientes (Se mantiene)
@app.callback(
    Output('doctor-patient-select', 'options'),
    [Input('url', 'pathname'), 
     Input('doctor-patient-select', 'search_value')], 
    State('user-session-state', 'data')
)
def load_patients_for_viewer(pathname, search_value, user_data):
    if pathname == '/patient-data-viewer' and user_data.get('role') == 'medico':
        try:
            patients = db.get_all_patients_for_doctor(user_data['username'])
            
            if search_value:
                search_term = search_value.lower()
                patients = [
                    p for p in patients if search_term in p['full_name'].lower() or search_term in p['username'].lower()
                ]
                
            return [
                {'label': f"👤 {p['full_name']} ({p['username']})", 'value': p['username']}
                for p in patients
            ]
        except Exception as e:
            print(f"Error loading patients for viewer: {e}")
            return []
    return []

# Callback: Mostrar datos del paciente seleccionado en el Visor (MODIFICADA para incluir gráficos)
# Callback: Mostrar datos del paciente seleccionado en el Visor (MODIFICADA para incluir HISTORIAL DETALLADO)
@app.callback(
    [Output('doctor-patient-display', 'children'),
     Output('doctor-selected-patient-username', 'data', allow_duplicate=True),
     Output('doctor-ecg-container', 'style')],
    Input('doctor-patient-select', 'value'),
    prevent_initial_call=True
)
def display_selected_patient_data(patient_username):
    if not patient_username:
        return (html.P("Selecciona un paciente de la lista para comenzar.", 
                       style={'textAlign': 'center', 'color': COLORS['muted'], 'padding': '20px'}), 
                None, 
                {'display': 'none'}) 
    
    try:
        user_data = db.get_complete_user_data(patient_username)
        
        # --- GENERACIÓN DE GRÁFICOS ---
        # --- GENERACIÓN DE GRÁFICOS ---
        fig_q1, fig_q2 = create_questionnaire_plot(user_data.get('questionnaires', []))
        exercise_fig = create_exercise_plot(user_data.get('exercises', []))
        
        # --- CARDS DE INFORMACIÓN PERSONAL Y MÉDICA ---
        personal_info = html.Div([
            html.H4("📋 Información Personal", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
            dbc.Row([
                dbc.Col([
                    html.P([html.Strong("👤 Nombre: "), user_data.get('basic_info', {}).get('full_name', 'N/A')]),
                    html.P([html.Strong("📧 Email: "), user_data.get('profile', {}).get('email', 'N/A')]),
                    html.P([html.Strong("📞 Teléfono: "), user_data.get('profile', {}).get('phone', 'N/A')]),
                ], width=6),
                dbc.Col([
                    html.P([html.Strong("🆔 DNI: "), user_data.get('profile', {}).get('dni', 'N/A')]),
                    html.P([html.Strong("🎂 Fecha Nacimiento: "), user_data.get('profile', {}).get('birth_date', 'N/A')]),
                    html.P([html.Strong("🏠 Dirección: "), user_data.get('profile', {}).get('address', 'N/A')]),
                ], width=6)
            ])
        ], style=STYLES['card'])
        
        medical_info = html.Div([
            html.H4("🏥 Información Médica", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
            dbc.Row([
                dbc.Col([
                    html.P([html.Strong("📝 Diagnóstico: "), user_data.get('patient_info', {}).get('diagnosis', 'N/A')]),
                    html.P([html.Strong("👨‍⚕️ Médico: "), user_data.get('patient_info', {}).get('doctor_user', 'N/A')]),
                    html.P([html.Strong("🩸 Tipo Sangre: "), user_data.get('profile', {}).get('blood_type', 'N/A')]),
                ], width=6),
                dbc.Col([
                    html.P([html.Strong("⚠️ Alergias: "), user_data.get('profile', {}).get('allergies', 'N/A')]),
                    html.P([html.Strong("💊 Medicamentos: "), user_data.get('profile', {}).get('current_medications', 'N/A')]),
                    html.P([html.Strong("📋 Condiciones: "), user_data.get('profile', {}).get('medical_conditions', 'N/A')]),
                ], width=6)
            ])
        ], style=STYLES['card'])

        # --- CARDS DE GRÁFICOS ---
        graph_q_card = html.Div([
            html.H4("📈 Progreso de Cuestionarios", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=fig_q1, config={'displayModeBar': False}), width=12, lg=6),
                dbc.Col(dcc.Graph(figure=fig_q2, config={'displayModeBar': False}), width=12, lg=6),
            ])
        ], style=STYLES['card'])

        graph_e_card = html.Div([
            html.H4("📊 Gráfica de Ejercicios", style={'color': COLORS['primary'], 'marginBottom': '15px'}),
            dcc.Graph(figure=exercise_fig),
        ], style=STYLES['card'])

        # --- NUEVO: LISTAS DE HISTORIAL DETALLADO (IGUAL QUE EL PACIENTE) ---
        
        # 1. Historial de Cuestionarios (Texto)
        quests_list = user_data.get('questionnaires', [])
        # Ordenar por fecha descendente
        quests_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        history_q_text_card = html.Div([
            html.H4("📝 Historial Detallado de Respuestas", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
            html.Div([
                html.Div([
                    html.H5(f"📋 {q.get('questionnaire_title', 'Cuestionario')}", 
                                    style={'color': COLORS['primary'], 'marginBottom': '8px', 'fontSize': '16px'}),
                    html.P(f"🕒 {q.get('timestamp', 'Fecha no disponible')}", 
                                    style={'color': COLORS['muted'], 'fontSize': '14px', 'marginBottom': '10px'}),
                    
                    html.Ul([
                        html.Li([
                            html.Strong(f"{key.replace('_', ' ').title()}: "),
                            html.Span(str(value))
                        ], style={'marginBottom': '4px', 'fontSize': '13px', 'color': COLORS['text']})
                        for key, value in q.get('responses', {}).items()
                    ], style={'paddingLeft': '20px'}),
                    
                    html.Hr(style={'margin': '15px 0'})
                ]) for q in quests_list
            ], style={'maxHeight': '400px', 'overflowY': 'auto'}) # Scroll para que no ocupe demasiado si hay muchos
        ] if quests_list else html.P("📭 No hay cuestionarios completados."), style=STYLES['card'])

        # 2. Historial de Ejercicios (Texto)
        ex_list = user_data.get('exercises', [])
        ex_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        history_e_text_card = html.Div([
            html.H4("💪 Historial Detallado de Ejercicios", style={'color': COLORS['primary'], 'marginBottom': '20px'}),
            html.Div([
                html.Div([
                    html.P([
                        html.Strong(f"Ejercicio: "),
                        html.Span(ex.get('exercise_name', ex['exercise_id'])),
                        html.Br(),
                        html.Strong(f"Fecha: "),
                        html.Span(ex['timestamp']),
                        html.Br(),
                        html.Strong(f"Series: "),
                        html.Span(f"{ex.get('sets', 'N/A')} × {ex.get('reps', 'N/A')} repeticiones"),
                        html.Br(),
                        html.Strong(f"Duración: "),
                        html.Span(f"{ex['duration_seconds']} segundos" if ex.get('duration_seconds') else "No registrada")
                    ], style={'marginBottom': '15px', 'padding': '10px', 'background': '#f8f9fa', 'borderRadius': '8px'})
                ]) for ex in ex_list
            ], style={'maxHeight': '400px', 'overflowY': 'auto'})
        ] if ex_list else html.P("📭 No hay ejercicios registrados."), style=STYLES['card'])
        
        # --- RETORNO DEL LAYOUT COMPLETO ---
        return html.Div([
            # Fila 1: Información Personal y Médica
            dbc.Row([
                dbc.Col([personal_info, medical_info], width=12),
            ]),
            # Fila 2: Gráficas
            dbc.Row([
                dbc.Col([graph_q_card], width=12, lg=6), 
                dbc.Col([graph_e_card], width=12, lg=6),
            ]),
            # Fila 3: Historiales Detallados (Texto) - NUEVO
            dbc.Row([
                dbc.Col([history_q_text_card], width=12, lg=6),
                dbc.Col([history_e_text_card], width=12, lg=6),
            ]),
        ]), patient_username, {'display': 'block'} 
    
    except Exception as e:
        print(f"Error al cargar datos y gráficos del paciente: {e}")
        return html.Div(f"❌ Error al cargar datos: {str(e)}", style={'color': 'red'}), patient_username, {'display': 'none'}

# Callback: Cancelar Edición de Cita (CORREGIDO: Ahora sólo tiene el botón de Cerrar)
@app.callback(
    Output('edit-appointment-modal', 'is_open', allow_duplicate=True),
    Input('cancel-edit-appt-btn', 'n_clicks'),
    prevent_initial_call=True
)
def cancel_edit_appointment(n_clicks):
    if n_clicks:
        return False
    return dash.no_update

# Callback: Cargar pacientes asignados para el dropdown del médico (NUEVO)
@app.callback(
    Output('assigned-patient-select-disassociate', 'options'),
    [Input('url', 'pathname'),
     Input('disassociate-patient-button', 'n_clicks')], # Recargar tras desasociar
    State('current-user-data', 'data')
)
def load_assigned_patients_for_disassociation(pathname, n_clicks_disassociate, user_data):
    if pathname == '/' and user_data.get('role') == 'medico':
        try:
            doctor_username = user_data['username']
            patients = db.get_all_patients_for_doctor(doctor_username) # Ya obtiene solo los asignados
            
            return [
                {'label': f"👤 {p['full_name']} ({p['username']})", 'value': p['username']}
                for p in patients
            ]
        except Exception as e:
            print(f"Error cargando pacientes para desasociación: {e}")
            return [{'label': f"Error: {e}", 'value': 'error', 'disabled': True}]
    return []

# Callback: Desasociar Paciente del Médico (NUEVO)
@app.callback(
    [Output('disassociate-patient-feedback','children'), 
     Output('assigned-patient-select-disassociate','value'), # Limpiar campo
     Output('unassigned-patient-select', 'options', allow_duplicate=True)], # Recargar la lista de asignables
    Input('disassociate-patient-button','n_clicks'),
    [State('assigned-patient-select-disassociate','value'), 
     State('current-user-data','data')],
    prevent_initial_call=True
)
def disassociate_patient(n_clicks, patient_username, user_data):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update
        
    if not patient_username:
        return html.Div("⚠️ Selecciona un paciente para desasociar.", style={'color':'red'}), dash.no_update, dash.no_update
    
    try:
        # Desasociar el paciente
        if db.disassociate_patient(patient_username):
            feedback = html.Div(f"✅ Paciente {patient_username} desasociado correctamente.", style={'color':'green'})
            
            # Recargar la lista de pacientes que el doctor puede asignar
            doctor_username = user_data['username']
            patients_for_reassignment = db.get_unassigned_patients_or_unassigned_to_doctor(doctor_username)
            new_unassigned_options = [
                {'label': f"👤 {p['full_name']} ({p['username']}) - {'No asignado' if p['is_unassigned'] else 'Reasignar'}", 'value': p['username']}
                for p in patients_for_reassignment
            ]

            return feedback, None, new_unassigned_options
        else:
            feedback = html.Div(f"❌ Error: Paciente {patient_username} no encontrado.", style={'color':'red'})
            return feedback, dash.no_update, dash.no_update
            
    except Exception as e:
        return html.Div(f"❌ Error al desasociar paciente: {e}", style={'color':'red'}), dash.no_update, dash.no_update

# Callback: Cargar pacientes asignados para el dropdown del médico (NUEVO)
@app.callback(
    Output('assigned-patient-select-disassociate', 'options', allow_duplicate=True),
    Input('disassociate-patient-button', 'n_clicks'), # Recargar tras desasociar
    State('current-user-data', 'data'),
    prevent_initial_call=True
)
def reload_assigned_patients_for_disassociation(n_clicks_disassociate, user_data):
    # Se activará después de la desasociación para actualizar la lista.
    if n_clicks_disassociate and n_clicks_disassociate > 0:
        try:
            doctor_username = user_data['username']
            patients = db.get_all_patients_for_doctor(doctor_username)
            return [
                {'label': f"👤 {p['full_name']} ({p['username']})", 'value': p['username']}
                for p in patients
            ]
        except Exception as e:
            return [{'label': f"Error: {e}", 'value': 'error', 'disabled': True}]
    return dash.no_update # Si no es por el botón de desasociar, no actualizar

# ==========================================================================
# --- CALLBACK DE ACTUALIZACIÓN DE SENSORES EN TIEMPO REAL (ESTABLE) ---
# ==========================================================================
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-export-csv", "n_clicks"), # Usar el clic como disparador principal
    State("doctor-patient-select", "value"),
    prevent_initial_call=True, # IMPORTANTE
)
def export_patient_data_to_csv(n_clicks, patient_username):
    # Validar que se hizo clic y que hay un paciente seleccionado
    if n_clicks is None or n_clicks == 0 or not patient_username:
        return dash.no_update
    
    # 1. Obtener datos de la DB
    user_data = db.get_complete_user_data(patient_username)
    
    # 2. Preparar datos de ejercicios
    exercises = user_data.get('exercises', [])
    if exercises:
        df_exercises = pd.DataFrame(exercises)
        df_exercises['Tipo_Dato'] = 'EJERCICIO'
    else:
        df_exercises = pd.DataFrame()

    # 3. Preparar datos de cuestionarios (aplanando las respuestas)
    quests = user_data.get('questionnaires', [])
    quest_rows = []
    for q in quests:
        row = {
            'timestamp': q['timestamp'],
            'exercise_name': q['questionnaire_title'],
            'Tipo_Dato': 'CUESTIONARIO'
        }
        # Añadir respuestas como columnas extras
        for k, v in q['responses'].items():
            row[f"Respuesta_{k}"] = v
        quest_rows.append(row)
    
    df_quests = pd.DataFrame(quest_rows)

    # 4. Combinar todo en un reporte único
    df_final = pd.concat([df_exercises, df_quests], axis=0, ignore_index=True)
    
    # Añadir info del paciente a cada fila
    df_final['Paciente'] = user_data['basic_info']['full_name']
    df_final['DNI'] = user_data['profile'].get('dni', 'N/A')

    # 5. Generar CSV
    return dcc.send_data_frame(df_final.to_csv, f"reporte_{patient_username}_{datetime.now().strftime('%Y%m%d')}.csv", index=False)

@app.callback(
    [Output('live-ecg-graph', 'figure'), 
     Output('live-imu-graph', 'figure'),
     Output('ecg-status-msg', 'children'), 
     Output('imu-status-msg', 'children')],
    Input('sensor-interval', 'n_intervals'),
    State('exercise-execution-modal', 'is_open')
)
def update_sensor_charts(n, is_open):
    """Actualiza las gráficas con ejes y cuadrículas totalmente fijas para evitar parpadeos"""
    if not is_open or not os.path.exists(STREAM_FILE):
        empty_fig = go.Figure().update_layout(height=250, template="plotly_white")
        return empty_fig, empty_fig, "⏸️ Esperando datos...", "⏸️ Esperando datos..."
    
    try:
        # 1. Cargar los últimos 50 puntos
        df = pd.read_csv(STREAM_FILE).tail(50)
        if df.empty or len(df) < 2:
            return dash.no_update, dash.no_update, "📊 Recolectando...", "📊 Recolectando..."
        
        x_vals = list(range(50))
        y_ecg = df['ecg'].tolist()
        y_imu = df['accel_x'].tolist()
        
        # Relleno preventivo para mantener el ancho de la línea constante al inicio
        while len(y_ecg) < 50: y_ecg.insert(0, None)
        while len(y_imu) < 50: y_imu.insert(0, None)
        
        # 2. Gráfica ECG Rígida
        has_arrhythmia = (df['status_ecg'] == 'RED_FLAG_ARRHYTHMIA').any()
        fig_ecg = go.Figure(go.Scatter(
            x=x_vals, y=y_ecg, mode='lines', 
            line=dict(color="#ef4444" if has_arrhythmia else "#10b981", width=2.5),
            hoverinfo='none'
        ))
        
        fig_ecg.update_layout(
            height=250,
            margin=dict(l=60, r=20, t=40, b=40), # Margen izquierdo fijo para evitar saltos horizontales
            template="plotly_white",
            title="❤️ Monitorización Cardíaca en Vivo",
            xaxis=dict(range=[0, 49], fixedrange=True, showgrid=True, gridcolor="#f0f0f0"),
            yaxis=dict(
                range=[-1.0, 2.0],  # Rango vertical estricto
                fixedrange=True,
                tickformat=".1f",   # Mantiene el ancho de los números constante (ej. 1.0 vs 0.9)
                dtick=0.5,          # Cuadrícula inamovible
                gridcolor="#f0f0f0"
            ),
            showlegend=False,
            uirevision='constant'   # Mantiene el estado de la UI entre actualizaciones
        )

        # 3. Gráfica IMU Rígida
        has_fatigue = (df['status_imu'] == 'RED_FLAG_FATIGUE').any()
        fig_imu = go.Figure(go.Scatter(
            x=x_vals, y=y_imu, mode='lines', fill='tozeroy', 
            line=dict(color="#f59e0b" if has_fatigue else "#3b82f6", width=2.5),
            hoverinfo='none'
        ))
        
        fig_imu.update_layout(
            height=250,
            margin=dict(l=60, r=20, t=40, b=40),
            template="plotly_white",
            title="📐 Ángulo de Rodilla (Grados)",
            xaxis=dict(range=[0, 49], fixedrange=True, showgrid=True, gridcolor="#f0f0f0"),
            yaxis=dict(
                range=[0, 100],     # Rango fijo para el ángulo de la rodilla
                fixedrange=True,
                tickformat="d",     # Formato entero para estabilidad
                dtick=25,           # Divisiones claras
                gridcolor="#f0f0f0"
            ),
            showlegend=False,
            uirevision='constant'
        )
        
        ecg_msg = "⚠️ ARRITMIA DETECTADA" if has_arrhythmia else "✅ Ritmo Normal"
        imu_msg = "⚠️ FATIGA DETECTADA" if has_fatigue else "✅ Movimiento Fluido"
        
        return fig_ecg, fig_imu, ecg_msg, imu_msg
        
    except Exception as e:
        print(f"Error en sensores: {e}")
        return dash.no_update, dash.no_update, "❌ Error", "❌ Error"

# --- FUNCIONES DEL SIMULADOR ---
def generate_ecg_sample(t, base_bpm=75):
    heart_rate = base_bpm / 60.0
    ecg = 0.5 * np.sin(2 * np.pi * heart_rate * t)
    qrs_time = t % (1.0 / heart_rate)
    if 0.1 < qrs_time < 0.2:
        ecg += 0.8 * np.exp(-((qrs_time - 0.15) ** 2) / 0.001)
    noise = np.random.normal(0, 0.05)
    ecg += noise
    status = "RED_FLAG_ARRHYTHMIA" if abs(noise) > 0.12 else "NORMAL"
    return ecg, status

def generate_imu_sample(t, exercise_phase='extension'):
    angle = min(90, 45 * np.sin(0.5 * t) + 45) if exercise_phase == 'extension' else max(0, 90 - 45 * np.sin(0.5 * t))
    accel_x = angle
    accel_y = np.random.normal(0, 2)
    accel_z = np.random.normal(10, 1)
    gyro_x = 20 * np.cos(0.5 * t)
    gyro_y = np.random.normal(0, 1)
    gyro_z = np.random.normal(0, 1)
    status = "RED_FLAG_FATIGUE" if abs(accel_y) > 5 or abs(gyro_y) > 3 else "NORMAL"
    return accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, status

def init_stream_file():
    with open(STREAM_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'ecg', 'accel_x', 'accel_y', 'accel_z', 
                        'gyro_x', 'gyro_y', 'gyro_z', 'status_ecg', 'status_imu'])

def run_simulator():
    init_stream_file()
    start_time = time.time()
    sample_count = 0
    FAST_SAMPLE_RATE = 0.1 
    while True:
        try:
            current_time = time.time() - start_time
            exercise_phase = 'extension' if (sample_count // 20) % 2 == 0 else 'flexion'
            base_bpm = 75 + 10 * np.sin(0.1 * current_time)
            ecg, status_ecg = generate_ecg_sample(current_time, base_bpm)
            imu_data = generate_imu_sample(current_time, exercise_phase)
            with open(STREAM_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    f"{ecg:.4f}", f"{imu_data[0]:.2f}", f"{imu_data[1]:.2f}", f"{imu_data[2]:.2f}",
                    f"{imu_data[3]:.2f}", f"{imu_data[4]:.2f}", f"{imu_data[5]:.2f}",
                    status_ecg, imu_data[6]
                ])
            sample_count += 1
            time.sleep(FAST_SAMPLE_RATE)
        except Exception as e:
            print(f"⚠️ Error en simulador: {e}")
            break

# ==========================================================================
# --- INICIO DEL SISTEMA ---
# ==========================================================================
if __name__ == '__main__':
    # 1. Iniciar el simulador PRIMERO
    print("✅ Iniciando hilos de simulación...")
    simulation_thread = threading.Thread(target=run_simulator, daemon=True)
    simulation_thread.start()
    
    # Pausa para asegurar que data/sensor_data_stream.csv existe antes de que Dash cargue
    time.sleep(1.5) 
    
    print("🚀 Servidor RehabiDesk levantando en http://127.0.0.1:8050")
    
    # 2. Ejecución del servidor
    # debug=True + use_reloader=False es la combinación más estable para hilos secundarios
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=8050, 
        use_reloader=False # CRÍTICO: Si está en True, cierra el hilo del simulador y da error de señal
    )



