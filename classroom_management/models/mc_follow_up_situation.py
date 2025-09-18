from odoo import _, api, fields, models

class MCFollowUpSituation(models.Model):
    _name = 'mc.follow.up.situation'
    _description = 'Follow up Situation'
    
    name = fields.Char('Name', required=True)
    color = fields.Char(string="Symbol Color")
