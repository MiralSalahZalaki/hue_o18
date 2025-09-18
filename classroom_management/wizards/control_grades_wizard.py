from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ControlGradesWizard(models.TransientModel):
    _name = 'control.grades.wizard'
    _description = 'Control Grades Wizard'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    term_id = fields.Many2one('education.academic.term', required=True,  domain="[('school_year_id.company_id', '=', company_id)]")
    grade_id = fields.Many2one('education.class', string="Grade", required=True, domain="[('school', '=', company_id)]")
    distribution = fields.Many2one('mc.grade.distribution', string="Grade Distribution", domain="[('assessment','=',False),('control','=',True),('company_id', '=', company_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", domain="[('class_id', '=', grade_id)]")
   
    assessment_times_domain = fields.Binary(string="Assessment Domain", 
                                          help="Dynamic domain used for assessment times", 
                                          compute="_compute_assessment_times_domain")
    
    assessments_times = fields.Many2one("mc.assessment.times", string="Assessment Time",
                                        domain="assessment_times_domain")
    
    @api.onchange('term_id')
    def _onchange_term_id(self):
        self.distribution = False

    @api.depends('company_id', 'term_id', 'grade_id')
    def _compute_assessment_times_domain(self):
        for rec in self:
            domain = [('id', '=', -1)]
            if rec.company_id:
                domain = [('company_id', '=', rec.company_id.id),('distribution','=',True)]
                if rec.grade_id:
                    domain.append(('grade_ids', 'in', [rec.grade_id.id]))
                if rec.term_id and rec.term_id.start_date and rec.term_id.end_date:
                    domain.append(('start_date', '>=', rec.term_id.start_date))
                    domain.append(('end_date', '<=', rec.term_id.end_date))
            rec.assessment_times_domain = domain


    def generate_control_grades_report_wizard(self):
        if not all([self.grade_id, self.term_id, self.company_id]):
            raise ValidationError("Please fill all required fields: Company, Grade, and Term")
        
        return self.env.ref('classroom_management.action_report_control').report_action(self)