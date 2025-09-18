from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    school_identifier = fields.Char(string="School Identifier")