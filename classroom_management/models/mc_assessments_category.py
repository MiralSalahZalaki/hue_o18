from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCAssessmentCategory(models.Model):
    _name = 'mc.assessments.category'
    _description = 'Assessment category' 
    _rec_name = "item"

    item = fields.Many2one('mc.assessments.category.types', required = True)
    
    max_score = fields.Float(string="Max Score")
    weight = fields.Float(string="Weight")
    best_of = fields.Integer(string="Best Of")
    control = fields.Selection([('system','By System'),('multi','Multi'),('control','Control'),('project','Project')])
    assessments_category_grading_method_id = fields.Many2one('mc.generic.template', string="assessments_category_id")