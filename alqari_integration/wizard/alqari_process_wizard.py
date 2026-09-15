from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AlQariProcessWizard(models.TransientModel):
    _name = "alqari.process.wizard"
    _description = "Process document with Al-Qari"

    name = fields.Char(string="Document Name", default=lambda self: _("New Document"))
    upload_file = fields.Binary(string="Upload Document", required=True, attachment=False)
    upload_filename = fields.Char(string="Filename")
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
    extract_field_line_ids = fields.One2many(
        "alqari.process.wizard.line",
        "wizard_id",
        string="Extract Fields",
        domain=[("line_type", "=", "extract")],
        context={"default_line_type": "extract"},
    )
    run_classify = fields.Boolean(string="Classify document type", default=False)
    category_line_ids = fields.One2many(
        "alqari.process.wizard.line",
        "wizard_id",
        string="Categories",
        domain=[("line_type", "=", "category")],
        context={"default_line_type": "category"},
    )
    run_validate = fields.Boolean(string="Validate extracted fields", default=False)
    required_field_line_ids = fields.One2many(
        "alqari.process.wizard.line",
        "wizard_id",
        string="Required Fields",
        domain=[("line_type", "=", "required")],
        context={"default_line_type": "required"},
    )
    validation_rules = fields.Text(
        string="Validation Rules",
        help="Optional business rules. Leave empty to use settings default.",
    )
    validation_rule_line_ids = fields.One2many(
        "alqari.process.wizard.validation.line",
        "wizard_id",
        string="Validation Rules",
    )
    run_human_review = fields.Boolean(string="Send to human review", default=False)
    human_review_trigger = fields.Selection(
        [
            ("always", "Always"),
            ("validation_fail", "When validation fails (API result)"),
        ],
        string="Human Review Trigger",
        default="validation_fail",
    )
    review_assignee_email = fields.Char(string="Reviewer Email")
    review_instructions = fields.Text(string="Review Instructions")
    review_send_email = fields.Boolean(string="Send review email", default=True)

    @api.model
    def _settings(self):
        return self.env["alqari.settings.helper"]

    @api.model
    def _line_commands_from_csv(self, csv_value, line_type):
        helper = self._settings()
        return [
            (0, 0, {"line_type": line_type, "name": name, "sequence": (index + 1) * 10})
            for index, name in enumerate(helper.split_csv(csv_value))
        ]

    @staticmethod
    def _lines_to_csv(lines):
        return ", ".join(line.name.strip() for line in lines if line.name and line.name.strip())

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        cfg = self._settings().get_defaults()
        if "extract_field_line_ids" in fields_list and not defaults.get("extract_field_line_ids"):
            defaults["extract_field_line_ids"] = self._line_commands_from_csv(
                cfg["extract_fields"], "extract"
            )
        if "ocr_language" in fields_list and not defaults.get("ocr_language"):
            defaults["ocr_language"] = cfg["ocr_language"]
        if "ocr_output_format" in fields_list and not defaults.get("ocr_output_format"):
            defaults["ocr_output_format"] = cfg["ocr_output"]
        if "category_line_ids" in fields_list and not defaults.get("category_line_ids"):
            defaults["category_line_ids"] = self._line_commands_from_csv(
                cfg["classify_categories"], "category"
            )
        if "required_field_line_ids" in fields_list and not defaults.get("required_field_line_ids"):
            defaults["required_field_line_ids"] = self._line_commands_from_csv(
                cfg["validation_required_fields"], "required"
            )
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
    def _validation_line_commands(lines):
        return [
            (
                0,
                0,
                {
                    "sequence": line.sequence,
                    "field_name": line.field_name,
                    "check_type": line.check_type,
                    "compare_value": line.compare_value,
                    "severity": line.severity,
                    "message": line.message,
                },
            )
            for line in lines
        ]

    def _create_attachment_from_upload(self):
        self.ensure_one()
        if not self.upload_file:
            raise UserError(_("Upload a PDF before processing."))
        return self.env["ir.attachment"].create(
            {
                "name": self.upload_filename or "document.pdf",
                "datas": self.upload_file,
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "application/pdf",
            }
        )

    def action_process(self):
        self.ensure_one()
        attachment = self._create_attachment_from_upload()
        if not attachment.raw:
            raise UserError(_("Upload a PDF before processing."))

        fields_to_extract = self._lines_to_csv(self.extract_field_line_ids)
        classify_categories = self._lines_to_csv(self.category_line_ids)
        validation_required_fields = self._lines_to_csv(self.required_field_line_ids)

        doc = self.env["alqari.document"].create_from_attachment(attachment)
        doc.write(
            {
                "name": self.name or attachment.name or _("Al-Qari document"),
                "ocr_language": self.ocr_language,
                "ocr_output_format": self.ocr_output_format,
                "fields_to_extract": fields_to_extract,
                "run_classify": self.run_classify,
                "run_validate": self.run_validate,
                "classify_categories": classify_categories,
                "validation_required_fields": validation_required_fields,
                "validation_rules": self.validation_rules,
                "run_human_review": self.run_human_review,
                "human_review_trigger": self.human_review_trigger,
                "review_assignee_email": self.review_assignee_email,
                "review_instructions": self.review_instructions,
                "review_send_email": self.review_send_email,
                "validation_rule_line_ids": self._validation_line_commands(
                    self.validation_rule_line_ids
                ),
            }
        )
        field_list = self._settings().split_csv(fields_to_extract)
        doc.action_process(fields_to_extract=field_list)

        return {
            "type": "ir.actions.act_window",
            "name": _("Al-Qari Document"),
            "res_model": "alqari.document",
            "res_id": doc.id,
            "view_mode": "form",
            "target": "current",
        }
