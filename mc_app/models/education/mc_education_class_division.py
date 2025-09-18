from odoo import models, fields, api

class MCEducationClass(models.Model):
    _inherit = 'education.class.division'

    school_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company,  required=True)
    room_id =  fields.Many2one('mc.rooms', string='Default Room')
    ldap_ou = fields.Many2one('student.ldap.directory')
    ms_channel = fields.Char(string="Microsoft Teams Channel")
    sds_level = fields.Char(string="Microsoft SDS level")
    faculty_id = fields.Many2one('education.faculty',
                                 string='Class Faculty', required=False,
                                 help="Class teacher/Faculty")

    grade_sequence = fields.Integer(string="Sequence")
                                 
    
    @api.model
    def create(self, vals):
        """Create a class division and automatically create its standard class record if not already present."""
        educationClassDivision = super(MCEducationClass, self).create(vals)
        educationClassDivision.create_or_update_required_records()
        return educationClassDivision

    def write(self, vals):
        """Ensure standard class records are updated if class_id or division_id changes."""
        res = super(MCEducationClass, self).write(vals)
        self.create_or_update_required_records()
        return res
    

    def unlink(self):
        """Ensure related standard class records are deleted when a division is removed."""
        for division in self:
            self.env['mc.standard.class'].sudo().search([
                ('class_division_id', '=', division.division_id.id)
            ]).unlink()

            self.env['mc.syllabus.per.class'].sudo().search([
            ('class_division_id', '=', division.id)
            ]).unlink()

        return super(MCEducationClass, self).unlink()

    def create_or_update_required_records(self):
        """
        Create or update both standard class and syllabus per class records
        for this class division.
        """
        for rec in self:
            # Step 1: Ensure standard class exists
            mc_standard_class = self.env['mc.standard.class'].sudo().search([
                ('class_id', '=', rec.class_id.id),
                ('class_division_id', '=', rec.division_id.id)
            ], limit=1)
            
            if not mc_standard_class:
                mc_standard_class = self.env['mc.standard.class'].create({
                    'class_id': rec.class_id.id,
                    'class_division_id': rec.division_id.id,
                    'company_id': rec.school_id.id if rec.school_id else self.env.company.id,
                })
            
            # Step 2: Create syllabus per class records
            grade_syllabuses = self.env['education.syllabus'].sudo().search([
                ('class_id', '=', rec.class_id.id),
            ])
            
            for syllabus in grade_syllabuses:
                # Check if a syllabus per class record already exists
                existing_syllabus_per_class = self.env['mc.syllabus.per.class'].sudo().search([
                    ('syllabus_id', '=', syllabus.id),
                    ('class_division_id', '=', rec.id)
                ], limit=1)
                
                if not existing_syllabus_per_class:
                    # Create a new syllabus per class record
                    syllabus_per_class = self.env['mc.syllabus.per.class'].create({
                        'syllabus_id': syllabus.id,
                        'class_division_id': rec.id,
                        'elective': syllabus.elective,
                        'company_id': rec.school_id.id if rec.school_id else self.env.company.id,
                        'mc_standard_class_id': mc_standard_class.id
                    })
                    
                    # Enroll students if this is not an elective syllabus
                    if not syllabus.elective:
                        students = self.env['education.student'].sudo().search([('class_division_id', '=', rec.id)])
                        
                        # Create enrollment records for each student
                        enrollments = [(0, 0, {
                            'student_id': student.id,
                            'role': 'student',
                            'active': True,
                            'user_class': syllabus_per_class.id
                        }) for student in students]
                        
                        syllabus_per_class.write({'enrollment_per_class_ids': enrollments})