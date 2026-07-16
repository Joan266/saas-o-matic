# Vibe Coding — Registro del Proceso

Este directorio documenta el desarrollo iterativo con IA: prompts clave,
decisiones de auditoría, correcciones aplicadas y capturas visuales.

---

## Cómo usamos la IA en este proyecto

- **Herramienta:** Claude Code (claude-sonnet-4-6)
- **Workflow:** Spec-Driven → la IA recibe specs precisas, no descripciones vagas
- **Control de calidad:** Hooks PostToolUse con ruff (Python) ejecutados automáticamente
- **Visual QA:** Playwright screenshots tras cada vista completada

---

## Estructura de este directorio

```
vibe-coding/
├── 00-proceso-template.md   ← este archivo
├── 01-backend-log.md        ← decisiones y correcciones durante el backend
├── 02-frontend-log.md       ← decisiones y correcciones durante el frontend
└── screenshots/             ← capturas Playwright de cada vista
```

---

## Log template (copiar para cada sesión)

```markdown
### [FECHA] — [Feature]

**Prompt enviado:**
> [texto exacto del prompt]

**Lo que generó la IA:**
[descripción breve]

**Auditoría:**
- [ ] Lógica de negocio correcta
- [ ] Tipos/schemas alineados con spec
- [ ] Sin queries SQL con f-strings
- [ ] Manejo de errores presente
- [ ] Tests cubiertos

**Correcciones aplicadas:**
- [qué se cambió y por qué]

**Decisión final:** ACEPTADO / MODIFICADO / RECHAZADO
```
