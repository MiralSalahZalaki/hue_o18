from odoo import models, fields, api
from datetime import datetime ,timedelta

class PaidReportWizard(models.TransientModel):
    _name = 'paid.report.wizard'
    _description = 'Paid Report Wizard'

    employee_id = fields.Many2one('res.users')
    date_from = fields.Date(string="From", required=True, default=lambda self: datetime.today() - timedelta(days=5))
    date_to = fields.Date(string="To", required=True, default=lambda self: datetime.today())
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    term_id = fields.Many2many('education.fee.installment', string="Fee Term")
    account_id = fields.Many2many(
        'account.account',
        string="Fee Account",
        domain="[('company_ids', 'in', [company_id])]"
    )
    account_journal = fields.Many2many('account.journal', string="Journals", domain=[('type','in',['bank','cash']),('journal_user','=',False)])
    financial_years = fields.Many2one('mc.financial.years')
    grade_ids = fields.Many2many(
        "education.class",
        string="Grades",
        domain="[('school', '=', company_id)]"
    )


    def generate_paid_report_wizard(self):
        return self.env.ref('mc_app.action_paid_report_template').report_action(self)