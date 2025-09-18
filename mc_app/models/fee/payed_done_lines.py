from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

class PayedDoneLines(models.Model):
    _name = 'payed.done.lines'
    _description = 'Paid Done Lines'
    _rec_name = 'payment_id'

    date = fields.Date(
        string='Payment Date',
        required=True,
    )
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        readonly=True,
        required=False,
    )
    account_id = fields.Many2one(
        'account.account',
        string='Account',
        readonly=True,
        required=True,
    )
    price_unit = fields.Float(
        string='Paid Amount',
        readonly=True,
        required=True,
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        ondelete='cascade',
    )
    student_id = fields.Many2one(
        'education.student',
        string='Student',
        readonly=True,
    )
    fee_category_id = fields.Many2one(
        'education.fee.category',
        string='Fee Category',
        readonly=True,
    )

    

