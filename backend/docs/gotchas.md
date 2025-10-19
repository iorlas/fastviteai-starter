# Backend Gotchas

Common pitfalls and best practices for the FastAPI backend. Keep this list compact for quick reference.

---

## 1. Pydantic Schemas: Use BaseSchema
Inherit from `BaseSchema` not `BaseModel`. Auto-converts empty datetime strings to None (HTML form compatibility). Works with `datetime | None` and `Annotated[datetime | None, ...]`.
**See:** `app/core/base_schema.py`

---

**Last Updated:** 2025-10-19
