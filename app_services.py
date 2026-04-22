from datetime import datetime, timedelta
import json


class FightService:
    @staticmethod
    def sync_weighin_date(fight_date):
        if not fight_date:
            return None
        try:
            fight_dt = datetime.fromisoformat(fight_date).date()
            return (fight_dt - timedelta(days=1)).isoformat()
        except Exception:
            return None

    @staticmethod
    def add_fight_entry(user_db, username, fight_date, fight_target_weight, weigh_in_date, opponent, location, current_weight):
        if not username:
            return False, "Usuario no autenticado.", None

        if not fight_date or not opponent or not location:
            return False, "Completa fecha, oponente y lugar del combate.", None

        if username not in user_db:
            return False, "Usuario no encontrado en la base de datos.", None

        try:
            target_weight_value = float(fight_target_weight) if fight_target_weight not in [None, ""] else None
        except (TypeError, ValueError):
            target_weight_value = None

        if not weigh_in_date:
            weigh_in_date = FightService.sync_weighin_date(fight_date)

        fights = user_db[username].get("fights", [])
        fights.append({
            "date": fight_date,
            "opponent": str(opponent).strip(),
            "location": str(location).strip(),
            "target_weight": target_weight_value,
            "weigh_in_date": weigh_in_date,
        })
        user_db[username]["fights"] = fights

        if current_weight not in [None, ""]:
            try:
                profile_data = user_db[username].get("profile", {})
                profile_data["current_weight"] = float(current_weight)
                user_db[username]["profile"] = profile_data
            except (TypeError, ValueError):
                pass

        return True, "Combate agregado correctamente.", fights

    @staticmethod
    def get_fight_selector_options(user_db, username):
        if not username:
            return []

        fights = user_db.get(username, {}).get("fights", [])
        if not fights:
            return []

        return [
            {
                "label": (
                    f"{fight.get('date', 'N/A')} vs {fight.get('opponent', 'Rival')} @ {fight.get('location', 'Unknown')} "
                    f"| {fight.get('target_weight', 'N/A')} kg | 🗓️ {fight.get('weigh_in_date', 'N/A')}"
                ),
                "value": json.dumps(fight),
            }
            for fight in fights
        ]

    @staticmethod
    def parse_selected_fight_data(selected_fight_data):
        if isinstance(selected_fight_data, dict):
            return selected_fight_data
        if isinstance(selected_fight_data, str) and selected_fight_data.strip():
            try:
                parsed = json.loads(selected_fight_data)
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                return None
        return None


class ExerciseService:
    @staticmethod
    def get_recommended_exercises(health_status, injury_types, healthy_exercises, knee_exercises, elbow_exercises, shoulder_exercises):
        if health_status == "listo":
            return healthy_exercises

        if health_status == "lesionado" and injury_types:
            if not isinstance(injury_types, list):
                injury_types = [injury_types]

            combined_exercises = []
            seen_ids = set()
            injury_map = {
                "rodilla": knee_exercises,
                "codo": elbow_exercises,
                "hombro": shoulder_exercises,
            }

            for injury_type in injury_types:
                for ex in injury_map.get(injury_type, []):
                    ex_id = ex.get("id")
                    if ex_id not in seen_ids:
                        combined_exercises.append(ex)
                        seen_ids.add(ex_id)
            return combined_exercises

        return []

    @staticmethod
    def get_exercise_title(health_status, injury_types):
        if health_status == "lesionado" and injury_types:
            names = []
            for injury in injury_types:
                if injury == "rodilla":
                    names.append("Rodilla")
                elif injury == "codo":
                    names.append("Codo")
                elif injury == "hombro":
                    names.append("Hombro")
            if names:
                return f"Ejercicios de {' y '.join(names)}"
        return "Ejercicios para Luchador Sano"

    @staticmethod
    def resolve_exercise(pool, exercise_id):
        return next((ex for ex in (pool or []) if ex.get("id") == exercise_id), None)

    @staticmethod
    def compute_duration_seconds(start_time_iso):
        end_time = datetime.now()
        start_time_obj = datetime.fromisoformat(start_time_iso) if start_time_iso else end_time
        duration_seconds = int((end_time - start_time_obj).total_seconds())
        return end_time, duration_seconds


class AppointmentService:
    STATUS_MAP = {
        "scheduled": {"text": "Pendiente", "color": "warning"},
        "confirmed": {"text": "Confirmada", "color": "success"},
        "cancelled": {"text": "Cancelada", "color": "danger"},
        "attended": {"text": "Atendida", "color": "primary"},
        "default": {"text": "Desconocido", "color": "muted"},
    }

    @staticmethod
    def filter_appointments_by_type(appointments, filter_type="all"):
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        if filter_type == "today":
            appointments = [
                app for app in appointments
                if today_start <= datetime.fromisoformat(app["datetime"]) <= today_end
            ]
        elif filter_type == "past":
            appointments = [
                app for app in appointments
                if datetime.fromisoformat(app["datetime"]) < today_start
            ]

        appointments.sort(key=lambda x: x["datetime"], reverse=True)
        return appointments

    @staticmethod
    def validate_new_appointment(patient_username, date, time, hospital, office, user_data):
        if not patient_username or not date or not time or not hospital or not office:
            return False, "⚠️ Faltan campos obligatorios para crear la cita (excepto Comentarios).", None

        if not user_data or user_data.get("role") != "medico" or not user_data.get("username"):
            return False, "❌ Sesión inválida para agendar cita. Vuelve a iniciar sesión.", None

        try:
            appointment_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return False, "❌ Error: Formato de fecha/hora inválido.", None

        if appointment_dt <= datetime.now():
            return False, "❌ Error: No se puede crear una cita para un día u hora anterior a la actual.", None

        return True, "", appointment_dt.isoformat()

    @staticmethod
    def build_appointment_payload(patient_username, user_data, appointment_datetime, hospital, office, comments):
        return {
            "patient_username": patient_username,
            "professional_username": user_data["username"],
            "professional_name": user_data["full_name"],
            "professional_role": user_data["role"],
            "datetime": appointment_datetime,
            "hospital": hospital,
            "office": office,
            "comments": comments or "",
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
        }

    @staticmethod
    def resolve_patient_action(action_type):
        if "confirm-appt-patient-btn" in str(action_type):
            return "confirmed", "✅ Cita confirmada con éxito."
        if "cancel-appt-patient-btn" in str(action_type):
            return "cancelled", "❌ Cita cancelada. Historial actualizado."
        return None, ""
