"""Thin HTTP client for Al-Qari /services/integration/* endpoints."""

from __future__ import annotations

import json
from typing import Any

import requests
from odoo.exceptions import UserError

from .alqari_settings import DEFAULT_API_BASE_URL


def _mime_type(filename: str) -> str:
    name = (filename or "").lower()
    if name.endswith(".png"):
        return "image/png"
    if name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if name.endswith(".webp"):
        return "image/webp"
    if name.endswith((".tif", ".tiff")):
        return "image/tiff"
    return "application/pdf"


class AlQariClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 300):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = (api_key or "").strip()
        self.timeout = timeout
        if not self.base_url or not self.api_key:
            raise UserError(
                "Al-Qari is not configured. Go to Settings → Al-Qari and set Base URL + API Key."
            )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.request(method, url, headers=self._headers(), timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise UserError(f"Al-Qari connection failed: {exc}") from exc
        if resp.status_code == 401:
            raise UserError("Al-Qari API key is invalid or expired.")
        if resp.status_code == 402:
            raise UserError("Al-Qari account has insufficient credits.")
        if resp.status_code >= 400:
            detail = resp.text[:2000]
            try:
                payload = resp.json()
                detail = payload.get("detail") or json.dumps(payload, ensure_ascii=False)
            except Exception:
                pass
            raise UserError(f"Al-Qari API error ({resp.status_code}): {detail}")
        if not resp.content:
            return {}
        return resp.json()

    def upload_ocr(
        self,
        file_bytes: bytes,
        filename: str,
        *,
        language: str = "auto",
        output_format: str = "plain-text",
    ) -> dict[str, Any]:
        params = {
            "language": language,
            "output_format": output_format,
            "return_boxes": "false",
            "fail_if_below_threshold": "false",
        }
        safe_name = filename or "document.pdf"
        files = {"file": (safe_name, file_bytes, _mime_type(safe_name))}
        return self._request("POST", "/services/integration/upload-ocr", params=params, files=files)

    def extract_fields(
        self,
        document_id: str,
        fields: list[str],
        *,
        instructions: str = "",
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "document_id": document_id,
            "fields": fields,
            "instructions": instructions,
            "strict": False,
        }
        if state:
            body["state"] = state
        return self._request("POST", "/services/integration/extract-fields", json=body)

    def classify(
        self,
        document_id: str,
        categories: list[str],
        *,
        min_confidence: float = 0.0,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "document_id": document_id,
            "categories": categories,
            "min_confidence": min_confidence,
        }
        if state:
            body["state"] = state
        return self._request("POST", "/services/integration/classify", json=body)

    def validate(
        self,
        document_id: str,
        *,
        mode: str = "auto",
        rules: list | str | None = None,
        required_fields: list[str] | None = None,
        fail_on_warning: bool = False,
        min_score_to_pass: float | None = None,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "document_id": document_id,
            "mode": mode,
            "fail_on_warning": fail_on_warning,
        }
        if rules:
            body["rules"] = rules
        if required_fields:
            body["required_fields"] = required_fields
        if min_score_to_pass is not None:
            body["min_score_to_pass"] = min_score_to_pass
        if state:
            body["state"] = state
        return self._request("POST", "/services/integration/validate", json=body)

    def human_review(
        self,
        document_id: str,
        *,
        assignee_email: str = "",
        instructions: str = "",
        email_subject: str = "",
        send_email: bool = True,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "document_id": document_id,
            "assignee_email": assignee_email,
            "instructions": instructions,
            "email_subject": email_subject,
            "send_email": send_email,
        }
        if state:
            body["state"] = state
        return self._request("POST", "/services/integration/human-review", json=body)

    def get_review_task(self, review_task_id: str) -> dict[str, Any]:
        return self._request("GET", f"/workflows/reviews/{review_task_id}")

    def test_connection(self) -> None:
        """Verify API URL is reachable and the key looks valid."""
        if not self.api_key.startswith("qari_"):
            raise UserError("API key should start with qari_.")
        try:
            resp = requests.get(f"{self.base_url}/docs", timeout=15)
        except requests.RequestException as exc:
            raise UserError(f"Cannot reach Al-Qari API: {exc}") from exc
        if resp.status_code >= 500:
            raise UserError(f"Al-Qari API returned server error ({resp.status_code}).")

    @classmethod
    def from_env(cls, env) -> "AlQariClient":
        icp = env["ir.config_parameter"].sudo()
        base_url = icp.get_param("alqari.api_base_url", DEFAULT_API_BASE_URL)
        api_key = icp.get_param("alqari.api_key", "")
        return cls(base_url=base_url, api_key=api_key)

    @staticmethod
    def flatten_response(response: dict[str, Any]) -> dict[str, Any]:
        """Merge document_id + output (same shape as n8n nodes)."""
        output = response.get("output")
        if isinstance(output, dict):
            return {"document_id": response.get("document_id"), **output}
        return response
