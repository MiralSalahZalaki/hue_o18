from odoo import models, fields, api
from datetime import datetime, timedelta


class TreasuryReportWizard(models.TransientModel):
    _name = 'treasury.report.wizard'
    _description = 'Treasury Report Wizard'

    employee_id = fields.Many2one('res.users', string="Employee")
    date_from = fields.Date(string="From", required=True, default=lambda self: datetime.today() - timedelta(days=5))
    date_to = fields.Date(string="To", required=True, default=lambda self: datetime.today())
    fee_category_id = fields.Many2one('education.fee.category', string="Fee Category")
    fee_payment_term = fields.Many2one('education.fee.installment', string="Fee Payment Term")
    account_journal = fields.Many2many('account.journal', string="Journals", domain=[('type','in',['bank','cash']),('journal_user','=',False)])
    financial_year = fields.Many2one('mc.financial.years', string="Financial Year")



    def generate_treasury_report_wizard(self):
        return self.env.ref('mc_app.action_treasury_report_template').report_action(self)
