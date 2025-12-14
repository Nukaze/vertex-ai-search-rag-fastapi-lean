# API Payload Examples - Complete Reference

**Service:** vertex-ai-search-rag-fastapi-lean
**Endpoint:** `POST /api/vertex-search`
**Updated:** 2025-12-14

---

## 📋 Table of Contents

1. [Basic Payloads](#1-basic-payloads)
2. [Query Enhancement Fields](#2-query-enhancement-fields)
3. [Filtering Fields](#3-filtering-fields)
4. [Boosting Fields](#4-boosting-fields)
5. [Faceting Fields](#5-faceting-fields)
6. [Summary Customization Fields](#6-summary-customization-fields)
7. [Model Generation Fields (Streaming)](#7-model-generation-fields-streaming)
8. [Complete Examples](#8-complete-examples)
9. [cURL Examples](#9-curl-examples)

---

## 1. Basic Payloads

### 1.1 Minimal Request (Direct Mode)

```json
POST /api/vertex-search
Content-Type: application/json

{
  "query": "คอร์ส AI"
}
```

**Result:** Uses all defaults (direct mode, pageSize=5, stable model, Thai language)

---

### 1.2 Minimal Request (Streaming Mode)

```json
{
  "query": "คอร์ส data analytics",
  "mode": "streaming"
}
```

**Result:** Streams response using Gemini with default generation config

---

### 1.3 Basic with Page Size

```json
{
  "query": "แนะนำคอร์สเรียน",
  "mode": "direct",
  "pageSize": 10
}
```

**Fields:**
- `query` (required): Your search query (1-500 chars)
- `mode` (optional): "streaming" or "direct" (default: "streaming")
- `pageSize` (optional): 1-50 results (default: 5)

---

## 2. Query Enhancement Fields

### 2.1 Query Expansion

```json
{
  "query": "python",
  "queryExpansion": "AUTO"
}
```

**Options:**
- `"AUTO"` - Expand when helpful (default)
- `"DISABLED"` - Use exact query only
- `"ALWAYS"` - Always expand

**Example - Disable Expansion:**
```json
{
  "query": "python programming",
  "queryExpansion": "DISABLED"
}
```

---

### 2.2 Spell Correction

```json
{
  "query": "phyton programing",
  "spellCorrection": "AUTO"
}
```

**Options:**
- `"AUTO"` - Auto-correct and search (default)
- `"DISABLED"` - No spell checking
- `"SUGGESTION_ONLY"` - Show suggestions without auto-correct

**Example - Suggestion Only:**
```json
{
  "query": "datascience",
  "spellCorrection": "SUGGESTION_ONLY"
}
```

---

## 3. Filtering Fields

### 3.1 Simple Category Filter

```json
{
  "query": "คอร์สเรียน",
  "filter": "category: ANY(\"course\")"
}
```

---

### 3.2 Price Range Filter

```json
{
  "query": "คอร์ส",
  "filter": "price < 5000"
}
```

---

### 3.3 Multiple Conditions (AND)

```json
{
  "query": "คอร์สสำหรับมือใหม่",
  "filter": "category: ANY(\"course\") AND difficulty: ANY(\"beginner\") AND price < 3000"
}
```

---

### 3.4 Complex Logic (OR)

```json
{
  "query": "เรียนออนไลน์",
  "filter": "(delivery: ANY(\"online\")) OR (location: GEO_DISTANCE(\"Bangkok\", 20000))"
}
```

---

### 3.5 Canonical Filter (Default Filter)

```json
{
  "query": "คอร์ส",
  "filter": "category: ANY(\"course\")",
  "canonicalFilter": "status: ANY(\"published\") AND language: ANY(\"th\")"
}
```

**Use Case:** Canonical filter applies when query expansion is used

---

### 3.6 Filter Syntax Reference

```json
{
  "query": "courses",
  "filter": "category: ANY(\"course\", \"workshop\") AND price: IN(0, 5000) AND rating >= 4.0 AND NOT status: ANY(\"archived\")"
}
```

**Operators:**
- Text: `ANY("value1", "value2")`
- Numbers: `<`, `>`, `<=`, `>=`, `=`, `IN(min, max)`
- Logic: `AND`, `OR`, `NOT`, `-`
- Geo: `GEO_DISTANCE("location", meters)`

---

## 4. Boosting Fields

### 4.1 Condition Boost (Single)

```json
{
  "query": "คอร์ส AI",
  "boostSpec": {
    "conditionBoostSpecs": [
      {
        "condition": "featured = \"true\"",
        "boost": 0.5
      }
    ]
  }
}
```

**Fields:**
- `condition`: Filter expression
- `boost`: -1.0 to 1.0 (0.5 = 50% boost)

---

### 4.2 Multiple Condition Boosts

```json
{
  "query": "คอร์สยอดนิยม",
  "boostSpec": {
    "conditionBoostSpecs": [
      {
        "condition": "rating >= 4.5",
        "boost": 0.6
      },
      {
        "condition": "rating >= 4.0 AND rating < 4.5",
        "boost": 0.3
      },
      {
        "condition": "enrollment_count > 100",
        "boost": 0.4
      }
    ]
  }
}
```

---

### 4.3 Freshness Boost

```json
{
  "query": "คอร์สใหม่",
  "boostSpec": {
    "freshnessBoostSpecs": [
      {
        "datetimeField": "published_date",
        "freshnessDuration": "30d",
        "boost": 0.7
      }
    ]
  }
}
```

**Fields:**
- `datetimeField`: Field name (e.g., "published_date", "updated_at")
- `freshnessDuration`: Duration (e.g., "7d", "30d", "90d")
- `boost`: -1.0 to 1.0

---

### 4.4 Combined Boosting

```json
{
  "query": "แนะนำคอร์ส",
  "boostSpec": {
    "conditionBoostSpecs": [
      {
        "condition": "featured = \"true\"",
        "boost": 0.5
      },
      {
        "condition": "rating >= 4.5",
        "boost": 0.4
      }
    ],
    "freshnessBoostSpecs": [
      {
        "datetimeField": "published_date",
        "freshnessDuration": "60d",
        "boost": 0.3
      }
    ]
  }
}
```

---

## 5. Faceting Fields

### 5.1 Single Facet

```json
{
  "query": "คอร์สเรียน",
  "facetSpecs": [
    {
      "facetKey": {
        "key": "category"
      },
      "limit": 20
    }
  ]
}
```

**Response:**
```json
{
  "facets": [
    {
      "key": "category",
      "values": [
        {"value": "course", "count": 45},
        {"value": "faq", "count": 23}
      ]
    }
  ]
}
```

---

### 5.2 Multiple Facets

```json
{
  "query": "คอร์ส",
  "facetSpecs": [
    {
      "facetKey": {
        "key": "category"
      },
      "limit": 20
    },
    {
      "facetKey": {
        "key": "difficulty"
      },
      "limit": 10
    },
    {
      "facetKey": {
        "key": "delivery_mode"
      },
      "limit": 5
    }
  ]
}
```

---

### 5.3 Facet with Restricted Values

```json
{
  "query": "courses",
  "facetSpecs": [
    {
      "facetKey": {
        "key": "difficulty",
        "restrictedValues": ["beginner", "intermediate", "advanced"]
      },
      "limit": 10
    }
  ]
}
```

---

### 5.4 All Facet Fields

```json
{
  "query": "search",
  "facetSpecs": [
    {
      "facetKey": {
        "key": "category",
        "restrictedValues": ["course", "workshop", "webinar"]
      },
      "limit": 20,
      "excludedFilterKeys": ["price"],
      "enableDynamicPosition": true
    }
  ]
}
```

**Fields:**
- `facetKey.key` (required): Field name
- `facetKey.restrictedValues` (optional): Limit to specific values
- `limit` (optional): Max values (default: 20, max: 100)
- `excludedFilterKeys` (optional): Filter keys to exclude
- `enableDynamicPosition` (optional): Enable dynamic positioning (default: true)

---

## 6. Summary Customization Fields

### 6.1 Custom System Prompt

```json
{
  "query": "ฉันควรเรียนอะไร",
  "mode": "direct",
  "customSystemPrompt": "คุณเป็นที่ปรึกษาการเรียนรู้ของ 9Expert Training มีความเชี่ยวชาญด้าน Data Science และ AI โปรดตอบคำถามโดย:\n1. ให้คำแนะนำที่เป็นกันเองและเข้าใจง่าย\n2. แนะนำคอร์สที่เหมาะกับระดับของผู้เรียน\n3. บอกทักษะที่ต้องพัฒนาและขั้นตอนการเรียนรู้"
}
```

**Max length:** 2000 characters

---

### 6.2 Semantic Chunks

```json
{
  "query": "คอร์ส AI",
  "useSemanticChunks": true
}
```

**Options:**
- `true` - Use semantic chunking for better quality (default)
- `false` - Use standard chunking

---

### 6.3 Summary Result Count

```json
{
  "query": "แนะนำคอร์ส",
  "summaryResultCount": 8
}
```

**Range:** 1-10 (default: 5)

---

### 6.4 Language Code

```json
{
  "query": "AI courses",
  "languageCode": "en"
}
```

**Options:** "th", "en", "ja", "zh", etc. (BCP-47 codes)
**Default:** "th"

---

### 6.5 Summary Model Version (Direct Mode)

```json
{
  "query": "คอร์ส data science",
  "mode": "direct",
  "summaryModelVersion": "preview"
}
```

**Options:**
- `"stable"` - Production model (default)
- `"preview"` - Latest features

---

### 6.6 Complete Summary Config

```json
{
  "query": "แนะนำเส้นทางเรียน",
  "mode": "direct",
  "customSystemPrompt": "คุณเป็นผู้เชี่ยวชาญด้านการศึกษา...",
  "useSemanticChunks": true,
  "summaryResultCount": 8,
  "languageCode": "th",
  "summaryModelVersion": "stable"
}
```

---

## 7. Model Generation Fields (Streaming)

### 7.1 Temperature

```json
{
  "query": "คอร์ส AI",
  "mode": "streaming",
  "temperature": 0.7
}
```

**Range:** 0.0-2.0
**Use Cases:**
- 0.0-0.3: Factual Q&A
- 0.6-0.8: Conversational
- 0.9-1.5: Creative

---

### 7.2 Top-K

```json
{
  "query": "What is Python",
  "mode": "streaming",
  "topK": 20
}
```

**Range:** 1-40
**Use Cases:**
- 1-10: Technical docs
- 20-40: Natural conversation

---

### 7.3 Top-P

```json
{
  "query": "แนะนำคอร์ส",
  "mode": "streaming",
  "topP": 0.95
}
```

**Range:** 0.0-1.0
**Use Cases:**
- 0.1-0.5: Focused
- 0.8-0.95: Balanced
- 0.95-1.0: Diverse

---

### 7.4 Max Output Tokens

```json
{
  "query": "อธิบาย machine learning",
  "mode": "streaming",
  "maxOutputTokens": 2048
}
```

**Range:** 1-8192
**Approximate words:**
- 256 tokens ≈ 190 words
- 512 tokens ≈ 380 words
- 1024 tokens ≈ 760 words
- 2048 tokens ≈ 1500 words
- 4096 tokens ≈ 3000 words

---

### 7.5 Model Selection

```json
{
  "query": "คอร์ส AI",
  "mode": "streaming",
  "model": "gemini-2.0-flash"
}
```

**Options:**
- "gemini-2.0-flash" (default)
- "gemini-1.5-pro"
- "gemini-1.5-flash"

---

### 7.6 Complete Generation Config

```json
{
  "query": "สร้างแผนการเรียนแบบ personalized",
  "mode": "streaming",
  "model": "gemini-2.0-flash",
  "temperature": 0.8,
  "topK": 40,
  "topP": 0.95,
  "maxOutputTokens": 1536
}
```

---

## 8. Complete Examples

### 8.1 Production E-Commerce Search

```json
{
  "query": "คอร์ส data science สำหรับมือใหม่",
  "mode": "direct",
  "pageSize": 20,

  "queryExpansion": "AUTO",
  "spellCorrection": "AUTO",

  "filter": "category: ANY(\"course\") AND difficulty: ANY(\"beginner\", \"intermediate\") AND price < 10000",
  "canonicalFilter": "status: ANY(\"published\") AND language: ANY(\"th\")",

  "boostSpec": {
    "conditionBoostSpecs": [
      {
        "condition": "featured = \"true\"",
        "boost": 0.6
      },
      {
        "condition": "rating >= 4.5",
        "boost": 0.5
      },
      {
        "condition": "enrollment_count > 100",
        "boost": 0.3
      }
    ],
    "freshnessBoostSpecs": [
      {
        "datetimeField": "published_date",
        "freshnessDuration": "90d",
        "boost": 0.4
      }
    ]
  },

  "facetSpecs": [
    {
      "facetKey": {"key": "category"},
      "limit": 20
    },
    {
      "facetKey": {"key": "difficulty"},
      "limit": 10
    },
    {
      "facetKey": {"key": "instructor"},
      "limit": 15
    }
  ],

  "relevanceThreshold": "MEDIUM",

  "customSystemPrompt": "คุณเป็นที่ปรึกษาด้านการเรียนรู้ของ 9Expert Training แนะนำคอร์สโดยเน้นความเหมาะสมกับระดับของผู้เรียน ให้รายละเอียดเกี่ยวกับเนื้อหา ทักษะที่ได้ และขั้นตอนการเรียน",
  "useSemanticChunks": true,
  "summaryResultCount": 8,
  "languageCode": "th",
  "summaryModelVersion": "stable",

  "returnRelevanceScore": true,
  "safeSearch": false
}
```

---

### 8.2 Interactive Chatbot (Streaming)

```json
{
  "query": "แนะนำเส้นทางเรียน AI จากเริ่มต้น",
  "mode": "streaming",
  "pageSize": 10,

  "model": "gemini-2.0-flash",
  "temperature": 0.7,
  "topK": 40,
  "topP": 0.95,
  "maxOutputTokens": 1536,

  "filter": "category: ANY(\"course\") AND difficulty: ANY(\"beginner\")",

  "boostSpec": {
    "conditionBoostSpecs": [
      {
        "condition": "rating >= 4.0",
        "boost": 0.4
      }
    ]
  },

  "useSemanticChunks": true,
  "languageCode": "th"
}
```

---

### 8.3 Factual Q&A (Low Temperature)

```json
{
  "query": "Python คืออะไร ใช้ทำอะไรได้บ้าง",
  "mode": "streaming",

  "model": "gemini-2.0-flash",
  "temperature": 0.2,
  "topK": 20,
  "topP": 0.8,
  "maxOutputTokens": 512,

  "pageSize": 5,
  "useSemanticChunks": true,
  "languageCode": "th"
}
```

---

### 8.4 Creative Recommendations (High Temperature)

```json
{
  "query": "สร้างแผนการเรียนที่เหมาะกับฉัน",
  "mode": "streaming",

  "model": "gemini-2.0-flash",
  "temperature": 0.9,
  "topK": 40,
  "topP": 0.95,
  "maxOutputTokens": 2048,

  "boostSpec": {
    "conditionBoostSpecs": [
      {
        "condition": "popular = \"true\"",
        "boost": 0.3
      }
    ]
  },

  "customSystemPrompt": "คุณเป็น AI ที่สร้างแผนการเรียนแบบ personalized ตอบแบบสร้างสรรค์และเป็นมิตร",
  "languageCode": "th"
}
```

---

### 8.5 Faceted Catalog Search

```json
{
  "query": "*",
  "mode": "direct",
  "pageSize": 50,

  "filter": "category: ANY(\"course\") AND status: ANY(\"published\")",

  "facetSpecs": [
    {
      "facetKey": {"key": "category"},
      "limit": 20
    },
    {
      "facetKey": {"key": "difficulty"},
      "limit": 10
    },
    {
      "facetKey": {"key": "delivery_mode"},
      "limit": 5
    },
    {
      "facetKey": {"key": "instructor"},
      "limit": 15
    },
    {
      "facetKey": {"key": "duration_hours"},
      "limit": 10
    }
  ],

  "relevanceThreshold": "LOW",
  "summaryResultCount": 10,
  "useSemanticChunks": true
}
```

---

## 9. cURL Examples

### 9.1 Basic Request

```bash
curl -X POST http://localhost:8000/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "คอร์ส AI",
    "mode": "direct"
  }'
```

---

### 9.2 With Filtering

```bash
curl -X POST http://localhost:8000/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "คอร์สเรียน",
    "filter": "category: ANY(\"course\") AND price < 5000",
    "pageSize": 10
  }'
```

---

### 9.3 With Boosting

```bash
curl -X POST http://localhost:8000/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "คอร์ส AI",
    "boostSpec": {
      "conditionBoostSpecs": [
        {
          "condition": "featured = \"true\"",
          "boost": 0.5
        }
      ]
    }
  }'
```

---

### 9.4 Streaming with Temperature

```bash
curl -X POST http://localhost:8000/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "แนะนำคอร์ส",
    "mode": "streaming",
    "temperature": 0.8,
    "maxOutputTokens": 1024
  }'
```

---

### 9.5 Complete Production Request

```bash
curl -X POST http://localhost:8000/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "คอร์ส data analytics สำหรับมือใหม่",
    "mode": "direct",
    "pageSize": 20,
    "filter": "category: ANY(\"course\") AND difficulty: ANY(\"beginner\")",
    "boostSpec": {
      "conditionBoostSpecs": [
        {"condition": "rating >= 4.5", "boost": 0.5}
      ]
    },
    "facetSpecs": [
      {"facetKey": {"key": "category"}, "limit": 20}
    ],
    "useSemanticChunks": true,
    "languageCode": "th"
  }'
```

---

## 10. Field Reference Table

| Field | Type | Required | Default | Mode | Description |
|-------|------|----------|---------|------|-------------|
| `query` | string | ✅ Yes | - | Both | Search query (1-500 chars) |
| `mode` | string | No | "streaming" | Both | "streaming" or "direct" |
| `pageSize` | integer | No | 5 | Both | Results count (1-50) |
| `model` | string | No | "gemini-2.0-flash" | Streaming | Gemini model name |
| `queryExpansion` | string | No | "AUTO" | Both | AUTO/DISABLED/ALWAYS |
| `spellCorrection` | string | No | "AUTO" | Both | AUTO/DISABLED/SUGGESTION_ONLY |
| `filter` | string | No | null | Both | Filter expression |
| `canonicalFilter` | string | No | null | Both | Default filter |
| `boostSpec` | object | No | null | Both | Boosting configuration |
| `facetSpecs` | array | No | null | Both | Facet specifications |
| `relevanceThreshold` | string | No | null | Both | LOWEST/LOW/MEDIUM/HIGH/HIGHEST |
| `customSystemPrompt` | string | No | null | Direct | Custom AI prompt (max 2000 chars) |
| `useSemanticChunks` | boolean | No | true | Direct | Use semantic chunking |
| `summaryResultCount` | integer | No | 5 | Direct | Summary results (1-10) |
| `languageCode` | string | No | "th" | Both | BCP-47 language code |
| `summaryModelVersion` | string | No | "stable" | Direct | "stable" or "preview" |
| `temperature` | float | No | null | Streaming | Sampling temperature (0.0-2.0) |
| `topK` | integer | No | null | Streaming | Top-K sampling (1-40) |
| `topP` | float | No | null | Streaming | Top-P sampling (0.0-1.0) |
| `maxOutputTokens` | integer | No | null | Streaming | Max tokens (1-8192) |
| `returnRelevanceScore` | boolean | No | false | Both | Include relevance scores |
| `safeSearch` | boolean | No | false | Both | Enable safe search |

---

**End of Payload Examples**

For configuration details, see: `VERTEX_AI_SEARCH_COMPLETE_CONFIG.md`
For model parameters, see: `MODEL_GENERATION_PARAMETERS.md`
For usage patterns, see: `VERTEX_AI_SEARCH_USAGE_EXAMPLES.md`
