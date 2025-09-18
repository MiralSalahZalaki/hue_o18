from odoo import models, fields

class MCBlockReason(models.Model):
    _name = 'mc.block.reason'

    name = fields.Char()