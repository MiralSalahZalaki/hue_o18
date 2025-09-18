from odoo import _, api, fields, models

class MCFollowUpNotes(models.Model):
    _name = 'mc.follow.up.notes'
    _description = 'Follow up Notes'
    
    name = fields.Char('Name', required=True)