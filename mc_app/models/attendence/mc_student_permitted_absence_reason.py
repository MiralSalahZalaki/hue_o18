from odoo import models, fields

class MCPremittedAbsenceReason(models.Model):
    _name = 'mc.student.permitted.absence.reason'
    _description = 'Student Absence Reasons'

    name = fields.Char(string="Name", required = True)
    