from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging
from odoo.exceptions import ValidationError


class GradingAttendenceReportWizard(models.TransientModel):
    _name = 'grading.attendance.report.wizard'
    _description = 'Grading Attendance Report wizard'
    
    company_id = fields.Many2one('res.company', string='School', 
                                default=lambda self: self.env.company, required=True)
    term_id = fields.Many2one('education.academic.term', domain="[('school_year_id.company_id', '=', company_id)]", required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True, 
                              domain="[('school','=',company_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", 
                              domain="[('class_id','=',grade_id)]")
    
    # تم تغيير Binary إلى Char
    assessment_times_domain = fields.Char(string="assessment domain", 
                                         help="Dynamic domain used for assessment times", 
                                         compute="_compute_assessment_times_domain")
    
    assessments_times = fields.Many2many("mc.assessment.times", string="Assessment Time",
                                        domain="assessment_times_domain", required=True)
    
    # تم تغيير Binary إلى Char  
    student_ids_domain = fields.Char(string="students domain",
                                    help="Dynamic domain for students based on grade and class",
                                    compute="_compute_student_ids_domain")
                                     
    student_ids = fields.Many2many('education.student', string="Student", 
                                  required=True,
                                  domain="student_ids_domain")
    
    @api.depends('company_id', 'term_id', 'grade_id')
    def _compute_assessment_times_domain(self):
        for rec in self:
            domain = "[('id','=',-1)]"  # تم تغيير إلى string
            if rec.company_id and rec.grade_id and rec.term_id:
                domain = str([
                    ('company_id', '=', rec.company_id.id),
                    ('grade_ids', 'in', rec.grade_id.id),
                    ('start_date', '>=', rec.term_id.start_date.strftime('%Y-%m-%d')),
                    ('end_date', '<=', rec.term_id.end_date.strftime('%Y-%m-%d')),
                    ('distribution','=', False)
                ])
            rec.assessment_times_domain = domain
    
    @api.depends('grade_id', 'class_id')
    def _compute_student_ids_domain(self):
        for rec in self:
            domain = "[('id','=',-1)]"  # تم تغيير إلى string
            if rec.grade_id:
                domain_list = [('grade_id', '=', rec.grade_id.id)]
                if rec.class_id:
                    domain_list.append(('class_division_id', '=', rec.class_id.id))
                domain = str(domain_list)
            rec.student_ids_domain = domain
    
    @api.onchange('class_id')
    def _onchange_class_id(self):
        self.student_ids = False

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.student_ids = False
        self.class_id = False
    


    def generate_grading_attendence_report_wizard(self):
        if not all([self.grade_id, self.company_id, self.assessments_times]):
            raise ValidationError("يرجى ملء جميع الحقول المطلوبة: المدرسة، الصف، وأوقات التقييم")

        return self.env.ref('classroom_management.action_report_grading_attendence').report_action(self)