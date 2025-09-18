from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCCustomAssessmentCategory(models.Model):
    _name = 'mc.custom.assessments.category'
    _description = 'Custom Assessment category' 
    _rec_name = "item"


    item = fields.Many2one('mc.assessments.category.types', required = True)
    
    max_score = fields.Float(string="Max Score")
    best_of = fields.Integer(string="Best Of")
    control = fields.Selection([('system','By System'),('multi','Multi'),('control','Control'),('project','Project')])
    assessments_custom_category_id = fields.Many2one('mc.custom.template', string="assessments_category_id")


    
    @api.depends('max_score', 'assessments_custom_category_id.total_assessments_score')
    def _compute_weight(self):
        for rec in self:
            total_score = rec.assessments_custom_category_id.total_assessments_score
            rec.weight = (rec.max_score or 0.0) / total_score *100 if total_score else 0.0

    weight = fields.Float(string="Weight", compute="_compute_weight", store=True)

    @api.constrains('assessments_custom_category_id')
    def _check_assessments_category_weight(self):
        for rec in self:
            total = sum(line.weight for line in rec.assessments_custom_category_id)
            if total > 100:
                raise ValidationError("Total weight of assessments category must not exceed 100%.")
