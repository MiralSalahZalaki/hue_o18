
from odoo import models, fields, api

class MCStandardClass(models.Model):
    _name = 'mc.standard.class'
    _description = 'Standard Class'

    name = fields.Char(compute="_get_name")
    class_id = fields.Many2one('education.class', string='Grade', required=True)
    class_division_id = fields.Many2one('education.division', string='Class Division', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    standard_per_class_id = fields.One2many('mc.syllabus.per.class', 'mc_standard_class_id', string='Syllabus', store= True)

    @api.depends('class_id','class_division_id')
    def _get_name(self):
        for rec in self:
            if rec.class_division_id and rec.class_id:
                rec.name =   f"{rec.class_id.name} - {rec.class_division_id.name}" 
    
    
    """ @api.onchange('standard_per_class_id')
    def _onchange_standard_per_class_id(self):
        #When teacher is assigned in subjects page, update the corresponding syllabus per class
        for subject in self.standard_per_class_id:
            if subject.faculty_regular_id:
                # Find the corresponding record in mc.syllabus.per.class
                syllabus_per_class = self.env['mc.syllabus.per.class'].sudo().search([
                    ('syllabus_id', '=', subject.syllabus_id.id),
                    ('class_division_id', '=', self.class_division_id.id)
                ], limit=1)
                
                if syllabus_per_class:
                    # Update the faculty in the syllabus per class record
                    syllabus_per_class.write({
                        'faculty_regular_id': subject.faculty_regular_id.id,
                    }) """