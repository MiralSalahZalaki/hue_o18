from odoo import models, fields, api
from collections import defaultdict


class StudentsAbsenceDaysWizard(models.TransientModel):
    _name = 'students.absence.days.wizard'
    _description = 'Students Absence Days Wizard'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True)
    class_division_id = fields.Many2one('education.class.division', string="Class", domain="[('class_id', '=', grade_id)]")
    date_from = fields.Date( string="Form" , required=True)
    date_to= fields.Date( string="To" , required=True)
    permitted_absence = fields.Boolean(string="Permitted Absence")

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.class_division_id = False


    def generate_students_absence_days_report(self):
        return self.env.ref('mc_app.action_students_absence_days_report').report_action(self)
    