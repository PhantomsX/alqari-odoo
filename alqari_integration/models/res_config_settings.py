from odoo import _, fields, models
from odoo.exceptions import UserError

from .alqari_client import AlQariClient
from .alqari_settings import DEFAULT_API_BASE_URL, DEFAULT_CATEGORIES, DEFAULT_EXTRACT_FIELDS


class ResConfigSettingsExtractFieldLine(models.TransientModel):
    _name = "res.config.settings.extract.field.line"
    _description = "Al-Qari Settings Extract Field Line"
    _order = "sequence, id"

    settings_id = fields.Many2one("res.config.settings", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Field Name", required=True)


class ResConfigSettingsCategoryLine(models.TransientModel):
    _name = "res.config.settings.category.line"
    _description = "Al-Qari Settings Category Line"
    _order = "sequence, id"

    settings_id = fields.Many2one("res.config.settings", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Category", required=True)


class ResConfigSettingsRequiredFieldLine(models.TransientModel):
    _name = "res.config.settings.required.field.line"
    _description = "Al-Qari Settings Required Field Line"
    _order = "sequence, id"

    settings_id = fields.Many2one("res.config.settings", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Required Field", required=True)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    alqari_api_base_url = fields.Char(
        string="API Base URL",
        config_parameter="alqari.api_base_url",
        default=DEFAULT_API_BASE_URL,
        help="Production API endpoint. Default: https://api.alqari.sa",
    )
    alqari_api_key = fields.Char(
        string="API Key",
        config_parameter="alqari.api_key",
        help="Your qari_... API key from the Al-Qari dashboard.",
    )
    alqari_default_extract_fields = fields.Char(
        string="Extract Fields Storage",
        config_parameter="alqari.default_extract_fields",
        default=DEFAULT_EXTRACT_FIELDS,
        help="Comma-separated field names extracted from each document.",
    )
    alqari_extract_field_line_ids = fields.One2many(
        "res.config.settings.extract.field.line",
        "settings_id",
        string="Extract Fields",
    )
    alqari_default_ocr_language = fields.Selection(
        [
            ("auto", "Auto-detect"),
            ("ar", "Arabic"),
            ("en", "English"),
        ],
        string="OCR Language",
        config_parameter="alqari.default_ocr_language",
        default="auto",
    )
    alqari_default_ocr_output = fields.Selection(
        [
            ("plain-text", "Plain text"),
            ("markdown", "Markdown"),
            ("layout", "Layout"),
        ],
        string="OCR Output",
        config_parameter="alqari.default_ocr_output",
        default="plain-text",
    )
    alqari_default_classify_categories = fields.Char(
        string="Categories Storage",
        config_parameter="alqari.default_classify_categories",
        default=DEFAULT_CATEGORIES,
        help="Comma-separated document types used when classification is enabled.",
    )
    alqari_category_line_ids = fields.One2many(
        "res.config.settings.category.line",
        "settings_id",
        string="Categories",
    )
    alqari_classify_min_confidence = fields.Float(
        string="Min Confidence",
        config_parameter="alqari.classify_min_confidence",
        default=0.0,
        help="Minimum classifier confidence (0–1). Results below this use the fallback category.",
    )
    alqari_default_run_classify = fields.Boolean(
        string="Classify by Default",
        config_parameter="alqari.default_run_classify",
        default=False,
    )
    alqari_default_run_validate = fields.Boolean(
        string="Validate by Default",
        config_parameter="alqari.default_run_validate",
        default=False,
    )
    alqari_validation_required_fields = fields.Char(
        string="Required Fields Storage",
        config_parameter="alqari.validation_required_fields",
        default=DEFAULT_EXTRACT_FIELDS,
        help="Extracted fields that must be present for validation to pass.",
    )
    alqari_required_field_line_ids = fields.One2many(
        "res.config.settings.required.field.line",
        "settings_id",
        string="Required Fields",
    )
    alqari_validation_rules = fields.Text(
        string="Validation Rules",
        help="Optional business rules checked against the document (plain text or one rule per line).",
    )
    alqari_validation_min_score = fields.Float(
        string="Min Pass Score",
        config_parameter="alqari.validation_min_score",
        help="Optional minimum validation score (0–100). Leave empty to skip score checks.",
    )
    alqari_validation_fail_on_warning = fields.Boolean(
        string="Fail on Warnings",
        config_parameter="alqari.validation_fail_on_warning",
        default=False,
    )
    alqari_default_run_human_review = fields.Boolean(
        string="Human Review by Default",
        config_parameter="alqari.default_run_human_review",
        default=False,
    )
    alqari_human_review_trigger = fields.Selection(
        [
            ("always", "Always"),
            ("validation_fail", "When validation fails (API result)"),
        ],
        string="Human Review Trigger",
        config_parameter="alqari.human_review_trigger",
        default="validation_fail",
    )
    alqari_review_assignee_email = fields.Char(
        string="Reviewer Email",
        config_parameter="alqari.review_assignee_email",
        help="Email of the Al-Qari reviewer who receives the review notification.",
    )
    alqari_review_instructions = fields.Text(
        string="Review Instructions",
        help="Instructions shown to the reviewer in Al-Qari and in the notification email.",
    )
    alqari_review_send_email = fields.Boolean(
        string="Send Review Email",
        config_parameter="alqari.review_send_email",
        default=True,
    )

    @staticmethod
    def _lines_to_csv(lines):
        return ", ".join(line.name.strip() for line in lines if line.name and line.name.strip())

    @staticmethod
    def _line_commands_from_csv(csv_value):
        helper = None
        names = [part.strip() for part in (csv_value or "").split(",") if part.strip()]
        return [(0, 0, {"name": name, "sequence": (index + 1) * 10}) for index, name in enumerate(names)]

    def get_values(self):
        res = super().get_values()
        icp = self.env["ir.config_parameter"].sudo()
        res["alqari_validation_rules"] = icp.get_param("alqari.validation_rules", "") or ""
        res["alqari_review_instructions"] = icp.get_param("alqari.review_instructions", "") or ""
        res["alqari_extract_field_line_ids"] = self._line_commands_from_csv(
            res.get("alqari_default_extract_fields") or DEFAULT_EXTRACT_FIELDS
        )
        res["alqari_category_line_ids"] = self._line_commands_from_csv(
            res.get("alqari_default_classify_categories") or DEFAULT_CATEGORIES
        )
        res["alqari_required_field_line_ids"] = self._line_commands_from_csv(
            res.get("alqari_validation_required_fields") or DEFAULT_EXTRACT_FIELDS
        )
        return res

    def set_values(self):
        for record in self:
            record.alqari_default_extract_fields = record._lines_to_csv(record.alqari_extract_field_line_ids)
            record.alqari_default_classify_categories = record._lines_to_csv(record.alqari_category_line_ids)
            record.alqari_validation_required_fields = record._lines_to_csv(record.alqari_required_field_line_ids)
        super().set_values()
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("alqari.validation_rules", self.alqari_validation_rules or "")
        icp.set_param("alqari.review_instructions", self.alqari_review_instructions or "")

    def action_alqari_test_connection(self):
        self.ensure_one()
        try:
            client = AlQariClient(
                base_url=self.alqari_api_base_url,
                api_key=self.alqari_api_key or "",
            )
            client.test_connection()
        except UserError as exc:
            raise UserError(_("Connection test failed: %s") % exc) from exc
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Al-Qari"),
                "message": _("Connection successful. API URL is reachable and key format looks valid."),
                "type": "success",
                "sticky": False,
            },
        }
