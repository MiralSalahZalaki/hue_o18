from odoo import models, fields, api
import random  # For employee codes as text


class RevealerReport(models.TransientModel):
    _name = 'revealer.report.wizard'
    _description = 'Revealer Report Wizard'
    
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    stage_id = fields.Many2one('mc.education.stages', string='Educational Stage')
    total_sessions = fields.Boolean()

    def generate_timetable_revealer_report(self):
        return self.env.ref('mc_app.action_revealer_reports_template').report_action(self)