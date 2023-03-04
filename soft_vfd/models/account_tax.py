from odoo import models, fields, api

class AccountTax(models.Model):
    _inherit = "account.tax"
    tra_tax_code = fields.Selection(
        [
            ("1", "Standard Rate (18%)"),
            ("2", "Special Rate (0%)"),
            ("3", "Zero rated (0%)"),
            ("4", "Special Relief (0%)"),
            ("5", "Exempt (0%)"),
        ],
        string=" TRA tax code",
        copy=False,
    )
