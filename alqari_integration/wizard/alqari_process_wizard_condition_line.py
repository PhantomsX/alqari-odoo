from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..models.alqari_field_condition import VALIDATION_CHECKS, VALIDATION_NO_COMPARE


class AlQariProcessWizardValidationLine(models.TransientModel):
    _name = "alqari.process.wizard.validation.line"
    _description = "Al-Qari Process Wizard Validation Check"
    _order = "sequence, id"

    wizard_id = fields.Many2one("alqari.process.wizard", required=True, ondelete="cascade")
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
                raise ValidationError("Compare value is required for this check.")
