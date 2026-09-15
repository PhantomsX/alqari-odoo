import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .alqari_client import AlQariClient
from .alqari_field_condition import validation_checks_to_api_rules
from .alqari_settings import DEFAULT_CATEGORIES, DEFAULT_EXTRACT_FIELDS


class AlQariDocument(models.Model):
    _name = "alqari.document"
    _description = "Al-Qari Processed Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(required=True, tracking=True, default=lambda self: _("New Document"))
    upload_file = fields.Binary(string="Upload Document", attachment=False)
    upload_filename = fields.Char(string="Filename")
    attachment_id = fields.Many2one("ir.attachment", ondelete="set null", readonly=True)
    file_name = fields.Char(string="File", compute="_compute_file_name", store=True)
    document_id = fields.Char(string="Al-Qari Document ID", index=True, tracking=True, copy=False)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("processing", "Processing"),
            ("awaiting_review", "Awaiting Review"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="draft",
        tracking=True,
        copy=False,
    )
    ocr_language = fields.Selection(
        [
            ("auto", "Auto-detect"),
            ("ar", "Arabic"),
            ("en", "English"),
        ],
        default="auto",
        string="OCR Language",
    )
    ocr_output_format = fields.Selection(
        [
            ("plain-text", "Plain text"),
            ("markdown", "Markdown"),
            ("layout", "Layout"),
        ],
        default="plain-text",
        string="OCR Output",
    )
    fields_to_extract = fields.Char(
        string="Fields to Extract",
        help="Comma-separated field names to extract after OCR.",
    )
    run_classify = fields.Boolean(string="Classify document type", default=False)
    run_validate = fields.Boolean(string="Run validation", default=False)
    classify_categories = fields.Char(
        string="Categories",
        help="Comma-separated categories used when classification is enabled.",
    )
    validation_required_fields = fields.Char(
        string="Required Fields",
        help="Extracted fields that must be present when validation is enabled.",
    )
    validation_rules = fields.Text(
        string="Validation Rules",
        help="Optional business rules checked against the document text and extracted fields.",
    )
    run_human_review = fields.Boolean(string="Send to human review", default=False)
    human_review_trigger = fields.Selection(
        [
            ("always", "Always"),
            ("validation_fail", "When validation fails (API result)"),
        ],
        string="Human Review Trigger",
        default="validation_fail",
        help="Human review is triggered from Al-Qari API validation results only.",
    )
    validation_rule_line_ids = fields.One2many(
        "alqari.document.condition.line",
        "document_id",
        string="Validation Rules",
    )
    review_assignee_email = fields.Char(string="Reviewer Email")
    review_instructions = fields.Text(string="Review Instructions")
    review_send_email = fields.Boolean(string="Send review email", default=True)
    review_task_id = fields.Char(string="Review Task ID", copy=False, readonly=True)
    review_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Review Status",
        copy=False,
        readonly=True,
    )
    review_email_sent = fields.Boolean(string="Review Email Sent", copy=False, readonly=True)
    ocr_text = fields.Text(string="OCR Text", copy=False)
    doc_type = fields.Char(string="Document Type", copy=False)
    extracted_fields_json = fields.Text(string="Extracted Fields (JSON)", copy=False)
    validation_json = fields.Text(string="Validation (JSON)", copy=False)
    validation_passed = fields.Boolean(compute="_compute_validation_summary", copy=False)
    validation_summary = fields.Char(compute="_compute_validation_summary", copy=False)
    validation_summary_html = fields.Html(
        string="Validation Result", compute="_compute_validation_summary_html", sanitize=False
    )
    error_message = fields.Text(copy=False)
    res_model = fields.Char(index=True)
    res_id = fields.Integer(index=True)

    extracted_invoice_number = fields.Char(
        string="Invoice #", compute="_compute_extracted_summary", store=True, copy=False
    )
    extracted_total = fields.Char(
        string="Total", compute="_compute_extracted_summary", store=True, copy=False
    )
    extracted_date = fields.Char(
        string="Date", compute="_compute_extracted_summary", store=True, copy=False
    )
    extracted_vendor = fields.Char(
        string="Vendor", compute="_compute_extracted_summary", store=True, copy=False
    )
    fields_summary_html = fields.Html(
        string="All Extracted Fields", compute="_compute_fields_summary_html", sanitize=False
    )
    color = fields.Integer(compute="_compute_color")

    @api.depends("attachment_id", "upload_filename")
    def _compute_file_name(self):
        for rec in self:
            rec.file_name = rec.upload_filename or (rec.attachment_id.name if rec.attachment_id else False)

    @api.depends("state")
    def _compute_color(self):
        palette = {"draft": 4, "processing": 2, "awaiting_review": 3, "done": 10, "error": 1}
        for rec in self:
            rec.color = palette.get(rec.state, 0)

    @api.depends("validation_json")
    def _compute_validation_summary(self):
        for rec in self:
            rec.validation_passed = False
            rec.validation_summary = False
            payload = rec._parsed_validation_payload()
            if not payload:
                continue
            passed = payload.get("passed")
            if passed is None:
                overall = str(payload.get("overall_verdict") or payload.get("overall") or "").upper()
                passed = overall == "PASS"
            rec.validation_passed = bool(passed)
            rec.validation_summary = "PASS" if passed else "FAIL"

    @api.depends("validation_json")
    def _compute_validation_summary_html(self):
        for rec in self:
            payload = rec._parsed_validation_payload()
            if not payload:
                rec.validation_summary_html = False
                continue
            passed = payload.get("passed")
            if passed is None:
                overall = str(payload.get("overall_verdict") or payload.get("overall") or "").upper()
                passed = overall == "PASS"
            summary = "PASS" if passed else "FAIL"
            failures = payload.get("failures") or []
            rule_results = payload.get("rule_results") or []
            status_class = "success" if passed else "danger"
            rows = [
                f"<tr><td style='padding:6px 12px;font-weight:600;'>Overall</td>"
                f"<td style='padding:6px 12px;'><span class='badge text-bg-{status_class}'>"
                f"{summary}</span></td></tr>"
            ]
            score = payload.get("score")
            if score is not None:
                rows.append(
                    f"<tr><td style='padding:6px 12px;font-weight:600;'>Score</td>"
                    f"<td style='padding:6px 12px;'>{score}</td></tr>"
                )
            for failure in failures:
                rows.append(
                    f"<tr><td style='padding:6px 12px;font-weight:600;'>Failure</td>"
                    f"<td style='padding:6px 12px;'>{failure}</td></tr>"
                )
            for result in rule_results:
                if not isinstance(result, dict):
                    continue
                rows.append(
                    f"<tr><td style='padding:6px 12px;font-weight:600;'>{result.get('rule', 'Rule')}</td>"
                    f"<td style='padding:6px 12px;'>{result.get('verdict', '')} — {result.get('reason', '')}</td></tr>"
                )
            rec.validation_summary_html = (
                "<table class='table table-sm table-borderless' style='width:100%;'>"
                + "".join(rows)
                + "</table>"
            )

    def _parsed_validation_payload(self) -> dict:
        self.ensure_one()
        if not self.validation_json:
            return {}
        try:
            payload = json.loads(self.validation_json)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    @api.depends("extracted_fields_json")
    def _compute_extracted_summary(self):
        for rec in self:
            data = rec._parsed_extracted_fields()
            rec.extracted_invoice_number = rec._field_value(data, "invoice_number")
            rec.extracted_total = rec._field_value(data, "total")
            rec.extracted_date = rec._field_value(data, "date")
            rec.extracted_vendor = rec._field_value(data, "vendor_name")

    @api.depends("extracted_fields_json")
    def _compute_fields_summary_html(self):
        for rec in self:
            rec.fields_summary_html = rec._build_fields_html(rec._parsed_extracted_fields())

    def _parsed_extracted_fields(self) -> dict:
        self.ensure_one()
        if not self.extracted_fields_json:
            return {}
        try:
            payload = json.loads(self.extracted_fields_json)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _field_value(data: dict, key: str) -> str:
        value = data.get(key)
        if value is None or value == "":
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _build_fields_html(self, data: dict) -> str:
        if not data:
            return "<p class='text-muted'>No extracted fields yet.</p>"
        skip = {"document_id"}
        rows = []
        for key, value in sorted(data.items()):
            if key in skip:
                continue
            if isinstance(value, (dict, list)):
                display = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                display = value if value is not None else ""
            rows.append(
                f"<tr><td style='padding:6px 12px;font-weight:600;width:180px;'>{key}</td>"
                f"<td style='padding:6px 12px;'>{display}</td></tr>"
            )
        return (
            "<table class='table table-sm table-borderless' style='width:100%;'>"
            + "".join(rows)
            + "</table>"
        )

    @api.model
    def _settings(self):
        return self.env["alqari.settings.helper"]

    def _default_fields_to_extract(self) -> list[str]:
        return self._settings().split_csv(self._settings().get_defaults()["extract_fields"])

    def _resolve_classify_categories(self) -> list[str]:
        self.ensure_one()
        categories = self._settings().split_csv(self.classify_categories)
        if not categories:
            categories = self._settings().split_csv(
                self._settings().get_defaults()["classify_categories"]
            )
        return categories or self._settings().split_csv(DEFAULT_CATEGORIES)

    def _resolve_validation_config(self) -> dict:
        self.ensure_one()
        defaults = self._settings().get_defaults()
        required_fields = self._settings().split_csv(self.validation_required_fields)
        if not required_fields:
            required_fields = self._settings().split_csv(defaults["validation_required_fields"])
        text_rules = (self.validation_rules or defaults["validation_rules"] or "").strip()
        min_score = defaults["validation_min_score"]
        min_score_value = float(min_score) if min_score not in (False, "", None) else None
        rules = self._settings().resolve_validation_rules(text_rules)
        document_rules = validation_checks_to_api_rules(self.validation_rule_line_ids)
        if document_rules:
            if isinstance(rules, list):
                rules = rules + document_rules
            elif rules:
                rules = [rules, *document_rules]
            else:
                rules = document_rules
        return {
            "required_fields": required_fields,
            "rules": rules,
            "fail_on_warning": defaults["validation_fail_on_warning"],
            "min_score_to_pass": min_score_value,
        }

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        cfg = self._settings().get_defaults()
        if "fields_to_extract" in fields_list and not defaults.get("fields_to_extract"):
            defaults["fields_to_extract"] = cfg["extract_fields"]
        if "ocr_language" in fields_list and not defaults.get("ocr_language"):
            defaults["ocr_language"] = cfg["ocr_language"]
        if "ocr_output_format" in fields_list and not defaults.get("ocr_output_format"):
            defaults["ocr_output_format"] = cfg["ocr_output"]
        if "classify_categories" in fields_list and not defaults.get("classify_categories"):
            defaults["classify_categories"] = cfg["classify_categories"]
        if "validation_required_fields" in fields_list and not defaults.get("validation_required_fields"):
            defaults["validation_required_fields"] = cfg["validation_required_fields"]
        if "validation_rules" in fields_list and not defaults.get("validation_rules"):
            defaults["validation_rules"] = cfg["validation_rules"]
        if "run_classify" in fields_list and "run_classify" not in defaults:
            defaults["run_classify"] = cfg["run_classify"]
        if "run_validate" in fields_list and "run_validate" not in defaults:
            defaults["run_validate"] = cfg["run_validate"]
        if "run_human_review" in fields_list and "run_human_review" not in defaults:
            defaults["run_human_review"] = cfg["run_human_review"]
        if "human_review_trigger" in fields_list and "human_review_trigger" not in defaults:
            defaults["human_review_trigger"] = cfg["human_review_trigger"]
        if "review_assignee_email" in fields_list and not defaults.get("review_assignee_email"):
            defaults["review_assignee_email"] = cfg["review_assignee_email"]
        if "review_instructions" in fields_list and not defaults.get("review_instructions"):
            defaults["review_instructions"] = cfg["review_instructions"]
        if "review_send_email" in fields_list and "review_send_email" not in defaults:
            defaults["review_send_email"] = cfg["review_send_email"]
        return defaults

    @staticmethod
    def _validation_failed(payload: dict) -> bool:
        if not payload:
            return False
        passed = payload.get("passed")
        if passed is None:
            overall = str(payload.get("overall_verdict") or payload.get("overall") or "").upper()
            return overall != "PASS"
        return not bool(passed)

    def _resolve_human_review_config(self) -> dict:
        self.ensure_one()
        defaults = self._settings().get_defaults()
        return {
            "assignee_email": (self.review_assignee_email or defaults["review_assignee_email"] or "").strip(),
            "instructions": (self.review_instructions or defaults["review_instructions"] or "").strip(),
            "send_email": self.review_send_email if self.review_send_email is not None else defaults["review_send_email"],
        }

    def _should_submit_human_review(self, *, validation_failed: bool) -> bool:
        """Use only the Al-Qari validate API result — no local rule evaluation."""
        self.ensure_one()
        if not self.run_human_review or not self.document_id:
            return False
        trigger = self.human_review_trigger or "validation_fail"
        if trigger == "always":
            return True
        return bool(self.run_validate and validation_failed)

    def _validate_human_review_config(self):
        self.ensure_one()
        cfg = self._resolve_human_review_config()
        if cfg["send_email"] and not cfg["assignee_email"]:
            raise UserError(
                _("Set a reviewer email to send the human review notification, or disable Send review email.")
            )

    def _submit_human_review(self, client: AlQariClient):
        self.ensure_one()
        self._validate_human_review_config()
        cfg = self._resolve_human_review_config()
        api_state = self._settings().build_api_state(self._parsed_extracted_fields())
        validation_payload = self._parsed_validation_payload()
        if validation_payload:
            api_state["validation"] = validation_payload

        review = AlQariClient.flatten_response(
            client.human_review(
                self.document_id,
                assignee_email=cfg["assignee_email"],
                instructions=cfg["instructions"],
                send_email=cfg["send_email"],
                state=api_state,
            )
        )
        self.review_task_id = review.get("review_task_id")
        self.review_status = "pending"
        self.review_email_sent = bool(review.get("email_sent"))
        self.state = "awaiting_review"

        if cfg["send_email"] and not self.review_email_sent and review.get("email_error"):
            self.message_post(
                body=_("Human review created, but the notification email failed: %s")
                % review.get("email_error")
            )
        elif self.review_email_sent:
            self.message_post(
                body=_("Sent to human review. Notification email sent to %s.") % cfg["assignee_email"]
            )
        else:
            self.message_post(body=_("Sent to human review queue."))

    def _apply_review_context_fields(self, detail: dict):
        self.ensure_one()
        review_context = detail.get("review_context") or {}
        fields_payload = review_context.get("fields")
        if not isinstance(fields_payload, dict) or not fields_payload:
            return
        merged = self._parsed_extracted_fields()
        merged.update(fields_payload)
        self._set_json_field("extracted_fields_json", merged)

    def action_check_review_status(self):
        self.ensure_one()
        if not self.review_task_id:
            raise UserError(_("No human review task is linked to this document."))

        client = AlQariClient.from_env(self.env)
        detail = client.get_review_task(self.review_task_id)
        status = str(detail.get("status") or "").lower()
        self.review_status = status or self.review_status

        if status == "pending":
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Al-Qari"),
                    "message": _("Still awaiting human review."),
                    "type": "info",
                    "sticky": False,
                },
            }

        if status == "approved":
            self._apply_review_context_fields(detail)
            self.state = "done"
            self.error_message = False
            self.message_post(body=_("Human review approved."))
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Al-Qari"),
                    "message": _("Review approved. Extracted fields were updated if corrections were made."),
                    "type": "success",
                    "sticky": False,
                },
            }

        if status == "rejected":
            reason = detail.get("rejection_reason") or _("Review rejected.")
            self.state = "error"
            self.error_message = reason
            self.message_post(body=_("Human review rejected: %s") % reason)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Al-Qari"),
                    "message": reason,
                    "type": "warning",
                    "sticky": False,
                },
            }

        raise UserError(_("Unexpected review status: %s") % status)

    def _set_json_field(self, field_name: str, data) -> None:
        self[field_name] = json.dumps(data, ensure_ascii=False, indent=2) if data else False

    def _ensure_attachment_from_upload(self):
        """Create ir.attachment from the upload widget if the user picked a file."""
        self.ensure_one()
        if not self.upload_file:
            return self.attachment_id
        filename = self.upload_filename or self.name or "document.pdf"
        attachment = self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": self.upload_file,
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "application/pdf",
            }
        )
        self.write(
            {
                "attachment_id": attachment.id,
                "upload_file": False,
                "upload_filename": False,
            }
        )
        return attachment

    def action_process(self, fields_to_extract: list[str] | None = None):
        """Upload attachment → OCR → optional extract fields."""
        self.ensure_one()
        attachment = self._ensure_attachment_from_upload()
        if not attachment:
            raise UserError(_("Upload a PDF before processing."))
        file_bytes = attachment.raw
        if not file_bytes:
            raise UserError(_("Attachment has no file content."))

        client = AlQariClient.from_env(self.env)
        self.state = "processing"
        self.error_message = False
        try:
            upload = client.upload_ocr(
                file_bytes,
                attachment.name or "document.pdf",
                language=self.ocr_language or "auto",
                output_format=self.ocr_output_format or "plain-text",
            )
            self.document_id = upload.get("document_id")
            self.ocr_text = upload.get("text") or upload.get("markdown") or ""

            state_carry: dict = {k: v for k, v in upload.items() if k != "document_id"}
            fields_list = fields_to_extract or [
                f.strip() for f in (self.fields_to_extract or "").split(",") if f.strip()
            ] or self._default_fields_to_extract()
            if fields_list and self.document_id:
                extracted = AlQariClient.flatten_response(
                    client.extract_fields(self.document_id, fields_list, state=state_carry)
                )
                self._set_json_field("extracted_fields_json", extracted)
                if extracted.get("doc_type"):
                    self.doc_type = extracted["doc_type"]

            if self.run_classify and self.document_id:
                categories = self._resolve_classify_categories()
                if not categories:
                    raise UserError(_("Add at least one classification category in settings or on the document."))
                api_state = self._settings().build_api_state(self._parsed_extracted_fields())
                classified = AlQariClient.flatten_response(
                    client.classify(
                        self.document_id,
                        categories,
                        min_confidence=self._settings().get_defaults()["classify_min_confidence"],
                        state=api_state,
                    )
                )
                if classified.get("doc_type"):
                    self.doc_type = classified["doc_type"]

            validation_payload = {}
            if self.run_validate and self.document_id:
                validation_cfg = self._resolve_validation_config()
                api_state = self._settings().build_api_state(self._parsed_extracted_fields())
                validation_payload = AlQariClient.flatten_response(
                    client.validate(
                        self.document_id,
                        mode="auto",
                        rules=validation_cfg["rules"],
                        required_fields=validation_cfg["required_fields"],
                        fail_on_warning=validation_cfg["fail_on_warning"],
                        min_score_to_pass=validation_cfg["min_score_to_pass"],
                        state=api_state,
                    )
                )
                self._set_json_field("validation_json", validation_payload)

            validation_failed = self._validation_failed(validation_payload)
            if self._should_submit_human_review(validation_failed=validation_failed):
                self._submit_human_review(client)
            else:
                self.state = "done"
        except UserError as exc:
            self.state = "error"
            self.error_message = str(exc)
            raise
        except Exception as exc:  # noqa: BLE001 — surface to UI
            self.state = "error"
            self.error_message = str(exc)
            raise UserError(str(exc)) from exc
        return True

    @api.model
    def create_from_attachment(self, attachment, *, linked_record=None):
        vals = {
            "name": attachment.name or _("Al-Qari document"),
            "attachment_id": attachment.id,
        }
        if linked_record:
            vals["res_model"] = linked_record._name
            vals["res_id"] = linked_record.id
        return self.create(vals)
