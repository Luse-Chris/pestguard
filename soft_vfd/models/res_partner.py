# -*- coding: utf-8 -*-
import re
import logging

from odoo.exceptions import ValidationError
from odoo import models, fields, api

_logger = logging.getLogger('__name__')


class ResPartner(models.Model):
    _inherit = 'res.partner'
    tin = fields.Char(string='TIN #', copy=False)
    vrn = fields.Char(string='VRN #', copy=False)
    nida = fields.Char(string='NIDA ID #', copy=False)
    passport = fields.Char(string='Passport #', copy=False)
    voters_number = fields.Char(string='Voters Number', copy=False)
    driving_license = fields.Char(string='Driving license', copy=False)
    id_type = fields.Selection(
        [('1', 'TIN'),
         ('2', 'Driving License'),
         ('3', 'Voters Number'),
         ('4', 'Passport'),
         ('5', 'National Identity(NIDA)'),
         ('6', 'NIL (No ID)')], string='ID Type', copy=False)

    @api.onchange('tin')
    def validate_tin(self):
        if self.tin:
            if not re.match("^(?:\d{3}-){2}\d{3}$", self.tin):
                raise ValidationError('Invalid Tin Number Format (ex. xxx-xxx-xxx)')

    @api.onchange('vrn')
    def validate_vrn(self):
        if self.vrn:
            if not re.match("\d{8}[A-Z]$", self.vrn):
                raise ValidationError('Invalid VRN Format (ex. 12345678G)')

    @api.onchange('voters_number')
    def validate_voters_number(self):
        if self.voters_number:
            if not re.match("T-(?:\d{4}-){2}\d{3}-\d$", self.voters_number):
                raise ValidationError('Invalid Voter Number Format (ex. T-2000-7659-212-4)')

    @api.onchange('nida')
    def validate_nida(self):
        if self.nida:
            if not re.match("([12]\d{3}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])-\d{5}-\d{5}-\d{2}$)", self.nida):
                raise ValidationError(
                    'Invalid National Identification Number(NID) Format (ex. 19201220-12345-00001-12)')
