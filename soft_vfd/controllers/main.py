# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import hmac
import hashlib
import json
import lxml.etree as ET
from lxml.builder import ElementMaker 
from odoo import http
from odoo.tools import consteq
from odoo.exceptions import ValidationError
from odoo.http import request
_logger = logging.getLogger(__name__)

class VFDWebhookController(http.Controller):
    _callback_url = "/soft_vfd/events"
    def _verify_webhook_signature(self,webhook_secret):
        """ Check that the signature computed from the feedback matches the received one.

        :param str webhook_secret: The secret webhook key 
        :return: Whether the signatures match
        :rtype: str
        """
        if not webhook_secret:
            _logger.warning("ignored webhook event due to undefined webhook secret")
            return False
        event_payload = request.httprequest.data.decode('utf-8')
        received_signature = request.httprequest.headers.get('VFD-Signature')

        # Compare signatures
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            event_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        if not consteq(received_signature, expected_signature):
            _logger.warning("ignored event with invalid signature")
            return False
        return True
    @http.route(_callback_url, type='json', auth='public', methods=['POST'], csrf=False)
    def vfd_webhook(self):
        """ 
          Process the data returned by VFD Webhook Event
        """
        data = json.loads(request.httprequest.data)
        _logger.info(f"Received VFD Webhook Event: {VFDWebhookController._callback_url}:\n{pprint.pformat(data)}")
        fd = request.env["vfd.service"].sudo()._get_virtual_device()
        if self._verify_webhook_signature(fd.webhook_secret):
           request.env["vfd.receipt"].sudo()._process_receipt_posted_event(data)
       
        return "Okay"
    
   