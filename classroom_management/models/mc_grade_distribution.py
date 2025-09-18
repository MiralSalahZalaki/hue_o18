from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCGradeDistribution(models.Model):
    _name = 'mc.grade.distribution'
    _description = 'Grade Distribution' 

    name = fields.Char(string="Name", required=True)
    control = fields.Boolean(string="Control")
    assessment = fields.Boolean(string="Assessment")
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)
   