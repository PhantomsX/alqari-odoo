# Changelog — Al-Qari Odoo Module

## 17.0.1.0.9 — 2026-09-16

### Fixed
- Apps Store feature grid: aligned headings and body text across all four columns

## 17.0.1.0.8 — 2026-09-16

### Changed
- Regenerated Apps Store **icon** (256x256) and **banner** (880x450) from the Al-Qari chat-bubble logo SVG
- Redesigned `static/description/index.html` listing with hero screenshot and cleaner layout

## 17.0.1.0.6 — 2026-09-15

### Fixed
- Manifest version uses Odoo 17 format (`17.0.1.0.6`) required by Apps Store scanner

## 1.0.6 — 2026-09-15

### Changed
- **API-only connector:** removed local routing condition evaluation and visual condition builder
- Human review triggers use Al-Qari validate API results only (`always` or `validation_fail`)
- Validation rules are sent to the API as JSON; Odoo does not evaluate them locally

## 1.0.5 — 2026-09-14

### Added
- Human review with email notifications and review status polling
- Visual routing condition builder (compare extracted fields)
- Structured validation rules UI (required, greater than, contains, etc.)
- Image upload support (PNG/JPG) in addition to PDF
- List-based extract fields, categories, and required fields in settings/wizard

### Changed
- Production API default: `https://api.alqari.sa`
- Customer-facing copy no longer references dev/sandbox endpoints
- Improved numeric parsing for totals with currency suffixes (e.g. `1,150.00 SAR`)

## 1.0.0 — 2026-09-13

First production release.

### Features
- Al-Qari app with branded menu and logo
- Process Document wizard (upload → OCR → extract)
- Document kanban, list, and form views with extracted summary
- Settings: API URL, key, test connection, OCR/extraction defaults
- Configurable classification categories
- **Field Validation Rules** — structured checks (e.g. total > 10000)
- AI validation rules (free text) as fallback
- Required-field validation
- Role-based access: User and Administrator
- Customer install guide (`CUSTOMER_INSTALL.md`)
- Release packaging script (`package.ps1`)

### Requirements
- Odoo 17
- Python `requests`
- Al-Qari API key (`qari_...`)
