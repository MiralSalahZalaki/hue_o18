from odoo import models, fields, api ,_
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

class MCAccountJournal(models.Model):
    _inherit = 'account.journal'
    _description = 'MC Account Journal'

    journal_user = fields.Boolean(
        string='Use in Point of Sale',
        default=False,
        type='boolean',
        help = 'Check this box if this journal define a payment method that can be used in a point of sale.'
    )

      