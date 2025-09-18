from odoo import api, fields, models, _

class MCSyllabus(models.Model):
    _inherit = 'education.syllabus'
    
    arabic_name = fields.Char()
    sequence = fields.Integer()
    company_id = fields.Many2one('res.company', string="School", default=lambda self: self.env.company, required=True)
    regular_week = fields.Integer(string="Regular/Week")
    elective = fields.Boolean()
    
    
    allis_name = fields.Char(string="Allis Name")
    certificate_name = fields.Char()	
    color = fields.Char() 
    special_week = fields.Integer()
    hidden_official_report = fields.Boolean()  
    hidden_management_report = fields.Boolean()  
    add_to_total = fields.Boolean()  
    create_team = fields.Boolean()  
    domain = fields.Many2one('mc.syllabus.domain')

    class_id = fields.Many2one('education.class', string='Class',
                               help="Enter the class for syllabus", required=True) #grade

    available_subject_ids = fields.Many2many(
        'education.subject', 
        string='Available Subjects', 
        compute='_compute_available_subject_ids', 
        store=True
    )

    subject_id = fields.Many2one('education.subject', domain="[('id', 'in', available_subject_ids)]",
                                 string='Subject', help="Select subjects", required=True)
    
    #standard_id = fields.Many2one('mc.standard.class')
    active = fields.Boolean(string="Active", default=True)  # إضافة خاصية الأرشفة


    ################# Elective.syallabus.Students
    students = fields.One2many(
        'mc.elective.syllabus.students',
        'syllabus_id',
        string="Students",
        domain="[('company_id', '=', company_id.id)]"
     
    )

    @api.depends('class_id')
    def _compute_available_subject_ids(self):
        for rec in self:
            if rec.class_id:
                assigned_subject_ids = self.env['education.syllabus'].search([
                    ('class_id', '=', rec.class_id.id)
                ]).mapped('subject_id.id')
                
                # Set the domain (subjects not assigned to this class)
                rec.available_subject_ids = [(6, 0, self.env['education.subject'].search([
                    ('id', 'not in', assigned_subject_ids)
                ]).ids)]
            else:
                rec.available_subject_ids = [(5, 0, 0)]

    # Add SQL constraint to prevent duplicate subject-class combinations
    _sql_constraints = [
        ('unique_subject_class',
         'UNIQUE(subject_id,class_id)',
         'This subject is already assigned to this class!')
    ]
    
    @api.constrains('total_hours')
    def validate_time(self):
        """This method doesn't perform any validation"""
        pass
    
    @api.model
    def create(self, vals):
        """Override create to handle syllabus enrollment based on elective status."""
        syllabus = super(MCSyllabus, self).create(vals)
        self._handle_syllabus_elective_change(syllabus, syllabus.elective)
        return syllabus


    @api.model
    def write(self, vals):
        """Override write to handle any change in the record."""
        result = super(MCSyllabus, self).write(vals)

        for syllabus in self:
            syllabus._handle_syllabus_elective_change(syllabus,syllabus.elective)

        return result
   
    
    def unlink(self):
        for record in self:
            self.env['mc.elective.syllabus.students'].search([
                ('syllabus_id', '=', record.id)
            ]).unlink()

        return super(MCSyllabus, self).unlink()

    
    def _handle_syllabus_elective_change(self, syllabus, is_elective):
        """Handles the transition between elective and non-elective syllabus."""
        self.env['mc.syllabus.per.class'].search([
            ('syllabus_id', '=', syllabus.id)
        ]).unlink()

        if not is_elective:
            # When Convert to non-elective -Use this  to remove records  in mc.elective.syllabus.students if there are records 
            self.env['mc.elective.syllabus.students'].search([
                ('syllabus_id', '=', syllabus.id)
            ]).unlink()
            
            divisions = self.env['education.class.division'].search([('class_id', '=', syllabus.class_id.id)])
            for division in divisions:
                mc_standard_class = self.env['mc.standard.class'].search([
                    ('class_id', '=', syllabus.class_id.id),
                    ('class_division_id', '=', division.division_id.id)
                ], limit=1)

                syllabus_per_class = self.env['mc.syllabus.per.class'].create({
                    'syllabus_id': syllabus.id,
                    'class_division_id': division.id,
                    'elective': False,
                    'company_id': syllabus.company_id.id,
                    'mc_standard_class_id': mc_standard_class.id if mc_standard_class else False
                })

                students = self.env['education.student'].search([('class_division_id', '=', division.id)])
                self._enroll_students(syllabus_per_class, students)

        else:
            class_students_map = {}

            # Iterate over the elective students related to the syllabus
            for elective_student in syllabus.students:
                student = self.env['education.student'].search([
                    ('id', '=', elective_student.student_id.id)
                ], limit=1)
            
                # Check if the student and their class division exist
                if student and student.class_division_id:
                    # Group students by their class division
                    class_students_map.setdefault(student.class_division_id.id, []).append(student.id)
                
            # Now loop over the grouped class divisions and create records in syllabus.per.class
            for class_div_id, student_ids in class_students_map.items():
                # Find the related division
                division = self.env['education.class.division'].browse(class_div_id)
                
                # Find the standard class
                mc_standard_class = self.env['mc.standard.class'].search([
                    ('class_id', '=', syllabus.class_id.id),
                    ('class_division_id', '=', division.division_id.id)
                ], limit=1)

                syllabus_per_class = self.env['mc.syllabus.per.class'].create({
                    'syllabus_id': syllabus.id,
                    'class_division_id': class_div_id,
                    'elective': True,
                    'company_id': syllabus.company_id.id,
                    'mc_standard_class_id': mc_standard_class.id if mc_standard_class else False
                })


                # Enroll students into this syllabus per class record
                self._enroll_students(syllabus_per_class, student_ids, is_elective=True, syllabus=syllabus, class_div_id=class_div_id)

    def _enroll_students(self, syllabus_per_class, students, is_elective=False, syllabus=None, class_div_id=None):
        """Handles student enrollments for elective and non-elective syllabus."""
        enrollments = [(0, 0, {
            'student_id': student.id if not is_elective else student,
            'role': 'student',
            'active': True,
            'user_class': syllabus_per_class.id
        }) for student in students]

        syllabus_per_class.write({'enrollment_per_class_ids': enrollments})

        if is_elective and syllabus and class_div_id:
            for student_id in students:
                if not self.env['mc.elective.syllabus.students'].search_count([
                    ('syllabus_id', '=', syllabus.id),
                    ('class_id', '=', class_div_id),
                    ('student_id', '=', student_id)
                ]):
                    self.env['mc.elective.syllabus.students'].create({
                        'syllabus_id': syllabus.id,
                        'class_id': class_div_id,
                        'company_id': syllabus.company_id.id,  # Fixed from company to company_id
                        'student_id': student_id,
                        'grade_id': syllabus.class_id.id,
                    })