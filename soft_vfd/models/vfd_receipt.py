# -*- coding: utf-8 -*-
import re
import html
import logging
from datetime import datetime

import pytz
from requests.exceptions import HTTPError

from odoo import api, fields, models
from odoo.tools.float_utils import float_repr
from odoo.exceptions import UserError

from . import exceptions

_logger = logging.getLogger(__name__)

def get_tax_line(taxes):
    if len(taxes) != 1:
        raise UserError("line must have at least one tax")
    if not taxes[0].tra_tax_code:
        raise UserError("TRA tax code is required in taxes")
    return int(taxes[0].tra_tax_code)


def get_customer_id(partner):
    if (partner.company_type == "company" and partner.tin) or partner.id_type == "1":
        # return [1, partner.tin.replace("-", "")]
        return [1, partner.tin]
    if partner.id_type == "2":
        return [2, partner.driving_license]
    if partner.id_type == "3":
        return [3, partner.voters_number]
    if partner.id_type == "4":
        return [4, partner.passport]
    if partner.id_type == "5":
        return [5, partner.nida]
    return [6, ""]

RECEIPT_STATE = [
            ("outgoing", "In Queue"),
            ("submitted", "Submitted"),
            ("posted", "Posted"),
            ("error", "Error"),
            ("cancelled", "Cancelled"),
]

class VfdReceipt(models.Model):
    _name = "vfd.receipt"
    _description = "TRA Receipts"
    _rec_name = "number"
    _order = "id DESC"
    _check_company_auto = True
    _sql_constraints = [
        ("order_id_uniq", "unique (order_id)", "Pos Order must be unique!"),
        ("invoice_id_uniq", "unique (invoice_id)", "Invoice  must be unique!"),
    ]  

    number = fields.Char("Number", default="New")
    order_id = fields.Many2one("pos.order", "Pos Order", check_company=True)
    invoice_id = fields.Many2one("account.move", "Invoice", check_company=True)
    date = fields.Date("Posted Date", help="Date of Issue ")
    time = fields.Char("Posted Time", help="Time of the issue")
    tin = fields.Char("TIN", help="TAX identification number of the business owner")
    reg_id = fields.Char(
        "Registration ID",
        help="This is a unique ID issued to a virtual device (Taxpayer Billing "
        "System) upon a successful registration. User should not be able to "
        "program REGID, it should only be received from TRA server.",
        required=True
    )
    efd_serial = fields.Char(
        "EFD Serial",
        help="This is the serial number assigned to the virtual device (Taxpayer "
        "Billing System) also as known as CERTKEY. This number is composed of "
        "two digits that represent the manufacturer code followed by two "
        "letters representing the Tanzania country code and followed by the "
        "serial number of the production. This information will be provided by "
        "TRA",
        required=True
    )
    cust_id_type = fields.Integer(
        "Customer ID TYPE",
        help="Buyer Used ID type. This can be one of the following "
        "1=TIN 2=Driving License 3=Voters Number 4=Passport 5=NID "
        "(National Identity) 6=NIL (If there is no ID)",
        required=True
    )
    cust_id = fields.Char(
        "Customer ID", help="Identification Number corresponding to the type chosen"
    )
    cust_name = fields.Char("Customer Name", help="Name of the Buyer")
    mobile_num = fields.Char("Mobile Num", help="Buyer’s Mobile Number")
    rct_num = fields.Char(
        "RCTNUM",
        help="This represent receipt/invoice number of each transaction that is unique for "
        "every transaction. RCTNUM starts with 1 and continue with sequence "
        "throughout. It will keep incrementing for every transaction. RCTNUM will be "
        "equal to GC where this is a global counter",
        # required=True
    )
    gc = fields.Integer(
        "GC",
        help="GC is a global counter of the receipts/invoice issued from day one and shall keep "
        "incrementing throughout the life of the VFD",
        #  required=True,
         index=True
    )
    dc = fields.Integer(
        "DC",
        help="DC is the Daily Counter and is a sequence of receipts/ invoices issued for the "
        "day. DC will reset to 1 the following day up to the last receipt/ invoiceissued",
        # required=True,
        index=True
    )
    z_num = fields.Char(
        "ZNUM",
        help="ZNUM for VFDs will be a number in format of (YYYYMMDD) e.g. 20190626 and this "
        "will change on Daily Basis i.e. ZNUM for Today: 20191018, ZNUM for yesterday: "
        "20191017, ZNUM for tomorrow: 20191019. ZNUM is date of transaction written in "
        "number format.",
        #  required=True
    )
    reference = fields.Char("Reference",)
    line_ids = fields.One2many(
        "vfd.receipt.line",
        "receipt_id",
        string="Receipt Lines",
        copy=True,
        readonly=True,
        check_company=True
    )
    rctv_num = fields.Char(
        "RCTVNUM",
        help="A receipt/invoice verification number composes of RECEIPTCODE and GC i.e. "
        "GC appended to RECEIPTCODE. During registration, a VFD will be provided "
        "with RECEIPTCODE",
        # required=True
    )
    total_tax_excl = fields.Float("TOTALTAXEXCL", compute="_compute_totals")
    total_tax_incl = fields.Float(
        "TOTALTAXINCL",
        help="Total amount of all the items inclusive of taxes",
        compute="_compute_totals",
        store=True,
    )
    discount = fields.Float(
        "DISCOUNT",
        default=0.00,
        help="Amount discounted from the total of all the items exclusive of tax",
        compute="_compute_totals",
        store=True,
    )
    payment_type = fields.Selection(
        selection=[
            ("CASH", "CASH"),
            ("CHEQUE", "CHEQUE"),
            ("CCARD", "CCARD"),
            ("EMONEY", "EMONEY"),
            ("INVOICE", "INVOICE")
        ],
        string="Payment Type",
        default="CASH",
        required=True
    )
    pmt_amount = fields.Float(
        "PMTAMOUNT", default=0.00, help="Payment amount based on payment type used",
    )
    net_amt_a = fields.Float(
        string="Net Amount A-18.00",default=0.0
    )
    net_amt_b = fields.Float(
        string="Net Amount B-0.00",default=0.0
    )
    net_amt_c = fields.Float(
        string="Net Amount C-0.00",default=0.0
    )
    net_amt_d = fields.Float(
        string="Net Amount D-0.00", default=0.0
    )
    net_amt_e = fields.Float(
        string="Net Amount E-0.00",default=0.0
    )

    vat_amt_a = fields.Float(
        string="Tax Amount A-18.00",default=0.0
    )
    vat_amt_b = fields.Float(
        string="Tax Amount B-0.00", default=0.0
    )
    vat_amt_c = fields.Float(
        string="Tax Amount C-0.00",default=0.0
    )
    vat_amt_d = fields.Float(
        string="TAX Amount D-0.00",default=0.0
    )
    vat_amt_e = fields.Float(
        string="TAX Amount E-0.00",default=0.0
    )
    qr_code = fields.Char("Qrcode")
    state = fields.Selection(
        RECEIPT_STATE,
        "Invoice/Receipt Status",
        readonly=True,
        copy=False,
        default="outgoing",
        required=True,
    )

    error_code = fields.Selection(
        [
            ("tax_error", "Tax Error"),
            ("unhandled_exception", "Unhandled Exceptions"),
            ("invalid_signature", "Invalid Signature"),
            ("failed_to_queue", "Failed to queue"),
            ("invalid_routing_key_header", "Invalid routing key header"),
            ("invalid_token_bearer", "Invalid token Bearer"),
            ("xsd_validation_failure", "XSD validation failure"),
            ("timeout_error", "Timeout Error"),
            ("http_error", "Http Error"),
            ("401_authorization_denied","401 Authorization denied")
        ]
    )
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company
    )
    error_message = fields.Char("Error Message")
    tra_response_date = fields.Date("TRA Response Date")
    tra_response_time = fields.Char("TRA Response Time")
     
    @api.depends(
        "line_ids.discount",
        "line_ids.price_unit",
        "line_ids.sub_total",
        "line_ids.tax_amt",
        "line_ids.price_total",
    )
    def _compute_totals(self):
        for record in self:
            record = record.with_company(record.company_id)
            discount = 0.0
            price_total = 0.0
            sub_total = 0.0
            for line in record.line_ids:
                discount += line.discount / 100 * line.price_unit
                price_total += line.price_total
                sub_total += line.sub_total
            record.total_tax_excl = sub_total
            record.total_tax_incl = price_total
            record.pmt_amount = price_total
            record.discount = discount

    def action_post_receipt(self):
        try:
            for record in self:
                if record.state not  in ["posted","cancelled"]:
                   record = record.with_company(record.company_id)
                   record._post_receipt(raise_exception=True)
        except Exception as e:
            raise UserError(str(e))
           
    def create_receipt_from_order(self, order):
        """
        Create vfd receipt from pos order

        Args:
            order (record): Pos order

        """
        fd = self.env["vfd.service"]._get_virtual_device()
        now = datetime.now(
                tz=pytz.timezone("Africa/Dar_es_salaam")
        )  # converts datetime to Tanzania time zone
        line_values = []
        customer_id_type = 6 # No customer ID
        customer_id = None
        if order.partner_id:
            customer_id_type, customer_id = get_customer_id(order.partner_id)
        for line in order.lines:
            line_values.append((0,0,{
                "desc": line.full_product_name or line.name,
                "qty": int(line.qty),
                "tax_code": get_tax_line(line.tax_ids),
                "amt": line.price_subtotal_incl / line.qty,
                "tax_code": get_tax_line(line.tax_ids),
                "tax_amt": line.price_subtotal_incl - line.price_subtotal,
                "sub_total": line.price_subtotal,
                "price_total": line.price_subtotal_incl,
                "discount": line.discount,
                "price_unit": line.price_unit,
                "company_id": self.env.company.id
            },))

        return super(VfdReceipt, self).create(
                [
                    {
                        "number": self.env["ir.sequence"].next_by_code("vfd.receipt"),
                        "order_id": order.id,
                        "reference": order.name,
                        "date": now.strftime("%Y-%m-%d"),
                        "time": now.strftime("%H:%M:%S"),
                        "reg_id": fd.reg_id,
                        "efd_serial": fd.efd_serial,
                        "cust_id_type": customer_id_type,
                        "cust_id": customer_id,
                        "cust_name": order.partner_id.name if order.partner_id else None,
                        "mobile_num": None,
                        "line_ids": line_values,
                        "payment_type": "CASH",
                        "company_id": self.env.company.id,
                    }
                ]
            )
    def create_receipt_from_invoice(self, invoice):
        """
        Create vfd receipt from invoice

        Args:
            invoice (record): Odoo invoice

        """
        fd = self.env["vfd.service"]._get_virtual_device()
        now = datetime.now(
            tz=pytz.timezone("Africa/Dar_es_salaam")
        )  # converts datetime to Tanzania time zone
        time = now.strftime("%H:%M:%S") 
        line_values = []
        customer_id_type = 6 # No customer ID
        customer_id = None
        customer_id_type, customer_id = get_customer_id(invoice.partner_id)
        for line in invoice.line_ids:
            if line.display_type == "product":
                line_values.append((0,0,{
                    "desc": line.name,
                    "qty": int(line.quantity),
                    "amt": line.price_total / line.quantity,
                    "tax_code": get_tax_line(line.tax_ids),
                    "tax_amt": line.price_total - line.price_subtotal,
                    "sub_total": line.price_subtotal,
                    "price_total": line.price_total,
                    "discount": line.discount,
                    "price_unit": line.price_unit,
                    "company_id": self.env.company.id
                },))
        return super(VfdReceipt, self).create([{
                "number": self.env["ir.sequence"].next_by_code("vfd.receipt"),
                "invoice_id": invoice.id,
                "reference": invoice.name,
                "date": now.strftime("%Y-%m-%d"),
                "time": time,
                "tin": fd.tin.replace("-", ""),
                "reg_id": fd.reg_id,
                "efd_serial": fd.efd_serial,
                "cust_id_type": customer_id_type,
                "cust_id": customer_id,
                "cust_name": invoice.partner_id.name if invoice.partner_id else None,
                "mobile_num": None,
                "line_ids": line_values,
                "payment_type": "INVOICE",
                "company_id": self.env.company.id,
            }])
        
    def _post_receipt(self, raise_exception=False):
        res = {}
        try:
            fd = self.env["vfd.service"]._get_virtual_device()
            if not fd:
                raise Exception('No active Virtual Fiscal device found for this company ')
            receipt_dict = self.to_dict()
            res = fd.post_receipt(receipt_dict)
            if res["state"] == "posted":
                self.tra_response_date = res.get("tra_response_date")
                self.tra_response_time = res.get("tra_response_time")
                self.state = "posted"
            elif res["state"] == "error":
                self.tra_response_date = res.get("tra_response_date")
                self.tra_response_time = res.get("tra_response_time")
                self.state = "error"
            else:
              self.write({
                 "state": "submitted",
                 "error_code": "",
                 "gc": res.get("gc"),
                 "dc": res.get("dc"),
                 "z_num": res.get("z_num"),
                 "rct_num": res.get("rct_num"),
                 "rctv_num": res.get("rctv_num"),
                 "qr_code": res.get("qr_code"),
                 "net_amt_a": res.get("net_amt_a"),
                 "net_amt_b": res.get("net_amt_b"),
                 "net_amt_c": res.get("net_amt_c"),
                 "net_amt_d": res.get("net_amt_d"),
                 "net_amt_e": res.get("net_amt_e"),
                 "vat_amt_a": res.get("vat_amt_a"),
                 "vat_amt_b": res.get("vat_amt_b"),
                 "vat_amt_c": res.get("vat_amt_c"),
                 "vat_amt_d": res.get("vat_amt_d"),
                "vat_amt_e": res.get("vat_amt_e")
            })
        except exceptions.VFDError as vfd_error:
            _logger.exception(vfd_error)
            if raise_exception:
                raise
            error = {"error_code": vfd_error.error_code,"error_message": vfd_error.error_message}
            self._postprocess_sent_receipt(error, res)
        except HTTPError as http_error:
            _logger.exception(http_error.response.text)
            if raise_exception:
                raise
            self._postprocess_sent_receipt({"error_code": "http_error", "error_message": None})
        except Exception as e:
            _logger.exception(e)
            if raise_exception:
                raise
            error = {"error_code": "unhandled_exception", "error_message": str(e)}
            self._postprocess_sent_receipt(error)

    def _process_receipt_posted_event(self, data):
        record = self.search([("reference", "=", data.get("reference"))], limit=1)
        if record and data["type"] == "receipt_posted":
           record.tra_response_date = data.get("tra_response_date")
           record.tra_response_time = data.get("tra_response_time")
           if data.get("state") == "posted":
              record.state = "posted"
           elif data.get("state") == "error":
              record.error_code = data.get("error_code")
              record.state =  "error"
           else:
             _logger.info(f"Unhandled status code {data.get('state')}")
        else:
            _logger.info(f"Receipt with reference  {data.get('reference')} not found")



    def _postprocess_sent_receipt(self, error):
        self.write(
                {
                    "error_code": error["error_code"],
                    "error_message": error["error_message"],
                    "state": "error",
                }
            )
    def _cron_action_post_receipt(self):
        pending_receipts = self.search([("state", "in", ["outgoing","submitted","error"])])
        for receipt in pending_receipts:
            receipt = receipt.with_company(receipt.company_id)
            receipt._post_receipt()

    def to_dict(self):
        return {
                "date": str(self.date),
                "time": self.time,
                "tin": self.tin,
                "cust_id_type": self.cust_id_type,
                "cust_id": self.cust_id,
                "cust_name": self.cust_name,
                "mobile_num": self.mobile_num,
                "reference": self.reference ,
                "line_ids": [
                              {
                                "desc": line.desc,
                                "qty": line.qty,
                                "tax_code": line.tax_code,
                                "amt": float_repr(line.price_unit,2),
                                "tax_amt": float_repr(line.tax_amt,2),
                                "discount": float_repr(line.discount, 2),
                                "sub_total": float_repr(line.sub_total, 2),
                                "price_total": float_repr(line.price_total, 2)
                            } 
                            for line in self.line_ids],
                "total_tax_excl": float_repr(self.total_tax_excl, 2),
                "total_tax_incl": float_repr(self.total_tax_incl, 2),
                "discount": float_repr(self.discount, 2),
                "payment_type": self.payment_type
            }
   
    
class VfdReceiptLine(models.Model):
    _name = "vfd.receipt.line"
    _description = "VFD Receipt Line"
    _check_company_auto = True
    receipt_id = fields.Many2one(
        "vfd.receipt",
        string="TRA Receipt",
        index=True,
        required=True,
        readonly=True,
        auto_join=True,
        check_company=True,
        ondelete="cascade",
        help="The receipt of this entry line.",
    )
    desc = fields.Char(
        "DESC", help="Name of items can either be standard or entered by user"
    )
    qty = fields.Integer("QTY", help="Quantity")
    tax_code = fields.Integer(
        "TAXCODE",
        help="Applicable tax on the item 1= Standard Rate (18%) 2= Special Rate (0%) "
        "3= Zero rated (0%) 4= Special Relief (0%) 5= Exempt (0%)",
    )
    amt = fields.Float(
        "AMT", default=0.00,digits=(16, 2), help="Total Amount Inclusive of taxes divide by quantity"
    )
    sub_total = fields.Float(
        "Sub Total", default=0.00,digits=(16, 2), help="Total Amount Inclusive of taxes"
    )
    price_total = fields.Float(
        "Price Total", default=0.00,digits=(16, 2), help="Total Price Tax Inclusive"
    )
    tax_amt = fields.Float("Tax amount", default=0.00,digits=(16, 2), help="Total Tax Amount")
    discount = fields.Float("Discount", default=0.00,digits=(16, 2), help="Discountt")
    price_unit = fields.Float("Price Unit",digits=(16, 2), default=0.00)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company
    )