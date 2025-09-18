from odoo import models, fields, api

class EducationFeeType(models.Model):
    _inherit = 'education.fee.type'

    bank_account_id = fields.Many2one('mc.fee.bank.account', string='Bank Account')
    property_account_income_id = fields.Many2one('account.account', string='Income Account', help="Keep this field empty to use the default value from the product category.")
    categ_id = fields.Many2one('product.category', string='Internal Category', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company , required=True)


