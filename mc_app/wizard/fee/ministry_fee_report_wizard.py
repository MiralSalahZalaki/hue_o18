from odoo import models, fields, api
from datetime import datetime ,timedelta

class MinistryFeeReportWizard(models.TransientModel):
    _name = 'ministry.fee.report.wizard'
    _description = 'Ministry Fee Report Wizard'

    employee_id = fields.Many2one('res.users')
    date_from = fields.Date(string="From", required=True, default=lambda self: datetime.today() - timedelta(days=5))
    date_to = fields.Date(string="To", required=True, default=lambda self: datetime.today())
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    term_id = fields.Many2many('education.fee.installment', string="Fee Term")
    account_id = fields.Many2many(
        'account.account',
        string="Fee Account",
    )
    account_journal = fields.Many2many('account.journal', string="Journals", domain=[('type','in',['bank','cash']),('journal_user','=',False)])
    inv_status = fields.Selection([('not_paid','Not Paid'),('paid','Paid')])
    financial_years = fields.Many2one(
    'mc.financial.years',
    required=True,
    default=lambda self: self.env['mc.financial.years'].sudo().search([('current_financial_year', '=', True)], limit=1))



    def generate_ministry_fee_report_wizard(self):
        return self.env.ref('mc_app.action_ministry_fee_report_template').report_action(self)