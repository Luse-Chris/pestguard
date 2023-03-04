import requests
import io
import qrcode
import base64
from odoo import api, models,_ 
from odoo.tools.image import image_data_uri
from  ..models.utils import format_currency
from ..models.pos_order import TAX_CODE_MAP

class TraVFDReceipt(models.AbstractModel):
    _name = 'report.pos_tra_vfd.vfd_receipt'
    _description = "VFD Receipt Report PDF"
    def build_qr_code_uri(self, content):
        qr_code = qrcode.QRCode(version=4, box_size=4, border=1)
        qr_code.add_data(content)
        qr_code.make(fit=True)
        qr_img = qr_code.make_image()
        buffered = io.BytesIO()
        qr_img.save(buffered, format="PNG")
        res = image_data_uri(base64.b64encode(buffered.getvalue()))
        return res

    def _get_report_values(self, docids, data=None):
        fd = self.env["pos.tra.service"]._get_virtual_device()
        return {
              'docs': self.env["account.move"].browse(docids),
              'doc_model': 'account.move',
              'data': data,
              'fd':fd,
              'format_currency': format_currency,
              'build_qr_code_uri': self.build_qr_code_uri,
              'TAX_CODE_MAP': TAX_CODE_MAP
        }
    