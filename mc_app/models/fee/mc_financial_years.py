from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class MCFinancialYears(models.Model):
    _name = 'mc.financial.years'
    _description = 'MC Financial Years'

    name = fields.Char(string='Name', required=True)
    academic_year = fields.Many2one('education.academic.year', string="Academic Year")

    year = fields.Selection(
    selection=[
        ('2010', '2010'),
        ('2011', '2011'),
        ('2012', '2012'),
        ('2013', '2013'),
        ('2014', '2014'),
        ('2015', '2015'),
        ('2016', '2016'),
        ('2017', '2017'),
        ('2018', '2018'),
        ('2019', '2019'),
        ('2020', '2020'),
        ('2021', '2021'),
        ('2022', '2022'),
        ('2023', '2023'),
        ('2024', '2024'),
        ('2025', '2025'),
    ], string='Year')


    active_year = fields.Boolean(string='Active Year')

    current_financial_year = fields.Boolean(string='Current Financial Year')

    discounts = fields.One2many(
        'education.fee.discount',
        'financial_year',
        string='Year Discounts'
    )

    financial_schools_ids = fields.One2many(
        'education.financial.schools',
        'financial_year',
        string='School'
    )

