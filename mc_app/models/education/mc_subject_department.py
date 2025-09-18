from odoo import models, fields

class MCSubjectDepartment(models.Model):
    _name = 'mc.subject.department'
    _description = 'Subject Department'

    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)

    department = fields.Many2one('hr.department', string="Department")
    department_manager = fields.Many2one('hr.employee', string="Department Manager", related='department.manager_id', store=True, readonly=False)
    other_department = fields.Many2many('hr.department', string="Other Departments")
    respon = fields.Many2many('res.users', string="Respon", domain=[('is_student', '=', False)])
    general_microsoft_teams = fields.Char(string="General Microsoft Teams")
