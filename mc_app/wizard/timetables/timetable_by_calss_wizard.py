from odoo import models, fields, api


class TimetableByClass(models.TransientModel):
    _name = 'timetable.by.calss.wizard'
    _description = 'Timetable by class Report Wizard'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True)
    student_id = fields.Many2many('education.student', string="Student", domain="[('grade_id', '=', grade_id),('class_division_id','=',class_division_id)]")
    class_division_id = fields.Many2one('education.class.division', string="Class", domain="[('class_id', '=', grade_id)]", required=True)

    @api.onchange('class_division_id')
    def _onchange_class_division(self):
        self.student_id = False

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.student_id = False
        self.class_division_id = False

    def generate_timetable_class_report(self):
        return self.env.ref('mc_app.action_report_timetable_by_class_template').report_action(self)