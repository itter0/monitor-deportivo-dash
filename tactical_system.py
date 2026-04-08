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
    weigh_in_date: Optional[str] = None  # Fecha de pesaje (ISO format)
    fight_weight: Optional[float] = None  # Peso objetivo del combate
    
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
            "weigh_in_date": self.weigh_in_date,
            "fight_weight": self.fight_weight,
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
            weigh_in_date=data.get("weigh_in_date"),
            fight_weight=data.get("fight_weight"),
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
    Genera un calendario de entrenamiento DETALLADO día a día desde hoy hasta la fecha objetivo.
    Cada día incluye tareas ESPECÍFICAS basadas en:
    - Técnicas del game plan (rounds)
    - Debilidades del rival
    - Phaseprogresión
    - Planes nutricionales concretos
    - Recuperación y control de fatiga
    """
    from datetime import datetime as dt, timedelta as td
    
    calendar = []
    
    try:
        today = dt.now().date()
        target = dt.fromisoformat(target_date).date()
        days_until_fight = (target - today).days
    except:
        return []

    weigh_in_date = None
    try:
        if plan.weigh_in_date:
            weigh_in_date = dt.fromisoformat(plan.weigh_in_date).date()
    except Exception:
        weigh_in_date = None
    
    if days_until_fight <= 0:
        return []
    
    # MAPA TÉCNICO: Extraer técnicas del game plan para cada round
    round_technique_map = {}
    for r in plan.game_plan_rounds:
        round_technique_map[r.round_number] = {
            'focus': r.focus,
            'techniques': r.techniques,
            'contingency': r.contingency
        }
    
    # DEBILIDADES A EXPLOTAR
    weaknesses_to_exploit = plan.opponent.weaknesses if plan.opponent.weaknesses else ["General defense"]
    
    # MAPA DE EJERCICIOS POR FASE Y ENFOQUE
    drill_library = {
        'Striking': ['Pad work (jabs, crosses)', 'Kick drills', 'Head movement drills', 'Distance management'],
        'Grappling': ['Takedown drills', 'Clinch work', 'Top control', 'Submission chains'],
        'Balanced': ['Mixed sparring', 'Technical wrestling', 'Striking combinations', 'Transition drills'],
        'Clinch': ['Clinch entries', 'Clinch defense', 'Clinch striking', 'Clinch takedowns'],
        'Footwork': ['Lateral movement', 'Range control', 'Base maintenance', 'Angle cutting'],
        'Defense': ['Head movement', 'Sprawl practice', 'Distance management', 'Postural defense'],
        'Conditioning': ['High-intensity cardio', 'Sled pushes', 'Battle ropes', 'Energy system work'],
        'Recovery': ['Light aerobic work', 'Mobility', 'Stretching', 'Breathing work']
    }
    
    # Generar calendario día por día
    for day_offset in range(0, days_until_fight + 1):
        current_date = today + td(days=day_offset)
        days_left = days_until_fight - day_offset

        is_weigh_in_day = bool(weigh_in_date and current_date == weigh_in_date)
        is_fight_day = current_date == target
        
        # =====================================================================
        # DETERMINAR FASE - más específico
        # =====================================================================
        if is_fight_day:
            phase_name = "COMBATE"
            phase_focus = "Activación final y ejecución"
            intensity_level = "Máxima"
            session_type = "Warm-up + Combate"
        elif is_weigh_in_day:
            phase_name = "PESAJE"
            phase_focus = "Corte final y control"
            intensity_level = "Muy Baja"
            session_type = "Pesaje + descarga"
        elif weigh_in_date and current_date > weigh_in_date and current_date < target:
            phase_name = "POST-PESAJE"
            phase_focus = "Rehidratación y activación"
            intensity_level = "Baja"
            session_type = "Refeed + activación"
        elif days_left > 21:
            phase_name = "FASE 1: BASE BUILD"
            phase_focus = "Volumen y fundamentos"
            intensity_level = "Moderada"
            session_type = "Técnica + Volumen"
        elif days_left > 14:
            phase_name = "FASE 2: FORÇA"
            phase_focus = "Potencia y explosividad"
            intensity_level = "Alta"
            session_type = "Técnica + Intensidad"
        elif days_left > 7:
            phase_name = "FASE 3: PRE-PELEA"
            phase_focus = "Game plan específico"
            intensity_level = "Muy Alta"
            session_type = "Game plan training"
        elif days_left > 3:
            phase_name = "TAPERING: Descarga"
            phase_focus = "Técnica pura, sin fatiga"
            intensity_level = "Baja"
            session_type = "Técnica + Recuperación"
        else:
            phase_name = "SEMANA DE PELEA"
            phase_focus = "Mentalización y preparación mental"
            intensity_level = "Muy Baja"
            session_type = "Descanso activo"
        
        # =====================================================================
        # GENERAR TAREAS ESPECÍFICAS DEL DÍA
        # =====================================================================
        day_tasks = []
        special_day = is_weigh_in_day or is_fight_day or (weigh_in_date and current_date > weigh_in_date and current_date < target)
        weakness = ''

        if is_weigh_in_day:
            task_1 = "⚖️ PESAJE OFICIAL\n  → Presentarte en peso objetivo"
            task_2 = "💧 CORTO FINAL\n  → Mantener solo activación ligera y control de líquidos"
            task_3 = "🍽️ REHIDRATACIÓN INMEDIATA\n  → Electrolitos, carbohidratos rápidos y sales"
            task_4 = "🧠 CONTROL MENTAL\n  → Respiración, visualización y no gastar energía"
            day_tasks.extend([task_1, task_2, task_3, task_4])
        elif is_fight_day:
            task_1 = "🥊 COMBATE\n  → Warm-up, activación neuromuscular y ejecución del plan"
            task_2 = "🎯 ENTRADA AL PLAN\n  → Primeros intercambios según la estrategia definida"
            task_3 = "⚡ ADMINISTRAR ENERGÍA\n  → Ritmo, control del esfuerzo y adaptación al rival"
            task_4 = "🧠 ENFOQUE MENTAL\n  → Seguir instrucciones, respirar y mantener calma"
            day_tasks.extend([task_1, task_2, task_3, task_4])
        elif weigh_in_date and current_date > weigh_in_date and current_date < target:
            task_1 = "💦 REHIDRATACIÓN\n  → Recuperar volumen, sodio y glucógeno"
            task_2 = "🥗 COMIDA DE RECUPERACIÓN\n  → Carbohidratos fáciles + proteína magra"
            task_3 = "🧪 ACTIVACIÓN\n  → Movilidad, sombra ligera y timing"
            task_4 = "🧠 AJUSTE TÁCTICO\n  → Repasar plan de combate sin fatigar"
            day_tasks.extend([task_1, task_2, task_3, task_4])
        else:
            # Distribución de rounds a entrenar (cada 3-4 días enfoca un round diferente)
            round_to_focus = ((day_offset // 3) % len(round_technique_map)) + 1 if round_technique_map else 1
            
            # Tarea 1: ENFOQUE TÉCNICO ESPECÍFICO
            if round_to_focus in round_technique_map:
                round_data = round_technique_map[round_to_focus]
                task_1 = f"🥊 ROUND {round_to_focus} - {round_data['focus']}"
                if round_data['techniques']:
                    task_1 += f"\n  → Técnicas: {', '.join(round_data['techniques'][:2])}"
            else:
                task_1 = "🥊 Trabajo técnico general del game plan"
            
            day_tasks.append(task_1)
            
            # Tarea 2: ADAPTACIÓN AL RIVAL
            weakness_idx = day_offset % len(weaknesses_to_exploit)
            weakness = weaknesses_to_exploit[weakness_idx]
            
            if "Striking" in str(plan.opponent.style):
                task_2 = f"🛡️ EXPLOTAR DEBILIDAD: {weakness}\n  → Drills defensivos + ataques de rango"
            elif "Grappling" in str(plan.opponent.style):
                task_2 = f"🛡️ EXPLOTAR DEBILIDAD: {weakness}\n  → Trabajo de clinch + takedowns"
            else:
                task_2 = f"🛡️ EXPLOTAR DEBILIDAD: {weakness}\n  → Sparring técnico mixto"
            
            day_tasks.append(task_2)
            
            # Tarea 3: DRILLS BASADOS EN FASE
            if "BASE" in phase_name:
                drills_to_do = drill_library.get('Striking', []) + drill_library.get('Conditioning', [])
                task_3 = f"⚙️ DRILLS VOLUMEN\n  → {', '.join(drills_to_do[:3])}"
            elif "FORÇA" in phase_name:
                drills_to_do = drill_library.get('Balanced', []) + [d for d in drill_library.get('Striking', []) if 'combinations' in d.lower()]
                task_3 = f"⚙️ DRILLS ALTA INTENSIDAD\n  → {', '.join(drills_to_do[:3])}"
            elif "PRE" in phase_name:
                drills_to_do = drill_library.get('Balanced', [])
                task_3 = f"⚙️ SPARRING GAME PLAN\n  → {', '.join(drills_to_do[:2])}"
            elif "TAPER" in phase_name:
                drills_to_do = ["Técnica sin resistencia", "Movimiento puro", "Posicionamiento"]
                task_3 = f"⚙️ TÉCNICA PURA (Sin fatiga)\n  → {', '.join(drills_to_do[:2])}"
            else:  # Fight week
                drills_to_do = ["Shadowboxing", "Visualización", "Movilidad"]
                task_3 = f"⚙️ DESCANSO ACTIVO\n  → {', '.join(drills_to_do[:2])}"
            
            day_tasks.append(task_3)
            
            # Tarea 4: CONTINGENCIA (cada 2 semanas)
            if day_offset % 14 == 0 and round_technique_map and round_to_focus in round_technique_map:
                contingency = round_technique_map[round_to_focus].get('contingency', '')
                if contingency:
                    task_4 = f"🔄 ENTRENAR CONTINGENCIA\n  → {contingency[:80]}"
                    day_tasks.append(task_4)
        
        # =====================================================================
        # NUTRICIÓN ESPECÍFICA
        # =====================================================================
        if is_weigh_in_day:
            nutrition = "🍽️ Corte de peso\n  → Sódio mínimo, líquidos controlados y comida ligera"
        elif is_fight_day:
            nutrition = "🍽️ Combate\n  → Comida ligera pre-activación y sales según tolerancia"
        elif weigh_in_date and current_date > weigh_in_date and current_date < target:
            nutrition = "🍽️ Rehidratación\n  → Carbohidratos rápidos, sales, agua y proteína fácil"
        elif "BASE" in phase_name:
            nutrition = "🍽️ Alto volumen calórico\n  → Proteína: 2g x kg | Carbs: complejos | Grasas: equilibradas"
        elif "FORÇA" in phase_name:
            nutrition = "🍽️ Ganancias de fuerza\n  → Proteína: 2.2g x kg | Carbs pre/post: arroz, papas | Creatina"
        elif "PRE" in phase_name:
            nutrition = "🍽️ Energía para sparring\n  → Carbs >2.5g x kg | Proteína: 2g x kg | Sodio moderado"
        elif "TAPER" in phase_name:
            nutrition = "🍽️ Reducción gradual sodio\n  → Proteína: 2g x kg | Carbs: moderados | Agua: abundante"
        else:
            nutrition = "🍽️ Pre-pelea\n  → Ayuno ligero matutino | Comida ligera 3h previa | Hidratación"
        
        # =====================================================================
        # RECUPERACIÓN Y CONTROL
        # =====================================================================
        if is_weigh_in_day:
            recovery = "😴 Control de fatiga y calma\n  → Sin carga, respiración y preparación mental"
        elif is_fight_day:
            recovery = "😴 Post-combate\n  → Recuperación, enfriamiento y seguimiento médico"
        elif weigh_in_date and current_date > weigh_in_date and current_date < target:
            recovery = "😴 Activación suave\n  → Movilidad, caminatas y sueño suficiente"
        elif days_left <= 3:
            recovery = "😴 MÁXIMA RECUPERACIÓN\n  → Sueño 9h+ | Hielo/Calor | Masaje"
        elif days_left <= 7:
            recovery = "😴 Recuperación prioritaria\n  → Sueño 8-9h | Movilidad 15 min diarios"
        else:
            recovery = "😴 Dormire 7-8h + Movilidad 3x semana"
        
        # =====================================================================
        # MONITOREO Y CHECKPOINTS
        # =====================================================================
        checkpoint_msg = ""
        if day_offset % 7 == 0 and day_offset > 0:
            checkpoint_msg = "✅ CHECKPOINT SEMANAL: Revisar video, ajustar si es necesario"
        
        # =====================================================================
        # CONSTRUIR ENTRADA DEL CALENDARIO
        # =====================================================================
        day_entry = {
            "date": current_date.isoformat(),
            "day_number": day_offset + 1,
            "days_left": days_left,
            "phase": phase_name,
            "phase_focus": phase_focus,
            "intensity": intensity_level,
            "session_type": session_type,
            "tasks": day_tasks,  # Tareas específicas del día
            "nutrition": nutrition,
            "recovery": recovery,
            "opponent_name": plan.opponent.name,
            "opponent_weakness": weakness,
            "checkpoint": checkpoint_msg if checkpoint_msg else None,
            "day_of_week": current_date.strftime("%A"),
        }
        
        calendar.append(day_entry)
    
    return calendar


# ============================================================================
# GENERACIÓN DE PDF DE CALENDARIO (Opción C)
# ============================================================================

def generate_calendar_pdf(plan: TacticalPlan, target_date: str) -> bytes:
    """
    Genera un PDF DETALLADO con el calendario de entrenamiento día a día.
    Incluye tareas específicas, nutrición, recuperación, etc.
    """
    from io import BytesIO
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from datetime import datetime as dt
    
    # Obtener calendario
    calendar_data = generate_training_calendar(plan, target_date)
    if not calendar_data:
        return b''
    
    # Buffer para PDF
    pdf_buffer = BytesIO()
    
    # Crear documento (usar letter que es más grande)
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    
    # Estilos mejorados
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#E63946'),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1D3557'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#E63946'),
        spaceAfter=8,
        spaceBefore=6,
        fontName='Helvetica-Bold',
    )
    
    day_header_style = ParagraphStyle(
        'DayHeader',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#1D3557'),
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    
    task_style = ParagraphStyle(
        'Task',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        leading=11,
        leftIndent=10,
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        leading=12,
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#555555'),
        leading=10,
    )
    
    # Contenido
    content = []
    
    # === PORTADA ===
    content.append(Spacer(1, 0.3 * inch))
    content.append(Paragraph("🥊 PLAN TÁCTICO MMA", title_style))
    content.append(Spacer(1, 0.15 * inch))
    
    opp_name = plan.opponent.name
    opp_style = plan.opponent.style.value if hasattr(plan.opponent.style, 'value') else str(plan.opponent.style)
    content.append(Paragraph(f"<b>vs {opp_name}</b> ({opp_style})", subtitle_style))
    content.append(Spacer(1, 0.25 * inch))
    
    # Fechas
    try:
        target_dt = dt.fromisoformat(target_date).date()
        today_dt = dt.now().date()
        days_left = (target_dt - today_dt).days
        content.append(Paragraph(
            f"📅 Fecha del combate: <b>{target_dt.strftime('%d de %B de %Y')}</b>",
            day_header_style
        ))
        content.append(Paragraph(
            f"⏱️ Días de preparación: <b>{max(0, days_left)} días</b>",
            day_header_style
        ))
        if plan.weigh_in_date:
            try:
                weigh_dt = dt.fromisoformat(plan.weigh_in_date).date()
                content.append(Paragraph(
                    f"⚖️ Día de pesaje: <b>{weigh_dt.strftime('%d de %B de %Y')}</b>",
                    day_header_style
                ))
            except Exception:
                pass
        if plan.fight_weight is not None:
            try:
                fight_weight_value = float(plan.fight_weight)
                content.append(Paragraph(
                    f"🏷️ Peso objetivo del combate: <b>{fight_weight_value:.1f} kg</b>",
                    day_header_style
                ))
            except Exception:
                content.append(Paragraph(
                    f"🏷️ Peso objetivo del combate: <b>{plan.fight_weight}</b>",
                    day_header_style
                ))
    except:
        pass
    
    content.append(Spacer(1, 0.2 * inch))
    
    # === RESUMEN DEL RIVAL ===
    content.append(Paragraph("📋 ANÁLISIS DEL RIVAL", heading_style))
    
    content.append(Paragraph(
        f"<b>Estilo de lucha:</b> {opp_style}",
        normal_style
    ))
    
    if plan.opponent.strengths:
        content.append(Paragraph(
            f"<b>Fortalezas:</b> {', '.join(plan.opponent.strengths)}",
            normal_style
        ))
    
    if plan.opponent.weaknesses:
        content.append(Paragraph(
            f"<b>Debilidades a explotar:</b> {', '.join(plan.opponent.weaknesses)}",
            normal_style
        ))
    
    content.append(Spacer(1, 0.15 * inch))
    
    # === GAME PLAN ===
    content.append(Paragraph("🎯 GAME PLAN POR ROUNDS", heading_style))
    
    for rnd in plan.game_plan_rounds:
        content.append(Paragraph(
            f"<b>Round {rnd.round_number}:</b> {rnd.focus}",
            day_header_style
        ))
        
        if rnd.techniques:
            tech_list = '<br/>'.join([f"  • {t}" for t in rnd.techniques])
            content.append(Paragraph(f"<b>Técnicas:</b><br/>{tech_list}", task_style))
        
        if rnd.contingency:
            content.append(Paragraph(
                f"<b>Plan B:</b> {rnd.contingency}",
                task_style
            ))
        
        content.append(Spacer(1, 0.08 * inch))
    
    content.append(PageBreak())
    
    # === CALENDARIO DETALLADO DÍA A DÍA ===
    content.append(Paragraph("📅 CALENDARIO DE ENTRENAMIENTO DETALLADO", heading_style))
    content.append(Spacer(1, 0.1 * inch))
    
    # Agrupar por fase
    phases_seen = set()
    for day_data in calendar_data:
        phase_name = day_data.get('phase', '')
        
        if phase_name not in phases_seen:
            # Nueva fase encontrada - crear sección
            phases_seen.add(phase_name)
            content.append(Spacer(1, 0.05 * inch))
            content.append(Paragraph(f"{'='*60}", small_style))
            content.append(Paragraph(
                f"📌 {phase_name}",
                heading_style
            ))
            content.append(Paragraph(
                f"Enfoque: {day_data.get('phase_focus', '')} | Intensidad: {day_data.get('intensity', '')}",
                small_style
            ))
            content.append(Spacer(1, 0.08 * inch))
        
        # === ENTRADA DEL DÍA ===
        date_obj = dt.fromisoformat(day_data['date']).date()
        day_name = date_obj.strftime('%A').capitalize()
        
        day_title = f"DÍA {day_data['day_number']} - {date_obj.strftime('%d/%m/%Y')} ({day_name})"
        if day_data['days_left'] == 0:
            day_title += " 🏁 COMBATE"
        else:
            day_title += f" [{day_data['days_left']} días para combate]"
        
        content.append(Paragraph(day_title, day_header_style))
        
        # Tareas del día
        tasks = day_data.get('tasks', [])
        if tasks:
            for task in tasks:
                # Reemplazar saltos de línea para Paragraph
                task_html = task.replace('\n', '<br/>')
                content.append(Paragraph(f"  {task_html}", task_style))
            content.append(Spacer(1, 0.05 * inch))
        
        # Nutrición
        nutrition = day_data.get('nutrition', '')
        if nutrition:
            nutrition_html = nutrition.replace('\n', '<br/>')
            content.append(Paragraph(f"<b>🍽️ Nutrición:</b> {nutrition_html}", task_style))
        
        # Recuperación
        recovery = day_data.get('recovery', '')
        if recovery:
            recovery_html = recovery.replace('\n', '<br/>')
            content.append(Paragraph(f"<b>😴 Recuperación:</b> {recovery_html}", task_style))
        
        # Checkpoint
        checkpoint = day_data.get('checkpoint')
        if checkpoint:
            content.append(Paragraph(f"<b>✅ {checkpoint}</b>", task_style))
        
        content.append(Spacer(1, 0.1 * inch))
        
        # Salto de página cada 5 días o cuando cambio de fase
        if day_data['day_number'] % 5 == 0:
            next_phase = None
            for d in calendar_data:
                if d['day_number'] == day_data['day_number'] + 1:
                    next_phase = d.get('phase')
                    break
            
            if next_phase and next_phase != phase_name:
                content.append(PageBreak())
    
    # === RESUMEN FINAL ===
    content.append(PageBreak())
    content.append(Paragraph("📌 INSTRUCCIONES Y CONSEJOS FINALES", heading_style))
    
    final_text = """
    <b>✓ CÓMO USAR ESTE PLAN:</b><br/>
    1. Este calendario es tu guía concreta día a día.<br/>
    2. Cada día tiene tareas ESPECÍFICAS para prepararte contra tu rival.<br/>
    3. Sigue las fases: progresa de volumen → intensidad → descarga → peak.<br/>
    4. Monitorea tu nutrición según la fase (carbohidatos varían mucho).<br/>
    5. Los checkpoints semanales son críticos para ajustar si falta/sobra tiempo.<br/>
    <br/>
    <b>✓ SI ALGO NO VA BIEN:</b><br/>
    • Aumenta volumen si sientes que te falta resistencia.<br/>
    • Reduce intensidad si acumulas fatiga o lesiones.<br/>
    • Modifica nutrición si pierdes/ganas peso inesperadamente.<br/>
    • Consulta con tu entrenador de clinch/lucha si hay técnicas nuevas.<br/>
    <br/>
    <b>✓ ÚLTIMA SEMANA (PEAK WEEK):</b><br/>
    • Máxima recuperación, mínimo volumen.<br/>
    • Técnica pura sin resistencia.<br/>
    • Dormir 9+ horas diarias.<br/>
    • Mantener el peso objective 2-3 días antes.<br/>
    <br/>
    <b>¡ÉXITO EN TU COMBATE! 🥊</b>
    """
    
    content.append(Paragraph(final_text, normal_style))
    
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

