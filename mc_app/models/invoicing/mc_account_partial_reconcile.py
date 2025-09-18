# models/account_partial_reconcile.py (Create this file or add to an appropriate existing one)
from odoo import models, fields, api, _

class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    @api.model_create_multi
    def create(self, vals_list):
        reconciles = super().create(vals_list)
        
        for reconcile in reconciles:
            # We are interested in reconciliations between an invoice line and a payment line.
            # An invoice line typically has an invoice_id.
            # A payment line typically has a payment_id.

            invoice_line = False
            payment_line = False
            paid_amount = 0.0

            # Determine which move line is the invoice line and which is the payment line
            if reconcile.debit_move_id.move_id.is_invoice(include_receipts=True) and reconcile.credit_move_id.payment_id:
                invoice_line = reconcile.debit_move_id
                payment_line = reconcile.credit_move_id
                paid_amount = reconcile.amount # The amount of the partial reconciliation
            elif reconcile.credit_move_id.move_id.is_invoice(include_receipts=True) and reconcile.debit_move_id.payment_id:
                invoice_line = reconcile.credit_move_id
                payment_line = reconcile.debit_move_id
                paid_amount = reconcile.amount

            if invoice_line and payment_line:
                # Find the actual invoice line (account.move.line) associated with the reconciled debit/credit move line
                # Invoices and bills have lines of type 'out_invoice', 'in_invoice', etc.
                if invoice_line.invoice_id and invoice_line.display_type == 'product': # Ensure it's a product line, not a section/note
                    self.env['payed.done.lines'].create({
                        'date': payment_line.payment_id.date,
                        'payment_id': payment_line.payment_id.id,
                        'partner_id': invoice_line.invoice_id.partner_id.id,
                        'product_id': invoice_line.product_id.id,
                        'account_id': invoice_line.account_id.id,
                        'price_unit': paid_amount,  # The actual amount paid for this specific reconciliation
                        'invoice_id': invoice_line.invoice_id.id,
                        'invoice_line_id': invoice_line.id, # Link to the specific invoice line
                        'student_id': invoice_line.invoice_id.student_id.id if hasattr(invoice_line.invoice_id, 'student_id') else False,
                        'fee_category_id': invoice_line.fee_category_id.id if hasattr(invoice_line, 'fee_category_id') else False,
                    })

        return reconciles