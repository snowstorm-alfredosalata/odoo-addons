# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields
import requests
import base64
from odoo.tools import image

import logging

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    standard_package = fields.Float("Quantità d'Imballo")