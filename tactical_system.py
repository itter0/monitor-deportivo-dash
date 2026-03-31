"""
MÓDULO DE SISTEMA TÁCTICO REALISTA
===================================
Define el dominio, esquemas, enums y funciones de núcleo para el sistema de planes tácticos.
Realismo AVANZADO: adaptación dinámica, escenarios contingentes, scoring compuesto.
Independiente de Dash; puede ser testeado en aislamiento.

Schema Versioning: v1.0 a partir de 2026-03-25
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json

# ============================================================================
# ENUMS Y CONSTANTES DEL DOMINIO TÁCTICO
# ============================================================================

class OpponentStyle(str, Enum):
    """Estilos de lucha del rival."""
    STRIKING = "Striking"
    GRAPPLING = "Grappling"
    BALANCED = "Balanced"


class TacticalPlanStatus(str, Enum):
    """Estado del ciclo de vida del plan táctico."""
    ACTIVE = "active"  # Plan en construcción o ejecución
    EXECUTED = "executed"  # Pelea realizada
    ARCHIVED = "archived"  # Plan pasado sin ejecución


class TacticalRiskSeverity(str, Enum):
    """Severidad de riesgo físico para decisiones tácticas."""
    LOW = "low"  # Verde, sin restricción
    MEDIUM = "medium"  # Amarillo, requiere monitoreo
    HIGH = "high"  # Rojo, restricción táctica importante


class CampPhase(str, Enum):
    """Fases del campamento de entrenamiento (días hasta pelea)."""
    PRE_FIGHT_HIGH_INTENSITY = "Pre-Pelea (Alta Intensidad)"  # < 7 días
    TAPERING = "Descarga (Volumen Bajo)"  # 3-7 días
    FIGHT_WEEK = "Semana de Pelea"  # 0-3 días
    RECOVERY = "Recuperación"  # Post-pelea
    BASE_BUILDING = "Base (Volumen Alto)"  # > 21 días


# ============================================================================
# ESQUEMAS DE DATOS TÁCTICOS
# ============================================================================

@dataclass
class OpponentProfile:
    """Perfil del rival: caracterización manual y recomendaciones contra él."""
    name: str
    style: OpponentStyle
    strengths: List[str] = field(default_factory=list)  # Ej: ['Precise striking', 'Head movement']
    weaknesses: List[str] = field(default_factory=list)  # Ej: ['Takedown defense', 'Clinch']
    notes: str = ""
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "style": self.style.value,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "OpponentProfile":
        return cls(
            name=data.get("name", "Anonymous"),
            style=OpponentStyle(data.get("style", "Balanced")),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            notes=data.get("notes", ""),
        )


@dataclass
class RoundGamePlan:
    """Plan de juego para un round específico."""
    round_number: int  # 1, 2, 3, etc.
    focus: str  # Ej: "Distance management", "Clinch dominance", "Submission hunt"
    techniques: List[str] = field(default_factory=list)  # Ej: ['Jab teaser', 'Low kicks']
    contingency: str = ""  # Qué hacer si el plan A falla
    
    def to_dict(self) -> dict:
        return {
            "round_number": self.round_number,
            "focus": self.focus,
            "techniques": self.techniques,
            "contingency": self.contingency,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RoundGamePlan":
        return cls(
            round_number=data.get("round_number", 1),
            focus=data.get("focus", ""),
            techniques=data.get("techniques", []),
            contingency=data.get("contingency", ""),
        )


@dataclass
class ContingencyScenario:
    """Escenario contingente con trigger y plan B."""
    scenario_name: str  # Ej: "Rival domina clinch"
    trigger: str  # Condición que activa: Ej: "Clinch time > 40% en R2"
    response_techniques: List[str] = field(default_factory=list)  # Técnicas recomendadas
    risk_level: TacticalRiskSeverity = TacticalRiskSeverity.MEDIUM
    
    def to_dict(self) -> dict:
        return {
            "scenario_name": self.scenario_name,
            "trigger": self.trigger,
            "response_techniques": self.response_techniques,
            "risk_level": self.risk_level.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ContingencyScenario":
        return cls(
            scenario_name=data.get("scenario_name", ""),
            trigger=data.get("trigger", ""),
            response_techniques=data.get("response_techniques", []),
            risk_level=TacticalRiskSeverity(data.get("risk_level", "medium")),
        )


@dataclass
class ExecutionLog:
    """Registro de ejecución real de una sesión táctica."""
    session_date: str  # ISO format
    round_executed: int
    focus_achieved: bool  # ¿Se ejecutó el foco bien?
    techniques_landed: List[str] = field(default_factory=list)
    contingency_triggered: Optional[str] = None  # Qué escenario se activó
    adaptation_notes: str = ""  # Observaciones post-sesión
    physiological_stress: Optional[float] = None  # BPM máximo, fatiga 0-10
    
    def to_dict(self) -> dict:
        return {
            "session_date": self.session_date,
            "round_executed": self.round_executed,
            "focus_achieved": self.focus_achieved,
            "techniques_landed": self.techniques_landed,
            "contingency_triggered": self.contingency_triggered,
            "adaptation_notes": self.adaptation_notes,
            "physiological_stress": self.physiological_stress,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionLog":
        return cls(
            session_date=data.get("session_date", datetime.now().isoformat()),
            round_executed=data.get("round_executed", 0),
            focus_achieved=data.get("focus_achieved", False),
            techniques_landed=data.get("techniques_landed", []),
            contingency_triggered=data.get("contingency_triggered"),
            adaptation_notes=data.get("adaptation_notes", ""),
            physiological_stress=data.get("physiological_stress"),
        )


@dataclass
class PlanVersion:
    """Historial de versiones de un plan táctico."""
    version_number: int  # 1, 2, 3, etc.
    created_at: str  # ISO format
    created_by: str = "system"  # "system" o "user"
    change_description: str = ""  # Ej: "Added round 4", "Updated opponent profile"
    plan_snapshot: Dict = field(default_factory=dict)  # Copia completa del plan en este punto
    
    def to_dict(self) -> dict:
        return {
            "version_number": self.version_number,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "change_description": self.change_description,
            "plan_snapshot": self.plan_snapshot,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PlanVersion":
        return cls(
            version_number=data.get("version_number", 1),
            created_at=data.get("created_at", datetime.now().isoformat()),
            created_by=data.get("created_by", "system"),
            change_description=data.get("change_description", ""),
            plan_snapshot=data.get("plan_snapshot", {}),
        )


@dataclass
class TacticalPlan:
    """Plan táctico completo para una pelea."""
    fight_id: str  # Identificador único (ej: "fight-001", puede ser None para draft)
    opponent: OpponentProfile
    my_specialty: OpponentStyle  # Estilo propio del luchador
    my_phase: CampPhase  # Fase de campamento cuando se crea
    game_plan_rounds: List[RoundGamePlan] = field(default_factory=list)
    contingencies: List[ContingencyScenario] = field(default_factory=list)
    drill_focus: List[str] = field(default_factory=list)  # Ej: ['wrestling_takedown', 'clinch_drills']
    injury_restrictions: Dict[str, str] = field(default_factory=dict)  # {injury_type: restriction}
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: TacticalPlanStatus = TacticalPlanStatus.ACTIVE
    execution_logs: List[ExecutionLog] = field(default_factory=list)
    version: str = "1.0"  # Schema versioning para migraciones futuras
    adaptive_adjustments: List[Dict] = field(default_factory=list)  # Cambios aplicados por sistema
    version_history: List[PlanVersion] = field(default_factory=list)  # NUEVO: Historial completo de versiones
    target_date: Optional[str] = None  # NUEVO: Fecha objetivo de la pelea (ISO format)
    target_days_left: int = 30  # NUEVO: Días hasta la pelea
    
    def to_dict(self) -> dict:
        return {
            "fight_id": self.fight_id,
            "opponent": self.opponent.to_dict(),
            "my_specialty": self.my_specialty.value,
            "my_phase": self.my_phase.value,
            "game_plan_rounds": [r.to_dict() for r in self.game_plan_rounds],
            "contingencies": [c.to_dict() for c in self.contingencies],
            "drill_focus": self.drill_focus,
            "injury_restrictions": self.injury_restrictions,
            "created_at": self.created_at,
            "status": self.status.value,
            "execution_logs": [log.to_dict() for log in self.execution_logs],
            "version": self.version,
            "adaptive_adjustments": self.adaptive_adjustments,
            "version_history": [v.to_dict() for v in self.version_history],
            "target_date": self.target_date,
            "target_days_left": self.target_days_left,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TacticalPlan":
        return cls(
            fight_id=data.get("fight_id"),
            opponent=OpponentProfile.from_dict(data.get("opponent", {})),
            my_specialty=OpponentStyle(data.get("my_specialty", "Balanced")),
            my_phase=CampPhase(data.get("my_phase", "Base (Volumen Alto)")),
            game_plan_rounds=[RoundGamePlan.from_dict(r) for r in data.get("game_plan_rounds", [])],
            contingencies=[ContingencyScenario.from_dict(c) for c in data.get("contingencies", [])],
            drill_focus=data.get("drill_focus", []),
            injury_restrictions=data.get("injury_restrictions", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            status=TacticalPlanStatus(data.get("status", "active")),
            execution_logs=[ExecutionLog.from_dict(log) for log in data.get("execution_logs", [])],
            version=data.get("version", "1.0"),
            adaptive_adjustments=data.get("adaptive_adjustments", []),
            version_history=[PlanVersion.from_dict(v) for v in data.get("version_history", [])],
            target_date=data.get("target_date"),
            target_days_left=data.get("target_days_left", 30),
        )


# ============================================================================
# FUNCIONES DE NORMALIZACIÓN Y VALIDACIÓN
# ============================================================================

def normalize_opponent_style(style_input: Optional[str]) -> OpponentStyle:
    """Normaliza entrada de estilo de rival a enum válido."""
    if not style_input:
        return OpponentStyle.BALANCED
    style_lower = str(style_input).lower().strip()
    for e in OpponentStyle:
        if style_lower == e.value.lower():
            return e
    return OpponentStyle.BALANCED


def normalize_plan_status(status_input: Optional[str]) -> TacticalPlanStatus:
    """Normaliza entrada de estado del plan."""
    if not status_input:
        return TacticalPlanStatus.ACTIVE
    status_lower = str(status_input).lower().strip()
    for e in TacticalPlanStatus:
        if status_lower == e.value.lower():
            return e
    return TacticalPlanStatus.ACTIVE


def normalize_camp_phase(phase_input: Optional[str]) -> CampPhase:
    """Normaliza entrada de fase de campamento."""
    if not phase_input:
        return CampPhase.BASE_BUILDING
    phase_lower = str(phase_input).lower().strip()
    for e in CampPhase:
        if phase_lower == e.value.lower():
            return e
    return CampPhase.BASE_BUILDING


def is_tactical_plan_valid(plan: TacticalPlan) -> Tuple[bool, List[str]]:
    """Valida integridad de un plan táctico. Retorna (is_valid, list_of_errors)."""
    errors = []
    
    if not plan.opponent or not plan.opponent.name:
        errors.append("Opponent name es requerido.")
    
    if not plan.game_plan_rounds:
        errors.append("Al menos un round de game plan es requerido.")
    else:
        for rnd in plan.game_plan_rounds:
            if not rnd.focus:
                errors.append(f"Round {rnd.round_number}: focus no puede estar vacío.")
    
    if not plan.drill_focus:
        errors.append("Al menos un drill focus es requerido.")
    
    return len(errors) == 0, errors


# ============================================================================
# FUNCIONES DE LÓGICA TÁCTICA (Avanzada)
# ============================================================================

def recommend_counter_strategy(
    opponent_style: OpponentStyle,
    my_specialty: OpponentStyle,
    opponent_strengths: List[str],
    opponent_weaknesses: List[str]
) -> Dict[str, any]:
    """
    Motor de recomendaciones tácticas básico.
    Retorna estrategia inicial basada en matchup estilo + fortalezas/debilidades.
    """
    strategy = {
        "primary_focus": "",
        "counter_to_strengths": [],  # Técnicas que neutralizan sus fortalezas
        "exploit_weaknesses": [],  # Técnicas que atacan debilidades
        "drill_recommendations": [],
    }
    
    # Lógica coreana: Striking vs Grappling matchup
    if my_specialty == OpponentStyle.STRIKING and opponent_style == OpponentStyle.GRAPPLING:
        strategy["primary_focus"] = "Maintain distance, avoid clinch"
        strategy["counter_to_strengths"] = ["Footwork drills", "Circling"]
        strategy["exploit_weaknesses"] = ["Striking combinations", "Head movement"]
        strategy["drill_recommendations"] = ["footwork_drills", "striking_distance"]
    
    elif my_specialty == OpponentStyle.GRAPPLING and opponent_style == OpponentStyle.STRIKING:
        strategy["primary_focus"] = "Establish clinch, control distance"
        strategy["counter_to_strengths"] = ["Head slip", "Clinch transition"]
        strategy["exploit_weaknesses"] = ["Takedown setup", "Ground control"]
        strategy["drill_recommendations"] = ["clinch_drills", "wrestling_takedown"]
    
    elif my_specialty == opponent_style:
        strategy["primary_focus"] = f"Master your {my_specialty.value} game better than them"
        strategy["counter_to_strengths"] = ["Practice against their specific counters"]
        strategy["exploit_weaknesses"] = ["Refine your technique advantages"]
        strategy["drill_recommendations"] = [f"{my_specialty.value.lower()}_refinement"]
    
    else:  # BALANCED vs anything o misceláneos
        strategy["primary_focus"] = "Adaptability and versatility"
        strategy["counter_to_strengths"] = ["Counter-striking", "Counter-grappling"]
        strategy["exploit_weaknesses"] = ["Expose one-dimensional weakness"]
        strategy["drill_recommendations"] = ["mixed_drills", f"counter_{opponent_style.value.lower()}"]
    
    return strategy


def adjust_plan_for_injury_risk(
    plan: TacticalPlan,
    injury_type: str,
    risk_severity: TacticalRiskSeverity
) -> List[Dict]:
    """
    Ajusta plan táctico en función de restricción por lesión.
    Retorna lista de ajustes aplicados (para registro de adaptación dinámica).
    """
    adjustments = []
    
    if risk_severity == TacticalRiskSeverity.HIGH:
        # Restricción severa: evitar técnicas de alto riesgo
        affected_techniques = _get_high_risk_techniques_for_injury(injury_type)
        for rnd in plan.game_plan_rounds:
            removed = [t for t in rnd.techniques if t in affected_techniques]
            if removed:
                rnd.techniques = [t for t in rnd.techniques if t not in affected_techniques]
                adjustments.append({
                    "round": rnd.round_number,
                    "reason": f"Injury restriction (HIGH): {injury_type}",
                    "removed_techniques": removed,
                    "timestamp": datetime.now().isoformat(),
                })
    
    elif risk_severity == TacticalRiskSeverity.MEDIUM:
        # Restricción moderada: monitoreo y técnicas alternativas
        plan.contingencies.append(
            ContingencyScenario(
                scenario_name=f"Pain flare-up: {injury_type}",
                trigger="If pain increases during session",
                response_techniques=["Switch to defensive posture", "Increase distance management"],
                risk_level=TacticalRiskSeverity.HIGH,
            )
        )
        adjustments.append({
            "reason": f"Injury monitoring (MEDIUM): {injury_type}",
            "action": "Added contingency for pain flare-up",
            "timestamp": datetime.now().isoformat(),
        })
    
    plan.injury_restrictions[injury_type] = risk_severity.value
    return adjustments


def score_plan_execution(execution_log: ExecutionLog, plan_round: RoundGamePlan) -> float:
    """
    Calcula score de ejecución (0-100) para un round.
    Basado en: focus logrado, técnicas landed vs planeadas, contingencia evitada.
    """
    score = 50.0  # Base
    
    if execution_log.focus_achieved:
        score += 25
    
    if len(execution_log.techniques_landed) > 0:
        landed_ratio = len(execution_log.techniques_landed) / max(len(plan_round.techniques), 1)
        score += min(20, landed_ratio * 20)
    
    if execution_log.contingency_triggered is None:
        score += 5
    
    return min(100.0, max(0.0, score))


def generate_initial_tactical_plan(
    opponent: OpponentProfile,
    athlete_specialty: OpponentStyle,
    camp_phase: CampPhase,
    num_rounds: int = 3,
    injury_restrictions: Optional[Dict[str, str]] = None
) -> TacticalPlan:
    """
    Genera un plan táctico INICIAL completo y realista.
    Basado en: estilo del rival, especialidad del atleta, fase de campamento.
    Retorna plan con rounds, contingencias y recomendaciones de drills.
    """
    plan = TacticalPlan(
        fight_id=None,  # Se asigna en UI cuando se guarda
        opponent=opponent,
        my_specialty=athlete_specialty,
        my_phase=camp_phase,
    )
    
    # Generar estrategia de matchup
    matchup_strategy = recommend_counter_strategy(
        opponent_style=opponent.style,
        my_specialty=athlete_specialty,
        opponent_strengths=opponent.strengths,
        opponent_weaknesses=opponent.weaknesses,
    )
    
    # Generar plans de game por round (tácticas evolucionar con rounds)
    for round_num in range(1, num_rounds + 1):
        if round_num == 1:
            focus = f"Establish {matchup_strategy['primary_focus']}"
            techniques = matchup_strategy['counter_to_strengths'][:2]
        elif round_num == 2:
            focus = "Maintain pressure and exploit weaknesses"
            techniques = matchup_strategy['exploit_weaknesses'][:2]
        else:
            focus = "Close rounds with dominant control"
            techniques = (matchup_strategy['exploit_weaknesses'] + ['Wrestling takedown'])[:2]
        
        contingency = ""
        if round_num == 1:
            contingency = "If struggling with distance, adjust footwork and use clinch disruption."
        elif round_num == 2:
            contingency = "If opponent adjusts, shift from primary to secondary techniques."
        else:
            contingency = "If tired, switch to submissions or dominant ground position."
        
        plan.game_plan_rounds.append(
            RoundGamePlan(
                round_number=round_num,
                focus=focus,
                techniques=techniques,
                contingency=contingency,
            )
        )
    
    # Agregar contingencias genéricas
    if opponent.style == OpponentStyle.STRIKING:
        plan.contingencies.extend([
            ContingencyScenario(
                scenario_name="Opponent overpowers striking",
                trigger="If caught by heavy counter or combo",
                response_techniques=["Clinch", "Head movement", "Retreat and reset"],
                risk_level=TacticalRiskSeverity.MEDIUM,
            ),
        ])
    elif opponent.style == OpponentStyle.GRAPPLING:
        plan.contingencies.extend([
            ContingencyScenario(
                scenario_name="Caught in grappling exchange",
                trigger="If opponent initiates wrestling",
                response_techniques=["Submission defense", "Hip escape", "Guard retention"],
                risk_level=TacticalRiskSeverity.HIGH,
            ),
        ])
    
    # Agregar recomendaciones de drills
    plan.drill_focus = matchup_strategy['drill_recommendations'][:3]
    
    # Aplicar restricciones por lesión si existen
    if injury_restrictions:
        for injury_type, risk_str in injury_restrictions.items():
            risk_severity = TacticalRiskSeverity(risk_str)
            adjust_plan_for_injury_risk(plan, injury_type, risk_severity)
    
    return plan


def adapt_plan_for_session_performance(
    plan: TacticalPlan,
    current_bpm_max: Optional[float] = None,
    fatigue_level: Optional[float] = None,  # 0-10
    pain_level: Optional[float] = None,  # 0-10
) -> List[Dict]:
    """
    Adapta plan táctico DINÁMICAMENTE basado en condiciones físicas actuales.
    Retorna lista de ajustes aplicados (para trazabilidad).
    """
    adjustments = []
    
    # Criterio 1: Fatiga alta → reducir volumen, enfocar en técnicas clave
    if fatigue_level is not None and fatigue_level > 7.0:
        for rnd in plan.game_plan_rounds:
            if len(rnd.techniques) > 2:
                removed = rnd.techniques[2:]
                rnd.techniques = rnd.techniques[:2]
                adjustments.append({
                    "round": rnd.round_number,
                    "reason": f"High fatigue ({fatigue_level:.1f}/10): reduce technique volume",
                    "action": f"Reduced techniques from {len(removed) + 2} to 2",
                    "timestamp": datetime.now().isoformat(),
                })
    
    # Criterio 2: BPM máximo muy alto → riesgo cardiovascular, cambiar a técnicas defensivas
    if current_bpm_max is not None and current_bpm_max > 180:
        for rnd in plan.game_plan_rounds:
            rnd.focus = f"Conservative {rnd.focus}: prioritize efficiency over volume"
        adjustments.append({
            "round": "all",
            "reason": f"CVconcern (BPM max: {current_bpm_max}): shift to conservative strategy",
            "action": "Updated all round focuses to defensive efficiency",
            "timestamp": datetime.now().isoformat(),
        })
    
    # Criterio 3: Dolor recurrente → reactivar contingencia de riesgo alto
    if pain_level is not None and pain_level > 6.0:
        if not any(c.scenario_name == "Pain flare-up detected" for c in plan.contingencies):
            plan.contingencies.append(
                ContingencyScenario(
                    scenario_name="Pain flare-up detected",
                    trigger=f"If pain increases beyond {pain_level}",
                    response_techniques=["Defensive posture", "Avoid aggressive setups"],
                    risk_level=TacticalRiskSeverity.HIGH,
                )
            )
            adjustments.append({
                "round": "all",
                "reason": f"Recurring pain ({pain_level:.1f}/10): safety priority",
                "action": "Added high-risk pain contingency",
                "timestamp": datetime.now().isoformat(),
            })
    
    plan.adaptive_adjustments.extend(adjustments)
    return adjustments


def propose_contingency_for_scenario(
    opponent: OpponentProfile,
    current_round: int,
    scenario_description: str,
) -> ContingencyScenario:
    """
    Propone una contingencia (plan B) para un escenario específico detectado en tiempo real.
    Ej: "Rival está usando leg kicks agresivamente"
    """
    response_techniques = []
    risk = TacticalRiskSeverity.MEDIUM
    
    # Heurística simple: detectar palabras clave en scenario_description
    if "leg kick" in scenario_description.lower():
        response_techniques = ["Check leg kicks", "Retreat from distance", "Clinch"]
        risk = TacticalRiskSeverity.MEDIUM
    elif "strike" in scenario_description.lower() or "striking" in scenario_description.lower():
        response_techniques = ["Head movement", "Clinch", "Distance manage"]
        risk = TacticalRiskSeverity.MEDIUM
    elif "takedown" in scenario_description.lower() or "wrestling" in scenario_description.lower():
        response_techniques = ["Sprawl", "Frame", "Footwork"]
        risk = TacticalRiskSeverity.HIGH
    elif "submit" in scenario_description.lower():
        response_techniques = ["Tap strategically", "Escape positioning", "Defense"]
        risk = TacticalRiskSeverity.HIGH
    else:
        response_techniques = ["Reset", "Reassess", "Stick to game plan"]
    
    return ContingencyScenario(
        scenario_name=scenario_description,
        trigger=f"Round {current_round}: {scenario_description}",
        response_techniques=response_techniques,
        risk_level=risk,
    )


def calculate_plan_effectiveness_score(
    plan: TacticalPlan,
    execution_logs: List[ExecutionLog]
) -> Dict[str, float]:
    """
    Calcula score compuesto de efectividad del plan basado en logs de ejecución.
    Retorna dict: {preparation_score, execution_score, adaptation_score, overall_score}
    """
    if not execution_logs:
        return {
            "preparation_score": 0.0,
            "execution_score": 0.0,
            "adaptation_score": 0.0,
            "overall_score": 0.0,
        }
    
    # Preparation: ¿Qué tan bien planificado estuvo? (based on game plan rounds completitud)
    round_completeness = len(plan.game_plan_rounds) / 3.0  # Normalizar a 3 rounds
    drill_readiness = min(1.0, len(plan.drill_focus) / 4.0)
    preparation_score = (round_completeness + drill_readiness) * 50
    
    # Execution: ¿Qué tan bien se ejecutaron los plans?
    execution_scores = []
    for log in execution_logs:
        matching_round = None
        for rnd in plan.game_plan_rounds:
            if rnd.round_number == log.round_executed:
                matching_round = rnd
                break
        if matching_round:
            execution_scores.append(score_plan_execution(log, matching_round))
    
    execution_score = (sum(execution_scores) / len(execution_scores)) if execution_scores else 0.0
    
    # Adaptation: ¿Qué tan bien se adaptó el plan? (based on contingencies triggered vs applied)
    contingencies_triggered = sum(1 for log in execution_logs if log.contingency_triggered)
    adaptation_opportunity = len(plan.contingencies)
    adaptation_score = 50.0 if contingencies_triggered == 0 else min(100.0, 50.0 + (contingencies_triggered / max(adaptation_opportunity, 1)) * 50)
    
    overall_score = (preparation_score + execution_score + adaptation_score) / 3.0
    
    return {
        "preparation_score": preparation_score,
        "execution_score": execution_score,
        "adaptation_score": adaptation_score,
        "overall_score": overall_score,
    }


def _get_high_risk_techniques_for_injury(injury_type: str) -> List[str]:
    """Mapper: injury_type -> lista de técnicas a evitar."""
    mapping = {
        "knee": ["Takedown", "Leg kick", "Knee strike"],
        "shoulder": ["Overhead strike", "Clinch work", "Throw"],
        "elbow": ["Elbow strike", "Arm lock"],
        "back": ["Takedown", "Ground control", "Clinch"],
        "head": ["Head strike", "Clinch contact"],
    }
    return mapping.get(injury_type.lower(), [])


# ============================================================================
# FUNCIONES DE COMPATIBILIDAD Y MIGRACIÓN
# ============================================================================

def ensure_tactical_structure(user_data: dict) -> dict:
    """
    Garantiza que la estructura táctica existe en datos de usuario.
    Si no existe, inicializa arrays vacíos. (Compatibilidad legacy)
    """
    if "tactical_plans" not in user_data:
        user_data["tactical_plans"] = []
    return user_data


# ============================================================================
# EXPORTACIÓN DE CONSTANTES Y PLANTILLAS
# ============================================================================

# Template para crear un plan táctico vacío (para UI)
DEFAULT_TACTICAL_PLAN_TEMPLATE = {
    "opponent": {
        "name": "",
        "style": "Balanced",
        "strengths": [],
        "weaknesses": [],
        "notes": "",
    },
    "my_specialty": "Balanced",
    "my_phase": "Base (Volumen Alto)",
    "game_plan_rounds": [],
    "contingencies": [],
    "drill_focus": [],
    "injury_restrictions": {},
}

OPPONENT_STYLE_OPTIONS = [e.value for e in OpponentStyle]
CAMP_PHASE_OPTIONS = [e.value for e in CampPhase]
COMMON_TECHNIQUES = [
    "Jab", "Cross", "Hook", "Uppercut",
    "Leg kick", "Knee strike", "Takedown", "Clinch",
    "Submission setup", "Guard", "Head movement",
]
COMMON_DRILLS = [
    "striking_distance", "clinch_drills", "wrestling_takedown",
    "submission_defense", "footwork_drills", "cardio",
]


# ============================================================================
# VALIDACIÓN AVANZADA DE PLANES (Opción C)
# ============================================================================

def validate_plan_advanced(plan: TacticalPlan, athlete_weight: Optional[float] = None, weight_class_limit: Optional[float] = None) -> Dict[str, any]:
    """
    Validación AVANZADA de un plan táctico.
    Retorna dict con: {is_valid, errors[], warnings[], recommendations[]}
    """
    errors = []
    warnings = []
    recommendations = []
    
    # 1. VALIDACIÓN DE INTEGRIDAD BÁSICA
    if not plan.opponent or not plan.opponent.name:
        errors.append("❌ El nombre del rival es obligatorio.")
    
    if not plan.game_plan_rounds:
        errors.append("❌ Debes tener al menos un round de game plan.")
    else:
        # Validar cada round
        for i, rnd in enumerate(plan.game_plan_rounds, 1):
            if not rnd.focus or len(rnd.focus) < 5:
                errors.append(f"❌ Round {i}: el focus debe tener al menos 5 caracteres.")
            if not rnd.techniques or len(rnd.techniques) == 0:
                warnings.append(f"⚠️ Round {i}: sin técnicas definidas. Se recomienda agregar al menos 2.")
    
    if not plan.drill_focus or len(plan.drill_focus) == 0:
        warnings.append("⚠️ Sin drills de enfoque. Es recomendable tener al menos 1.")
    
    # 2. VALIDACIÓN DE COHERENCIA TÁCTICA
    if plan.opponent.style == OpponentStyle.STRIKING and plan.my_specialty == OpponentStyle.GRAPPLING:
        if not any("clinch" in t.lower() or "distance" in rnd.focus.lower() 
                  for rnd in plan.game_plan_rounds 
                  for t in rnd.techniques):
            warnings.append("⚠️ Como grappler vs striker, deberías enfocarte en clinch/distance control.")
    
    # 3. VALIDACIÓN DE PESO/CATEGORÍA
    if athlete_weight and weight_class_limit:
        weight_diff = float(athlete_weight) - float(weight_class_limit)
        if weight_diff > 5:
            errors.append(f"❌ Peso alarmante: {weight_diff:.1f}kg sobre el limite. Plan para corte de peso urgente.")
        elif weight_diff > 2:
            warnings.append(f"⚠️ Estás {weight_diff:.1f}kg sobre el límite. Planifica corte de peso.")
    
    # 4. VALIDACIÓN DE FECHA OBJETIVO
    if plan.target_date:
        try:
            from datetime import datetime as dt
            target = dt.fromisoformat(plan.target_date).date()
            today = dt.now().date()
            days_left = (target - today).days
            
            if days_left < 0:
                errors.append("❌ La fecha objetivo ya ha pasado.")
            elif days_left < 3:
                warnings.append("⚠️ Pelea muy pronto (< 3 días). Asegúrate de tener el plan finalizado.")
            elif days_left > 180:
                recommendations.append("💡 Plazo muy largo (> 180 días). Considera dividir en ciclos más cortos.")
        except:
            pass
    
    # 5. RECOMENDACIONES TÁCTICAS DINÁMICAS
    if len(plan.opponent.strengths) == 0:
        recommendations.append("💡 Agrega las fortalezas del rival para mejores contra-estrategias.")
    
    if len(plan.contingencies) < 2:
        recommendations.append("💡 Es recomendable tener al menos 2 contingencias por round.")
    
    if len(plan.game_plan_rounds) > 5:
        recommendations.append("💡 Más de 5 rounds puede ser excesivo. Considera agrupar estrategias.")
    
    is_valid = len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "recommendations": recommendations,
        "validation_timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# GENERACIÓN DE CALENDARIO (Opción C)
# ============================================================================

def generate_training_calendar(plan: TacticalPlan, target_date: str) -> List[Dict]:
    """
    Genera un calendario de entrenamiento día a día desde hoy hasta la fecha objetivo.
    Cada día incluye: fecha, fase de entrenamiento projetada, drills sugeridos, notas nutricionales.
    Retorna lista de dict con estructura de calendario.
    """
    from datetime import datetime as dt, timedelta as td
    
    calendar = []
    
    try:
        today = dt.now().date()
        target = dt.fromisoformat(target_date).date()
        days_until_fight = (target - today).days
    except:
        return []
    
    if days_until_fight <= 0:
        return []
    
    # Determinar fases según days_until_fight
    phase_breakdown = {
        "base_building": (days_until_fight, days_until_fight - int(days_until_fight * 0.6)),  # 60% del tiempo
        "volume_technical": (int(days_until_fight * 0.6), int(days_until_fight * 0.2)),  # 40% del tiempo
        "high_intensity": (int(days_until_fight * 0.2), 15),  # Últimas 2 semanas
        "tapering": (14, 7),  # Última semana
        "peak_week": (7, 0),  # Última semana antes de pelea
    }
    
    # Generar calendario día por día
    for day_offset in range(0, days_until_fight + 1):
        current_date = today + td(days=day_offset)
        days_left = days_until_fight - day_offset
        
        # Determinar fase del día
        if days_left > 14:
            phase = "BASE BUILDING - Volumen Alto"
            intensity = "40-60%"
        elif days_left > 7:
            phase = "PRE-PELEA - Alta Intensidad"
            intensity = "70-85%"
        elif days_left > 3:
            phase = "TAPERING - Bajo Volumen"
            intensity = "50-70%"
        elif days_left >= 0:
            phase = "PEAK WEEK - Explosividad"
            intensity = "30-50%"
        else:
            phase = "PELEA"
            intensity = "100%"
        
        # Seleccionar drills según fase
        if "BASE" in phase:
            suggested_drills = plan.drill_focus + ["Cardio", "Fuerza base"]
        elif "HIGH" in phase:
            suggested_drills = plan.drill_focus + ["Sparring intenso", "Simulación de rounds"]
        elif "TAPER" in phase:
            suggested_drills = ["Técnica pura", "Movimiento"]
        else:
            suggested_drills = ["Descanso / Recuperación", "Visualización"]
        
        # Notas nutricionales por fase
        if "BASE" in phase:
            nutrition = "Dieta de ganancia: proteína alta + carbohidratos complejos"
        elif "HIGH" in phase:
            nutrition = "Carbohidratos para mantener energía en sparring intenso"
        elif "TAPER" in phase:
            nutrition = "Reducir sodio, mantener proteína, aumentar hidratación"
        else:
            nutrition = "Ayuno o comida ligera pre-pelea"
        
        day_entry = {
            "date": current_date.isoformat(),
            "day_number": day_offset + 1,
            "days_left": days_left,
            "phase": phase,
            "intensity": intensity,
            "drills": suggested_drills[:3],  # Top 3
            "nutrition": nutrition,
            "opponent_focus": plan.opponent.name if day_offset % 3 == 0 else None,  # Cada 3 días recordar el rival
            "checkpoint": "Revisar avance" if day_offset % 7 == 0 else None,  # Weekly checkpoints
        }
        
        calendar.append(day_entry)
    
    return calendar


# ============================================================================
# GENERACIÓN DE PDF DE CALENDARIO (Opción C)
# ============================================================================

def generate_calendar_pdf(plan: TacticalPlan, target_date: str) -> bytes:
    """
    Genera un PDF con el calendario de entrenamiento día a día + plan táctico.
    Retorna bytes del PDF.
    """
    from io import BytesIO
    from calendar import monthrange
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER
    from datetime import datetime as dt
    
    # Obtener calendario
    calendar_data = generate_training_calendar(plan, target_date)
    if not calendar_data:
        return b''
    
    # Buffer para PDF
    pdf_buffer = BytesIO()
    
    # Crear documento
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#E63946'),  # Rojo deportivo
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1D3557'),  # Azul oscuro
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold',
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leading=14,
    )
    
    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        leading=10,
    )
    
    # Contenido
    content = []
    
    # PORTADA
    content.append(Spacer(1, 0.5 * inch))
    content.append(Paragraph(f"🥊 PLAN TÁCTICO MMA", title_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Información del rival
    opp_name = plan.opponent.name
    opp_style = plan.opponent.style.value if hasattr(plan.opponent.style, 'value') else str(plan.opponent.style)
    content.append(Paragraph(f"vs <b>{opp_name}</b> ({opp_style})", heading_style))
    content.append(Spacer(1, 0.15 * inch))
    
    try:
        target_dt = dt.fromisoformat(target_date).date()
        today_dt = dt.now().date()
        days_left = (target_dt - today_dt).days
        content.append(Paragraph(f"📅 Fecha Pelea: {target_dt.strftime('%d/%m/%Y')} | ⏱️ Días: {max(0, days_left)}", normal_style))
    except:
        pass
    
    content.append(Spacer(1, 0.3 * inch))
    
    # RESUMEN DE ROUNDS
    content.append(Paragraph("📋 GAME PLAN POR ROUNDS", heading_style))
    
    for rnd in plan.game_plan_rounds:
        round_text = f"<b>Round {rnd.round_number}:</b> {rnd.focus}"
        content.append(Paragraph(round_text, normal_style))
        
        if rnd.techniques:
            tech_text = f"<b>Técnicas:</b> {', '.join(rnd.techniques)}"
            content.append(Paragraph(tech_text, small_style))
        
        if rnd.contingency:
            cont_text = f"<b>Plan B:</b> {rnd.contingency}"
            content.append(Paragraph(cont_text, small_style))
        
        content.append(Spacer(1, 0.1 * inch))
    
    content.append(PageBreak())
    
    # CALENDARIO VISUAL POR MES (Lunes-Domingo)
    content.append(Paragraph("📅 CALENDARIO DE ENTRENAMIENTO", heading_style))

    date_to_entry = {d.get("date"): d for d in calendar_data}
    start_date = dt.fromisoformat(calendar_data[0]["date"]).date()
    end_date = dt.fromisoformat(calendar_data[-1]["date"]).date()

    content.append(Paragraph(
        f"Inicio del plan: <b>{start_date.strftime('%d/%m/%Y')}</b> &nbsp;&nbsp;&nbsp; Objetivo: <b>{end_date.strftime('%d/%m/%Y')}</b>",
        normal_style
    ))
    content.append(Spacer(1, 0.15 * inch))

    legend_data = [[
        "Recorte", "Sparring/Alta", "Base Técnica", "Tapering", "Peak"
    ]]
    legend_table = Table(legend_data, colWidths=[1.1*inch, 1.3*inch, 1.2*inch, 1.0*inch, 0.9*inch])
    legend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#ffb703')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f94144')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#90e0ef')),
        ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#ffd166')),
        ('BACKGROUND', (4, 0), (4, 0), colors.HexColor('#ef476f')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    content.append(legend_table)
    content.append(Spacer(1, 0.15 * inch))

    month_names_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    weekday_headers = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    def _month_iter(start_d, end_d):
        y, m = start_d.year, start_d.month
        while (y, m) <= (end_d.year, end_d.month):
            yield y, m
            if m == 12:
                y += 1
                m = 1
            else:
                m += 1

    def _cell_color(day_entry):
        if not day_entry:
            return colors.HexColor('#f2f2f2')
        phase = str(day_entry.get('phase', '')).upper()
        days_left = int(day_entry.get('days_left', 0))
        if 7 < days_left <= 14:
            return colors.HexColor('#ffb703')
        if 'PEAK' in phase:
            return colors.HexColor('#ef476f')
        if 'TAPER' in phase:
            return colors.HexColor('#ffd166')
        if 'PRE-PELEA' in phase or 'HIGH' in phase:
            return colors.HexColor('#f94144')
        if 'BASE' in phase:
            return colors.HexColor('#90e0ef')
        return colors.white

    for (year, month) in _month_iter(start_date, end_date):
        content.append(Paragraph(f"{month_names_es[month]} {year}", heading_style))

        first_weekday, num_days = monthrange(year, month)  # Monday=0
        table_data = [weekday_headers]

        current_day = 1
        week = [""] * 7
        for wd in range(first_weekday, 7):
            date_iso = dt(year, month, current_day).date().isoformat()
            day_entry = date_to_entry.get(date_iso)
            if day_entry:
                tag = ""
                phase = str(day_entry.get('phase', '')).upper()
                days_left = int(day_entry.get('days_left', 0))
                if 7 < days_left <= 14:
                    tag = "RECORTE"
                elif 'PEAK' in phase:
                    tag = "PEAK"
                elif 'TAPER' in phase:
                    tag = "TAPER"
                elif 'PRE-PELEA' in phase or 'HIGH' in phase:
                    tag = "SPARRING"
                elif 'BASE' in phase:
                    tag = "BASE"
                week[wd] = f"{current_day}\n{day_entry.get('intensity', '')}\n{tag}"
            else:
                week[wd] = ""
            current_day += 1
        table_data.append(week)

        while current_day <= num_days:
            week = [""] * 7
            for wd in range(7):
                if current_day > num_days:
                    break
                date_iso = dt(year, month, current_day).date().isoformat()
                day_entry = date_to_entry.get(date_iso)
                if day_entry:
                    tag = ""
                    phase = str(day_entry.get('phase', '')).upper()
                    days_left = int(day_entry.get('days_left', 0))
                    if 7 < days_left <= 14:
                        tag = "RECORTE"
                    elif 'PEAK' in phase:
                        tag = "PEAK"
                    elif 'TAPER' in phase:
                        tag = "TAPER"
                    elif 'PRE-PELEA' in phase or 'HIGH' in phase:
                        tag = "SPARRING"
                    elif 'BASE' in phase:
                        tag = "BASE"
                    week[wd] = f"{current_day}\n{day_entry.get('intensity', '')}\n{tag}"
                else:
                    week[wd] = f"{current_day}"
                current_day += 1
            table_data.append(week)

        cal_table = Table(table_data, colWidths=[1.05*inch]*7, rowHeights=[0.30*inch] + [0.85*inch]*(len(table_data)-1))
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1D3557')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0, 1), (-1, -1), 3),
            ('RIGHTPADDING', (0, 1), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ]

        for r in range(1, len(table_data)):
            for c in range(7):
                value = table_data[r][c]
                if not value:
                    style_cmds.append(('BACKGROUND', (c, r), (c, r), colors.HexColor('#f2f2f2')))
                    continue
                first_line = str(value).split('\n')[0]
                try:
                    day_num = int(first_line)
                    date_iso = dt(year, month, day_num).date().isoformat()
                except Exception:
                    date_iso = None
                day_entry = date_to_entry.get(date_iso) if date_iso else None
                style_cmds.append(('BACKGROUND', (c, r), (c, r), _cell_color(day_entry)))

        cal_table.setStyle(TableStyle(style_cmds))
        content.append(cal_table)
        content.append(Spacer(1, 0.12 * inch))

        if month != end_date.month or year != end_date.year:
            content.append(PageBreak())
    
    # FOOTER
    content.append(PageBreak())
    content.append(Paragraph("📌 NOTAS IMPORTANTES", heading_style))
    content.append(Paragraph(
        "➤ Este plan es guía. Adapta según tu evolución real.<br/>"
        "➤ Revisa checkpoints semanales (cada martes).<br/>"
        "➤ La fase cambiar si falta más/menos tiempo.<br/>"
        "➤ Consulta con tu entrenador ante dudas.",
        normal_style
    ))
    
    # Build PDF
    doc.build(content)
    pdf_buffer.seek(0)
    
    return pdf_buffer.getvalue()


# ============================================================================
# COMPARADOR DE PLANES (Opción C)
# ============================================================================

def compare_tactical_plans(plan1: TacticalPlan, plan2: TacticalPlan) -> Dict[str, any]:
    """
    Compara dos planes tácticos lado a lado.
    Retorna análisis detallado de similitudes y diferencias.
    """
    comparison = {
        "plan1_id": plan1.fight_id or "Plan 1",
        "plan2_id": plan2.fight_id or "Plan 2",
        "timestamp": datetime.now().isoformat(),
        "opponent_comparison": {},
        "rounds_comparison": [],
        "drill_focus_comparison": {},
        "contingency_comparison": {},
        "effectiveness_delta": {},
        "recommendation": "",
    }
    
    # 1 COMPARACIÓN DE RIVALES
    comparison["opponent_comparison"] = {
        "plan1_opponent": plan1.opponent.name,
        "plan2_opponent": plan2.opponent.name,
        "same_opponent": plan1.opponent.name.lower() == plan2.opponent.name.lower(),
        "style_match": plan1.opponent.style == plan2.opponent.style,
        "strengths_overlap": len(set(plan1.opponent.strengths) & set(plan2.opponent.strengths)),
        "weaknesses_overlap": len(set(plan1.opponent.weaknesses) & set(plan2.opponent.weaknesses)),
    }
    
    # 2. COMPARACIÓN DE ROUNDS
    max_rounds = max(len(plan1.game_plan_rounds), len(plan2.game_plan_rounds))
    for i in range(max_rounds):
        r1 = plan1.game_plan_rounds[i] if i < len(plan1.game_plan_rounds) else None
        r2 = plan2.game_plan_rounds[i] if i < len(plan2.game_plan_rounds) else None
        
        round_comp = {
            "round": i + 1,
            "plan1_focus": r1.focus if r1 else "No existe",
            "plan2_focus": r2.focus if r2 else "No existe",
            "techniques_overlap": len(set(r1.techniques) & set(r2.techniques)) if r1 and r2 else 0,
        }
        comparison["rounds_comparison"].append(round_comp)
    
    # 3. COMPARACIÓN DE DRILLS
    comparison["drill_focus_comparison"] = {
        "plan1_drills": plan1.drill_focus,
        "plan2_drills": plan2.drill_focus,
        "common_drills": list(set(plan1.drill_focus) & set(plan2.drill_focus)),
        "unique_to_plan1": list(set(plan1.drill_focus) - set(plan2.drill_focus)),
        "unique_to_plan2": list(set(plan2.drill_focus) - set(plan1.drill_focus)),
    }
    
    # 4. COMPARACIÓN DE CONTINGENCIAS
    comparison["contingency_comparison"] = {
        "plan1_count": len(plan1.contingencies),
        "plan2_count": len(plan2.contingencies),
        "overlap": sum(1 for c1 in plan1.contingencies 
                      for c2 in plan2.contingencies 
                      if c1.scenario_name.lower() == c2.scenario_name.lower()),
    }
    
    # 5. RECOMENDACIÓN FINAL
    if len(plan1.game_plan_rounds) > len(plan2.game_plan_rounds):
        comparison["recommendation"] = f"Plan 1 tiene más detalle ({len(plan1.game_plan_rounds)} rounds vs {len(plan2.game_plan_rounds)})."
    elif len(plan2.game_plan_rounds) > len(plan1.game_plan_rounds):
        comparison["recommendation"] = f"Plan 2 tiene más detalle ({len(plan2.game_plan_rounds)} rounds vs {len(plan1.game_plan_rounds)})."
    else:
        comparison["recommendation"] = "Ambos planes tienen complejidad similar."
    
    return comparison


# ============================================================================
# HISTORIAL DE VERSIONES (Opción C)
# ============================================================================

def create_plan_version(plan: TacticalPlan, change_description: str, created_by: str = "user") -> PlanVersion:
    """
    Crea un snapshot del plan actual como versión. Se usa cuando hay cambios significativos.
    """
    version_number = len(plan.version_history) + 1
    
    version = PlanVersion(
        version_number=version_number,
        created_at=datetime.now().isoformat(),
        created_by=created_by,
        change_description=change_description,
        plan_snapshot=plan.to_dict(),
    )
    
    plan.version_history.append(version)
    return version


def restore_plan_version(plan: TacticalPlan, version_number: int) -> bool:
    """
    Restaura un plan a una versión específica del historial.
    Retorna True si la restauración fue exitosa.
    """
    target_version = None
    for v in plan.version_history:
        if v.version_number == version_number:
            target_version = v
            break
    
    if not target_version:
        return False
    
    # Restaurar desde snapshot
    restored_plan = TacticalPlan.from_dict(target_version.plan_snapshot)
    
    # Copiar atributos restaurados al plan actual
    plan.opponent = restored_plan.opponent
    plan.game_plan_rounds = restored_plan.game_plan_rounds
    plan.contingencies = restored_plan.contingencies
    plan.drill_focus = restored_plan.drill_focus
    plan.my_phase = restored_plan.my_phase
    
    # Registrar la restauración como nueva versión
    create_plan_version(plan, f"Restored from version {version_number}", created_by="system")
    
    return True


def get_plan_version_diff(plan: TacticalPlan, version_number: int) -> Dict[str, any]:
    """
    Muestra las diferencias entre el plan actual y una versión histórica.
    """
    target_version = None
    for v in plan.version_history:
        if v.version_number == version_number:
            target_version = v
            break
    
    if not target_version:
        return {}
    
    restored = TacticalPlan.from_dict(target_version.plan_snapshot)
    
    diff = {
        "version_number": version_number,
        "created_at": target_version.created_at,
        "change_description": target_version.change_description,
        "round_count_changed": len(restored.game_plan_rounds) != len(plan.game_plan_rounds),
        "old_round_count": len(restored.game_plan_rounds),
        "new_round_count": len(plan.game_plan_rounds),
        "drills_added": list(set(plan.drill_focus) - set(restored.drill_focus)),
        "drills_removed": list(set(restored.drill_focus) - set(plan.drill_focus)),
        "contingencies_added": len(plan.contingencies) - len(restored.contingencies),
    }
    
    return diff

