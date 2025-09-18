from odoo import models, fields, api ,_
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero
import datetime


class MCAccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'MC Account Move (Account Invoice Before)'

    student_code = fields.Char(
    string='Student Code',
    readonly=True, 
    required=False,
    searchable=True,
    sortable=True,
    store=True,
    related='student_id.student_code'  
    )

    financial_year = fields.Many2one('mc.financial.years', string='Financial Years')

    has_refund = fields.Boolean(
        string='has refund',
    )

    bus_cancel = fields.Boolean(
        string='Bus Cancel',
        type='boolean',
    )

    fee_payment_term = fields.Many2one('education.fee.installment',string='Fee Payment Term')

    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled')
        ],
        help='* The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. * The \'Open\' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice. * The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. * The \'Cancelled\' status is used when user cancel invoice.',
        readonly=True,
        required=False,
        searchable=True,
        sortable=True,
        store=True,
        default='draft'
    )

    # If they need it to change from posted to open, Add another state to be paid and make it paid once it paid in payment state
    """ state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Open'), #Change Posted sate to open
            ('cancel', 'Cancelled')
        ],
        help='* The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. * The \'Open\' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice. * The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. * The \'Cancelled\' status is used when user cancel invoice.',
        readonly=True,
        required=False,
        searchable=True,
        sortable=True,
        store=True,
        default='draft'
    ) """


    def action_post(self):
        res = super().action_post()

        for move in self:
            if move.name and move.name != '/' and move.company_id.company_registry:
                parts = move.name.split('/')
                registry = move.company_id.company_registry

                # تأكد إن registry مش موجود أصلاً
                if registry not in parts:
                    # ضيفه بعد أول جزء فقط (مثلاً: TFEE/ → TFEE/MC/)
                    parts.insert(1, registry)
                    move.name = '/'.join(parts)

        return res
    
    
    
    
    payed_done_line_ids = fields.One2many('payed.done.lines', 'invoice_id', compute='_compute_payed_done_lines', store=True)

    @api.depends('payment_ids', 'payment_ids.state')
    def _compute_payed_done_lines(self):
        """تحديث الـ payed_done_line_ids بناءً على تفاصيل المدفوعات المرتبطة بالفاتورة."""
        for record in self:
            # البحث عن المدفوعات المرتبطة بالفاتورة دي
            payments = self.env['account.payment'].sudo().search([('invoice_ids', 'in', record.id)])
            lines_vals = []

            # حساب إجمالي مبلغ الفاتورة لتوزيع الدفع نسبيًا
            total_invoice = sum(record.invoice_line_ids.mapped('price_total'))
            
            for payment in payments:
                # توزيع مبلغ الدفع على سطور الفاتورة
                for line in record.invoice_line_ids:
                    # لو إجمالي الفاتورة صفر، بنتجنب القسمة على صفر
                    if not total_invoice:
                        allocated_amount = 0
                    else:
                        # توزيع المبلغ بنسبة سعر السطر لإجمالي الفاتورة
                        allocated_amount = (line.price_total / total_invoice) * payment.amount

                    # تحضير القيم لسجل payed.done.lines
                    vals = {
                        'date': payment.date,
                        'payment_id': payment.id,
                        'partner_id': payment.partner_id.id,
                        'product_id': line.product_id.id,
                        'account_id': line.account_id.id,
                        'price_unit': allocated_amount,
                        'invoice_id': record.id,
                        'student_id': record.student_id.id if 'student_id' in record else False,
                        'fee_category_id': line.fee_category_id.id if 'fee_category_id' in line else False,
                    }
                    lines_vals.append(vals)

            # حذف السجلات القديمة في payed_done_line_ids
            record.payed_done_line_ids.unlink()
            # إنشاء سجلات جديدة بالقيم المحسوبة
            self.env['payed.done.lines'].create(lines_vals)
