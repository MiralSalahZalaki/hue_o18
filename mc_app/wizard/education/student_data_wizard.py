from odoo import models, fields, api
from datetime import datetime, date


class StudentDataWizard(models.TransientModel):
    _name = 'student.data.wizard'
    _description = 'Student Data Report Wizard'

    title = fields.Char(string="Title")
    report_view = fields.Selection([
        ('en','English ltr'),
        ('ar','Arabic rtl'),
    ], default='en', string="Report View", required=True)
    company_id = fields.Many2one('res.company', string='School',default=lambda self: self.env.company)
    display_name = fields.Selection([('en','English'),('ar','Arabic')], default='en', string="Display Name", required=True)
    
    student_status = fields.Selection([
        ('all','All'),
        ('new','New'),
        ('passed','Passed'),
        ('passed-stay','Passed Stay'),
        ('stay','Stay'),
        ('left','Left'),
    ] , default='all',string="Enrollment Status", required=True)
    grade_id = fields.Many2one('education.class', string="Grade")

    code = fields.Char(string="Identification Code")
    full_name = fields.Char(string="Full Name")
    first_name = fields.Char(string="First Name")
    surname = fields.Char(string="Surname")
    birth_date = fields.Date(string="Birth Date")
    gender = fields.Selection([
        ('male','Male'),
        ('female','Female'),
    ], string="Gender")
    entrance_year = fields.Many2one('education.academic.year', string="Entrance Year")
    enrollment_date = fields.Date(string="Enrollment Date")
    city = fields.Char()
    founder_son = fields.Boolean(default=False)
    founder_son_level = fields.Selection([
        ('1','Level 1'),
        ('2','Level 2'),
        ('3','Level 3'),
        ('4','Level 4'),
        ('5','Level 5'),
        ('6','Level 6'),
        ('7','Level 7'),
        ('8','Level 8'),
        ('9','Level 9'),
        ('10','Level 10'),
    ])
    worker_son = fields.Boolean(default=False)
    worker_son_level = fields.Selection([
        ('1','Level 1'),
        ('2','Level 2'),
        ('3','Level 3'),
        ('4','Level 4'),
        ('5','Level 5'),
        ('6','Level 6'),
        ('7','Level 7'),
        ('8','Level 8'),
        ('9','Level 9'),
        ('10','Level 10'),
    ])
    join_bus = fields.Boolean(default=False)
    bus_city_id = fields.Many2one('mc.bus.city')
    year_next_oct = fields.Char()

    prev_school = fields.Many2one('mc.education.institute', string="Previous School")
    prev_school_type = fields.Many2one('mc.prev.school.type', string="Previous School")
    first_school = fields.Many2one('mc.education.institute', string="Financial First School")
    student_first_school = fields.Many2one('mc.education.institute', string="Student First School")
    ministry_exmpt = fields.Boolean(string="Ministry Exmpt")
    nationality = fields.Many2one('res.country', string="Nationality")
    parent_status = fields.Selection([
                                        ('married','Married'),
                                        ('divorced','Divorced'),
                                        ('نزاع_قضائي','نزاعي قضائي')])
    old_entrance_year = fields.Many2one('education.academic.year', string="Old Entrance Year")
    
    religion = fields.Many2one('mc.religion', string="Religion")
    is_sibling = fields.Boolean(string="Sibling")
    archived = fields.Boolean(string="Archived")
    age_details = fields.Boolean(string="Age Details")
    school_transferred_to = fields.Many2one('mc.education.institute', string="Transferred School")
    left_date_from = fields.Date(string="Left Date From")
    left_date_to = fields.Date(string="Left Date To")
    per_page = fields.Char(string="Per Page")

    FIXED_SELECTION = [
    ('student_code', 'Code'),
    ('grade_id', 'Grade'),
    ('class_division_id', 'Class'),
    ('name', 'First Name'),
    ('last_name', 'Surname'),
    ('father_id', 'Father Name'),
    ('full_english_name', 'English Full Name'),
    ('full_arabic_name', 'Arabic Full Name'),
    ('place_of_birth', 'Place of Birth'),
    ('mobile', 'Student Mobile'),
    ('father_mobile', 'Father Mobile'),
    ('father_email', 'Father Email'),
    ('father_profession', 'Father Job'),
    ('mother_id', 'Mother Name'),
    ('mother_mobile', 'Mother Mobile'),
    ('mother_email', 'Mother Email'),
    ('mother_profession', 'Mother Job'),
    ('entrance_year', 'Entrance Year'),
    ('street', 'Home Address'),
    ('state_id', 'District'),
    ('city', 'City Address'),
    ('phone', 'Telephone'),
    ('student_national_id', 'National ID'),
    ('date_of_birth', 'Date of Birth'),
    ('religion_id', 'Religion'),
    ('nationality_id', 'Nationality'),
    ('year_next_oct', 'Age in First of October'),
    ('street2', 'Suburb'),
    ('enrollment_date', 'Applicant Date'),
    ('create_date', 'Create Date'),
    ('join_bus', 'Join Bus'),
    ('bus_city', 'Bus City'),
    ('gender', 'Gender'),
    ('founder_son', 'Founder Son'),
    ('worker_son', 'Worker Son'),
    ('first_school', 'Financial First School'),
    ('student_first_school', 'Student First School'),
    ('prev_school_id', 'Previous School'),
    ('prev_school_type', 'Previous School Type'),
    ('parent_status', 'Parent Status'),
    ('is_sibling', 'Sibling'),
    ('father_national_id', 'Father National ID'),
    ('mother_national_id', 'Mother National ID'),
    ('password', 'Password'),
    ('old_entrance_year', 'Old Entrance Year'),
    ('guardian', 'Guardian Name'),
    ('reason_of_guardian', 'Reason of Guardian'),
    ('relation_to_student', 'Relation to Student'),
    ('seat_number', 'Seat Number'),
    ('student_status', 'Student Status'),
    ('email', 'Student Email'),

]
    first_field = fields.Selection(FIXED_SELECTION, string="First Field", default ="student_code")
    second_field = fields.Selection(FIXED_SELECTION, string="Second Field", default ="grade_id")
    third_field = fields.Selection(FIXED_SELECTION, string="Third Field", default ="class_division_id")
    fourth_field = fields.Selection(FIXED_SELECTION, string="Fourth Field")
    fifth_field = fields.Selection(FIXED_SELECTION, string="Fifth Field")
    sixth_field = fields.Selection(FIXED_SELECTION, string="Sixth Field")
    seven_field = fields.Selection(FIXED_SELECTION, string="Seventh Field")
    eighth_field = fields.Selection(FIXED_SELECTION, string="Eighth Field")
    ninth_field = fields.Selection(FIXED_SELECTION, string="Ninth Field")
    tenth_field = fields.Selection(FIXED_SELECTION, string="Tenth Field")
    order_by = fields.Selection([
    ('first_name', 'First Name'),
    ('last_name', 'Surname'),  
    ('full_english_name', 'English Full Name'),
    ('full_arabic_name', 'Arabic Full Name'),
    ('date_of_birth desc', 'Age (Ascending)'),  
    ('date_of_birth', 'Age (Descending)'),
    ('enrollment_date', 'Enrollment Date'),  
    ('create_date', 'Creation Date'),
    ('admission_class_id', 'Grades')
], string="Order By", default = 'full_english_name')

    class_division_id = fields.Many2one('education.class.division', 
                                   string="Class",
                                   domain="[('class_id', '=', grade_id)]")
    student_id = fields.Many2one('education.student', 
                                string="Student",
                                domain="[('grade_id', '=', grade_id),('class_division_id','=',class_division_id)]")
    student_resultes = fields.One2many('education.student', compute="_compute_students_result")

    
    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.student_id = False
        self.class_division_id = False

    @api.onchange('class_division_id')
    def _onchange_class_division(self):
        self.student_id = False

    @api.onchange('student_id')
    def _onchange_student_id(self):
        self.code = self.student_id.student_code

    @api.onchange('code')
    def _onchange_code(self):
        self.student_id = self.env['education.student'].sudo().search([('student_code','=',self.code)])

    @api.depends('grade_id', 'class_division_id', 'code', 'student_id')
    def _compute_students_result(self):
        for rec in self:
            domain = [('company_id','=',rec.company_id.id)]
            
            # البحث حسب الصف
            if rec.grade_id:
                domain.append(('grade_id', '=', rec.grade_id.id))
                
            # البحث حسب الفصل
            if rec.class_division_id:
                domain.append(('class_division_id', '=', rec.class_division_id.id))
                
            # البحث حسب كود الطالب
            if rec.code:
                domain.append(('student_code', '=', rec.code))

            # البحث حسب كود النوع
            if rec.gender:
                domain.append(('gender', '=', rec.gender))

            #البحث حسب كود الديانه 
            if rec.religion:
                domain.append(('religion_id', '=', rec.religion.id))

            if rec.enrollment_date:
                domain.append(('enrollment_date', '=', rec.enrollment_date))    

            if rec.city:
                domain.append(('city', '=', rec.city))    

            if rec.join_bus:
                domain.append(('join_bus', '=', rec.join_bus))    

            if rec.bus_city_id:
                domain.append(('bus_city', '=', rec.bus_city_id.id))    

            if rec.founder_son:
                domain.append(('founder_son', '=', rec.founder_son))    

            if rec.founder_son_level:
                domain.append(('founder_son_level', '=', rec.founder_son_level))    

            if rec.worker_son:
                domain.append(('worker_son', '=', rec.worker_son))    

            if rec.worker_son_level:
                domain.append(('worker_son_level', '=', rec.worker_son_level))    

            if rec.student_first_school:
                domain.append(('student_first_school', '=', rec.student_first_school.id))    

            if rec.first_school:
                domain.append(('first_school', '=', rec.first_school.id))    

            if rec.prev_school:
                domain.append(('prev_school', '=', rec.prev_school.id))    

            if rec.prev_school_type:
                domain.append(('prev_school_type', '=', rec.prev_school_type.id))    

            if rec.nationality:
                domain.append(('nationality_id', '=', rec.nationality.id))    

            if rec.ministry_exmpt:
                domain.append(('ministry_subject_exempted', '=', rec.ministry_exmpt))    

            if rec.parent_status:
                domain.append(('parent_status', '=', rec.parent_status))    

            if rec.religion:
                domain.append(('religion_id', '=', rec.religion.id))    

            if rec.is_sibling:
               domain.append(('is_sibling', '=', rec.is_sibling))

            if rec.birth_date:
               domain.append(('date_of_birth', '=', rec.birth_date))

            if rec.first_name:
                domain += ['|',
                        ('full_english_name', 'ilike', rec.first_name),
                        ('full_arabic_name', 'ilike', rec.first_name)]
                
            if rec.full_name:
                domain += ['|',
                        ('full_english_name', 'ilike', rec.full_name),
                        ('full_arabic_name', 'ilike', rec.full_name)]
            
            if rec.surname:
                domain += ['|',
                        ('full_english_name', 'ilike', '%' + rec.surname),
                        ('full_arabic_name', 'ilike', '%' + rec.surname)]   

            if rec.entrance_year:
               domain.append(('entrance_year', '=', rec.entrance_year.id))

            if rec.old_entrance_year:
               domain.append(('old_student_year', '=', rec.old_entrance_year.id))

            if rec.archived:
               domain.append(('active', '=', False))

            if rec.year_next_oct:
                domain.append(('age_next_oct', 'ilike', rec.year_next_oct + ' year'))

  
            # البحث حسب الطالب المحدد مباشرة
            if rec.student_id:
                domain.append(('id', '=', rec.student_id.id))
                
            order = rec.order_by
            rec.student_resultes = self.env['education.student'].sudo().search(domain, order=order)

        
    def generate_student_report(self):
        return self.env.ref('mc_app.action_report_student_data_template').report_action(self)
