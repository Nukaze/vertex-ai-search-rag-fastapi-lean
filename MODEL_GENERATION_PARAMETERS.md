# Model Generation Parameters Guide

**Service:** vertex-ai-search-rag-fastapi-lean
**Updated:** 2025-12-14
**Purpose:** Control model generation behavior for both Direct and Streaming modes

---

## 📌 Overview

The Vertex AI Search service supports two modes with different model control options:

| Mode | AI Engine | Configurable Parameters |
|------|-----------|------------------------|
| **Direct** | Vertex AI built-in summarization | Model version, page size, language |
| **Streaming** | Gemini (via API) | Temperature, top-K, top-P, max tokens, model |

---

## 🎛️ Direct Mode - Vertex AI Summary Model

### Available Parameters

```json
{
  "mode": "direct",
  "summaryModelVersion": "stable" | "preview",
  "summaryResultCount": 5,
  "pageSize": 10,
  "languageCode": "th",
  "useSemanticChunks": true
}
```

### Model Version Options

| Version | Description | Use Case |
|---------|-------------|----------|
| `"stable"` | Production model (default) | Production deployments, consistent results |
| `"preview"` | Latest model with new features | Testing, early access to improvements |

### Example: Using Preview Model

```json
POST /api/vertex-search

{
  "query": "คอร์ส data analytics",
  "mode": "direct",
  "summaryModelVersion": "preview",
  "pageSize": 10,
  "summaryResultCount": 5
}
```

---

## 🔥 Streaming Mode - Gemini Generation Config

### Full Parameter Control

```json
{
  "mode": "streaming",
  "model": "gemini-2.0-flash",
  "temperature": 0.7,
  "topK": 40,
  "topP": 0.95,
  "maxOutputTokens": 2048,
  "pageSize": 10
}
```

---

### 1. Temperature

**Controls randomness and creativity**

| Value | Behavior | Use Case |
|-------|----------|----------|
| `0.0` | Deterministic, focused | Factual Q&A, documentation |
| `0.3-0.5` | Balanced | General chatbot, recommendations |
| `0.7-1.0` | Creative | Brainstorming, varied responses |
| `1.5-2.0` | Very creative | Story generation, exploration |

**Examples:**

```json
// Factual, consistent answers
{
  "temperature": 0.2,
  "query": "What is Python?"
}

// Creative course recommendations
{
  "temperature": 0.8,
  "query": "แนะนำคอร์สที่น่าสนใจ"
}
```

---

### 2. Top-K

**Limits vocabulary to top K most probable tokens**

| Value | Behavior | Use Case |
|-------|----------|----------|
| `1-10` | Very focused, limited vocabulary | Technical documentation |
| `20-40` | Balanced diversity | General chatbot (default: 40) |

**Examples:**

```json
// Precise technical answers
{
  "topK": 10,
  "temperature": 0.3
}

// Natural conversational style
{
  "topK": 40,
  "temperature": 0.7
}
```

---

### 3. Top-P (Nucleus Sampling)

**Cumulative probability threshold for token selection**

| Value | Behavior | Use Case |
|-------|----------|----------|
| `0.1-0.5` | Very focused | Precise answers |
| `0.8-0.95` | Balanced | General use (default: 0.95) |
| `0.95-1.0` | Maximum diversity | Creative generation |

**Examples:**

```json
// Focused, on-topic responses
{
  "topP": 0.5,
  "temperature": 0.4
}

// Natural, diverse language
{
  "topP": 0.95,
  "temperature": 0.7
}
```

---

### 4. Max Output Tokens

**Controls response length**

| Value | Words (approx) | Use Case |
|-------|----------------|----------|
| `256` | ~190 | Short summaries |
| `512` | ~380 | Brief explanations |
| `1024` | ~760 | Standard responses |
| `2048` | ~1500 | Detailed explanations |
| `4096` | ~3000 | Long-form content |
| `8192` | ~6000 | Very detailed documentation |

**Examples:**

```json
// Brief answer
{
  "maxOutputTokens": 256,
  "query": "What is AI?"
}

// Comprehensive explanation
{
  "maxOutputTokens": 2048,
  "query": "Explain machine learning in detail"
}
```

---

## 🎯 Recommended Configurations

### Use Case 1: Factual Q&A (Course Information)

```json
{
  "mode": "streaming",
  "temperature": 0.2,
  "topK": 20,
  "topP": 0.8,
  "maxOutputTokens": 512,
  "query": "คอร์ส Python มีอะไรบ้าง"
}
```

**Why:** Low temperature ensures factual accuracy, moderate token limits keep answers concise.

---

### Use Case 2: Conversational Assistant

```json
{
  "mode": "streaming",
  "temperature": 0.7,
  "topK": 40,
  "topP": 0.95,
  "maxOutputTokens": 1024,
  "query": "แนะนำเส้นทางเรียนรู้ AI"
}
```

**Why:** Balanced temperature for natural conversation, sufficient tokens for detailed guidance.

---

### Use Case 3: Creative Recommendations

```json
{
  "mode": "streaming",
  "temperature": 0.9,
  "topK": 40,
  "topP": 0.95,
  "maxOutputTokens": 1536,
  "query": "สร้างแผนการเรียนแบบ personalized"
}
```

**Why:** Higher temperature allows creative, personalized suggestions.

---

### Use Case 4: Technical Documentation

```json
{
  "mode": "streaming",
  "temperature": 0.1,
  "topK": 10,
  "topP": 0.7,
  "maxOutputTokens": 2048,
  "query": "อธิบาย API endpoint ทั้งหมด"
}
```

**Why:** Very low temperature for accuracy, sufficient tokens for complete documentation.

---

### Use Case 5: Production Summary (Consistent)

```json
{
  "mode": "direct",
  "summaryModelVersion": "stable",
  "pageSize": 10,
  "summaryResultCount": 5,
  "useSemanticChunks": true,
  "languageCode": "th"
}
```

**Why:** Stable model for production, semantic chunks for quality, Thai language.

---

## ⚙️ Parameter Interactions

### Temperature + Top-K + Top-P

These parameters work together to control output diversity:

```json
// Most conservative (factual)
{
  "temperature": 0.1,
  "topK": 10,
  "topP": 0.5
}

// Balanced (recommended default)
{
  "temperature": 0.7,
  "topK": 40,
  "topP": 0.95
}

// Most creative
{
  "temperature": 1.5,
  "topK": 40,
  "topP": 1.0
}
```

### Common Combinations

| Personality | temperature | topK | topP | maxOutputTokens |
|-------------|-------------|------|------|-----------------|
| **Precise Expert** | 0.1-0.3 | 10-20 | 0.5-0.7 | 512-1024 |
| **Balanced Assistant** | 0.6-0.8 | 30-40 | 0.9-0.95 | 1024-2048 |
| **Creative Guide** | 0.9-1.2 | 40 | 0.95-1.0 | 1536-2048 |

---

## 🧪 Testing & Calibration

### Step 1: Start with Defaults

```json
{
  "mode": "streaming",
  "model": "gemini-2.0-flash",
  // Use defaults (temperature=None, topK=None, etc.)
}
```

### Step 2: Adjust Temperature

Test different temperatures with the same query:

```bash
# Test low temperature
curl -X POST /api/vertex-search -d '{
  "query": "คอร์ส AI",
  "mode": "streaming",
  "temperature": 0.2
}'

# Test high temperature
curl -X POST /api/vertex-search -d '{
  "query": "คอร์ส AI",
  "mode": "streaming",
  "temperature": 1.0
}'
```

### Step 3: Fine-tune Other Parameters

Once temperature is set, adjust:
1. `maxOutputTokens` - Control length
2. `topP` - Fine-tune diversity
3. `topK` - Optional, usually keep at 40

---

## 📊 Comparison: Direct vs Streaming

| Feature | Direct Mode | Streaming Mode |
|---------|-------------|----------------|
| **Speed** | Fast (single response) | Progressive (chunks) |
| **Control** | Limited (model version only) | Full (temp, top-K, etc.) |
| **Cost** | Lower | Higher (Gemini API) |
| **Consistency** | High (stable model) | Varies with temp |
| **UX** | Wait for complete response | Real-time typing effect |
| **Use Case** | Production, consistent results | Interactive chat, customization |

---

## 🚀 Quick Reference

### Minimal Request (Direct)
```json
{"query": "คอร์ส AI", "mode": "direct"}
```

### Minimal Request (Streaming)
```json
{"query": "คอร์ส AI", "mode": "streaming"}
```

### Full Control (Streaming)
```json
{
  "query": "แนะนำคอร์ส",
  "mode": "streaming",
  "model": "gemini-2.0-flash",
  "temperature": 0.7,
  "topK": 40,
  "topP": 0.95,
  "maxOutputTokens": 1536,
  "pageSize": 10
}
```

### Production (Direct)
```json
{
  "query": "คอร์ส data analytics",
  "mode": "direct",
  "summaryModelVersion": "stable",
  "pageSize": 10,
  "useSemanticChunks": true,
  "languageCode": "th"
}
```

---

## 🔧 Troubleshooting

### Issue: Responses too random/inconsistent

**Solution:** Lower temperature and topP
```json
{
  "temperature": 0.2,
  "topP": 0.7
}
```

### Issue: Responses too generic/robotic

**Solution:** Increase temperature
```json
{
  "temperature": 0.8
}
```

### Issue: Responses too long

**Solution:** Reduce maxOutputTokens
```json
{
  "maxOutputTokens": 512
}
```

### Issue: Responses too short

**Solution:** Increase maxOutputTokens
```json
{
  "maxOutputTokens": 2048
}
```

---

## 📝 Best Practices

1. **Start simple** - Use defaults first, then customize
2. **Test variations** - Same query with different parameters
3. **Monitor quality** - Track user satisfaction per config
4. **Document configs** - Save working configurations
5. **Use direct mode** for production consistency
6. **Use streaming mode** for interactive experiences

---

## 🎓 Examples by Industry

### E-Learning Platform (9Expert)

```json
{
  "mode": "streaming",
  "temperature": 0.6,
  "topK": 30,
  "maxOutputTokens": 1024,
  "customSystemPrompt": "คุณเป็นที่ปรึกษาการเรียนรู้ที่เข้าใจความต้องการของผู้เรียน..."
}
```

### Technical Documentation

```json
{
  "mode": "direct",
  "summaryModelVersion": "stable",
  "useSemanticChunks": true,
  "summaryResultCount": 8
}
```

### Customer Support

```json
{
  "mode": "streaming",
  "temperature": 0.5,
  "topP": 0.9,
  "maxOutputTokens": 800
}
```

---

**End of Documentation**

For complete API reference, see: `VERTEX_AI_SEARCH_COMPLETE_CONFIG.md`
For usage examples, see: `VERTEX_AI_SEARCH_USAGE_EXAMPLES.md`
