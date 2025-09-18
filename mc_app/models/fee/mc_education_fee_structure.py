from odoo import models, fields, api

class EducationFeeStructure(models.Model):
    _inherit = 'education.fee.structure'

    financial_year = fields.Many2one('mc.financial.years', string='Financial Year' , required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company , required=True)
    grade =  fields.Many2many('education.class', string="Grade", domain="[('school', '=', company_id)]")

    @api.depends('fee_type_ids.fee_amount')
    def compute_total(self):
        for rec in self:
            rec.amount_total = sum(line.fee_amount for line in rec.fee_type_ids)



class EducationFeeStructureLines(models.Model):
    _inherit = 'education.fee.structure.lines'

    apply_discount = fields.Boolean(default = False, string="Apply Discount")
    fee_installment_ids = fields.One2many('education.fee.installment.lines','fee_structure', string="Fee Installment")
    fee_amount = fields.Float(
        string='Amount',
        store=True,
        required=True,
        help='القيمة بعد إلغاء الربط بـ lst_price.',   
    )
 
class EducationFeeInstallment(models.Model):
    _name = 'education.fee.installment'

    name = fields.Char(string="Installment Name", required=True)
    fee_installment_dates_ids = fields.One2many('education.fee.installment.date','fee_installment_id', string="Fee Dates")

    

class EducationFeeInstallmentDates(models.Model):
    _name = 'education.fee.installment.date'

    fee_installment_id = fields.Many2one('education.fee.installment')
    due_date = fields.Date(string="Due Date")
    receipt_date = fields.Date(string="Receipt Date")
    financial_year = fields.Many2one('mc.financial.years', string='Financial Year' )

class EducationFeeInstallmentLines(models.Model):
    _name = 'education.fee.installment.lines'

    installment = fields.Many2one('education.fee.installment', string="Installment", required=True)
    fee_amount = fields.Float(string="Amount", required=True)
    fee_structure = fields.Many2one('education.fee.structure.lines')