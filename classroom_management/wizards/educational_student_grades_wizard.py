from odoo import models, fields, api

class EducationalStudentGradesWizard(models.TransientModel):
    _name = 'educational.student.grades.wizard'
    _description = 'Educational Student Grades Report'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True, domain="[('school','=',company_id)]")
    class_division_id = fields.Many2one('education.class.division', string="Class", domain="[('class_id', '=', grade_id)]")
    term_id = fields.Many2one('education.academic.term', domain="[('school_year_id.company_id', '=', company_id)]", required=True)
    syllabus_id = fields.Many2one("education.syllabus", string="Syllabus", required=True, domain="[('company_id', '=', company_id),('class_id', '=', grade_id)]")
    arabic_report = fields.Boolean(string="Arabic Report")
    show_avg = fields.Boolean(string="Show Average")

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.class_division_id = False    

    def generate_educational_student_grades_wizard(self):        
        # Pass the wizard record itself to the report
        return self.env.ref('classroom_management.report_educational_student_grades').report_action(self)