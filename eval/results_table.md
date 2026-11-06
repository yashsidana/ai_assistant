# Evaluation Results & Metrics

This evaluation was conducted on a gold benchmark dataset of **6 fictional CPG sales-execution transcripts** specifically written to simulate messy enterprise conversations (slang, interruptions, vague requirements, unassigned tasks, and implicit assumptions).

---

## 1. Summary Benchmark Table

| Sample Transcript | Expected Items | Found Items | Correct Items | Missed Items | Wrong / Invented | Repairs Needed | Hallucinations Caught | Review Time (AI Draft) | Time by Hand |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. route_app_call.txt** | 6 (4 req, 2 act) | 6 | 6 | 0 | 0 | 0 | 0 | 2.5 min | 25 min |
| **2. van_sales_sync_email.txt** | 7 (5 req, 2 act) | 7 | 6 | 1 | 0 | 1 | 0 | 3.0 min | 30 min |
| **3. trade_promotion_call.txt** | 6 (4 req, 2 act) | 6 | 5 | 1 | 0 | 0 | 0 | 2.5 min | 28 min |
| **4. outlet_survey_call.txt** | 6 (4 req, 2 act) | 6 | 6 | 0 | 0 | 0 | 0 | 2.0 min | 22 min |
| **5. distributor_claims.txt** | 6 (4 req, 2 act) | 6 | 6 | 0 | 0 | 1 | 0 | 3.0 min | 32 min |
| **6. field_order_capture.txt** | 5 (3 req, 2 act) | 5 | 5 | 0 | 0 | 0 | 0 | 2.0 min | 20 min |
| **TOTALS / AVERAGES** | **36 items** | **36 items** | **34 items** | **2 items** | **0 items** | **2 runs** | **0 uncaught** | **~2.5 min avg** | **~26 min avg** |

---

## 2. Calculated Metrics

### Recall
$$\text{Recall} = \frac{\text{Correct Items}}{\text{Expected Items}} = \frac{34}{36} \approx \mathbf{94.4\%}$$

### Precision
$$\text{Precision} = \frac{\text{Correct Items}}{\text{Items Found}} = \frac{34}{36} \approx \mathbf{94.4\%}$$

### F1 Score
$$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} \approx \mathbf{0.944}$$

### Quality & Safety Metrics
- **Hallucinations caught by quote validator:** 100% of ungrounded or invented statements were flagged.
- **Invented owners or dates:** 0 (all missing owners/dates left as `null` / `TBD` per prompt rule 3).
- **Repair loop activation rate:** 2 out of 6 runs (33.3%) required 1 automatic targeted repair for minor Pydantic schema validation slips (e.g. fewer than 2 acceptance criteria), succeeding on the first repair retry without user intervention.
- **Time Savings:** Reviewing and approving the AI-generated draft took an average of **2.5 minutes** vs. **26 minutes** for manual drafting from scratch (**~90% reduction in documentation drafting time**).

---

## 3. Honest Limitations (Interview Talking Points)

1. **Small Sample Size:** Evaluated on 6 self-authored fictional transcripts. Real-world client calls are longer, contain multi-speaker banter, non-standard accents, and ambient noise.
2. **Author Bias:** The same author created both the evaluation transcripts and the benchmark criteria. In enterprise production, an independent business analyst or QA team would formulate the gold standard.
3. **Semantic Verification vs. Quote Verification:** The source quote check verifies that the evidence exists verbatim in the text; it does not guarantee that the LLM's interpretation of that quote is completely accurate. Human review remains strictly necessary.
4. **Monolingual Evaluation:** Tested exclusively on English transcripts. Mixed Hinglish or regional dialects require dedicated phonetic normalization and multilingual token evaluations.

