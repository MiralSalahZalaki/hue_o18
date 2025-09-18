from odoo import models, fields, api

class MCEducationAttendenceLines(models.Model):
    _inherit = 'education.attendance.line'

       
    student_arabic_name = fields.Char(string='Student Arabic Name', related='student_id.full_arabic_name')
    student_english_name = fields.Char(string='Student English Name', related='student_id.full_english_name')
    present_morning = fields.Boolean(string='Morning', default= True,store=True,
                                     help="Enable if the student is present "
                                          "in the morning.")
    sickness_absence = fields.Boolean()
    
    sickness_reason = fields.Many2one(
    'mc.student.permitted.absence.reason',
    string="Sickness Reason",readonly=True, store=True,)

    """ sickness_reason = fields.Many2one( 'mc.student.permitted.absence',  
                                        string='Permitted Absence',   
                                        readonly=True,                           
                                        store=True) """