from odoo import models, fields, api
from datetime import date, datetime
import re
from odoo.exceptions import UserError , ValidationError
from dateutil.relativedelta import relativedelta



class MCEducationStudent(models.Model):
    _inherit = 'education.student'
    
    full_english_name = fields.Char(store=True)
    full_arabic_name = fields.Char(store=True)
    student_national_id = fields.Char(string="Student National ID", size=14, required=True)
    student_code = fields.Char(required=True, copy=False, store= True,)
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete="cascade", )
    place_of_birth = fields.Char(string="Governorate")
    age_next_oct = fields.Char(string="Age Next October", compute="_compute_age_next_oct", store=True)


    religion_id = fields.Many2one('mc.religion', string="Religion")
    birth_certificate_number = fields.Char()
    internal_student = fields.Boolean()
    application_id = fields.Many2one('education.application', string="Application No") 
    need_transportation_facility = fields.Boolean(string = "Need Transportation Facility", default=False)	
    admission_class_id = fields.Many2one('education.class', string="Admission Grade", domain="[('school', '=', company_id)]",
        help="Enter Class to which the admission is seeking")
    grade_id =  fields.Many2one('education.class', string="Grade", domain="[('school', '=', company_id)]")
    academic_year_id = fields.Many2one('education.academic.year')
    student_first_year = fields.Many2one('education.academic.year')
    old_student_year = fields.Many2one('education.academic.year')
    prev_school_id = fields.Many2one('mc.education.institute')
    prev_school_type = fields.Many2one('mc.prev.school.type')
    
    result_block_reason = fields.Many2one('mc.block.reason', string="Result Block Reason")	
    login_email  = fields.Char(string="Login", compute="_get_login_email")
    password  = fields.Char(string="Password")
    seat_number  = fields.Char(string="Seat Number")

    siblings_ids = fields.Many2many(
        'education.student', 'student_sibling_rel',
        'student_id', 'sibling_id', string='Siblings',
        compute="_compute_siblings_ids"
    ) 
    
    is_sibling = fields.Boolean(string="Has Siblings", compute="_compute_is_sibling", store=True)

    @api.depends('siblings_ids')
    def _compute_is_sibling(self):
        for rec in self:
            rec.is_sibling = bool(rec.siblings_ids)
       
    state = fields.Selection([
        ('online-draft', 'Online Draft'),
        ('online-done', 'Online Done'),
        ('draft', 'Draft'),
        ('verification','Verify'),
        ('approve', 'Approve'),
        ('reject', 'Rejected'), ('done', 'Done')
    ], string='State', required=True, default='done',
    track_visibility='onchange', copy=False, help="Stages of admission")
    
    #syllabus_id = fields.Many2one('education.syllabus')         
    
    ############## MC Info
    enrollment_date = fields.Date()
    entrance_year = fields.Many2one('education.academic.year')
    founder_son = fields.Boolean(defualt=False)
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
    worker_son = fields.Boolean(defualt=False)
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
    join_bus = fields.Boolean(defualt=False)
    bus_city = fields.Many2one('mc.bus.city')
    ministry_subject_exempted = fields.Boolean(defualt=False)
    first_school = fields.Many2one('mc.education.institute')
    student_first_school = fields.Many2one('mc.education.institute')
    elem_school = fields.Many2one('mc.education.institute')
    prep_school = fields.Many2one('mc.education.institute')

    student_status = fields.Selection([
        ('new','New'),
        ('passed','Passed'),
        ('passed_stay','Passed Stay'),
        ('stay','Stay'),
        ('left','Left'),
    ])



    father_name = fields.Char()
    father_national_id = fields.Char(size=14)
    father_profession = fields.Char()
    father_mobile = fields.Char()
    father_email = fields.Char()
    father_educational_qualifications = fields.Char()
    father_birthdate = fields.Date(string="Father Birthdate")
    father_governorate = fields.Char(string="Father Governorate")
    father_english_level = fields.Selection([
                                        ('high','High'),
                                        ('medium','Medium'),
                                        ('low','Low')])
    father_status = fields.Selection([('alive','Alive'),('dead','Dead')], default="alive")
    father_religion = fields.Selection([('muslim','Muslim'),('christian','Christian'),('other','Other')], string="Religion")
    father_id = fields.Many2one('res.partner', string="Father ID")

    mother_name = fields.Char()
    mother_national_id = fields.Char(size=14)
    mother_profession = fields.Char()
    mother_mobile = fields.Char()
    mother_email = fields.Char()
    mother_educational_qualifications = fields.Char()
    mother_birthdate = fields.Date(string="Mother Birthdate")
    mother_governorate = fields.Char(string="Mother Governorate")
    mother_english_level = fields.Selection([
                                        ('high','High'),
                                        ('medium','Medium'),
                                        ('low','Low')])
    mother_status = fields.Selection([('alive','Alive'),('dead','Dead')], default="alive")
    mother_religion = fields.Selection([('muslim','Muslim'),('christian','Christian'),('other','Other')], siblings_ids="Religion")
    mother_id = fields.Many2one('res.partner', string="Mother ID")



    

    parent_status = fields.Selection([
                                        ('married','Married'),
                                        ('divorced','Divorced'),
                                        ('نزاع_قضائي','نزاعي قضائي')])
    relation_to_student = fields.Many2one('mc.student.relation')
    guardian = fields.Char()
    reason_of_guardian = fields.Char()
    emergency_mobile = fields.Char()
    detailed_address = fields.Char()
    guardian_note = fields.Text()
    guardian_national_id = fields.Char(size=14)
    guardian_id = fields.Many2one('res.partner')
    guardian_profession = fields.Char()

    unpaid_invoices = fields.Boolean()
    allow_features = fields.Boolean()
    myschool_fees = fields.Boolean()
    financial_note = fields.Char()
    ms_azure_graph_id = fields.Char()
    ldap_object = fields.Char()
    ministry_code = fields.Char()
    


   
    medium_id = fields.Many2one('education.medium',
                                string="Medium", required=False,
                                help="Choose the Medium of class,"
                                     " like English, Hindi etc")
    sec_lang_id = fields.Many2one('education.subject',
                                  string="Second language",
                                  required=False,
                                  help="Choose the Second language",
                                  domain=[('is_language', '=', True)])
    mother_tongue = fields.Char(string="Mother Tongue", required=False,
                                domain=[('is_language', '=', True)],
                                help="Enter Student's Mother Tongue")
    blood_group = fields.Selection(
        [('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('o+', 'O+'),
         ('o-', 'O-'), ('ab-', 'AB-'), ('ab+', 'AB+')],
        string='Blood Group', required=False, help="Blood group of student",
        default='a+', track_visibility='onchange')
    

    elective_syllabus_id = fields.Many2one('education.syllabus',
                                            domain="[('elective', '=', True)]")
    
########### Guardian 
    @api.onchange('relation_to_student')
    def _onchacnge_guardian_relation(self):
        self.guardian_national_id = False
        self.guardian = False
        self.guardian_profession = False

        if self.relation_to_student:
            if self.relation_to_student.name in ['الاب', 'الام']:
                if self.relation_to_student.name == 'الاب':
                    self.guardian_national_id = self.father_national_id 
                    
                    self.update({
                        'guardian': self.father_name,
                        'guardian_profession': self.father_profession 
                    })
                else:
                    self.guardian_national_id = self.mother_national_id
                    self.update({
                        'guardian': self.mother_name,
                        'guardian_profession': self.mother_profession
                    })
########### Class History                 
    @api.onchange('grade_id', 'class_division_id', 'admission_class_id')
    def _onchange_grade_class_divisions(self):
    
        # فحص القيم قبل المتابعة لتجنب الأخطاء
        if not all([self.class_division_id, self.academic_year_id]):
            return

        existing_history = self.env['education.class.history'].search([
            ('academic_year_id', '=', self.academic_year_id.id),
            ('class_id', '=', self.class_division_id.id),
            ('student_id', '=', self._origin.id or self.id)
        ])
                    
        if not existing_history:
            class_history = self.env['education.class.history'].create({
                'academic_year_id': self.academic_year_id.id,
                'class_id': self.class_division_id.id,
                'student_id': self._origin.id or self.id,
            })
            self.class_history_ids |= class_history

        return {
            'value': {
                'class_history_ids': [(6, 0, self.class_history_ids.ids)]
            }
        }
          
    
############# Check Unique of Student Code and seat number

    _sql_constraints = [('unique_st_code', 'UNIQUE(student_code)', "This student's code is already registered.")]
    
    @api.constrains('seat_number', 'grade_id')
    def _check_unique_seat_number_per_class(self):
        for rec in self:
            if rec.seat_number and rec.grade_id:
                existing = self.search([
                    ('id', '!=', rec.id),
                    ('seat_number', '=', rec.seat_number),
                    ('grade_id', '=', rec.grade_id.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        f"Seat number '{rec.seat_number}' is already assigned to another student in the same grade."
                    )

    @api.depends('student_code')
    def _get_login_email(self):
        for rec in self:
            rec.login_email = f"{rec.student_code.strip()}@mc.edu.eg" if rec.student_code else False

    @api.depends('student_national_id', 'date_of_birth')
    def _compute_age_next_oct(self):
        for rec in self:
            if rec.date_of_birth:

                today = date.today()
                next_october = date(today.year, 10, 1)

                if today > next_october:
                    next_october = date(today.year + 1, 10, 1)

                age_difference = relativedelta(next_october, rec.date_of_birth)

                rec.age_next_oct = f"{age_difference.years} year, {age_difference.months} month, {age_difference.days} day"
            else:
                rec.age_next_oct = "" 


################# Get Siblings ids
    @api.depends('father_national_id')
    def _compute_siblings_ids(self):
        for student in self:
            if student._origin.id:  # لو السجل موجود (مش جديد)
                siblings = self.env['education.student'].sudo().search([
                    ('father_national_id', '=', student.father_national_id),
                    ('id', '!=', student._origin.id)
                ])
                student.siblings_ids = siblings
            else:
                student.siblings_ids = False  # للسجلات الجديدة



    def _is_eligible_for_sibling_discount(self):
        for student in self:
            if not student.father_national_id:
                return False
            # جيب الأخوات بس بدون الطالب نفسه
            siblings = student.siblings_ids
            if not siblings:  # لو مفيش أخوات، الطالب مش مؤهل
                return False
            # أضف الطالب نفسه للقايمة عشان نشمله في الترتيب
            all_siblings = siblings + student
            # Sort by birth_date (latest first) and then by id (lowest first for twins)
            sorted_siblings = sorted(all_siblings, key=lambda s: (s.date_of_birth or date.min, s.id))
            youngest = sorted_siblings[-1]  # The last one is the youngest
            twins = [s for s in sorted_siblings if s.date_of_birth == youngest.date_of_birth]
            if len(twins) > 1:  # Twins exist
                # Choose the twin with the lowest id (earliest admission)
                eligible_twin = min(twins, key=lambda s: s.id)
                return student in [eligible_twin, youngest]
            return student == youngest  # Only youngest if no twins