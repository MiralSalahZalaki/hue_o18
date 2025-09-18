from odoo import models, fields, api

class MCGradingMethod(models.Model):
    _name = 'mc.grading.method'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    grade_id = fields.Many2one("education.class", string="Grade", required=True)
    grading_method = fields.Selection([
        ('qualitative', 'Qualitative'),
        ('evaluation', 'Evaluation Scale'),
        ('numeric', 'Numeric Evaluation'),
        ('q_colors', 'Qualitative Colors'),
    ], required=True, string="Grading Method")
    grading_scale_id = fields.One2many('mc.grading.scale', 'grading_scale_id', string="Grading Scale")
    comment = fields.Char(string="Comment")
    school_year_id = fields.Many2one('education.academic.year', string="School Year")

    """ @api.onchange('grading_method')
    def _onchange_grading_method(self):
        return {
            'context': {
                'default_grading_method': self.grading_method,
            }
        } """