import logging
from datetime import datetime,timedelta

import pytz
from dateutil import parser

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class ZReport(models.Model):
    _name = "vfd.zreport"
    _description = "Z Report"
    _order = "id DESC"
    _rec_name = "z_number"
    _check_company_auto = True
    z_number = fields.Char(string="Z number")
    _sql_constraints = [("znumber_uniq", "unique(z_number, company_id)", "Znumber  must be unique per company!")]

    discounts = fields.Float(
        string="Discount",
        default=0.0,
        help="Total discounts issued",
    )
    corrections = fields.Float(string="Corrections", default=0)
    surcharges = fields.Float(string="Supercharges", default=0)
    tickets_void = fields.Float(
        string="Tickets Void",
        default=0,
        help="Total number of tickets voided/cancelled in "
        "the system and therefore not sent to tra",
    )
    tickets_fiscal = fields.Integer(
        string="Tickets Fiscal", default=0, store=True
    )
    tickets_non_fiscal = fields.Float(string="Tickets Non Fiscal", default=0)
    # Net amount
    net_amt_a = fields.Float(string="Net Amount A-18.00")
    net_amt_b = fields.Float(string="Net Amount B-0.00")
    net_amt_c = fields.Float(string="Net Amount C-0.00")
    net_amt_d = fields.Float(string="Net Amount D-0.00")
    net_amt_e = fields.Float(string="Net Amount E-0.00")
    # Taxes
    vat_amt_a = fields.Float(string="Tax Amount A-18.00")
    vat_amt_b = fields.Float(string="Tax Amount B-0.00")
    vat_amt_c = fields.Float(string="Tax Amount C-0.00")
    vat_amt_d = fields.Float(string="TAX Amount D-0.00")
    vat_amt_e = fields.Float(string="TAX Amount E-0.00")
    daily_total_amount = fields.Float(string="Daily Total Amount",help="sum of all sales for the day",)
    gross = fields.Float(string="Gross",help="cumulative sales from day one to present")
    cash_total = fields.Float(string="Cash Total",digits=(16,2), default=0.0)
    cheque_total = fields.Float(string="Cheque Total",digits=(16,2), default=0.0)
    cc_total = fields.Float(string="CCARD Total",digits=(16,2), default=0.0)
    invoice_total = fields.Float(string="Invoice Total", default=0)
    emoney_total = fields.Float(string="Emoney Total", default=0.0)
    vat_change_num = fields.Integer(string="VAT Change Number", default=0)
    head_change_num = fields.Integer(string="Head Change Number", default=0)
    date_issued = fields.Date(string="Date Issued")
    posted_date = fields.Datetime(string="Posted Date")
    time_issued = fields.Char(string="Time Issued")

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company
    )

    def action_open_tra_receipt(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("soft_vfd.soft_vfd_receipt_action")
        action['domain'] = [("z_num", "=",self.z_number)]
        action['context'] = {'search_default_outgoing': 0}
        return action
    
    def action_post_zreport(self):
        try:
            self = self.with_company(self.company_id)
            self._post_zreport()
        except Exception as e:
            raise UserError(str(e))
    def _cron_fetch_zreport(self):
        for fd in self.env["tra.vfd"].search([]):
            try:
                zreports = fd.fetch_zreports()
                for zreport in zreports:
                    if not self.search([("z_number", "=", zreport["z_number"])], limit=1):
                       self.create({
                           "z_number": zreport["z_number"],
                           "discounts": zreport["discounts"],
                           "corrections": zreport["corrections"],
                           "surcharges": zreport["surcharges"],
                           "tickets_void": zreport["tickets_void"],
                           "tickets_fiscal": zreport["tickets_fiscal"],
                           "tickets_non_fiscal": zreport["tickets_non_fiscal"],
                           "net_amt_a": zreport["net_amt_a"],
                           "net_amt_b": zreport["net_amt_b"],
                           "net_amt_c": zreport["net_amt_c"],
                           "net_amt_d": zreport["net_amt_d"],
                           "net_amt_e": zreport["net_amt_e"],
                           "vat_amt_a": zreport["vat_amt_a"],
                           "vat_amt_b": zreport["vat_amt_b"],
                           "vat_amt_c": zreport["vat_amt_c"],
                           "vat_amt_d": zreport["vat_amt_d"],
                           "vat_amt_e": zreport["vat_amt_e"],
                           "daily_total_amount": zreport["daily_total_amount"],
                           "gross": zreport["gross"],
                           "cash_total": zreport["cash_total"],
                           "cheque_total": zreport["cheque_total"],
                           "cc_total": zreport["cc_total"],
                           "invoice_total": zreport["invoice_total"],
                           "emoney_total": zreport["emoney_total"],
                           "vat_change_num": zreport["vat_change_num"],
                           "head_change_num": zreport["head_change_num"],
                           "date_issued": zreport["date_issued"],
                           "posted_date": parser.parse(zreport["posted_date"]).strftime("%Y-%m-%d %H:%M:%S"),
                           "time_issued": zreport["time_issued"],
                           "company_id": fd.company_id.id
                       })
                if zreports:
                   fd.last_zreport_date = fields.Date.today()
            except Exception as e:
                _logger.exception(e)
        
