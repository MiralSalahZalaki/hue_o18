from odoo import models, fields, api


class MCFeeBankAccount(models.Model):
    _name = 'mc.fee.bank.account'
    _description = 'MC Fee Bank Account'

    name = fields.Char(string='Name', required=True)
    iban = fields.Char(string='IBAN')
    bransh = fields.Char(string='Bransh')
    bank_account_no = fields.Char(string='Bank Account no.')
    swift_code	= fields.Char(string='Swift Code')
   