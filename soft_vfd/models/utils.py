from odoo.exceptions import ValidationError

def validate_line_tax(self, tax_ids):
    if len(tax_ids) != 1:
        raise ValidationError(f"Order line must have only one tax found {len(tax_ids)}")
    tax = self.env["account.tax"].browse(tax_ids[0])
    if not tax.tra_tax_code:
        raise ValidationError("TRA tax code is required in taxes")
    return True