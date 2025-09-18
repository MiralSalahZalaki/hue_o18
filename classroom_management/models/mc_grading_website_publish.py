from odoo import models, fields,api


class MCGradingWebsitePublish(models.Model):
    _name = 'mc.grading.website.publish'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required= True)
    menu_icon = fields.Char(required= True)
    menu_name = fields.Char(required= True)
    menu_link = fields.Char(required= True)
    portal_link = fields.Char(string= "Portal Web-service")
    portal_link2 = fields.Char(string= "Portal Web-service 2")
    grade_ids = fields.Many2many(
        "education.class",
        string="Grades",
        domain="[('school', '=', company_id)]"
    )
    inv_block = fields.Boolean(string="Block Invoices")
    publish = fields.Boolean(string="Publish")

    @api.onchange('company_id')
    def _onchange_company_id(self):
        for rec in self:
            if rec.company_id:
                rec.grade_ids = False