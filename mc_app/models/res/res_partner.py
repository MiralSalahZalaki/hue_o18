from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    # Education Page Fields
    nationality = fields.Many2one('res.country', string='Nationality', help='Select the Nationality')
    national_id = fields.Char(
        string='National ID',  
         
    )
    status = fields.Selection(
        selection=[('active', 'Active'), ('inactive', 'Inactive')],
        string='Live Status',
    )
    religion = fields.Selection(
        selection=[('islam', 'Islam'), ('christianity', 'Christianity'), ('other', 'Other')],
        string='Religion',  

    )
    is_driver = fields.Boolean(
        string='Is a Driver', help='Check this box if this contact is a driver.'
    )
    
    student_id = fields.Many2one(
        'education.student', string='Related Student',
         relation='education.student'
    )

    # Sales Page Fields
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        help='Utility field to express amount currency',
    )

    # General Fields (also in Sales context)
    opt_out = fields.Boolean(
        string='Opt-Out',
        help='If opt-out is checked, this contact has refused to receive emails for mass mailing and marketing campaign. Filter \'Available for Mass Mailing\' allows users to filter the partners when performing mass mailing.',
           
    )

    customer = fields.Boolean(string = 'Is a Customer')


