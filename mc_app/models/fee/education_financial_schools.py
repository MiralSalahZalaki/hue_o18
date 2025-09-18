
from odoo import models, fields, api
from datetime import date

class EducationFinancialSchools(models.Model):
    _name = 'education.financial.schools'
    _description = 'Education Financial Schools'

    school_id = fields.Many2one(
        'res.company',
        string='School',
        default=lambda self: self.env.company,
    )
    financial_year = fields.Many2one(
        'mc.financial.years',
        string='Financial Year',
    )
    school_fees = fields.Many2many(
        'education.fee.structure',
        string="School Fee",
    )
    student_id = fields.Many2many(
        'education.student',
        string="Run Student",
    )

    def generate_school_invoices(self):
        if self.student_id:
            students = self.student_id
        else:
            students = self.env['education.student'].sudo().search([
                ('company_id', '=', self.school_id.id)
            ])

        for student in students:
            if not student.grade_id:
                continue

            structures = self.school_fees.filtered(
                lambda s: student.grade_id.id in s.grade.ids
            )

            for structure in structures:
                if not structures:
                    continue

                installments = structure.fee_type_ids.mapped('fee_installment_ids.installment')

                for installment in installments:
                    invoice_lines = []

                    for fee_line in structure.fee_type_ids:
                        for inst_line in fee_line.fee_installment_ids:
                            if inst_line.installment == installment:
                                product = fee_line.fee_type_id.product_variant_id

                                # السعر الافتراضي من structure
                                price_unit = inst_line.fee_amount
                                currency_id = self.school_id.currency_id.id

                                # تعديل سعر الباص لو الطالب مشترك وليه مدينة بباص بسعر مختلف
                                if structure.category_id.bus_fee and student.join_bus and student.bus_city:
                                    price_unit = student.bus_city.fee_amount
                                    currency_id = student.bus_city.currency_id.id

                                invoice_lines.append((0, 0, {
                                    'product_id': product.id,
                                    'name': product.name,
                                    'quantity': 1,
                                    'price_unit': price_unit,
                                    'account_id': fee_line.fee_type_id.property_account_income_id.id,
                                    'currency_id': currency_id,
                                }))

                    if not invoice_lines:
                        continue

                    if structure.category_id.bus_fee and not student.join_bus:
                        continue

                    journal_id = structure.category_id.journal_id.id if structure.category_id and structure.category_id.journal_id else None
                    if not journal_id:
                        raise ValueError("No journal defined for the fee category.")

                    existing_invoice = self.env['account.move'].sudo().search([
                        ('student_id', '=', student.id),
                        ('financial_year', '=', self.financial_year.id),
                        ('fee_category_id', '=', structure.category_id.id),
                        ('fee_payment_term', '=', installment.id),
                        ('state', 'in', ['draft', 'posted']),
                        ('fee_structure_id', '=', structure.id),
                    ], limit=1)

                    if existing_invoice:
                        print(f"Invoice already exists for student {student.name} with financial_year {self.financial_year.name}, category {structure.category_id.name}, fee_payment_term {installment.name}, and state {existing_invoice.state}")
                        continue

                    invoice = self.env['account.move'].create({
                        'move_type': 'out_invoice',
                        'student_id': student.id,
                        'class_division_id': student.class_division_id.id,
                        'partner_id': student.partner_id.id,
                        'invoice_date': date.today(),
                        'invoice_user_id': self.env.user.id,
                        'company_id': self.school_id.id,
                        'financial_year': self.financial_year.id,
                        'is_fee': True,
                        'fee_category_id': structure.category_id.id,
                        'fee_structure_id': structure.id,
                        'fee_payment_term': installment.id,
                        'journal_id': journal_id,
                        'invoice_line_ids': invoice_lines,
                    })
                    invoice.action_post()

                    # إنشاء Credit Note للخصومات إذا كانت موجودة
                    self._create_discount_credit_note(student, invoice, structure, installment)

                     # Below was for posting only if discounts are applicable; otherwise, the invoice stays in draft state.
                    """ discounts = self._get_applicable_discounts(student)

                    if discounts:
                        invoice.action_post()
                        self._create_discount_credit_note(student, invoice, structure, installment)
                    else:
                        # تخلي الفاتورة في حالة draft ولا ترحلها
                        pass """

        return True


    def _create_discount_credit_note(self, student, invoice, structure, installment):
        """إنشاء Credit Note للخصومات المطبقة على الطالب"""
        discounts = self._get_applicable_discounts(student)
        credit_note_lines = []
        
        for discount in discounts:
            # التحقق من إعدادات الخصم حسب الفترة
            if discount.category_id.by_term:
                # إذا كان الخصم مرتبط بفترة معينة
                if not discount.category_id.choose_term or discount.category_id.choose_term.id != installment.id:
                    continue  # تخطي هذا الخصم إذا لم يكن للفترة الحالية
            
            # حساب الخصم للفترة الحالية
            discount_lines = self._calculate_discount_for_installment(
                student, discount, structure, installment, invoice
            )
            credit_note_lines.extend(discount_lines)

        # إنشاء Credit Note إذا كان هناك خصومات
        if credit_note_lines:
            credit_note = self.env['account.move'].create({
                'move_type': 'out_refund',
                'student_id': student.id,
                'class_division_id': student.class_division_id.id,
                'partner_id': student.partner_id.id,
                'invoice_date': date.today(),
                'invoice_user_id': self.env.user.id,
                'company_id': self.school_id.id,
                'financial_year': self.financial_year.id,
                'is_fee': True,
                'fee_category_id': structure.category_id.id,
                'fee_structure_id': structure.id,
                'fee_payment_term': installment.id,
                'journal_id': invoice.journal_id.id,
                'invoice_line_ids': credit_note_lines,
                'ref': f'Discount for Invoice {invoice.name}',
                'reversed_entry_id': invoice.id,  # ربط الـ Credit Note بالفاتورة الأصلية
            })
            credit_note.action_post()

            if credit_note:
                invoice.has_refund = True

    def _calculate_discount_for_installment(self, student, discount, structure, installment, invoice):
        """حساب الخصم للفترة الحالية"""
        discount_lines = []
        
        for fee_line in structure.fee_type_ids:
            if fee_line.fee_type_id.property_account_income_id == discount.property_account_income_id:
                # البحث عن المبلغ المطلوب خصمه من هذه الفترة
                inst_line = fee_line.fee_installment_ids.filtered(
                    lambda il: il.installment == installment
                )
                
                if not inst_line:
                    continue
                
                inst_line = inst_line[0]  # أخذ أول عنصر
                
                # حساب الخصم
                discount_value = self._calculate_discount_amount(
                    discount, fee_line, inst_line, student
                )
                
                if discount_value > 0:
                    discount_lines.append((0, 0, {
                        'product_id': discount.product_id.id,
                        'name': f"{discount.name} for {fee_line.fee_type_id.name}",
                        'quantity': 1,
                        'price_unit': discount_value,  # قيمة موجبة في الـ Credit Note
                        'account_id': discount.property_account_income_id.id,
                    }))
        
        return discount_lines

    def _calculate_discount_amount(self, discount, fee_line, inst_line, student):
        """حساب مقدار الخصم"""
        # لو الرسوم خاصة بالباص، نستخدم سعر الباص من مدينة الطالب
        base_amount = inst_line.fee_amount
        if fee_line.fee_type_id and fee_line.fee_type_id.category_id.bus_fee and student.join_bus and student.bus_city:
            base_amount = student.bus_city.fee_amount

        if discount.category_id.by_term:
            # الخصم يطبق على الفترة المحددة فقط
            if discount.discount_type == 'percent':
                discount_value = (base_amount * discount.discount_amount) / 100.0
            else:
                discount_value = discount.discount_amount
        else:
            # الخصم يطبق على إجمالي الرسوم مقسم على الفترات
            total_fee = sum(
                student.bus_city.fee_amount if (fee_line.fee_type_id.category_id.bus_fee and student.join_bus and student.bus_city)
                else il.fee_amount
                for il in fee_line.fee_installment_ids
            )
            num_installments = len(fee_line.fee_installment_ids)
            
            if discount.discount_type == 'percent':
                total_discount = (total_fee * discount.discount_amount) / 100.0
            else:
                total_discount = discount.discount_amount
            
            if total_discount > total_fee:
                total_discount = total_fee
            
            discount_value = total_discount / num_installments if num_installments > 0 else 0.0

        # التأكد من أن الخصم لا يتجاوز المبلغ المستحق
        if discount_value > base_amount:
            discount_value = base_amount

        return discount_value


    def _get_applicable_discounts(self, student):
        discounts = self.env['education.fee.discount'].sudo().search([
            ('financial_year', '=', self.financial_year.id),
            ('company_id', '=', self.school_id.id),
        ])
        applicable_discounts = []
        for discount in discounts:
            if self._check_discount_criteria(student, discount):
                applicable_discounts.append(discount)
        return applicable_discounts

    def _check_discount_criteria(self, student, discount):
        if discount.founder_son and student.founder_son and student.founder_son_level == discount.founder_son_level:
            return True
        if discount.worker_son and student.worker_son and student.worker_son_level == discount.worker_son_level:
            return True
        if student.worker_son and student.join_bus and student.bus_city.id in discount.mc_bus_cities.ids:
            return True
        if student.entrance_year and student.entrance_year.id in discount.entrance_year.ids:
            return True
        if discount.sibling_apply and student._is_eligible_for_sibling_discount():
            return True
        return False