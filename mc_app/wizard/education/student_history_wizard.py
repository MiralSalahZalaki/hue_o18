from odoo import models, fields, api
from datetime import datetime, date


class StudentHistoryWizard(models.TransientModel):
    _name = 'student.history.wizard'
    _description = 'Student History Report'


    quit_student = fields.Selection([
        ('enrolled','Enrolled Student'),
        ('quit','Quit Student'),
    ], default='enrolled', string="Quit Student", required=True)

    report_view = fields.Selection([
        ('en','English ltr'),
        ('ar','Arabic rtl'),
    ], default='en', string="Report View", required=True)

    company_id = fields.Many2one('res.company', string='School',default=lambda self: self.env.company)
  
    grade_id = fields.Many2one('education.class', string="Grade")

    student_code = fields.Char(string="Student Code")
    student_name = fields.Char()
   

    class_division_id = fields.Many2one('education.class.division', 
                                   string="Class",
                                   domain="[('class_id', '=', grade_id)]")
    student_id = fields.Many2one('education.student', 
                                string="Student",
                                domain="[('grade_id', '=', grade_id)]",required=True)

    
    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.student_id = False
        self.class_division_id = False   
        
        
    @api.onchange('student_id')
    def _onchange_student_id(self):
        if self.student_id:
            self.company_id = self.student_id.company_id
            self.grade_id = self.student_id.grade_id
            self.class_division_id = self.student_id.class_division_id
            self.student_code = self.student_id.student_code
            self.student_name = self.student_id.full_english_name

    @api.onchange('student_code')
    def _onchange_student_code(self):
        if self.student_code:
            student = self.env['education.student'].sudo().search([('student_code', '=', self.student_code)], limit=1)
            if student:
                self.student_id = student
            else:
                self.student_id = False
                return {
                    'warning': {
                        'title': "Student Not Found",
                        'message': "No student found with this code.",
                    }
                }


    
    def generate_student_histroy_report(self):
        return self.env.ref('mc_app.action_report_student_history_template').report_action(self)
    
  
