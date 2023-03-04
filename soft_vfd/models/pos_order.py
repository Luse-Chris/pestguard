# -*- coding: utf-8 -*-
import logging
import re

from odoo import models, fields, api
from odoo.tools.float_utils import float_repr
from odoo.exceptions import UserError, ValidationError

from .utils import validate_line_tax

_logger = logging.getLogger(__name__)

CUST_ID_TYPE_MAP = {
         1: 'TAXPAYER IDENTIFICATION NUMBER',
         2: 'DRIVING LICENSE',
         3: 'VOTERS NUMBER',
         4: 'PASSPORT',
         5: 'NATIONAL IDENTITY(NID)',
         6 : 'NIL'
}

TAX_CODE_MAP = {
    1: "A",
    2: "B",
    3: "C",
    4: "D",
    5: "E"
}
class PosOrder(models.Model):
    _inherit = "pos.order"
    tra_receipt_id = fields.Many2one('vfd.receipt', 'TRA receipt')
    tra_receipt_state = fields.Selection(string="Receipt State",related="tra_receipt_id.state")
    qr_code = fields.Char("Qrcode",related="tra_receipt_id.qr_code")
    # def _validate_orders(self, orders):
    #     # TODO we need to find away to validate currency
    #     # because TRA support only TSH

    #     for ui_order in orders:
    #         order = self._order_fields(ui_order["data"])
    #         lines = order.get("lines", [])
    #         lines = [] if isinstance(lines, bool) else lines
    #         for line in lines:
    #             self._validate_order_line(line[2])

    def _validate_order_line(self, line):
        tax_ids = line["tax_ids"][0][2]
        validate_line_tax(self, tax_ids)

    def action_open_tra_receipt(self):
        self.ensure_one()
        return {
            'name': self.tra_receipt_id.number,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tra.vfd.receipt',
            'res_id': self.tra_receipt_id.id
        }
    def action_pos_order_paid(self):
        order = super(PosOrder, self).action_pos_order_paid()
        pos_config = self.env["pos.config"].browse(self.session_id.config_id.id)
        if pos_config.is_vfd_enabled:
           try:
              if self.lines and self.amount_total > 0:
                 receipt = self.env["vfd.receipt"].sudo().create_receipt_from_order(self)
                 if receipt:
                    self.tra_receipt_id = receipt
                    receipt._post_receipt()
           except Exception as e:
            _logger.exception(e)
        return order

    def get_posted_receipt(self):
        self.ensure_one()
        fd = self.env["vfd.service"]._get_virtual_device()
        receipt = self.env["vfd.receipt"].search([("order_id","=", self.id),("state", "not in", ["outgoing", "cancelled"])],limit=1)
        if fd  and receipt.rct_num:
           receipt_dict = {
            # Company details
           "reg_name": fd.reg_name,
           "mobile": fd.mobile,
           "address": fd.address,
           "street": fd.street,
           "city": fd.city,
           "country": fd.country,
           "region": fd.region,
           "tax_office": fd.tax_office,
           "uin": fd.uin,
           "vrn": fd.vrn,
           "tin": fd.tin.replace("-", ""),
           "efd_serial": fd.efd_serial,
           # Customer details
           "cust_name": receipt.cust_name,
           "cust_vrn": receipt.order_id.partner_id.vrn,
           "cust_id": receipt.cust_id.replace("-","") if receipt.cust_id_type == 1 else receipt.cust_id,
           "cust_id_type": CUST_ID_TYPE_MAP.get(receipt.cust_id_type),
           "cust_mobile_num": receipt.mobile_num,
           
           # Receipt details
           "rct_num": receipt.rct_num,
           "rctv_num": receipt.rctv_num,
           "z_num": f"{receipt.dc}/{receipt.z_num}",
           "date": receipt.date,
           "time": receipt.time,
           "qrcode": receipt.qr_code,
           "lines": [{
                        "id": line.id,
                        "desc": line.desc,
                        "qty": line.qty,
                        "tax_code": TAX_CODE_MAP.get(line.tax_code),
                        "amt": float_repr(line.amt,2),
                    } for line in receipt.line_ids],
           "total_tax_excl": float_repr(receipt.total_tax_excl, 2),
           "vat_amt_a": float_repr(receipt.vat_amt_a,2),
           "vat_amt_b": float_repr(receipt.vat_amt_b,2),
           "vat_amt_c": float_repr(receipt.vat_amt_c,2),
           "vat_amt_d": float_repr(receipt.vat_amt_d,2),
           "vat_amt_e": float_repr(receipt.vat_amt_e,2),
           "total_tax":  float_repr(receipt.vat_amt_a +  receipt.vat_amt_b + receipt.vat_amt_c +receipt.vat_amt_d + receipt.vat_amt_e,2),
           "total_tax_incl": float_repr(receipt.total_tax_incl,2) }
           return receipt_dict
        return None

