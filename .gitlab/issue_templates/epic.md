<!-- 
  Epic Issue Template
  Use this for larger initiatives spanning multiple issues
  
  Naming convention:
    [EPIC] Your Epic Title          (neutral)
    🔧 EPIC: Your Epic Title        (infrastructure)
    🌍 EPIC: Your Epic Title        (i18n/global)
    🔗 EPIC: Your Epic Title        (integration/communication)
  
  Required Labels:
    type::epic          (mandatory)
    component::*        (mandatory, pick the primary component)
    priority::*         (mandatory)
    NO workflow:: label (Epics are tracked via child issues, not workflow states)
-->

## Overview

<!-- Describe the initiative in 2-3 sentences -->

## Business Case

<!-- Who benefits and why? Use team member context if relevant -->

## Scope

<!-- List deliverables as child issue references once created -->

- [ ] #XX — 🔍 RESEARCH: ...
- [ ] #YY — ⚙️ FEATURE: ...
- [ ] #ZZ — 🧪 TEST: ...
- [ ] #WW — 📖 DOCS: ...

## Technical Context

<!-- Optional: Architecture decisions, constraints, options table -->

## Dependencies

<!-- Document which issues or ADRs this epic depends on -->

## ADR References

<!-- Link relevant ADRs -->

- ADR-0XX (...)

## Success Criteria

- [ ] All child issues closed
- [ ] ADR created and merged (if applicable)  
- [ ] Documentation updated

---
Created: YYYY-MM-DD

/label ~"type::epic" ~"component::infrastructure" ~"priority::medium"
