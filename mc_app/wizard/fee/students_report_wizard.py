from odoo import models, fields, api

class StudentsReportWizard(models.TransientModel):
    _name = 'students.report.wizard'
    _description = 'Students Report Wizard'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    grade_ids = fields.Many2many(
        "education.class",
        string="Grades",
        domain="[('school', '=', company_id)]"
    )
    class_ids = fields.Many2many('education.class.division', 
                                          string='Class',  domain="[('class_id', 'in', grade_ids)]")
    invoice_customer_credit = fields.Selection(
        selection=[('all', 'All Invoices'),
                   ('out_invoice', 'Customer Invoices'),
                   ('out_refund', 'Customer Credit Notes')],
        string="Invoice Credit", required=True)

    std_status = fields.Selection(
        selection=[('all', 'All Students'),
                   ('enrolled', 'Enrolled Students'),
                   ('out', 'Out Students')],
        string="Student Status")

    invoice_type = fields.Selection(
        selection=[('regular', 'Regular'),
                   ('one', 'One Time'),
                   ('bus', 'Buses'),
                   ('hostel', 'Hostel'),
                   ('miscellaneous', 'Miscellaneous')],
        string="Invoice Type", required=True)

    invoice_state = fields.Selection(
        selection=[('all', 'All'),
                   ('paid', 'Full Paid'),
                   ('open', 'Not Paid'),
                   ('draft', 'Draft'),
                   ('draft_open', 'Draft & Open'),
                   ('ppaid', 'Partially Paid')],
        string="Invoice State", required=True)
    
        
    def get_students_report_wizard(self):
        pass

    def _generate_report(self):
        pass

    def generate_students_report_wizard(self):
        pass