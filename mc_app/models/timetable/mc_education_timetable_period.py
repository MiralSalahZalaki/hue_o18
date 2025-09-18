from odoo import models, fields, api

class MCEducationTimetablePeriod(models.Model):
    _inherit = 'timetable.period'
    
    break_flag = fields.Boolean(string ="Break")
   
   