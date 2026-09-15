"""Validation rule line models — serialize config for the Al-Qari API only.

All validation and routing decisions run on Al-Qari servers. Odoo does not
evaluate rules locally.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

VALIDATION_CHECKS = [
    ("required", "Required"),
    ("equals", "Equals"),
    ("greater_than", "Greater than"),
    ("greater_than_or_equal", "Greater than or equal"),
    ("less_than", "Less than"),
    ("less_than_or_equal", "Less than or equal"),
    ("contains", "Contains"),
]

VALIDATION_NO_COMPARE = {"required"}


def validation_checks_to_api_rules(condition_records) -> list[dict]:
    """Build /services/integration/validate rules payload (no local evaluation)."""
    rules = []
    for line in condition_records:
        payload = {
            "field": line.field_name.strip(),
            "type": line.check_type,
            "severity": line.severity or "error",
            "message": line.message
            or _("Validation failed for %(field)s", field=line.field_name),
        }
        if line.check_type not in VALIDATION_NO_COMPARE:
            payload["value"] = line.compare_value
        rules.append(payload)
    return rules


class AlQariDocumentConditionLine(models.Model):
    _name = "alqari.document.condition.line"
    _description = "Al-Qari Document Validation Check Line"
    _order = "sequence, id"

    document_id = fields.Many2one("alqari.document", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    field_name = fields.Char(required=True, string="Field")
    check_type = fields.Selection(VALIDATION_CHECKS, required=True, default="required", string="Check")
    compare_value = fields.Char(string="Compare Value")
    severity = fields.Selection(
        [("error", "Error"), ("warning", "Warning")],
        default="error",
        string="Severity",
    )
    message = fields.Char(string="Message")

    @api.constrains("check_type", "compare_value")
    def _check_compare_value(self):
        for line in self:
            if line.check_type not in VALIDATION_NO_COMPARE and not (line.compare_value or "").strip():
                raise ValidationError(
                    _("Validation check on '%(field)s' requires a compare value.")
                    % {"field": line.field_name}
                )
