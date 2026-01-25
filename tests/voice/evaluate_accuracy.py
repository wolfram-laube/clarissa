#!/usr/bin/env python3
"""
CLARISSA Voice Intent Evaluation Framework.

Evaluates intent parsing accuracy against test utterances.
Generates metrics and CI-compatible reports.

Usage:
    python evaluate_accuracy.py                    # Run with test_utterances.json
    python evaluate_accuracy.py --file custom.json # Custom utterance file
    python evaluate_accuracy.py --ci               # CI mode (exit code = fail if <90%)
"""

import json
import sys
import argparse
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime


@dataclass
class EvaluationResult:
    """Result of a single utterance evaluation."""
    utterance_id: str
    text: str
    expected_intent: str
    predicted_intent: str
    expected_slots: Dict[str, Any]
    predicted_slots: Dict[str, Any]
    expected_confidence: float
    actual_confidence: float
    intent_correct: bool
    slots_correct: bool
    confidence_met: bool
    
    @property
    def fully_correct(self) -> bool:
        return self.intent_correct and self.slots_correct and self.confidence_met


@dataclass
class EvaluationMetrics:
    """Aggregated evaluation metrics."""
    total: int = 0
    intent_correct: int = 0
    slots_correct: int = 0
    confidence_met: int = 0
    fully_correct: int = 0
    
    # Per-intent metrics
    per_intent: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {"total": 0, "correct": 0}))
    
    # Errors
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def intent_accuracy(self) -> float:
        return self.intent_correct / self.total if self.total > 0 else 0.0
    
    @property
    def slot_accuracy(self) -> float:
        return self.slots_correct / self.total if self.total > 0 else 0.0
    
    @property
    def overall_accuracy(self) -> float:
        return self.fully_correct / self.total if self.total > 0 else 0.0
    
    def add_result(self, result: EvaluationResult):
        """Add a single result to metrics."""
        self.total += 1
        
        if result.intent_correct:
            self.intent_correct += 1
        if result.slots_correct:
            self.slots_correct += 1
        if result.confidence_met:
            self.confidence_met += 1
        if result.fully_correct:
            self.fully_correct += 1
        
        # Per-intent tracking
        intent = result.expected_intent
        self.per_intent[intent]["total"] += 1
        if result.intent_correct:
            self.per_intent[intent]["correct"] += 1
        
        # Track errors
        if not result.fully_correct:
            self.errors.append({
                "id": result.utterance_id,
                "text": result.text,
                "expected": result.expected_intent,
                "predicted": result.predicted_intent,
                "expected_slots": result.expected_slots,
                "predicted_slots": result.predicted_slots,
                "issues": self._identify_issues(result)
            })
    
    def _identify_issues(self, result: EvaluationResult) -> List[str]:
        """Identify what went wrong."""
        issues = []
        if not result.intent_correct:
            issues.append(f"intent: expected '{result.expected_intent}', got '{result.predicted_intent}'")
        if not result.slots_correct:
            issues.append(f"slots mismatch")
        if not result.confidence_met:
            issues.append(f"confidence: expected >={result.expected_confidence:.2f}, got {result.actual_confidence:.2f}")
        return issues


def parse_intent_rules(text: str) -> Dict[str, Any]:
    """
    Rule-based intent parsing (mirror of IntentParser._parse_with_rules).
    Works without any API key.
    """
    text_lower = text.lower().strip()
    slots = {}
    
    # Cancel
    cancel_patterns = ["stop", "cancel", "never mind", "abort", "quit"]
    if text_lower in cancel_patterns or text_lower.startswith("cancel"):
        return {"intent": "cancel", "confidence": 1.0, "slots": {}}
    
    # Confirm
    confirm_patterns = ["yes", "yeah", "confirm", "ok", "okay", "do it", "go ahead"]
    if text_lower in confirm_patterns:
        return {"intent": "confirm", "confidence": 1.0, "slots": {}}
    
    # Help
    if text_lower == "help" or text_lower.startswith("what can") or \
       text_lower.startswith("how do i") or "help me" in text_lower or \
       "what commands" in text_lower:
        return {"intent": "help", "confidence": 1.0, "slots": {}}
    
    # Visualization
    viz_triggers = ["show", "display", "visualize", "plot", "view", "see", "what does"]
    is_viz = any(trigger in text_lower for trigger in viz_triggers)
    
    if is_viz:
        # Property extraction
        if "perm" in text_lower:
            slots["property"] = "permeability"
        elif "poro" in text_lower:
            slots["property"] = "porosity"
        elif "saturation" in text_lower or " sw " in text_lower:
            if "water" in text_lower:
                slots["property"] = "water_saturation"
            else:
                slots["property"] = "saturation"
        elif "pressure" in text_lower:
            slots["property"] = "pressure"
        
        # Layer extraction
        layer_match = re.search(r'layer\s*(\d+)', text_lower)
        if layer_match:
            slots["layer"] = int(layer_match.group(1))
        
        # Time extraction
        time_patterns = [
            r'(?:day|time)\s*(\d+)',
            r'at\s+(\d+)\s*(?:days?)?',
            r'(\d+)\s*days?'
        ]
        for pattern in time_patterns:
            time_match = re.search(pattern, text_lower)
            if time_match:
                slots["time_days"] = int(time_match.group(1))
                break
        
        # View type
        if "3d" in text_lower:
            slots["view_type"] = "3d"
        elif "animat" in text_lower:
            slots["view_type"] = "animation"
        elif "cross" in text_lower or "section" in text_lower:
            slots["view_type"] = "cross_section_xy"
        
        confidence = 0.95 if slots else 0.80
        return {"intent": "visualize_property", "confidence": confidence, "slots": slots}
    
    # Query
    query_triggers = ["what is", "how much", "tell me", "get", "current"]
    is_query = any(trigger in text_lower for trigger in query_triggers)
    
    if is_query:
        if "water cut" in text_lower:
            slots["property"] = "water_cut"
        elif "oil rate" in text_lower:
            slots["property"] = "oil_rate"
        elif "water" in text_lower and ("rate" in text_lower or "producing" in text_lower):
            slots["property"] = "water_rate"
        elif "pressure" in text_lower:
            slots["property"] = "pressure"
        
        # Well extraction
        well_match = re.search(r'(prod(?:ucer)?\s*\d+|inj(?:ector)?\s*\d+)', text_lower)
        if well_match:
            well = well_match.group(1).upper().replace(" ", "").replace("UCER", "").replace("ECTOR", "")
            slots["well"] = well
        
        if slots:
            return {"intent": "query_value", "confidence": 0.90, "slots": slots}
    
    # Navigate
    nav_triggers = ["go to", "navigate", "back to", "show me"]
    is_nav = any(trigger in text_lower for trigger in nav_triggers) and \
             any(target in text_lower for target in ["result", "sensitiv", "model", "export", "grid"])
    
    if is_nav:
        if "result" in text_lower:
            slots["target"] = "results"
        elif "sensitiv" in text_lower:
            slots["target"] = "sensitivity"
        elif "model" in text_lower:
            slots["target"] = "model"
        
        if slots:
            return {"intent": "navigate", "confidence": 0.90, "slots": slots}
    
    # Unknown
    return {"intent": "unknown", "confidence": 0.0, "slots": {}}


def compare_slots(expected: Dict[str, Any], predicted: Dict[str, Any]) -> bool:
    """
    Compare expected and predicted slots with fuzzy matching.
    """
    # Check all expected slots are present and match
    for key, expected_value in expected.items():
        if key not in predicted:
            # Allow property variants (saturation vs water_saturation)
            if key == "property":
                # Check for partial matches
                pred_prop = predicted.get("property", "")
                if expected_value in pred_prop or pred_prop in expected_value:
                    continue
            return False
        
        predicted_value = predicted[key]
        
        # Exact match
        if expected_value == predicted_value:
            continue
        
        # String normalization
        if isinstance(expected_value, str) and isinstance(predicted_value, str):
            if expected_value.lower().replace("_", "") == predicted_value.lower().replace("_", ""):
                continue
        
        # Property fuzzy match
        if key == "property":
            exp_norm = expected_value.lower().replace("_", "")
            pred_norm = predicted_value.lower().replace("_", "")
            if exp_norm in pred_norm or pred_norm in exp_norm:
                continue
        
        return False
    
    return True


def evaluate_utterance(utterance: Dict[str, Any]) -> EvaluationResult:
    """Evaluate a single utterance."""
    text = utterance["text"]
    expected_intent = utterance["expected_intent"]
    expected_slots = utterance.get("expected_slots", {})
    min_confidence = utterance.get("min_confidence", 0.8)
    
    # Parse
    result = parse_intent_rules(text)
    
    # Compare
    intent_correct = result["intent"] == expected_intent
    slots_correct = compare_slots(expected_slots, result["slots"])
    confidence_met = result["confidence"] >= min_confidence
    
    return EvaluationResult(
        utterance_id=utterance.get("id", "unknown"),
        text=text,
        expected_intent=expected_intent,
        predicted_intent=result["intent"],
        expected_slots=expected_slots,
        predicted_slots=result["slots"],
        expected_confidence=min_confidence,
        actual_confidence=result["confidence"],
        intent_correct=intent_correct,
        slots_correct=slots_correct,
        confidence_met=confidence_met
    )


def evaluate_dataset(utterances: List[Dict[str, Any]]) -> EvaluationMetrics:
    """Evaluate entire dataset."""
    metrics = EvaluationMetrics()
    
    for utterance in utterances:
        result = evaluate_utterance(utterance)
        metrics.add_result(result)
    
    return metrics


def print_report(metrics: EvaluationMetrics, verbose: bool = False):
    """Print evaluation report."""
    print("=" * 60)
    print("CLARISSA Voice Intent Evaluation Report")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Overall metrics
    print("📊 Overall Metrics")
    print("-" * 40)
    print(f"Total utterances:     {metrics.total}")
    print(f"Intent accuracy:      {metrics.intent_accuracy:.1%} ({metrics.intent_correct}/{metrics.total})")
    print(f"Slot accuracy:        {metrics.slot_accuracy:.1%} ({metrics.slots_correct}/{metrics.total})")
    print(f"Confidence met:       {metrics.confidence_met}/{metrics.total}")
    print(f"Fully correct:        {metrics.overall_accuracy:.1%} ({metrics.fully_correct}/{metrics.total})")
    print()
    
    # Per-intent breakdown
    print("📋 Per-Intent Accuracy")
    print("-" * 40)
    for intent, data in sorted(metrics.per_intent.items()):
        acc = data["correct"] / data["total"] if data["total"] > 0 else 0
        status = "✅" if acc >= 0.9 else "⚠️" if acc >= 0.7 else "❌"
        print(f"{status} {intent:25} {acc:.0%} ({data['correct']}/{data['total']})")
    print()
    
    # Errors
    if metrics.errors and verbose:
        print("❌ Errors")
        print("-" * 40)
        for err in metrics.errors[:10]:  # Show first 10
            print(f"  [{err['id']}] \"{err['text']}\"")
            for issue in err['issues']:
                print(f"    → {issue}")
        if len(metrics.errors) > 10:
            print(f"  ... and {len(metrics.errors) - 10} more errors")
        print()
    
    # Summary
    print("=" * 60)
    if metrics.overall_accuracy >= 0.9:
        print("✅ PASS - Accuracy target (90%) met!")
    else:
        print(f"❌ FAIL - Accuracy {metrics.overall_accuracy:.1%} below 90% target")
    print("=" * 60)


def generate_json_report(metrics: EvaluationMetrics) -> Dict[str, Any]:
    """Generate JSON report for CI integration."""
    return {
        "timestamp": datetime.now().isoformat(),
        "total": metrics.total,
        "accuracy": {
            "intent": metrics.intent_accuracy,
            "slots": metrics.slot_accuracy,
            "overall": metrics.overall_accuracy
        },
        "counts": {
            "intent_correct": metrics.intent_correct,
            "slots_correct": metrics.slots_correct,
            "confidence_met": metrics.confidence_met,
            "fully_correct": metrics.fully_correct
        },
        "per_intent": dict(metrics.per_intent),
        "errors": metrics.errors,
        "pass": metrics.overall_accuracy >= 0.9
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate CLARISSA voice intent accuracy")
    parser.add_argument("--file", "-f", default="test_utterances.json",
                       help="Path to utterances JSON file")
    parser.add_argument("--ci", action="store_true",
                       help="CI mode: exit 1 if accuracy < 90%")
    parser.add_argument("--json", action="store_true",
                       help="Output JSON report instead of text")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed error information")
    args = parser.parse_args()
    
    # Find utterances file
    utterance_file = Path(args.file)
    if not utterance_file.exists():
        # Try relative to script location
        script_dir = Path(__file__).parent
        utterance_file = script_dir / args.file
    
    if not utterance_file.exists():
        print(f"Error: Utterance file not found: {args.file}")
        sys.exit(1)
    
    # Load utterances
    with open(utterance_file) as f:
        data = json.load(f)
    
    utterances = data.get("utterances", data)
    if isinstance(utterances, dict):
        utterances = [utterances]
    
    # Evaluate
    metrics = evaluate_dataset(utterances)
    
    # Output
    if args.json:
        report = generate_json_report(metrics)
        print(json.dumps(report, indent=2))
    else:
        print_report(metrics, verbose=args.verbose)
    
    # CI exit code
    if args.ci and metrics.overall_accuracy < 0.9:
        sys.exit(1)


if __name__ == "__main__":
    main()