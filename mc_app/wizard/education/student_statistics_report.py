from odoo import models, fields, api
from datetime import datetime, date
from collections import Counter



class StudentStatisticsWizard(models.TransientModel):
    _name = 'student.statistics.wizard'
    _description = 'Student Statisitics Report'

    report_view = fields.Selection([
        ('en','English ltr'),
        ('ar','Arabic rtl'),
    ], default='en', string="Report View", required=True)

    company_id = fields.Many2one('res.company', string='School',default=lambda self: self.env.company , required=True)
    academic_year_id = fields.Many2one('education.academic.year' , required=True)
    
                     
    def action_generate_statistics_report(self):
        return self.env.ref('mc_app.action_report_statistics_template').report_action(self)

    
    