from odoo import fields, models


class AlQariProcessWizardLine(models.TransientModel):
    _name = "alqari.process.wizard.line"
    _description = "Al-Qari Process Wizard Line"
    _order = "sequence, id"

    wizard_id = fields.Many2one(
        "alqari.process.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )
    line_type = fields.Selection(
        [
            ("extract", "Extract Field"),
            ("category", "Category"),
            ("required", "Required Field"),
        ],
        required=True,
        index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Name", required=True)
