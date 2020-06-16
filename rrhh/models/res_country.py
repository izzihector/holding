# -*- coding: utf-8 -*-

from odoo import api, fields, models

class Country(models.Model):
    _inherit = 'res.country'

    informe_empleador_id = fields.Char('Identificador informe empleador')
