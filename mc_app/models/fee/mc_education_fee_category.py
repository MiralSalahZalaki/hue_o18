from odoo import models, fields, api

class EducationFeeCategory(models.Model):
    _inherit = 'education.fee.category'

    alias_name = fields.Char(string="Alias Name")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company , required=True)
    bus_fee = fields.Boolean(default= False, string="Is a bus fee ?")
    run_discount = fields.Boolean(default= True, string="Run Discounts ?")
    