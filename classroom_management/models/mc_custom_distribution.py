from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCCustomDistribution(models.Model):
    _name = 'mc.custom.distribution'
    _description = 'Custom Distribution' 
    _rec_name = 'item'


    item = fields.Many2one('mc.grade.distribution', required = True)
    minimum = fields.Float(string="Minimum")
    maximum = fields.Float(string="Maximum")
    report_mark = fields.Float(string="Report Mark")
    weight = fields.Float(string="Weight")
    best_of = fields.Integer(string="Best Of")
    control = fields.Selection([('system','By System'),('multi','Multi'),('control','Control'),('project','Project')])
    custom_grading_distribution_id = fields.Many2one('mc.custom.template', string="custom_grade_distribution_template")
    applicable = fields.Boolean(string="Applicable")
