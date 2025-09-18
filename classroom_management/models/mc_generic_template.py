from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MCGenericTemplate(models.Model):
    _name = 'mc.generic.template'
    _description = 'Generic Template' 

    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    grading_method = fields.Selection([
        ('qualitative', 'Qualitative'),
        ('evaluation', 'Evaluation Scale'),
        ('numeric', 'Numeric Evaluation'),
        ('q_colors', 'Qualitative Colors'),
    ], required=True, string="Grading Method")

    check_field = fields.Boolean(string='Check Field', store=True)
    grade_distribution_template = fields.One2many('mc.distribution.template', 'grade_distribution_id', string='Grade Distribution Template')
    assessments_category_id = fields.One2many('mc.assessments.category', 'assessments_category_grading_method_id', string='Assessments Category')

    maximum = fields.Float(string='Maximum', compute="_compute_total", store=True)
    minimum = fields.Float(string='Minimum', compute="_compute_total", store=True)
    weight = fields.Integer(string='Weight', compute="_compute_total", store=True)
    academic_report_grade_max = fields.Float(string='Academic Report Grade Max')
    academic_report_grade_min = fields.Float(string='Academic Report Grade Min')
    total_assessments_score = fields.Float(string='Total Assessments Score',compute="_compute_total", store=True)

    @api.onchange('grade_distribution_template')
    def _onchange_grade_distribution_template(self):
        for rec in self:
            has_assessment = False

            for template in rec.grade_distribution_template:
                if template.item and template.item.assessment:
                    has_assessment = True

            rec.check_field = has_assessment

    @api.depends('grade_distribution_template')
    def _compute_total(self):
        for rec in self:
            total_weight = 0.0
            total_minimum = 0.0
            total_maximum = 0.0
            total_assessments = 0.0
            
            for template in rec.grade_distribution_template:
                total_weight += template.weight or 0.0
                total_minimum += template.minimum or 0.0
                total_maximum += template.maximum or 0.0

                if template.item and template.item.assessment:
                    total_assessments += template.weight  or 0.0

            rec.total_assessments_score =  total_assessments
            rec.weight = total_weight
            rec.minimum = total_minimum
            rec.maximum = total_maximum