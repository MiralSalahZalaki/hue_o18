
from odoo import models, fields, api


class MinistryFeeReportAbstract(models.AbstractModel):
    _name = 'report.mc_app.ministry_fee_report_template'
    _description = 'Ministry Fee Report Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['ministry.fee.report.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_ministry_fee_report(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'ministry.fee.report.wizard',
            'docs': [wizard],

            'ministry_data': main_data['ministry_data'],
            'employee_name': main_data['employee_name'],
            'date_from': main_data['date_from'],
            'date_to': main_data['date_to'],
            'company_name': main_data['company_name'],
            'term_id': main_data['term_id'],
            'account_id': main_data['account_id'],
            'account_journal': main_data['account_journal'],
            'financial_years': main_data['financial_years'],
            'inv_status': main_data['inv_status'],
          
        }

    
    def _prepare_ministry_fee_report(self,wizard):
        domain = [
            ('company_id', '=', wizard.company_id.id),
            ('invoice_date_due', '>=', wizard.date_from),
            ('invoice_date_due', '<=', wizard.date_to),
            ('financial_year', '=', wizard.financial_years.id),
            ('move_type','=','out_invoice') # To get just what student paied
        ]

        if wizard.employee_id:
            domain.append(('user_id', '=', wizard.employee_id.id))
        if wizard.term_id:
            domain.append(('fee_payment_term', 'in', wizard.term_id.ids))
        if wizard.account_id:
            domain.append(('account_id', 'in', wizard.account_id.ids))
        if wizard.account_journal:
            domain.append(('journal_id', 'in', wizard.account_journal.ids))
        if wizard.inv_status:
            domain.append(('payment_state', '=', wizard.inv_status))

        invoices = self.env['account.move'].sudo().search(domain)

        result = []
        grouped = {}

        for inv in invoices:
            student = inv.student_id  # يفترض أنك عندك الحقل ده
            if student.id not in grouped:
                grouped[student.id] = {
                    'student_name': student.full_arabic_name,
                    'grade': student.grade_id.name if student.grade_id else '',
                    'total': 0.0,
                }
            grouped[student.id]['total'] += inv.amount_total

        result = list(grouped.values())
        
        return {
            'ministry_data':result,
            'employee_name': wizard.employee_id.name if wizard.employee_id else '',
            'date_from': wizard.date_from,
            'date_to': wizard.date_to,
            'company_name': wizard.company_id.name,
            'term_id': '/ '.join(wizard.term_id.mapped('name')) if wizard.term_id else 'All',
            'account_id': '/ '.join(wizard.account_id.mapped('name')) if wizard.account_id else 'All',
            'account_journal': '/ '.join(wizard.account_journal.mapped('name')) if wizard.account_journal else 'All',
            'financial_years':wizard.financial_years.name,
            'inv_status': wizard.inv_status,
        }
