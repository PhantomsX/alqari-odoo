from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .alqari_field_condition import VALIDATION_CHECKS, VALIDATION_NO_COMPARE


class AlQariValidationRule(models.Model):
    _name = "alqari.validation.rule"
    _description = "Al-Qari Field Validation Rule"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    field_name = fields.Char(
        required=True,
        string="Field",
        help="Extracted field name to validate, e.g. passport_number or total.",
    )
    severity = fields.Selection(
        [("error", "Error"), ("warning", "Warning")],
        default="error",
        required=True,
        string="Severity",
    )
    check_type = fields.Selection(
        VALIDATION_CHECKS,
        default="required",
        required=True,
        string="Check",
    )
    compare_value = fields.Char(
        string="Compare Value",
        help="Number or text to compare against. Not used for Required.",
    )
    message = fields.Char(
        string="Error Message",
        translate=True,
        help="Message shown when this rule is not satisfied.",
    )

    @api.constrains("check_type", "compare_value")
    def _check_compare_value(self):
        for rule in self:
            if rule.check_type not in VALIDATION_NO_COMPARE and not (rule.compare_value or "").strip():
                raise ValidationError(
                    _("Rule '%s' requires a compare value for check '%s'.")
                    % (rule.name, rule.check_type)
                )

    def to_api_rule(self) -> dict:
        self.ensure_one()
        payload = {
            "field": self.field_name.strip(),
            "type": self.check_type,
            "severity": self.severity or "error",
            "message": self.message
            or _("Validation failed for %(field)s", field=self.field_name),
        }
        if self.check_type not in VALIDATION_NO_COMPARE:
            payload["value"] = self.compare_value
        return payload

    @api.model
    def get_active_api_rules(self) -> list[dict]:
        return [rule.to_api_rule() for rule in self.search([("active", "=", True)])]
