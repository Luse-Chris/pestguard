# -- coding: utf-8 --
import io
import base64
import logging

import qrcode

from odoo.tools.image import image_data_uri
from odoo import models, fields, api
from odoo.exceptions import UserError

from .vfd_receipt import RECEIPT_STATE

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'
    tra_receipt_id = fields.Many2one('vfd.receipt', 'TRA receipt', copy=False)
    qr_code = fields.Char("Qrcode",related="tra_receipt_id.qr_code",copy=False)
    rctv_num = fields.Char("Qrcode",related="tra_receipt_id.rctv_num",copy=False)
    tra_receipt_state = fields.Selection(string="Receipt State",related="tra_receipt_id.state",copy=False)

    def action_open_tra_receipt(self):
        self.ensure_one()
        return {
            'name': self.tra_receipt_id.number,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'vfd.receipt',
            'res_id': self.tra_receipt_id.id
        }
    def action_create_tra_receipt(self):
        try:
            for record in self:
                if not record.tra_receipt_id  and record.state == "posted" and record.move_type == "out_invoice":
                   receipt = self.env["vfd.receipt"].sudo().create_receipt_from_invoice(record)
                   receipt.action_post_receipt()
                   if receipt:
                      record.tra_receipt_id = receipt
        except Exception as e:
            _logger.exception(e)
            raise UserError(str(e))
    def build_qr_code_uri(self, content):
        qr_code = qrcode.QRCode(version=4, box_size=4, border=1)
        qr_code.add_data(content)
        qr_code.make(fit=True)
        qr_img = qr_code.make_image()
        buffered = io.BytesIO()
        qr_img.save(buffered, format="PNG")
        res = image_data_uri(base64.b64encode(buffered.getvalue()))
        return res
