from odoo import models, fields, api


class EducationFeeDiscountCategory(models.Model):
    _name = 'education.fee.discount.config.category'
    _description = 'Education Fee Discount Category'

    name = fields.Char(string='Name', required=True)
    by_term = fields.Boolean()
    choose_term = fields.Many2one('education.fee.installment')
    