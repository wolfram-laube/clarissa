# ADR-026: CLARISSA Testing Strategy

| Status | Proposed |
|--------|----------|
| Date | 2026-01-22 |
| Authors | Wolfram Laube, Claude (AI Assistant) |
| Supersedes | - |
| Related | ADR-024 (Core System), ADR-025 (LLM Integration) |

---

## Context

CLARISSA is not an ordinary software system. The testing strategy must cover:

1. **Standard Software Testing**: Unit, Integration, E2E
2. **LLM Output Testing**: Wie testet man generierte Decks?
3. **Conversation Testing**: Dialog-Flows, Intent Recognition
4. **Simulation Validation**: Physical plausibility of results

Besondere Herausforderung: LLM-Outputs sind **non-deterministic**. Traditionelle assertEqual()-Tests greifen nicht.

---

## Decision

### Testing Pyramid for CLARISSA

```
                              ┌───────────────┐
                              │     E2E       │  Wenige, langsam, teuer
                              │  (Playwright) │  "User baut Modell via Chat"
                              └───────┬───────┘
                                      │
                         ┌────────────┴────────────┐
                         │      Integration        │  Moderate Anzahl
                         │   (Service-to-Service)  │  "API → LLM → Deck → Validator"
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              │                    Unit                        │  Many, fast, cheap
              │        (Functions, Classes, Validators)        │  "Deck Parser", "Keyword Validator"
              └───────────────────────────────────────────────┘

    + ─────────────────────────────────────────────────────────────────────────────
    
                    ┌─────────────────────────────────────────┐
                    │         CLARISSA-Specific Tests          │
                    │                                          │
                    │  ┌─────────────┐  ┌─────────────────┐   │
                    │  │ LLM Output  │  │   Simulation    │   │
                    │  │  Evaluation │  │   Validation    │   │
                    │  └─────────────┘  └─────────────────┘   │
                    │                                          │
                    │  ┌─────────────┐  ┌─────────────────┐   │
                    │  │Conversation │  │    Benchmark    │   │
                    │  │   Testing   │  │   Regression    │   │
                    │  └─────────────┘  └─────────────────┘   │
                    └─────────────────────────────────────────┘
```

---

## Test Categories

### 1. Unit Tests

Classic unit tests for deterministic components.

```python
# tests/unit/test_deck_parser.py

import pytest
from clarissa.simulation.deck_parser import EclipseDeckParser

class TestEclipseDeckParser:
    
    def test_parse_runspec_section(self):
        deck = """
        RUNSPEC
        TITLE
        Simple Test Model /
        DIMENS
        10 10 5 /
        """
        parser = EclipseDeckParser()
        result = parser.parse(deck)
        
        assert result.title == "Simple Test Model"
        assert result.dimensions == (10, 10, 5)
    
    def test_invalid_keyword_raises_error(self):
        deck = """
        RUNSPEC
        INVALID_KEYWORD
        """
        parser = EclipseDeckParser()
        
        with pytest.raises(UnknownKeywordError):
            parser.parse(deck)
    
    @pytest.mark.parametrize("keyword,expected", [
        ("WELSPECS", KeywordType.SCHEDULE),
        ("PORO", KeywordType.GRID),
        ("PVTO", KeywordType.PROPS),
    ])
    def test_keyword_classification(self, keyword, expected):
        assert classify_keyword(keyword) == expected
```

```python
# tests/unit/test_physics_validator.py

class TestPhysicsValidator:
    
    def test_pressure_gradient_plausible(self):
        """Normal hydrostatic gradient is ~0.433 psi/ft for water."""
        validator = PhysicsValidator()
        
        # Plausible
        assert validator.check_pressure_gradient(
            depth_ft=8000, pressure_psi=3500
        ).is_valid  # 0.4375 psi/ft - OK
        
        # Implausible
        result = validator.check_pressure_gradient(
            depth_ft=8000, pressure_psi=8000
        )
        assert not result.is_valid  # 1.0 psi/ft - too high
        assert "overpressure" in result.warning.lower()
    
    def test_porosity_range(self):
        validator = PhysicsValidator()
        
        assert validator.check_porosity(0.20).is_valid
        assert not validator.check_porosity(0.95).is_valid  # Impossible
        assert not validator.check_porosity(-0.1).is_valid  # Negative
```

### 2. Integration Tests

Cross-service tests, but without LLM (mocked).

```python
# tests/integration/test_deck_generation_pipeline.py

import pytest
from unittest.mock import AsyncMock, patch

class TestDeckGenerationPipeline:
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM to return deterministic output."""
        llm = AsyncMock()
        llm.chat.return_value = Response(
            content="""
            RUNSPEC
            TITLE
            Waterflood Model /
            DIMENS
            20 20 5 /
            
            GRID
            DX
            2000*100 /
            """,
            model="mock",
            usage={}
        )
        return llm
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocked_llm(self, mock_llm):
        """Test: NL Input → (mocked) LLM → Deck → Validator → Result."""
        
        with patch('clarissa.llm.get_llm', return_value=mock_llm):
            pipeline = DeckGenerationPipeline()
            
            result = await pipeline.generate(
                user_input="Create a simple waterflood model, 20x20x5 grid",
                context={}
            )
            
            assert result.deck is not None
            assert result.validation.is_valid
            assert "RUNSPEC" in result.deck
            assert "DIMENS" in result.deck
    
    @pytest.mark.asyncio
    async def test_validator_catches_invalid_deck(self, mock_llm):
        """Test that validator catches LLM mistakes."""
        
        # Make LLM return invalid deck
        mock_llm.chat.return_value = Response(
            content="""
            RUNSPEC
            DIMENS
            -5 10 10 /  -- Negative dimension!
            """,
            model="mock",
            usage={}
        )
        
        with patch('clarissa.llm.get_llm', return_value=mock_llm):
            pipeline = DeckGenerationPipeline()
            result = await pipeline.generate("...", {})
            
            assert not result.validation.is_valid
            assert "negative" in result.validation.errors[0].lower()
```

### 3. LLM Output Evaluation

**Das ist der Kern der Herausforderung.** LLM-Outputs sind nicht deterministisch.

#### Approach: Property-Based Testing + Semantic Validation

```python
# tests/llm/test_deck_generation_properties.py

import pytest
from clarissa.testing import LLMTestHarness

class TestDeckGenerationProperties:
    """
    Property-based tests for LLM-generated decks.
    We don't check exact output, but PROPERTIES that must hold.
    """
    
    @pytest.fixture
    def harness(self):
        return LLMTestHarness(
            model="claude-sonnet",  # or "ollama:llama3.1:70b" for local
            temperature=0.0,         # Reduce randomness for testing
            seed=42                  # If supported
        )
    
    @pytest.mark.llm
    @pytest.mark.asyncio
    async def test_generated_deck_is_syntactically_valid(self, harness):
        """Property: Any generated deck must parse without errors."""
        
        prompts = [
            "Create a simple black oil model",
            "Build a 5-spot waterflood pattern",
            "Generate a single-well depletion model",
        ]
        
        for prompt in prompts:
            deck = await harness.generate_deck(prompt)
            
            # Property 1: Must be parseable
            parse_result = EclipseDeckParser().parse(deck)
            assert parse_result.success, f"Failed to parse deck for: {prompt}"
            
            # Property 2: Must have required sections
            assert "RUNSPEC" in deck
            assert "GRID" in deck
            assert "SCHEDULE" in deck
    
    @pytest.mark.llm
    @pytest.mark.asyncio
    async def test_dimensions_match_request(self, harness):
        """Property: Grid dimensions should match user request."""
        
        deck = await harness.generate_deck(
            "Create a model with 50x50x10 grid"
        )
        
        parsed = EclipseDeckParser().parse(deck)
        nx, ny, nz = parsed.dimensions
        
        # Allow some flexibility (LLM might round)
        assert 45 <= nx <= 55
        assert 45 <= ny <= 55
        assert 8 <= nz <= 12
    
    @pytest.mark.llm
    @pytest.mark.asyncio
    async def test_well_count_matches_pattern(self, harness):
        """Property: 5-spot pattern should have ~5 wells."""
        
        deck = await harness.generate_deck(
            "Create a 5-spot waterflood pattern with 1 injector and 4 producers"
        )
        
        parsed = EclipseDeckParser().parse(deck)
        
        injectors = [w for w in parsed.wells if w.type == "INJECTOR"]
        producers = [w for w in parsed.wells if w.type == "PRODUCER"]
        
        assert len(injectors) >= 1
        assert len(producers) >= 4
    
    @pytest.mark.llm
    @pytest.mark.asyncio
    async def test_physics_plausibility(self, harness):
        """Property: Generated values must be physically plausible."""
        
        deck = await harness.generate_deck(
            "Create a typical sandstone reservoir at 8000 ft depth"
        )
        
        parsed = EclipseDeckParser().parse(deck)
        validator = PhysicsValidator()
        
        # Check porosity
        if parsed.porosity:
            result = validator.check_porosity(parsed.porosity.mean())
            assert result.is_valid, f"Implausible porosity: {parsed.porosity.mean()}"
        
        # Check permeability
        if parsed.permeability:
            result = validator.check_permeability(parsed.permeability.mean())
            assert result.is_valid
```

#### LLM Evaluation Metrics

```python
# clarissa/testing/llm_metrics.py

@dataclass
class DeckEvaluationResult:
    """Metrics for evaluating generated decks."""
    
    # Syntactic
    parses_successfully: bool
    syntax_errors: list[str]
    
    # Semantic
    has_required_sections: bool
    missing_sections: list[str]
    
    # Physical Plausibility
    physics_valid: bool
    physics_warnings: list[str]
    
    # Completeness
    completeness_score: float  # 0-1, how much of the request was fulfilled
    missing_elements: list[str]
    
    # Consistency
    internal_consistency: bool  # e.g., DIMENS matches actual data size
    consistency_errors: list[str]


class DeckEvaluator:
    """Evaluate LLM-generated decks against multiple criteria."""
    
    def evaluate(self, deck: str, original_request: str) -> DeckEvaluationResult:
        return DeckEvaluationResult(
            parses_successfully=self._check_syntax(deck),
            syntax_errors=self._get_syntax_errors(deck),
            has_required_sections=self._check_sections(deck),
            missing_sections=self._get_missing_sections(deck),
            physics_valid=self._check_physics(deck),
            physics_warnings=self._get_physics_warnings(deck),
            completeness_score=self._score_completeness(deck, original_request),
            missing_elements=self._get_missing_elements(deck, original_request),
            internal_consistency=self._check_consistency(deck),
            consistency_errors=self._get_consistency_errors(deck),
        )
```

### 4. Conversation Testing

Testing des Dialog-Flows.

```python
# tests/conversation/test_dialog_flows.py

class TestDialogFlows:
    """Test multi-turn conversation scenarios."""
    
    @pytest.mark.asyncio
    async def test_clarification_request_flow(self):
        """Test: Incomplete input → Clarification → Complete input."""
        
        session = ConversationSession()
        
        # Turn 1: Incomplete request
        response1 = await session.send("Build a reservoir model")
        
        assert response1.needs_clarification
        assert "dimensions" in response1.clarification_request.lower() or \
               "grid size" in response1.clarification_request.lower()
        
        # Turn 2: User provides details
        response2 = await session.send("20x20x5, sandstone, 8000 ft depth")
        
        assert response2.has_deck or response2.ready_to_generate
    
    @pytest.mark.asyncio
    async def test_modification_flow(self):
        """Test: Generate → Modify → Regenerate."""
        
        session = ConversationSession()
        
        # Generate initial deck
        await session.send("Create a waterflood model, 5-spot pattern")
        response1 = await session.send("Generate the deck")
        
        assert response1.has_deck
        initial_deck = response1.deck
        
        # Request modification
        response2 = await session.send("Add another injector in the corner")
        
        assert response2.has_deck
        modified_deck = response2.deck
        
        # Verify modification
        initial_wells = count_wells(initial_deck)
        modified_wells = count_wells(modified_deck)
        
        assert modified_wells["injectors"] == initial_wells["injectors"] + 1
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self):
        """Test: Invalid input → Error message → Recovery."""
        
        session = ConversationSession()
        
        # Invalid physics
        response1 = await session.send(
            "Create model with 200% porosity"  # Impossible
        )
        
        assert response1.has_warning or response1.has_error
        assert "porosity" in response1.message.lower()
        
        # User corrects
        response2 = await session.send("Sorry, I meant 20% porosity")
        
        assert not response2.has_error
```

### 5. Simulation Validation

**The ultimate test:** Does the simulation run and are the results plausible?

```python
# tests/simulation/test_simulation_validation.py

class TestSimulationValidation:
    """
    Tests that run actual simulations and validate results.
    These are SLOW and run nightly, not on every commit.
    """
    
    @pytest.fixture
    def simulator(self):
        return OPMFlowAdapter(opm_path="/usr/bin/flow")
    
    @pytest.mark.simulation
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_generated_deck_runs_successfully(self, simulator):
        """Generated deck should run without simulator errors."""
        
        # Generate a deck
        llm = OllamaAdapter(model="llama3.1:70b")
        deck = await llm.generate_deck("Simple 10x10x3 depletion model")
        
        # Run simulation
        job = await simulator.submit_job(deck, SimConfig(max_time_steps=100))
        
        # Wait for completion (with timeout)
        status = await asyncio.wait_for(
            simulator.wait_for_completion(job),
            timeout=300  # 5 minutes max
        )
        
        assert status == JobStatus.COMPLETED, f"Simulation failed: {status}"
    
    @pytest.mark.simulation
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_material_balance_satisfied(self, simulator):
        """Results should satisfy material balance."""
        
        deck = load_test_deck("spe1")
        job = await simulator.submit_job(deck, SimConfig())
        await simulator.wait_for_completion(job)
        
        results = await simulator.get_results(job)
        
        # Check material balance
        initial_oil = results.get_field_value("FOIP", time=0)
        final_oil = results.get_field_value("FOIP", time=-1)
        produced_oil = results.get_field_value("FOPT", time=-1)
        
        balance_error = abs((initial_oil - final_oil) - produced_oil) / initial_oil
        
        assert balance_error < 0.01, f"Material balance error: {balance_error:.2%}"
    
    @pytest.mark.simulation
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_waterflood_expected_behavior(self, simulator):
        """Waterflood should show expected production behavior."""
        
        deck = await generate_waterflood_deck()
        job = await simulator.submit_job(deck, SimConfig())
        await simulator.wait_for_completion(job)
        
        results = await simulator.get_results(job)
        
        # Water cut should increase over time (expected in waterflood)
        water_cuts = results.get_field_timeseries("FWCT")
        
        # Check trend (not exact values)
        early_wcut = water_cuts[:10].mean()
        late_wcut = water_cuts[-10:].mean()
        
        assert late_wcut > early_wcut, "Water cut should increase in waterflood"
```

### 6. Benchmark Regression Tests

Comparison against known solutions (SPE Comparative Solution Projects).

```python
# tests/benchmarks/test_spe_comparative.py

class TestSPEComparativeSolutions:
    """
    Test against SPE Comparative Solution Project results.
    These are industry-standard benchmarks.
    """
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    @pytest.mark.parametrize("spe_case", ["spe1", "spe3", "spe9"])
    @pytest.mark.asyncio
    async def test_spe_case_matches_reference(self, spe_case, simulator):
        """
        Run SPE cases and compare against published results.
        """
        deck = load_spe_deck(spe_case)
        reference = load_spe_reference_results(spe_case)
        
        job = await simulator.submit_job(deck, SimConfig())
        await simulator.wait_for_completion(job)
        results = await simulator.get_results(job)
        
        # Compare key metrics
        for metric in ["FOPT", "FWPT", "FGPT"]:
            our_value = results.get_final_value(metric)
            ref_value = reference.get_final_value(metric)
            
            relative_error = abs(our_value - ref_value) / ref_value
            
            assert relative_error < 0.05, \
                f"{spe_case} {metric}: {relative_error:.1%} error vs reference"
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_clarissa_generated_vs_manual_deck(self, simulator):
        """
        Compare CLARISSA-generated deck against manually created one.
        """
        # Manual reference deck
        manual_deck = load_test_deck("reference_waterflood")
        
        # CLARISSA-generated from same description
        clarissa_deck = await generate_deck_from_description(
            load_deck_description("reference_waterflood")
        )
        
        # Run both
        manual_results = await run_simulation(simulator, manual_deck)
        clarissa_results = await run_simulation(simulator, clarissa_deck)
        
        # Compare production profiles
        for metric in ["FOPT", "FWPT"]:
            correlation = compute_correlation(
                manual_results.get_timeseries(metric),
                clarissa_results.get_timeseries(metric)
            )
            
            assert correlation > 0.95, \
                f"CLARISSA deck {metric} doesn't match manual: r={correlation:.2f}"
```

---

## Test Infrastructure

### CI/CD Test Stages

```yaml
# .gitlab-ci.yml

stages:
  - lint
  - unit
  - integration
  - llm-evaluation
  - simulation
  - benchmark

# Fast, every commit
unit-tests:
  stage: unit
  script:
    - pytest tests/unit -v --cov=clarissa
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

# Medium, every commit
integration-tests:
  stage: integration
  script:
    - pytest tests/integration -v
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

# Expensive, only on main or manual trigger
llm-evaluation:
  stage: llm-evaluation
  tags: [gpu]  # Needs GPU for local LLM
  script:
    - pytest tests/llm -v -m "llm"
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - when: manual

# Very slow, nightly only
simulation-tests:
  stage: simulation
  tags: [simulation-runner]
  script:
    - pytest tests/simulation -v -m "simulation"
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"  # Nightly

# Weekly benchmarks
benchmark-tests:
  stage: benchmark
  tags: [simulation-runner]
  script:
    - pytest tests/benchmarks -v -m "benchmark"
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule" && $WEEKLY_BENCHMARK == "true"
```

### Test Markers

```python
# pytest.ini

[pytest]
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (services, mocked LLM)
    llm: Tests that call real LLM (slow, potentially costly)
    simulation: Tests that run actual simulations (very slow)
    benchmark: Benchmark regression tests (weekly)
    slow: Tests that take > 10 seconds
```

### Test Data Management

```
tests/
├── fixtures/
│   ├── decks/
│   │   ├── spe1.DATA
│   │   ├── spe3.DATA
│   │   ├── spe9.DATA
│   │   └── reference_waterflood.DATA
│   │
│   ├── reference_results/
│   │   ├── spe1_reference.json
│   │   └── spe9_reference.json
│   │
│   └── conversation_scenarios/
│       ├── simple_model.yaml
│       ├── waterflood_modification.yaml
│       └── error_recovery.yaml
│
├── unit/
├── integration/
├── llm/
├── simulation/
├── benchmarks/
└── conftest.py  # Shared fixtures
```

---

## Test Coverage Targets

| Category | Target | Rationale |
|----------|--------|-----------|
| **Unit Tests** | >90% | Core logic must be covered |
| **Integration** | >70% | Key paths covered |
| **LLM Evaluation** | N/A | Property-based, not line coverage |
| **Simulation** | Key scenarios | SPE cases + common patterns |

---

## Summary

| Test Type | What | When | Duration |
|-----------|------|------|----------|
| **Unit** | Parsers, Validators, Utils | Every commit | <1 min |
| **Integration** | Service pipelines (mocked LLM) | Every commit | <5 min |
| **LLM Evaluation** | Property-based deck tests | Main branch | ~10 min |
| **Conversation** | Dialog flows | Main branch | ~5 min |
| **Simulation** | Actually run simulations | Nightly | ~30 min |
| **Benchmark** | SPE cases, regression | Weekly | ~2 hours |

---

## References

- [ADR-024: CLARISSA Core System Architecture](./ADR-024-clarissa-core-system-architecture.md)
- [ADR-025: LLM Integration Strategy](./ADR-025-llm-integration-strategy.md)
- [SPE Comparative Solution Projects](https://www.spe.org/web/csp/)
- [pytest Documentation](https://docs.pytest.org/)
- [Property-Based Testing with Hypothesis](https://hypothesis.readthedocs.io/)