# -*- coding: utf-8 -*-
# © 2016 ClearCorp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class res_partner(models.Model):
    _inherit = 'res.partner'

    sponsor = fields.Boolean(string='Sponsor')
