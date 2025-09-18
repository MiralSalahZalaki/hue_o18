from odoo import models, fields, api
from datetime import timedelta


class ClassMissingWizard(models.TransientModel):
    _name = 'class.missing.attendence.wizard'
    _description = 'Class Missing wizard'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True)
    class_division_id = fields.Many2one('education.class.division', string="Class",
                                        domain="[('class_id', '=', grade_id)]", required=True)
    academic_year_id = fields.Many2one('education.academic.year', string='Academic Year',
                                       default=lambda self: self._get_current_academic_year())

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.class_division_id = False

    def _get_current_academic_year(self):
        current_year = self.env['education.academic.year'].sudo().search([('current', '=', True)], limit=1)
        return current_year.id if current_year else False


    def generate_behavior_class_report(self):
        """Generate the report for class attendance"""
        return self.env.ref('mc_app.action_class_missing_attendance_report').report_action(self)