from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AssessmentsReportWizard(models.TransientModel):
    _name = 'assessments.report.wizard'
    _description = 'Assessments Report wizard'
    
    company_id = fields.Many2one(
        'res.company', string='School',
        default=lambda self: self.env.company, required=True
    )
    grade_id = fields.Many2one('education.class', string="Grade", required=True, domain="[('school','=',company_id)]")
    distribution = fields.Boolean(string="Use Distribution")
    term_id = fields.Many2one('education.academic.term',  domain="[('school_year_id.company_id', '=', company_id)]")
    assessments_times = fields.Many2one("mc.assessment.times", string=" Assessment Time",
                                         domain ="[('company_id', '=', company_id), ('grade_ids', 'in', grade_id)]")
             
   
    def generate_assessments_report_wizard(self):
        if not self.grade_id :
                raise ValidationError("يجب تحديد Grade أولاً.")
        return self.env.ref('classroom_management.action_assessments_report_template').report_action(self)