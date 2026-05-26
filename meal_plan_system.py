"""
Motor de planes de comida personalizados.
Implementa varias estrategias de generacion para aproximar un flujo similar al plan tactico.
"""

from enum import Enum
from datetime import datetime


class MealPlanService:
    """Orquesta la lógica de planes de comida consumida por la capa Dash."""

    @staticmethod
    def build_draft(
        name,
        generation_logic,
        current_weight,
        target_weight,
        target_body_fat,
        duration,
        weight_change,
        dietary_constraints,
        food_preferences,
        supplement_use,
        meals_per_day,
        fight_context,
    ):
        generation_logic = generation_logic or 'goal_based'
        generated = generate_personalized_meal_plan(
            name=name,
            generation_logic=generation_logic,
            current_weight=current_weight,
            target_weight=target_weight,
            target_body_fat=target_body_fat,
            duration_days=duration,
            selected_weight_change=weight_change,
            dietary_constraints=dietary_constraints,
            food_preferences=food_preferences,
            supplement_use=supplement_use,
            meals_per_day=meals_per_day,
            fight_context=fight_context,
        )

        review = validate_meal_plan_advanced({
            'duration': generated.get('duration'),
            'target_weight': generated.get('target_weight'),
            'target_body_fat': generated.get('target_body_fat'),
            'current_weight': current_weight,
            'generation_logic': generated.get('generation_logic')
        })

        generated_meta = {
            'generation_logic': generated.get('generation_logic'),
            'generated_macros': generated.get('generated_macros', {}),
            'target_body_fat': generated.get('target_body_fat'),
            'supplement_use': generated.get('supplement_use', ''),
            'dietary_constraints': dietary_constraints or '',
            'food_preferences': food_preferences or '',
            'meals_per_day': meals_per_day,
        }
        return generated, review, generated_meta

    @staticmethod
    def build_plan_for_save(
        name,
        generation_logic,
        weight_change,
        target_weight,
        target_body_fat,
        duration,
        status,
        dietary_constraints,
        food_preferences,
        supplement_use,
        meals_per_day,
        is_primary,
        description,
        notes,
        generated_meta,
        current_weight,
    ):
        try:
            target_weight_val = float(target_weight) if target_weight not in [None, ''] else None
        except (TypeError, ValueError):
            target_weight_val = None

        try:
            duration_val = int(duration) if duration and duration > 0 else 30
        except (TypeError, ValueError):
            duration_val = 30

        selected_logic = generation_logic or 'goal_based'
        macros_data = {}
        if isinstance(generated_meta, dict):
            selected_logic = generated_meta.get('generation_logic') or selected_logic
            if isinstance(generated_meta.get('generated_macros'), dict):
                macros_data = generated_meta.get('generated_macros')

        inferred_weight_change = weight_change or _resolve_weight_direction(current_weight, target_weight_val, None)

        meal_plan = {
            'name': str(name or '').strip(),
            'weight_change': inferred_weight_change,
            'target_weight': target_weight_val,
            'target_body_fat': _safe_float(target_body_fat),
            'duration': duration_val,
            'status': status or 'active',
            'generation_logic': selected_logic,
            'generated_macros': macros_data,
            'dietary_constraints': dietary_constraints or '',
            'food_preferences': food_preferences or '',
            'supplement_use': supplement_use or '',
            'meals_per_day': meals_per_day if meals_per_day else 5,
            'is_primary': bool(is_primary),
            'current_weight': current_weight,
            'description': description or '',
            'notes': notes or '',
            'created_date': datetime.now().isoformat(),
        }
        return meal_plan, validate_meal_plan_advanced(meal_plan)

    @staticmethod
    def delete_plan_by_index(meal_plans, idx):
        plans = list(meal_plans or [])
        if isinstance(idx, int) and 0 <= idx < len(plans):
            plans.pop(idx)
        return plans


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


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _get_meal_labels(meals_per_day):
    meals = max(3, min(7, _safe_int(meals_per_day, 5)))
    labels_map = {
        3: ["Desayuno", "Comida", "Cena"],
        4: ["Desayuno", "Comida", "Merienda", "Cena"],
        5: ["Desayuno", "Media manana", "Comida", "Merienda", "Cena"],
        6: ["Desayuno", "Media manana", "Comida", "Pre-entreno", "Cena", "Colacion nocturna"],
        7: ["Desayuno", "Media manana", "Comida", "Merienda", "Pre-entreno", "Cena", "Colacion nocturna"],
    }
    return labels_map.get(meals, labels_map[5])[:meals]


def _get_macro_percentages(meals_per_day):
    meals = max(3, min(7, _safe_int(meals_per_day, 5)))
    percentages_map = {
        3: [0.3, 0.4, 0.3],
        4: [0.25, 0.25, 0.2, 0.3],
        5: [0.22, 0.15, 0.26, 0.12, 0.25],
        6: [0.2, 0.12, 0.22, 0.16, 0.12, 0.18],
        7: [0.18, 0.1, 0.18, 0.14, 0.1, 0.14, 0.16],
    }
    return percentages_map.get(meals, percentages_map[5])[:meals]


def _build_meal_macro_breakdown(macros, meals_per_day):
    labels = _get_meal_labels(meals_per_day)
    percentages = _get_macro_percentages(meals_per_day)

    protein_total = int(macros.get("protein_total_g", 0))
    carbs_total = int(macros.get("carbs_total_g", 0))
    fats_total = int(macros.get("fats_total_g", 0))

    breakdown = []
    protein_allocated = 0
    carbs_allocated = 0
    fats_allocated = 0

    for idx, label in enumerate(labels):
        pct = percentages[idx] if idx < len(percentages) else (1.0 / len(labels))
        if idx == len(labels) - 1:
            protein_g = max(0, protein_total - protein_allocated)
            carbs_g = max(0, carbs_total - carbs_allocated)
            fats_g = max(0, fats_total - fats_allocated)
        else:
            protein_g = max(0, round(protein_total * pct))
            carbs_g = max(0, round(carbs_total * pct))
            fats_g = max(0, round(fats_total * pct))
            protein_allocated += protein_g
            carbs_allocated += carbs_g
            fats_allocated += fats_g

        breakdown.append({
            "meal": label,
            "protein_g": int(protein_g),
            "carbs_g": int(carbs_g),
            "fats_g": int(fats_g),
            "kcal": int((protein_g * 4) + (carbs_g * 4) + (fats_g * 9)),
        })

    return breakdown


def _format_macro_distribution(macros, meals_per_day):
    breakdown = _build_meal_macro_breakdown(macros, meals_per_day)
    lines = ["Distribucion sugerida por comida:"]
    for idx, meal in enumerate(breakdown, start=1):
        lines.append(
            f"{idx}) {meal['meal']}: P {meal['protein_g']} g | C {meal['carbs_g']} g | G {meal['fats_g']} g"
        )
    return breakdown, "\n".join(lines)


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


def _estimate_calories(direction, current_weight, meals_per_day, target_body_fat=None):
    weight = max(50.0, _safe_float(current_weight, 70.0))
    body_fat_target = _safe_float(target_body_fat, 15.0)
    body_fat_target = _clamp(body_fat_target, 3.0, 35.0)
    lean_mass = weight * (1 - body_fat_target / 100.0)

    base = 32 * weight
    if direction == MealWeightDirection.CUT.value:
        kcal = base - 400
        protein_factor = 2.3
        carb_floor = 2.0
        fats = 0.8
    elif direction == MealWeightDirection.GAIN.value:
        kcal = base + 300
        protein_factor = 1.9
        carb_floor = 3.6
        fats = 1.0
    elif direction == MealWeightDirection.MAINTAIN.value:
        kcal = base
        protein_factor = 2.0
        carb_floor = 3.0
        fats = 0.9
    else:
        kcal = base
        protein_factor = 1.8
        carb_floor = 2.8
        fats = 0.9

    protein = max(weight * 1.6, lean_mass * protein_factor)
    protein = round(protein)
    fats_g = round(weight * fats)
    remaining_kcal = max(0, kcal - (protein * 4) - (fats_g * 9))
    carbs = max(carb_floor, round(remaining_kcal / 4))

    return {
        "daily_kcal": int(round(kcal)),
        "protein_g_per_kg": round(protein / weight, 2),
        "carbs_g_per_kg": round(carbs / weight, 2),
        "fats_g_per_kg": round(fats_g / weight, 2),
        "protein_total_g": int(protein),
        "carbs_total_g": int(carbs),
        "fats_total_g": int(fats_g),
        "weight_reference_kg": round(weight, 1),
        "lean_mass_estimate_kg": round(lean_mass, 1),
        "target_body_fat_pct": round(body_fat_target, 1),
        "meals_per_day": meals_per_day,
    }


def _build_template_plan(direction, macros, constraints):
    _, distribution_text = _format_macro_distribution(macros, macros.get("meals_per_day", 5))
    return (
        f"Objetivo diario: {macros['daily_kcal']} kcal\n"
        f"Macros objetivo: {macros['daily_kcal']} kcal | "
        f"P {macros['protein_total_g']} g/día ({macros['protein_g_per_kg']} g/kg) | "
        f"C {macros['carbs_total_g']} g/día ({macros['carbs_g_per_kg']} g/kg) | "
        f"G {macros['fats_total_g']} g/día ({macros['fats_g_per_kg']} g/kg)\n\n"
        f"{distribution_text}\n\n"
        f"Restricciones a considerar: {constraints or 'Ninguna'}\n"
        "Usa equivalencias de alimentos para cumplir estos gramos sin imponer platos concretos."
    )


def _build_goal_based_plan(direction, macros, days_left, target_weight):
    objective_line = "Objetivo principal: recomposicion y consistencia."
    if direction == MealWeightDirection.CUT.value:
        objective_line = "Objetivo principal: reducir peso preservando rendimiento."
    elif direction == MealWeightDirection.GAIN.value:
        objective_line = "Objetivo principal: aumentar masa magra con superavit controlado."
    elif direction == MealWeightDirection.MAINTAIN.value:
        objective_line = "Objetivo principal: sostener peso y optimizar recuperacion."

    _, distribution_text = _format_macro_distribution(macros, macros.get("meals_per_day", 5))

    return (
        f"{objective_line}\n"
        f"Horizonte: {days_left} dias | Peso objetivo: {target_weight if target_weight is not None else 'no definido'} kg\n"
        f"{distribution_text}\n\n"
        "Ajuste semanal de porciones segun evolucion de peso y rendimiento.\n\n"
        f"Macros objetivo: {macros['daily_kcal']} kcal | "
        f"P {macros['protein_total_g']} g/día | "
        f"C {macros['carbs_total_g']} g/día | "
        f"G {macros['fats_total_g']} g/día"
    )


def _build_fight_camp_plan(direction, macros, days_left):
    if days_left <= 7:
        phase_text = "Fase semana de pelea: bajo residuo, sodio controlado, hidratacion protocolizada."
    elif days_left <= 21:
        phase_text = "Fase de descarga: mantener energia con menor volumen digestivo."
    else:
        phase_text = "Fase base: calidad nutricional, adherencia y soporte de cargas altas."

    _, distribution_text = _format_macro_distribution(macros, macros.get("meals_per_day", 5))

    return (
        f"{phase_text}\n"
        "Bloques por fase:\n"
        "- Base: reparto estable de macros y buena tolerancia digestiva\n"
        "- Descarga: ajustar volumen, fibra y sodio sin perder energia\n"
        "- Fight week: estrategia de peso y glucogeno sin comprometer rendimiento\n\n"
        f"Direccion de peso: {direction}\n"
        f"{distribution_text}\n\n"
        f"Macros objetivo: {macros['daily_kcal']} kcal | "
        f"P {macros['protein_total_g']} g/día | "
        f"C {macros['carbs_total_g']} g/día | "
        f"G {macros['fats_total_g']} g/día"
    )


def _build_manual_hybrid_plan(base_plan, preferences):
    return (
        "Borrador automatico + personalizacion manual\n\n"
        f"{base_plan}\n\n"
        "Ajustes del atleta:\n"
        f"- Preferencias: {preferences or 'No especificadas'}\n"
        "- Reemplazar fuentes de alimento segun tolerancia sin alterar los gramos objetivo\n"
        "- Confirmar checklist de compras semanal\n"
        "- Definir colaciones para dias de doble sesion"
    )


def validate_meal_plan_advanced(plan_dict):
    warnings = []

    duration = _safe_int(plan_dict.get("duration"), 30)
    target_weight = _safe_float(plan_dict.get("target_weight"))
    target_body_fat = _safe_float(plan_dict.get("target_body_fat"))
    current_weight = _safe_float(plan_dict.get("current_weight"))
    logic = plan_dict.get("generation_logic")

    if duration < 7:
        warnings.append("Duracion muy corta; considera al menos 7 dias para evaluar adherencia.")

    if current_weight is not None and target_weight is not None:
        delta = abs(current_weight - target_weight)
        if delta > 8:
            warnings.append("Diferencia de peso elevada; revisar seguridad y ritmo semanal.")

    if target_body_fat is not None and not 3 <= target_body_fat <= 35:
        warnings.append("El porcentaje de grasa objetivo está fuera del rango clínico habitual (3-35%).")

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
    target_body_fat,
    duration_days,
    selected_weight_change,
    dietary_constraints,
    food_preferences,
    supplement_use,
    meals_per_day,
    fight_context=None,
):
    logic = str(generation_logic or MealPlanGenerationMode.TEMPLATE.value).strip().lower()
    if logic not in [m.value for m in MealPlanGenerationMode]:
        logic = MealPlanGenerationMode.TEMPLATE.value

    direction = _resolve_weight_direction(current_weight, target_weight, selected_weight_change)
    days_left = _safe_int(duration_days, 30)
    meals_count = max(3, min(7, _safe_int(meals_per_day, 5)))
    macros = _estimate_calories(direction, current_weight, meals_count, target_body_fat)
    meal_breakdown, distribution_text = _format_macro_distribution(macros, meals_count)
    macros["meal_breakdown"] = meal_breakdown
    macros["distribution_text"] = distribution_text

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
        "target_body_fat": _safe_float(target_body_fat),
        "duration": max(1, days_left),
        "status": "active",
        "description": description,
        "notes": (
            f"Logica: {logic} | Restricciones: {dietary_constraints or 'Ninguna'} | "
            f"Preferencias: {food_preferences or 'No especificadas'} | "
            f"Suplementos: {supplement_use or 'No especificados'}"
        ),
        "generated_macros": macros,
        "generation_logic": logic,
        "supplement_use": supplement_use or '',
        "created_date": datetime.now().isoformat(),
    }

    return generated_plan
