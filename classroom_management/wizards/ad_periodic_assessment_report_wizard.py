from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PeriodicAssessmentReportWizard(models.TransientModel):
    _name = 'periodic.assessment.report.wizard'
    _description = 'Periodic Assessment Report Wizard'

    company_id = fields.Many2one('res.company', string='School',  default=lambda self: self.env.company, required=True )
    term_id = fields.Many2one('education.academic.term', required=True,  domain="[('school_year_id.company_id', '=', company_id)]")
    grade_id = fields.Many2one('education.class', string="Grade", required=True , domain="[('school','=',company_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", domain="[('class_id','=',grade_id)]")
    student_view = fields.Boolean(string="Student View")
    
    # Adjust Domain of assessment_times
    assessment_times_domain = fields.Binary(string="assessment domain", 
                                          help="Dynamic domain used for assessment times", 
                                          compute="_compute_assessment_times_domain")
    
    assessments_times = fields.Many2many("mc.assessment.times", string="Assessment Time",
                                        domain="assessment_times_domain", required=True)
    
    # Adjust Domain of student_ids
    student_ids_domain = fields.Binary(string="students domain",
                                     help="Dynamic domain for students based on grade and class",
                                     compute="_compute_student_ids_domain")
                                     
    student_ids = fields.Many2many('education.student', string="Student", 
                                  required=True,
                                  domain="student_ids_domain")
    
    @api.depends('company_id', 'term_id', 'grade_id')
    def _compute_assessment_times_domain(self):
        for rec in self:
            domain = [('id','=',-1)]
            if rec.company_id and rec.grade_id and rec.term_id:
                domain = [
                    ('company_id', '=', rec.company_id.id),
                    ('grade_ids', 'in', rec.grade_id.id),
                    ('start_date', '>=', rec.term_id.start_date),
                    ('end_date', '<=', rec.term_id.end_date)
                ]
            rec.assessment_times_domain = domain
    
    @api.depends('grade_id', 'class_id')
    def _compute_student_ids_domain(self):
        for rec in self:
            domain = [('id','=',-1)]
            if rec.grade_id:
                domain = [('grade_id', '=', rec.grade_id.id)]
                if rec.class_id:
                    domain.append(('class_division_id', '=', rec.class_id.id))
            rec.student_ids_domain = domain
    
    @api.onchange('class_id')
    def _onchange_class_id(self):
        self.student_ids = False

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.student_ids = False
        self.class_id = False

    

    def generate_periodic_assessment_report_wizard(self):
        if not all([self.grade_id, self.term_id, self.company_id, self.assessments_times]):
            raise ValidationError("يرجى ملء جميع الحقول المطلوبة: المدرسة، الصف، والفصل الدراسي وفترة تقييم واحدة علي الأقل")

        return self.env.ref('classroom_management.action_report_ad_periodic_assessment').report_action(self)
    