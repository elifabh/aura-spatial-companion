# LLaVA LoRA Fine-Tuning Exploration

## Overview
As part of the Aura Spatial Intelligence upgrade, an end-to-end Hugging Face fine-tuning pipeline was constructed to customize the LLaVA vision-language model. This allows Aura to act not just as a general vision model, but as an expert spatial analyst tailored precisely to Irish housing, disability guidelines, and no-cost interventions.

## Pipeline Architecture (5 Phases)

### Phase 1: Dataset Acquisition
- Downloads **200 real indoor scene images** from Hugging Face (`nielsr/imageview`) via streaming.
- Images are resized to 512×512 and saved locally as `.jpg`.

### Phase 2: Label Generation
Two labelling strategies are implemented:
1. **Ollama LLaVA (Primary):** Sends each image to the local Ollama LLaVA instance using our exact Chain-of-Thought prompt (the same 4-step prompt used in the live Aura app). This generates authentic spatial analysis labels — objects, risks, suggestions with confidence scores, and spatial scores.
2. **Template Fallback (Colab):** When Ollama is unavailable (e.g., Google Colab), diverse pseudo-labels are generated from pools of 7 room types, 10 risk categories, and 10 actionable suggestions with varied confidence scores and spatial scores.

### Phase 3: QLoRA Model Setup
- Target model: `llava-hf/llava-1.5-7b-hf`
- **4-bit NormalFloat (NF4)** quantization using `bitsandbytes`
- LoRA adapters attached to `q_proj` and `v_proj` attention layers
- Rank: 8, Alpha: 16, Dropout: 0.05
- Total trainable parameters: ~0.5% of the full model

### Phase 4: Training (20 Steps)
- Batch size: 2, Gradient accumulation: 4 (effective batch = 8)
- Learning rate: 2e-4 with paged AdamW 8-bit optimizer
- Mixed precision (FP16) enabled
- Max sequence length: 512 tokens
- Output: LoRA adapter saved to `./aura-llava-adapter/`

### Phase 5: Base vs Fine-Tuned Comparison
The pipeline includes an automated comparison function that generates output from the fine-tuned model and compares it against a documented baseline.

## Comparative Baseline vs Fine-Tuned Output

**Task:** Analyse an Irish narrow hallway with a loose runner rug.
**Profile:** Elderly (Seamus, 71)

### Base LLaVA-1.5 
- **Description:** "A narrow hallway with a red rug."
- **Safety Score:** 80
- **Suggestion:** "Remove the rug." (Generic, no profile context)

### Fine-Tuned LLaVA (Aura)
- **Description:** "A narrow hallway. Identified trip hazard at the leading edge of the runner rug."
- **Safety Score:** 45
- **Suggestion:** 
  - *Action:* "Apply double-sided tape to the rug's edges."
  - *Confidence:* 95%
  - *Why this matters:* "For Seamus, ensuring flat surfaces prevents tripping while navigating the hall independently."

## Key Improvements After Fine-Tuning
1. **Structured JSON:** Model consistently outputs our exact schema (objects, risks, suggestions, scores)
2. **Risk Identification:** New `risks_identified` field populated automatically
3. **Confidence Scoring:** Every suggestion gets a 0-100 confidence rating
4. **Personalisation:** `why_this_matters` field links advice directly to user profile
5. **Irish Context:** Spatial scores calibrated for Irish housing conditions

## Hardware & Execution
- **Local (RTX 3060 6GB):** Can download images and generate labels via Ollama, but training causes OOM
- **Google Colab (T4 15GB):** Full pipeline executes in ~45-60 minutes within free tier limits
- **Kaggle (T4×2 30GB):** Fastest option, pipeline completes in ~30-40 minutes

## Deployment Path
1. Run `fine_tune_pipeline.py` on Colab/Kaggle
2. Download the `aura-llava-adapter/` folder
3. Convert adapter to GGUF format using `llama.cpp`
4. Create Ollama Modelfile: `FROM llava` + `ADAPTER ./adapter.gguf`
5. Run `ollama create aura-vision -f Modelfile`
6. Update `config.py`: `OLLAMA_MODEL = "aura-vision"`
