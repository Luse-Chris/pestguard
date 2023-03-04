import re
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class VirtualFiscalDevice(models.Model):
    _name = "vfd.vfd"
    _rec_name = "id"
    _check_company_auto = True
    _description = "Virtual Fiscal Device"
    _sql_constraints = [
        ("company_id_uniq", "unique (company_id)", "Company can't have multiple fiscal devices!"),
    ]

    # vfd credentials
    username = fields.Char("Username", help="Username to be used for Token Request")
    password = fields.Char("Password", help="Secret Key to be used for Token Request")
    access_token = fields.Char("Access token")
    token_exp_date = fields.Datetime("Expiration date")

    # Registration details
    reg_id = fields.Char("Registration ID", help="VFD System Registration Id")
    reg_name = fields.Char("Registration Name", help="Tax Payer Trading Name")
    uin = fields.Char(
        help="User identification number issued by TRA once Taxpayer has been registered in EFDMS"
    )
    efd_serial = fields.Char("EFD Serial", required=False)
    vrn = fields.Char("VRN", help="Vat Registration Number")
    tin = fields.Char(
        "Company Tin", help="Tax Identification Number of business owner", required=False
    )
    mobile = fields.Char("Mobile", help="Mobile/Telephone number")
    address = fields.Char("Address", help="Tax Payer’s Address")
    street = fields.Char("Street")
    city = fields.Char("City")
    region = fields.Char("Region", help="Tax Region")
    country = fields.Char("Country")
    gc = fields.Integer(
        "GC",
        default=1,
        help="GC is a global counter of the receipts/invoice issued from day one and shall keep "
        "incrementing. i.e. how many total receipts signed till date",
    )

    receipt_code = fields.Char(
        "Receipt Code",
        help="Also known as, RCTVCODE represents a unique code issued during "
        "registration.",
    )
    tax_office = fields.Char("Tax office", help="Tax Payer’s Tax Office")
    state = fields.Selection(
        [
            ("disabled", "Disabled"),
            ("dev", "Dev Mode"),
            ("prod", "Production Mode"),
        ],
        required=True,
        default="disabled",
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company
    )
    webhook_secret = fields.Char("Webhook Secret")
    last_zreport_date = fields.Date("Last Zreport Date")
    @api.depends("username", "password")
    def reset_access_token(self):
        for record in self:
            record.access_token = None
            record.token_exp_date = None
    def action_register(self):
        try:
            self = self.with_company(self.company_id)
            res = self.fetch_registration()
            self.write(
                {
                    "reg_id": res.get("reg_id"),
                    "uin": res.get("uin"),
                    "tin": res.get("tin"),
                    "vrn": res.get("vrn"),
                    "reg_name": res.get("reg_name"),
                    "receipt_code": res.get("receipt_code"),
                    "efd_serial": res.get("efd_serial"),
                    "tax_office": res.get("tax_office"),
                    "mobile": res.get("mobile"),
                    "address": res.get("address"),
                    "street": res.get("street"),
                    "city": res.get("city"),
                    "country": res.get("country"),
                    "region": res.get("region"),
                    "state": self.state,
                    "gc": res.get("gc"),
                }
            )
        except Exception as e:
            _logger.exception(e)
            raise UserError(str(e))
    def get_base_url(self):
        return self.env["vfd.service"]._get_base_url(self.state)
    def get_verification_url(self):
        return self.env["vfd.service"]._get_verification_url(self.state)
        
    def post_receipt(self, payload):
        return self.env["vfd.service"]._do_request("/receipts", data=payload, fd=self)

    def fetch_zreports(self):
        if self.last_zreport_date:
           return self.env["vfd.service"]._do_request(f"/zreports?since={self.last_zreport_date}",method="GET", fd=self)
        return self.env["vfd.service"]._do_request("/zreports",method="GET", fd=self)

    def fetch_registration(self):
        return self.env["vfd.service"]._do_request("/registration",method="GET", fd=self)

   