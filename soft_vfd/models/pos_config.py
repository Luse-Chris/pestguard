from odoo import models, fields, api
from odoo.exceptions import UserError

class PosConfig(models.Model):
    _inherit = "pos.config"
    is_vfd_enabled = fields.Boolean("VFD")
    @api.onchange("is_vfd_enabled")
    def check_vfd(self):
        if self.is_vfd_enabled:
            fd = self.env["vfd.service"]._get_virtual_device()
            if not fd:
               raise UserError("No Virtual Fiscal Device found for this company\nRegister Virtual Fiscal Device first.")