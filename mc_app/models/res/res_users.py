from odoo import fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'
    

    
    faculty_id = fields.Many2one(
    'education.faculty',
    compute="_compute_faculty_id",
    store=False)

    def _compute_faculty_id(self):
        for user in self:
            user.faculty_id = self.env['education.faculty'].search([('user_id', '=', user.id)], limit=1)


    """ stu_parent = fields.Boolean(string='Student Parent')
    father_user = fields.Many2one('res.users',string='Related Father')
    mother_user = fields.Many2one('res.users',string='Related Mother')
    guardian_user = fields.Many2one('res.users',string='Related Guardian') """