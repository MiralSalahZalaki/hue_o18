from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MCCustomTemplate(models.Model):
    _name = 'mc.custom.template'
    _description = 'Custom Template' 

    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    syllabus_id = fields.Many2one('education.syllabus', string="Syllabus" , required=True) 
    grading_method = fields.Selection([
        ('qualitative', 'Qualitative'),
        ('evaluation', 'Evaluation Scale'),
        ('numeric', 'Numeric Evaluation'),
        ('q_colors', 'Qualitative Colors'),
    ], required=True, string="Grading Method")

    school_year_id = fields.Many2one('education.academic.year', string="School Year")
    grade_id = fields.Many2one ('education.class', string="Grade", required=True) 

    custom_grade_distribution_template = fields.One2many('mc.custom.distribution', 'custom_grading_distribution_id', string='Grade Distribution Template')
    assessments_category_id = fields.One2many('mc.custom.assessments.category', 'assessments_custom_category_id', string='Assessments Category')

    maximum = fields.Float(string='Maximum', compute="_compute_total", store=True)
    minimum = fields.Float(string='Minimum', compute="_compute_total", store=True)
    weight = fields.Integer(string='Weight', compute="_compute_total", store=True)
    academic_report_grade_max = fields.Float(string='Academic Report Grade Max', required=True)
    academic_report_grade_min = fields.Float(string='Academic Report Grade Min', required=True)
    total_assessments_score = fields.Float(string='Total Assessments Score' , required=True)



    @api.depends('custom_grade_distribution_template')
    def _compute_total(self):
        for rec in self:
            total_weight = 0.0
            total_minimum = 0.0
            total_maximum = 0.0
            
            for template in rec.custom_grade_distribution_template:
                total_weight += template.weight or 0.0
                total_minimum += template.minimum or 0.0
                total_maximum += template.maximum or 0.0


            rec.weight = total_weight
            rec.minimum = total_minimum
            rec.maximum = total_maximum

    @api.constrains('weight')
    def _check_total_weight(self):
        for rec in self:
            if rec.weight > 100:
                raise ValidationError("Total weight from grade distribution must not exceed 100%.")

