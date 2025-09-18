from odoo import models, fields,api


class MCGradingTypes(models.Model):
    _name = 'mc.grading.types'

    name = fields.Char(string="Name")