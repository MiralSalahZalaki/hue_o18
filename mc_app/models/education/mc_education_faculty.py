from odoo import models, fields, api

class MCEducationFaculty(models.Model):
    _inherit = 'education.faculty'

       
    company_id = fields.Many2one('res.company')

    syllabus_special_class = fields.One2many('mc.syllabus.per.class','faculty_special_id', string="Faculty Special", store = True)

    syllabus_class = fields.One2many(
        'mc.syllabus.per.class', 'faculty_regular_id',
        string="Faculty Regular", store=True
    )

    user_id = fields.Many2one('res.users', related="employee_id.user_id")

    allowed_syllabus_ids = fields.Many2many(
        'education.syllabus', 
        compute='_compute_allowed_syllabus',
        string="Allowed Syllabus"
    )
    
    allowed_class_division_ids = fields.Many2many(
        'education.class.division', 
        compute='_compute_allowed_class_divisions',
        string="Allowed Class Divisions"
    )

        
    allowed_grade_ids = fields.Many2many(
        'education.class', 
        compute='_compute_allowed_grades',
        string="Allowed Grades"
    )
    
    
    @api.depends('syllabus_special_class', 'syllabus_class')
    def _compute_allowed_syllabus(self):
        for record in self:
            syllabus_ids = []
            
            for line in record.syllabus_special_class:
                if line.syllabus_id:
                    syllabus_ids.append(line.syllabus_id.id)
                    
            for line in record.syllabus_class:
                if line.syllabus_id:
                    syllabus_ids.append(line.syllabus_id.id)
            
            record.allowed_syllabus_ids = [(6, 0, list(set(syllabus_ids)))]
    
    @api.depends('syllabus_special_class', 'syllabus_class')
    def _compute_allowed_class_divisions(self):
        for record in self:
            class_division_ids = []
            
            # جمع الفصول من الجداول العادية والخاصة
            for line in record.syllabus_special_class:
                if line.class_division_id:
                    class_division_ids.append(line.class_division_id.id)
                    
            for line in record.syllabus_class:
                if line.class_division_id:
                    class_division_ids.append(line.class_division_id.id)
            
            record.allowed_class_division_ids = [(6, 0, list(set(class_division_ids)))]

    @api.depends('syllabus_special_class', 'syllabus_class')
    def _compute_allowed_grades(self):
        for record in self:
            allowed_grade_ids = []
            
            # جمع الفصول من الجداول العادية والخاصة
            for line in record.syllabus_special_class:
                if line.class_id:
                    allowed_grade_ids.append(line.class_id.id)
                    
            for line in record.syllabus_class:
                if line.class_division_id:
                    allowed_grade_ids.append(line.class_id.id)
            
            record.allowed_grade_ids = [(6, 0, list(set(allowed_grade_ids)))]


