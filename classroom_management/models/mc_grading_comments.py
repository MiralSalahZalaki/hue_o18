from odoo import models, fields,api


class MCGradingComments(models.Model):
    _name = 'mc.grading.comments'

    name = fields.Char(string="Name")
    grading_type_id = fields.Many2one('mc.grading.types', string="Grading Type")
