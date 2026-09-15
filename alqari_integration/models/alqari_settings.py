"""Shared helpers for reading Al-Qari integration settings."""

from __future__ import annotations

import json

from odoo import api, models

DEFAULT_CATEGORIES = "invoice, contract, receipt, purchase_order, other"
DEFAULT_EXTRACT_FIELDS = "invoice_number, total, date, vendor_name"
DEFAULT_API_BASE_URL = "https://api.alqari.sa"


class AlQariSettingsHelper(models.AbstractModel):
    _name = "alqari.settings.helper"
    _description = "Al-Qari configuration helpers"

    @api.model
    def _icp(self):
        return self.env["ir.config_parameter"].sudo()

    @api.model
    def split_csv(self, value: str | None) -> list[str]:
        return [part.strip() for part in (value or "").split(",") if part.strip()]

    @api.model
    def join_csv(self, values: list[str]) -> str:
        return ", ".join(value.strip() for value in values if value and value.strip())

    @api.model
    def get_defaults(self) -> dict:
        icp = self._icp()
        return {
            "api_base_url": icp.get_param("alqari.api_base_url", DEFAULT_API_BASE_URL),
            "extract_fields": icp.get_param("alqari.default_extract_fields", DEFAULT_EXTRACT_FIELDS),
            "ocr_language": icp.get_param("alqari.default_ocr_language", "auto"),
            "ocr_output": icp.get_param("alqari.default_ocr_output", "plain-text"),
            "classify_categories": icp.get_param("alqari.default_classify_categories", DEFAULT_CATEGORIES),
            "classify_min_confidence": float(icp.get_param("alqari.classify_min_confidence", "0") or 0),
            "run_classify": icp.get_param("alqari.default_run_classify", "False") == "True",
            "run_validate": icp.get_param("alqari.default_run_validate", "False") == "True",
            "validation_required_fields": icp.get_param(
                "alqari.validation_required_fields", DEFAULT_EXTRACT_FIELDS
            ),
            "validation_rules": icp.get_param("alqari.validation_rules", "") or "",
            "validation_min_score": icp.get_param("alqari.validation_min_score") or False,
            "validation_fail_on_warning": icp.get_param("alqari.validation_fail_on_warning", "False") == "True",
            "run_human_review": icp.get_param("alqari.default_run_human_review", "False") == "True",
            "human_review_trigger": icp.get_param("alqari.human_review_trigger", "validation_fail"),
            "review_assignee_email": icp.get_param("alqari.review_assignee_email", "") or "",
            "review_instructions": icp.get_param("alqari.review_instructions", "") or "",
            "review_send_email": icp.get_param("alqari.review_send_email", "True") == "True",
        }

    @api.model
    def resolve_validation_rules(self, text_rules: str | None = None) -> list | str | None:
        """Structured field rules take priority; free-text rules are the LLM fallback."""
        structured = self.env["alqari.validation.rule"].get_active_api_rules()
        if structured:
            return structured
        text = (text_rules or "").strip()
        if not text:
            text = (self.get_defaults().get("validation_rules") or "").strip()
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return text or None

    @api.model
    def build_api_state(self, extracted: dict | None) -> dict:
        """Shape extracted output for classify/validate API calls."""
        payload = dict(extracted or {})
        fields = {
            key: value
            for key, value in payload.items()
            if key not in ("document_id", "doc_type", "confidence")
        }
        state = dict(payload)
        state["fields"] = fields
        if payload.get("doc_type"):
            state["doc_type"] = payload["doc_type"]
        return state
