from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MCAssessmentsCategoryTypes(models.Model):
    _name = 'mc.assessments.category.types'
    _description = 'Assessments Category Types' 

    name = fields.Char(string="Name", required=True)
    attendance_assessment = fields.Boolean(string="Attendance Assessment")
    hidden_student_report = fields.Boolean(string="Hidden Student Report")
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required= True)

