
from odoo import models, fields, api


class TreasuryReportAbstract(models.AbstractModel):
    _name = 'report.mc_app.treasury_report_template'
    _description = 'Treasury Report Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['treasury.report.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_treasury_report(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'treasury.report.wizard',
            'docs': [wizard],

            'employee_name': main_data['employee_name'],
            'date_from': main_data['date_from'],
            'date_to': main_data['date_to'],
            'fee_payment_term': main_data['fee_payment_term'],
            'account_journal': main_data['account_journal'],
            'fee_category_id': main_data['fee_category_id'],
            'treasury_data': main_data['treasury_data'],
     
        }

    def _prepare_treasury_report(self,wizard):
        # Build domain for searching account.payment records
        domain = [
            ('date', '>=', wizard.date_from),
            ('date', '<=', wizard.date_to),
            ('state', '=', 'paid'),  # Only posted payments
            ('payment_type', '=', 'inbound'),  # Only incoming payments
        ]

        # Add journal filter only if specified
        if wizard.account_journal:
            domain.append(('journal_id', 'in', wizard.account_journal.ids))

        # Search for account.payment records
        payments = self.env['account.payment'].sudo().search(domain)

        # Prepare data for the report
        treasury_data = []
        for payment in payments:
            # Search for student record using partner_id from payment
            student = self.env['education.student'].sudo().search([('partner_id', '=', payment.partner_id.id)], limit=1)
            
            # Get the related invoice(s) from the payment
            invoices = False
            fee_category_name = 'N/A'
            
            # Try different ways to get the related invoice
            if hasattr(payment, 'reconciled_invoice_ids'):
                invoices = payment.reconciled_invoice_ids
            
            if not invoices and payment.move_id:
                # Try to get invoice from reconciled move lines
                reconciled_moves = payment.move_id.line_ids.mapped('matched_debit_ids.debit_move_id.move_id')
                invoices = reconciled_moves.filtered(lambda m: m.move_type == 'out_invoice')
            
            # Get the first invoice for the data
            invoice = invoices[0] if invoices else False
            
            # Get fee category from invoice if exists
            if invoice:
                if hasattr(invoice, 'fee_category_id') and invoice.fee_category_id:
                    fee_category_name = invoice.fee_category_id.name
                
                # Apply fee category filter if specified
                if wizard.fee_category_id and (not invoice.fee_category_id or invoice.fee_category_id.id != wizard.fee_category_id.id):
                    continue
                    
                # Apply fee payment term filter if specified  
                if wizard.fee_payment_term and (not hasattr(invoice, 'fee_payment_term') or invoice.fee_payment_term != wizard.fee_payment_term.id):
                    continue
                    
                # Apply financial year filter if specified
                if wizard.financial_year and (not hasattr(invoice, 'financial_year') or invoice.financial_year != wizard.financial_year.id):
                    continue
            else:
                # If no invoice found and filters are specified, skip this payment
                if wizard.fee_category_id or wizard.fee_payment_term or wizard.financial_year:
                    continue
            
            # Apply employee filter if specified
            if wizard.employee_id:
                # Check multiple fields for employee match
                employee_match = False
                if payment.create_uid and payment.create_uid.id == wizard.employee_id.id:
                    employee_match = True
                elif invoice and hasattr(invoice, 'user_id') and invoice.user_id and invoice.user_id.id == wizard.employee_id.id:
                    employee_match = True
                elif invoice and hasattr(invoice, 'invoice_user_id') and invoice.invoice_user_id and invoice.invoice_user_id.id == wizard.employee_id.id:
                    employee_match = True
                
                if not employee_match:
                    continue
            
            # Extract student data if found, otherwise use partner data
            student_code = 'N/A'
            student_name = payment.partner_id.name or 'N/A'
            grade = 'N/A'
            
            if student:
                if hasattr(student, 'student_code') and student.student_code:
                    student_code = student.student_code
                if hasattr(student, 'full_arabic_name') and student.full_arabic_name:
                    student_name = student.full_arabic_name
                elif hasattr(student, 'name') and student.name:
                    student_name = student.name
                if hasattr(student, 'grade_id') and student.grade_id:
                    grade = student.grade_id.name

            # Determine sales person
            sales_person = 'N/A'
            if invoice and hasattr(invoice, 'user_id') and invoice.user_id:
                sales_person = invoice.user_id.name
            elif payment.create_uid:
                sales_person = payment.create_uid.name

            # Get student data from invoice if available
            invoice_student_code = 'N/A'
            invoice_student_name = 'N/A'
            invoice_grade = 'N/A'
            invoice_number = 'N/A'
            
            if invoice:
                # Get student data from invoice
                invoice_student = self.env['education.student'].sudo().search([('partner_id', '=', invoice.partner_id.id)], limit=1)
                if invoice_student:
                    if hasattr(invoice_student, 'student_code') and invoice_student.student_code:
                        invoice_student_code = invoice_student.student_code
                    if hasattr(invoice_student, 'full_arabic_name') and invoice_student.full_arabic_name:
                        invoice_student_name = invoice_student.full_arabic_name
                    elif hasattr(invoice_student, 'name') and invoice_student.name:
                        invoice_student_name = invoice_student.name
                    if hasattr(invoice_student, 'grade_id') and invoice_student.grade_id:
                        invoice_grade = invoice_student.grade_id.name
                else:
                    # Use partner name if no student found
                    invoice_student_name = invoice.partner_id.name or 'N/A'
                
                # Get invoice number
                invoice_number = invoice.name or 'N/A'
            else:
                # Use payment student data if no invoice
                invoice_student_code = student_code
                invoice_student_name = student_name
                invoice_grade = grade

            treasury_data.append({
                'date': payment.date,
                'student_code': invoice_student_code,  # student_code from invoice
                'student_name': invoice_student_name,  # student_name from invoice
                'grade': invoice_grade,  # grade from invoice
                'paid_amount': payment.amount,  # Payment amount
                'invoice_type': fee_category_name,  # Fee category from invoice
                'invoice_number': invoice_number,  # related invoice name
                'currency': payment.currency_id.name,
                'journal': payment.journal_id.name,
                'sales_person': sales_person,
                'receipt_number': payment.name,  # Payment reference as receipt
            })

        return {
            'employee_name': wizard.employee_id.name if wizard.employee_id else 'All',
            'date_from': wizard.date_from,
            'date_to': wizard.date_to,
            'fee_payment_term': wizard.fee_payment_term.name if wizard.fee_payment_term else 'All',
            'account_journal': ', '.join(wizard.account_journal.mapped('name')) if wizard.account_journal else 'All',
            'fee_category_id': wizard.fee_category_id.name if wizard.fee_category_id else 'All',
            'treasury_data': treasury_data,
        }