
from odoo import models, fields, api


class PaidReportAbstract(models.AbstractModel):
    _name = 'report.mc_app.paid_report_template'
    _description = 'Paid Report Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['paid.report.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_paid_report(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'paid.report.wizard',
            'docs': [wizard],

            'employee_name': main_data['employee_name'],
            'date_from': main_data['date_from'],
            'date_to': main_data['date_to'],
            'company_name': main_data['company_name'],
            'paid_data': main_data['paid_data'],
            'term_id': main_data['term_id'],
            'account_id': main_data['account_id'],
            'account_journal': main_data['account_journal'],
            'financial_years':main_data['financial_years'],
            'currency': main_data['currency'], 
          
        }

    def _prepare_paid_report(self,wizard):
        """ Prepare a report of fully paid invoices """
        domain = [
            ('company_id', '=', wizard.company_id.id),
            ('invoice_date_due', '>=', wizard.date_from),
            ('invoice_date_due', '<=', wizard.date_to),
            ('state', '=', 'posted'),
            ('payment_state', '=', 'paid'),
        ]

        if wizard.employee_id:
            domain.append(('user_id', '=', wizard.employee_id.id))
        if wizard.account_id:
            domain.append(('account_id', 'in', wizard.account_id.ids))
        if wizard.account_journal:
            domain.append(('journal_id', 'in', wizard.account_journal.ids))
        if wizard.term_id:
            domain.append(('fee_payment_term', 'in', wizard.term_id.ids))
        if wizard.financial_years:
            domain.append(('financial_year', '=', wizard.financial_years.id))
        if wizard.grade_ids:
            students = self.env['education.student'].sudo().search([('grade_id', 'in', wizard.grade_ids.ids)])
            partner_ids = students.mapped('partner_id').ids
            domain.append(('partner_id', 'in', partner_ids))

        moves = self.env['account.move'].sudo().search(domain)

        paid_data = []
        for move in moves:
            student = self.env['education.student'].sudo().search([('partner_id', '=', move.partner_id.id)], limit=1)
            student_code = student.student_code if student else 'N/A'
            student_name = student.full_arabic_name or move.partner_id.name or 'N/A'
            grade = student.grade_id.name if student and student.grade_id else 'N/A'
            
            # Here we match the payment directly to this move
            payment = self.env['account.payment'].sudo().search([
                ('reconciled_invoice_ids', 'in', move.id),
                ('state', '=', 'paid')
            ], limit=1)
            payment_id = payment.name if payment else 'N/A'
            term = move.fee_payment_term.name if move.fee_payment_term else 'N/A'
            
            for invoice_line in move.invoice_line_ids:
                product_id = invoice_line.product_id.name if invoice_line.product_id else 'N/A'
                account_id = invoice_line.account_id.name if invoice_line.account_id else 'N/A'
                price_unit = invoice_line.price_unit

                paid_data.append({ 
                    'name': student_name,
                    'code': student_code,
                    'grade': grade,
                    'date': move.date,
                    'invoice_id': move.name,
                    'payment_id': payment_id,
                    'product_id': product_id,
                    'account_id': account_id,
                    'accountant': move.user_id.name or 'N/A',
                    'term': term,
                    'price_unit': price_unit,
                    'currency': move.currency_id,
                })
        return {
            'employee_name': wizard.employee_id.name or 'All',
            'date_from': wizard.date_from,
            'date_to': wizard.date_to,
            'company_name': wizard.company_id.name,
            'paid_data': paid_data,
            'term_id': '/ '.join(wizard.term_id.mapped('name')) if wizard.term_id else 'All',
            'account_id': '/ '.join(wizard.account_id.mapped('name')) if wizard.account_id else 'All',
            'account_journal': '/ '.join(wizard.account_journal.mapped('name')) if wizard.account_journal else 'All',
            'financial_years':wizard.financial_years.name,
            'currency': wizard.company_id.currency_id, 
        }