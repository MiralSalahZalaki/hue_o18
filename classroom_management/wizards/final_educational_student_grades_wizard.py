from odoo import models, fields, api
from collections import defaultdict

class FinalEducationalStudentGradesWizard(models.TransientModel):
    _name = 'final.educational.student.grades.wizard'
    _description = 'Final Educational Student Grades'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    term_id = fields.Many2one('education.academic.term', domain="[('school_year_id.company_id', '=', company_id)]", required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True, domain="[('school','=',company_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", domain="[('class_id','=',grade_id)]")
    syllabus_id = fields.Many2one("education.syllabus", string="Syllabus", required=True, domain="[('company_id', '=', company_id),('class_id', '=', grade_id)]")
    arabic_report = fields.Boolean(string="Arabic Report")

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.class_id = False
        self.syllabus_id = False

    def generate_final_educational_student_report_wizard(self):
    
        return self.env.ref('classroom_management.action_report_final_educational_student_grades').report_action(self)