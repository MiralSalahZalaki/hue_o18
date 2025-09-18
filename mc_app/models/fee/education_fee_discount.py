from odoo import models, fields, api

class EducationFeeDiscount(models.Model):
    _name = 'education.fee.discount'
    _description = 'Education Fee Discount'

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    product_id = fields.Many2one('product.product', string='Automatically created field to link to parent product.product', required=True, readonly=False, searchable=True, sortable=True, store=True)

    category_id = fields.Many2one('education.fee.discount.config.category', string='Category', required=True)
    financial_year = fields.Many2one('mc.financial.years', string='Financial Year', required=True)
    discount_type = fields.Selection([
        ('percent', 'Percentage'),
        ('amount', 'Amount'),
    ], string='Discount Type', required=True)

    discount_amount = fields.Float(string='Discount Amount', required=True)
    property_account_income_id = fields.Many2one('account.account', string='Income Account')

    school_transfered_from = fields.Many2one('mc.education.institute')

    sibling_apply = fields.Boolean(default=False)
    founder_son = fields.Boolean(default=False)
    founder_son_level = fields.Selection([
        ('1', 'Level 1'),
        ('2', 'Level 2'),
        ('3', 'Level 3'),
        ('4', 'Level 4'),
        ('5', 'Level 5'),
        ('6', 'Level 6'),
        ('7', 'Level 7'),
        ('8', 'Level 8'),
        ('9', 'Level 9'),
        ('10', 'Level 10'),
    ])
    worker_son = fields.Boolean(default=False)
    worker_son_level = fields.Selection([
        ('1', 'Level 1'),
        ('2', 'Level 2'),
        ('3', 'Level 3'),
        ('4', 'Level 4'),
        ('5', 'Level 5'),
        ('6', 'Level 6'),
        ('7', 'Level 7'),
        ('8', 'Level 8'),
        ('9', 'Level 9'),
        ('10', 'Level 10'),
    ])

    grade = fields.Many2many('education.class', string="Grade", domain="[('school', '=', company_id)]")
    entrance_year = fields.Many2many('education.academic.year')
    mc_bus_cities = fields.Many2many('mc.bus.city')
    paid_bus = fields.Boolean(default=False)
    paid_bus_financial_year = fields.Many2one('mc.financial.years', string='Paid Bus Financial Year')
    join_bus = fields.Selection([
        ('no', 'No'),
        ('yes', 'Yes'),
    ], string='Join Bus')

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically create a product when a discount is created."""
        products = []
        for vals in vals_list:
            product = self.env['product.product'].create({
                'name': vals.get('name', 'Discount Product'),
                'type': 'service',
                'list_price': 0.0,
                'default_code': f'DISC_{vals.get("id", "NEW")}',
                'company_id': vals.get('company_id'),
            })
            vals['product_id'] = product.id
            products.append(product)
        records = super(EducationFeeDiscount, self).create(vals_list)
        return records

    def update_existing_discounts(self):
        """Update existing discount records to create and link products."""
        for record in self.sudo().search([]):  # Get all existing records
            if not record.product_id:
                product = self.env['product.product'].create({
                    'name': record.name or 'Discount Product',
                    'type': 'service',
                    'list_price': 0.0,
                    'default_code': f'DISC_{record.id}',
                    'company_id': record.company_id.id,
                })
                record.product_id = product.id
        return True