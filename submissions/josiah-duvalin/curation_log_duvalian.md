### PXD046327
- deepest_step_reached: 5
- time_spent_min: ~70
- fields_decided_at: {disease_context: 1, organism_context: 5, sample_type: 2, subtype: 1, er_status: 1, her2_status: 1}
- ambiguities: "Steps 1-4 suggested just human organisms, but Step 5 mentioned xenographs multiple times. Not sure if the lack of ER or HER2 mentioned anywhere makes it non-evaluable, and if the step for that decision would be Step 5."
- changed_my_mind: "Misunderstood domain of sample_type and initially labeled it as 'Homo sapien.' Relabeled as 'cell line.'"
- ai_use: "Asked Claude to clarify what 'ER' in 'mitochondria-ER' meant; discovered it wasn't estrogen receptors but rather endoplasmic reticulum. No labels or rationales AI-generated."

### PXD037256
- deepest_step_reached: 2
- time_spent_min: 86
- fields_decided_at: {disease_context: 1, organism_context: 1, sample_type: 1, subtype: 2, er_status: 1, her2_status: 1}
- ambiguities: "No real ambiguities; I just need more practice and a clear definition of the domains of each field's `expected_value`"
- changed_my_mind: "Conflated organism_context with sample_type and labled it 'mixed:cell line and organoid'; relabeled them 'asserted:H460 and MCF7.'"
- ai_use: "Asked Claude what H460 and MCF7 are. No labels or rationales AI-generated."
