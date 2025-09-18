from odoo import models, fields, api

class TimetableMasterWizard(models.TransientModel):
    _name = 'timetable.master.wizard'
    _description = 'Timetable for Master Report Wizard'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    stage_id = fields.Many2one('mc.education.stages', string='Educational Stage', required=True)
    
  
    def generate_timetable_master_report(self):
        return self.env.ref('mc_app.action_report_timetable_by_master_template').report_action(self)