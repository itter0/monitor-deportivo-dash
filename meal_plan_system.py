"""
Motor de planes de comida personalizados.
Implementa varias estrategias de generacion para aproximar un flujo similar al plan tactico.
"""

from enum import Enum
from datetime import datetime


class MealPlanGenerationMode(str, Enum):
    TEMPLATE = "template"
    GOAL_BASED = "goal_based"
    FIGHT_CAMP = "fight_camp"
    MANUAL_HYBRID = "manual_hybrid"


class MealWeightDirection(str, Enum):
    GAIN = "gain"
    CUT = "cut"
    MAINTAIN = "maintain"
    NONE = "none"


def _safe_float(value, default=None):
    try:
        if value in [None, ""]:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        if value in [None, ""]:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_weight_direction(current_weight, target_weight, selected_direction):
    direction = str(selected_direction or "none").strip().lower()
    if direction in [MealWeightDirection.GAIN.value, MealWeightDirection.CUT.value, MealWeightDirection.MAINTAIN.value]:
        return direction

    current = _safe_float(current_weight)
    target = _safe_float(target_weight)
    if current is None or target is None:
        return MealWeightDirection.NONE.value

    diff = current - target
    if diff > 0.75:
        return MealWeightDirection.CUT.value
    if diff < -0.75:
        return MealWeightDirection.GAIN.value
    return MealWeightDirection.MAINTAIN.value


def _estimate_calories(direction, current_weight, meals_per_day):
    base = 32 * max(50.0, _safe_float(current_weight, 70.0))
    if direction == MealWeightDirection.CUT.value:
        kcal = base - 400
        protein = 2.1
        carbs = 3.0
        fats = 0.8
    elif direction == MealWeightDirection.GAIN.value:
        kcal = base + 300
        protein = 1.9
        carbs = 5.0
        fats = 1.0
    elif direction == MealWeightDirection.MAINTAIN.value:
        kcal = base
        protein = 1.8
        carbs = 4.0
        fats = 0.9
    else:
        kcal = base
        protein = 1.7
        carbs = 3.5
        fats = 0.9

    return {
        "daily_kcal": int(round(kcal)),
        "protein_g_per_kg": protein,
        "carbs_g_per_kg": carbs,
        "fats_g_per_kg": fats,
        "meals_per_day": meals_per_day,
    }


def _build_template_plan(direction, macros, constraints):
    return (
        "Desayuno: avena + fruta + claras de huevo\n"
        "Media manana: yogurt griego + frutos secos\n"
        "Almuerzo: arroz + pechuga + ensalada\n"
        "Merienda: sandwich integral + pavo\n"
        "Cena: pescado + vegetales + papa cocida\n\n"
        f"Macros objetivo: {macros['daily_kcal']} kcal | "
        f"P {macros['protein_g_per_kg']} g/kg | "
        f"C {macros['carbs_g_per_kg']} g/kg | "
        f"G {macros['fats_g_per_kg']} g/kg\n"
        f"Restricciones a considerar: {constraints or 'Ninguna'}"
    )


def _build_goal_based_plan(direction, macros, days_left, target_weight):
    objective_line = "Objetivo principal: recomposicion y consistencia."
    if direction == MealWeightDirection.CUT.value:
        objective_line = "Objetivo principal: reducir peso preservando rendimiento."
    elif direction == MealWeightDirection.GAIN.value:
        objective_line = "Objetivo principal: aumentar masa magra con superavit controlado."
    elif direction == MealWeightDirection.MAINTAIN.value:
        objective_line = "Objetivo principal: sostener peso y optimizar recuperacion."

    return (
        f"{objective_line}\n"
        f"Horizonte: {days_left} dias | Peso objetivo: {target_weight if target_weight is not None else 'no definido'} kg\n"
        "Distribucion sugerida:\n"
        "1) Comida pre-entreno alta en carbohidratos complejos\n"
        "2) Comida post-entreno rica en proteina y carbohidrato rapido\n"
        "3) Cena con proteina magra, verduras y grasa saludable\n"
        "4) Ajuste semanal de porciones segun evolucion de peso\n\n"
        f"Macros objetivo: {macros['daily_kcal']} kcal | "
        f"P {macros['protein_g_per_kg']} g/kg | "
        f"C {macros['carbs_g_per_kg']} g/kg | "
        f"G {macros['fats_g_per_kg']} g/kg"
    )


def _build_fight_camp_plan(direction, macros, days_left):
    if days_left <= 7:
        phase_text = "Fase semana de pelea: bajo residuo, sodio controlado, hidratacion protocolizada."
    elif days_left <= 21:
        phase_text = "Fase de descarga: mantener energia con menor volumen digestivo."
    else:
        phase_text = "Fase base: calidad nutricional, adherencia y soporte de cargas altas."

    return (
        f"{phase_text}\n"
        "Bloques por fase:\n"
        "- Base: alimentos simples, fibra moderada, timing de carbohidratos alrededor del entreno\n"
        "- Descarga: disminuir volumen de fibra y controlar retencion\n"
        "- Fight week: estrategia de peso y glucogeno sin comprometer rendimiento\n\n"
        f"Direccion de peso: {direction}\n"
        f"Macros objetivo: {macros['daily_kcal']} kcal | "
        f"P {macros['protein_g_per_kg']} g/kg | "
        f"C {macros['carbs_g_per_kg']} g/kg | "
        f"G {macros['fats_g_per_kg']} g/kg"
    )


def _build_manual_hybrid_plan(base_plan, preferences):
    return (
        "Borrador automatico + personalizacion manual\n\n"
        f"{base_plan}\n\n"
        "Ajustes del atleta:\n"
        f"- Preferencias: {preferences or 'No especificadas'}\n"
        "- Reemplazar fuentes de carbohidrato/proteina segun tolerancia\n"
        "- Confirmar checklist de compras semanal\n"
        "- Definir colaciones para dias de doble sesion"
    )


def validate_meal_plan_advanced(plan_dict):
    warnings = []

    duration = _safe_int(plan_dict.get("duration"), 30)
    target_weight = _safe_float(plan_dict.get("target_weight"))
    current_weight = _safe_float(plan_dict.get("current_weight"))
    logic = plan_dict.get("generation_logic")

    if duration < 7:
        warnings.append("Duracion muy corta; considera al menos 7 dias para evaluar adherencia.")

    if current_weight is not None and target_weight is not None:
        delta = abs(current_weight - target_weight)
        if delta > 8:
            warnings.append("Diferencia de peso elevada; revisar seguridad y ritmo semanal.")

    if logic not in [m.value for m in MealPlanGenerationMode]:
        warnings.append("Logica de generacion no valida; se aplico modo template por defecto.")

    return {
        "warnings": warnings,
        "is_ok": len(warnings) == 0,
    }


def generate_personalized_meal_plan(
    name,
    generation_logic,
    current_weight,
    target_weight,
    duration_days,
    selected_weight_change,
    dietary_constraints,
    food_preferences,
    meals_per_day,
    fight_context=None,
):
    logic = str(generation_logic or MealPlanGenerationMode.TEMPLATE.value).strip().lower()
    if logic not in [m.value for m in MealPlanGenerationMode]:
        logic = MealPlanGenerationMode.TEMPLATE.value

    direction = _resolve_weight_direction(current_weight, target_weight, selected_weight_change)
    days_left = _safe_int(duration_days, 30)
    meals_count = max(3, min(7, _safe_int(meals_per_day, 5)))
    macros = _estimate_calories(direction, current_weight, meals_count)

    template_text = _build_template_plan(direction, macros, dietary_constraints)
    if logic == MealPlanGenerationMode.GOAL_BASED.value:
        description = _build_goal_based_plan(direction, macros, days_left, target_weight)
    elif logic == MealPlanGenerationMode.FIGHT_CAMP.value:
        effective_days = days_left
        if isinstance(fight_context, dict) and fight_context.get("days_left") not in [None, ""]:
            effective_days = _safe_int(fight_context.get("days_left"), days_left)
        description = _build_fight_camp_plan(direction, macros, effective_days)
    elif logic == MealPlanGenerationMode.MANUAL_HYBRID.value:
        description = _build_manual_hybrid_plan(template_text, food_preferences)
    else:
        description = template_text

    title = name.strip() if name and str(name).strip() else f"Plan {logic.replace('_', ' ').title()}"

    generated_plan = {
        "name": title,
        "weight_change": direction,
        "target_weight": _safe_float(target_weight),
        "duration": max(1, days_left),
        "status": "active",
        "description": description,
        "notes": (
            f"Logica: {logic} | Restricciones: {dietary_constraints or 'Ninguna'} | "
            f"Preferencias: {food_preferences or 'No especificadas'}"
        ),
        "generated_macros": macros,
        "generation_logic": logic,
        "created_date": datetime.now().isoformat(),
    }

    return generated_plan
