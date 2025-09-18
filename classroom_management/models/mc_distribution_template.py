from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCDistributionTempalte(models.Model):
    _name = 'mc.distribution.template'
    _description = 'Distribution Template' 

    item = fields.Many2one('mc.grade.distribution', required = True)
    minimum = fields.Float(string="Minimum")
    maximum = fields.Float(string="Maximum")
    weight = fields.Float(string="Weight")
    best_of = fields.Integer(string="Best Of")
    control = fields.Selection([('system','By System'),('multi','Multi'),('control','Control'),('project','Project')])
    grade_distribution_id = fields.Many2one('mc.generic.template', string="grade_distribution_template")

