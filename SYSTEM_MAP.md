# System Map — How Roze's Claude Setup Works

---

## The architecture

```
VOICE DNA  ──────────────────────────────────────────────────────────────────┐
(VOICE_DNA.md)                                                                │
Applies to: EVERYTHING. All projects. All platforms. No exceptions.           │
                                                                              │
           ┌──────────────────────────────────────────────────────────────────┘
           │
           ├── CLAUDE CODE (this repo)
           │   Governed by: CLAUDE.md (auto-read every session)
           │   ├── Brand work → also reads BRAND.md
           │   └── Acting work → voice DNA only, no brand context
           │
           ├── CLAUDE.AI — PERSONAL BRAND PROJECT (phone/desktop)
           │   Instructions: paste BRAND_PROJECT_INSTRUCTIONS.md
           │   Applies: Voice DNA + Brand context
           │   Does NOT apply: Acting context
           │
           └── CLAUDE.AI — ACTING PROJECT (phone/desktop)
               Instructions: paste ACTING_PROJECT_INSTRUCTIONS.md
               Applies: Voice DNA only
               Does NOT apply: Brand positioning, content pillars, Instagram strategy
```

---

## What to paste where

### Claude.ai — Personal Brand Project
1. Open the Personal Brand Project on phone or desktop
2. Go to Project Instructions / Custom Instructions
3. Open `BRAND_PROJECT_INSTRUCTIONS.md`
4. Copy everything from the **second** horizontal line to the end
5. Paste into Project Instructions
6. When your brand project is complete, paste the output into the `BRAND CONTEXT` section

### Claude.ai — Acting Project
1. Open the Acting Project on phone or desktop
2. Go to Project Instructions / Custom Instructions
3. Open `ACTING_PROJECT_INSTRUCTIONS.md`
4. Copy everything from the **second** horizontal line to the end
5. Paste into Project Instructions

### Claude Code (this repo)
Already configured. `CLAUDE.md` is read automatically at the start of every session. No action needed.

---

## When the Personal Brand project is complete

1. Open `BRAND.md` in this repo
2. Paste the brand output into the relevant sections (positioning, audience, content pillars, etc.)
3. Open `BRAND_PROJECT_INSTRUCTIONS.md`
4. Find the `BRAND CONTEXT` section and paste the same content there
5. Update that section in your Claude.ai Personal Brand Project instructions

That's it. Both environments will then have the full picture.

---

## The rule in one sentence

**Voice DNA crosses everything. Brand context stays in brand work. Acting context stays in acting work.**

---

## Files and their purpose

| File | Purpose |
|---|---|
| `VOICE_DNA.md` | The master voice profile. The source of truth for how Roze writes and thinks. |
| `BRAND.md` | Personal brand framework. Audience, positioning, pillars, platform. Empty until brand project is done. |
| `CLAUDE.md` | Instructions for Claude Code sessions. Auto-applied. Handles the layer system. |
| `BRAND_PROJECT_INSTRUCTIONS.md` | Paste into Claude.ai Personal Brand Project. Full voice DNA + brand context. |
| `ACTING_PROJECT_INSTRUCTIONS.md` | Paste into Claude.ai Acting Project. Full voice DNA. Brand context explicitly excluded. |
| `SYSTEM_MAP.md` | This file. How everything connects. |
