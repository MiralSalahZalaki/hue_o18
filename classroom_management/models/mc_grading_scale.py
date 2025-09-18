from odoo import models, fields,api


class MCGradingScale(models.Model):
    _name = 'mc.grading.scale'
    _rec_name="symbol"

    symbol = fields.Char(string="Symbol")
    minimum = fields.Float(string="Minimum")
    maximum = fields.Float(string="Maximum")
    color = fields.Char(string="Symbol Color")
    description = fields.Char(string="Description")

    grading_scale_id = fields.Many2one('mc.grading.method', string="Grading Method")
