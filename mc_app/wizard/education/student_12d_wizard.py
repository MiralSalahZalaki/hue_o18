from odoo import models, fields, api
from datetime import datetime, date


class Student12DWizard(models.TransientModel):
    _name = 'student.12d.wizard'
    _description = 'Student 12D Report'

    title = fields.Char(string="Title")
    report_view = fields.Selection([
        ('en','English ltr'),
        ('ar','Arabic rtl'),
    ], default='en', string="Report View", required=True)
    company_id = fields.Many2one('res.company', string='School',default=lambda self: self.env.company)
    display_name = fields.Selection([('en','English'),('ar','Arabic')], default='en', string="Display Name", required=True)
    student_status = fields.Selection([
        ('all','All'),
        ('new','New'),
        ('passed','Passed'),
    ] , default='all',string="Enrollment Status", required=True)

    grade_id = fields.Many2one('education.class', string="Grade")
    code = fields.Char(string="Identification Code")
    class_division_id = fields.Many2one('education.class.division', 
                                   string="Class",
                                   domain="[('class_id', '=', grade_id)]")
    full_name = fields.Char(string="Full Name")
    first_name = fields.Char(string="First Name")
    surname = fields.Char(string="Surname")
    birth_date = fields.Date(string="Birth Date")
    gender = fields.Selection([
        ('male','Male'),
        ('female','Female'),
    ], string="Gender")
    order_by = fields.Selection([
    ('first_name', 'First Name'),
    ('last_name', 'Surname'),  
    ('full_english_name', 'English Full Name'),
    ('full_arabic_name', 'Arabic Full Name'),
    ], string="Order By")
    
    new_report = fields.Boolean(string="Apply 12D New Report")

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.class_division_id = False


   
    def action_generate_12d_report(self):
        return self.env.ref('mc_app.action_report_12d_template').report_action(self)

