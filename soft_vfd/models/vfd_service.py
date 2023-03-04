# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import datetime

import requests
from requests.exceptions import HTTPError, Timeout

from odoo import api, models,fields
from odoo.exceptions import UserError

from .exceptions import VFDValidationError, VFDAuthEror, VFDSubscriptionExpired, VFDInternalServerError

_logger = logging.getLogger(__name__)

TIMEOUT = 15

class VFDApi(models.AbstractModel):
    _name = "vfd.service"
    _description = "VFD API"

    def _get_virtual_device(self):
        fd = self.env["vfd.vfd"].search(
            [
             ('company_id','=', self.env.company.id),
             ('state','!=', "disabled"),
            ],limit=1)
        if fd:
           return fd
        raise UserError("No Active Fiscal Device found for the current company")

    @api.model
    def _get_base_url(self, environment):
        """TRA VFD URLS"""
        if environment == "prod":
            return "https://odoo-vfd.softnet.co.tz/api"
        # return "http://localhost:8000/api"
        return "https://odoo-vfd-test.softnet.co.tz/api"

    def _get_verification_url(self, environment):
        if  environment == "prod":
            return "https://verify.tra.go.tz"
        return "https://virtual.tra.go.tz/efdmsRctVerify"

    def _get_access_token(self, fd):
        if fd.token_exp_date and fd.access_token:
            now = fields.Datetime.now()
            if fd.token_exp_date > now:
               return fd.access_token
        try:
            res = self._generate_access_token(fd)
            fd.access_token = res["access_token"]
            fd.token_exp_date = fields.Datetime.now() + datetime.timedelta(seconds=res["expires_in"])
            return fd.access_token
        except Exception as e:
            _logger.exception(e)
            return None
    def _generate_access_token(self, fd):
        url = self._get_base_url(fd.state) + "/token" 
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "",
            "username": fd.username,
            "password": fd.password,
            "scope": "",
            "client_id": "",
            "client_secret": ""
        }
        res = requests.post(url, data=data, headers=headers, timeout=TIMEOUT)
        res.raise_for_status()
        res = res.json()
        return res
        
    def _do_request(self, uri,method="POST", headers=None, data=None, fd=None):
         try:
            fd = self._get_virtual_device() if not fd else fd
            url = self._get_base_url(fd.state) + uri
            access_token = self._get_access_token(fd)
            headers = {
               "Content-Type": "application/json",
               "Authorization": f"bearer {access_token}",
            }
            res = requests.request(method, url, headers=headers,json=data, timeout=TIMEOUT)
            res.raise_for_status()
            return res.json()
         except HTTPError as http_error:
             _logger.exception(http_error)
             if http_error.response.status_code == 401:
                raise VFDAuthEror(http_error.response.json())
             elif http_error.response.status_code == 403:
                raise VFDSubscriptionExpired(http_error.response.json())
             elif http_error.response.status_code == 422:
                raise VFDValidationError(http_error.response.json())
             elif http_error.response.status_code == 500:
                raise VFDInternalServerError(http_error.response.text)
             else:
                raise http_error
            
        #  raise
    # @api.model
    # def register(self):
    #     """
    #       Fetch Registration details
    #     """
    #     return self._do_request("/registration", method="GET")

    # def post_receipt(self, fd, payload):
    #     """
    #     Post Receipt
    #     """
    #     return self._do_request("/receipts",data=payload, fd=fd)

    # def get_zreport(self, fd, payload):
    #     """
    #     Post Receipt
    #     """
    #     return self._do_request("/receipts",data=payload, fd=fd)
    # def post_zreport(self, fd, payload):
    #     """
    #     After close of business, VFD must submit Z report, which is a summary of sales for the
    #     day. VFD should submit Z report of previous day the next day i.e. after midnight or before
    #     opening sales of next day.
    #     """
    #     access_token = self._get_access_token(fd)
    #     url = self._get_base_url(fd.state) + "/api/efdmszreport"
    #     headers = {
    #         "Content-Type": "application/xml",
    #         "Routing-Key": "vfdzreport",
    #         "Cert-Serial": base64.b64encode(fd.cert_key.encode()).decode(),
    #         "Authorization": f"bearer {access_token}",
    #     }
    #     signed_payload = self._sign_payload(fd, payload)
    #     _logger.info(
    #         f"VFD Post Zreport Request\nUri: {url} - Data : {signed_payload} !",
    #     )
    #     try:
    #         res = requests.post(
    #             url, data=signed_payload, headers=headers, timeout=TIMEOUT
    #         )
    #         res.raise_for_status()
    #         _logger.info(f"VFD Post Zreport Response: {res.text}")
    #         rct_ack = xmltodict.parse(res.text)["EFDMS"]["ZACK"]
    #         if rct_ack["ACKCODE"] == "0":
    #             return rct_ack
    #     except HTTPError as http_error:
    #         _logger.info(f"VFD Post Zreport Response: {http_error.response.text}")
    #         if http_error.response.status_code == 503:
    #            pass
    #         raise

    
       