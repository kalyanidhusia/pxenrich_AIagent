# Curation log — mkelley2

### PXD046327
- deepest_step_reached: 2
- time_spent_min: 60
- fields_decided_at: {disease_context: 1, organism_context: 1, sample_type: 2, subtype: 1, er_status: 1, her2_status: 1}
- ambiguities: "ER in mitochondria-ER contacts refers to endoplasmic reticulum. The receptor labels use the dataset's TNBC description. The rules card does not explicitly list that direction of inference."
- changed_my_mind: "I initially called the sample purified mitochondria-ER junctions. After the first benchmark run, I read the full PRIDE protocol and found that it describes both total cell lysates and mitochondria-ER contacts. I updated the label to mixed because the protocol describes both materials."
- ai_use: "I read the source pages, located and supplied specific quotes, wrote rationale sentences, and made the final label decisions. AI explained terms, looked up additional sources, suggested some labels and rationale wording, edited the JSON, ran the benchmark, and helped document disagreements."

### PXD037256
- deepest_step_reached: 5
- time_spent_min: 60
- fields_decided_at: {disease_context: 2, organism_context: 1, sample_type: 1, subtype: 5, er_status: 5, her2_status: 5}
- ambiguities: "The study includes two disease contexts and both 2D and 3D cultures. The paper's HER2 passage describes prior research and does not report receptor status for these samples. I did not find an explicit subtype or ER status in the sources I checked. I read the linked paper before the later file-list review."
- changed_my_mind: "I kept the labels after reviewing the disagreements. After verifying the ProteomeCentral evidence for organism context and sample type, I updated their citations to step 1."
- ai_use: "I read the source pages, located and supplied specific quotes, wrote rationale sentences, and made the final label decisions. AI explained terms, searched source text and files, suggested some labels and rationale wording, edited the JSON, ran the benchmark, and helped document disagreements."

The first benchmark run was on November 16, before any label commit. The November 13 instructions directed local validation before submission. The November 19 protocol requires a commit before the first run.
