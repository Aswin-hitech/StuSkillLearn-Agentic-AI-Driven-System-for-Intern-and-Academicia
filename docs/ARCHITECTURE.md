# StuSkillLink Architecture

```text
React 19 + Tailwind
        |
        v
FastAPI REST API + JWT role guards
        |
        +---------------- Multi-provider LLM gateway (NIM → Groq → Gemini → OpenRouter)
        |                 chat / model discovery / optional embeddings
        |
Six-agent orchestration boundary
        |
        v
Deterministic domain services
  - profile/eligibility prerequisites
  - LSRW rubric
  - skill normalization / gap analysis
  - hybrid weighted matching
  - preference-aware company ranking
  - category-aware multi-seat allocation
  - reject -> reallocation
  - internship feedback -> placement continuity
  - curriculum insight aggregation
        |
        v
SQLAlchemy transactional data layer
SQLite demo / PostgreSQL-Neon via DATABASE_URL
Optional MongoDB event mirror boundary
```

## Decision boundary
LLMs do not award seats. The provider gateway supports natural-language learning recommendations and evidence-grounded agent explanations. Each stage records provider/model provenance and is marked `DEGRADED` when deterministic fallback is used. Ranking and allocation remain deterministic and retain audit evidence.

## Six agents
1. Eligibility & Profile Agent
2. Skill & Communication Agent
3. Portfolio & Preference Agent
4. Matching & Allocation Agent
5. Academic Engagement Agent
6. Monitoring & Reallocation Agent

`app/agent_graph.py` runs the six deterministic domain stages as real LangGraph nodes. A dedicated fan-out node generates the six advisory LLM explanations concurrently, then a final node records the graph outcome. Every invocation uses a unique thread ID and a SQLite checkpointer locally; production can replace it with a PostgreSQL checkpointer without changing agent responsibilities.
