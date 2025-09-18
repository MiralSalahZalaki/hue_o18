from odoo import models, fields, api, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import re
from odoo.exceptions import UserError, ValidationError

class MCEducationApplication(models.Model):
    _inherit = 'education.application'


    full_english_name = fields.Char()
    full_arabic_name = fields.Char(required=True)
    student_national_id = fields.Char(string="Student National ID", size=14, required=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 
                             
                              string="Gender",
                              store=True,
                              compute="_get_gender")
  
    
    date_of_birth = fields.Date(string="Student Birthdate", required=True, store=True,
                                   compute='_get_student_bd')
    place_of_birth = fields.Char(string="Governorate", store=True,
                              compute='_get_student_governement')
    age_next_oct = fields.Char(string="Age Next October", compute="_compute_age_next_oct", store=True)

    religion_id = fields.Many2one('mc.religion', string="Religion")
    birth_certificate_number = fields.Char()
    internal_student = fields.Boolean()
    need_transportation_facility = fields.Boolean(string = "Need Transportation Facility", default=False)	

   
    state = fields.Selection([
        ('online-draft', 'Online Draft'),
        ('online-done', 'Online Done'),
        ('draft', 'Draft'),
        ('verification','Verify'),
        ('approve', 'Approve'),
        ('reject', 'Rejected'), ('done', 'Done')
    ], string='State', required=True, default='draft',
    track_visibility='onchange', copy=False, help="Stages of admission")



    ###########Change Required to FALSE

    email = fields.Char(string="Email", required= False,
                        help="Enter E-mail id for contact purpose")
    
    medium_id = fields.Many2one(
        'education.medium', string="Medium", required=False,
        help="Choose the Medium of class, like English, Hindi etc")
    
    sec_lang_id = fields.Many2one('education.subject',
                                  string="Second language", required=False,
                                  domain=[('is_language', '=', True)],
                                  help="Choose the Second language")
    
    mother_tongue = fields.Char(string="Mother Tongue",
                                required=False,
                                help="Enter Student's Mother Tongue")
    
    first_name = fields.Char(string='Name', required=False,
                             help="Enter First name of Student")
    
    mobile = fields.Char(string="Mobile", required=False,
                         help="Enter Mobile num for contact purpose")
    
    blood_group = fields.Selection(
        [('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('o+', 'O+'),
         ('o-', 'O-'), ('ab-', 'AB-'), ('ab+', 'AB+')],
        string='Blood Group', required=False, default='a+',
        track_visibility='onchange', help="Your Blood Group is")
    
    guardian_id = fields.Many2one('res.partner',
                                  string="Guardian", required=False,
                                  domain=[('is_parent', '=', True)],
                                  help="Tell us who will take care of you")
    

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    admission_class_id = fields.Many2one(
        'education.class', string="Class",
        required=False, domain="[('school', '=', company_id)]",
        help="Enter Class to which the admission is seeking")

    ###########END Change Required


    ###########Override in prev school field

    prev_school_id = fields.Many2one('mc.education.institute',
                                    string='Previous Institution',
                                    help="Enter the name of previous "
                                        "institution")
    prev_school = fields.Char()
    



    siblings_ids = fields.Many2many(
        'education.student',       
        'application_sibling_rel',  
        'application_id',           
        'sibling_id',              
        string='Siblings'          
    )


    father_name = fields.Char()
    father_national_id = fields.Char(size=14)
    father_profession = fields.Char()
    father_mobile = fields.Char()
    father_email = fields.Char()
    father_educational_qualifications = fields.Char()
    father_status = fields.Selection([('alive','Alive'),('dead','Dead')], default="alive")
    father_birthdate = fields.Date(string="Father Birthdate", compute='_get_father_bd',store=True)
    father_governorate = fields.Char(string="Father Governorate", compute='_get_father_governement',store=True)
    father_english_level = fields.Selection([
                                        ('high','High'),
                                        ('medium','Medium'),
                                        ('low','Low')])

    mother_name = fields.Char()
    mother_national_id = fields.Char(size=14)
    mother_profession = fields.Char()
    mother_mobile = fields.Char()
    mother_email = fields.Char()
    mother_educational_qualifications = fields.Char()
    mother_status = fields.Selection([('alive','Alive'),('dead','Dead')], default="alive")
    mother_birthdate = fields.Date(string="Mother Birthdate", compute='_get_mother_bd',store=True)
    mother_governorate = fields.Char(string="Mother Governorate", compute='_get_mother_governement',store=True)
    mother_english_level = fields.Selection([
                                        ('high','High'),
                                        ('medium','Medium'),
                                        ('low','Low')])
    

    parent_status = fields.Selection([
                                        ('married','Married'),
                                        ('divorced','Divorced'),
                                        ('نزاع_قضائي','نزاعي قضائي')])
    relation_to_student = fields.Many2one('mc.student.relation')
    guardian = fields.Char()
    guardian_national_id = fields.Char(size=14)
    reason_of_guardian = fields.Char()
    emergency_mobile = fields.Char()
    detailed_address = fields.Char()
    guardian_note = fields.Text()
    #readonly_guardian = fields.Boolean(default=False)


############## Application Info
    enrollment_date = fields.Date(default=fields.Datetime.now,
                                     required=True, help="Date of Enrollment")
    entrance_year = fields.Many2one('education.academic.year',default=lambda self: self._get_current_academic_year())
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
    bus_city = fields.Many2one('mc.bus.city')

    COMPANY_PREFIXES = {
            "Mansoura College 2 International American School": "2",
            "Mansoura College British School": "3",
            "Mansoura College Language School MC": "1",
            "Modern Mansoura College Language Scholl MMC": "4",
        }

    def create_student_code(self):
        for rec in self:
            if rec.company_id:
                company_prefix = self.COMPANY_PREFIXES.get(rec.company_id.name, "0")  
            if rec.entrance_year:
                year_suffix = str(rec.entrance_year.name)[-2:] 
                last_student = self.env['education.student'].search(
                     [('entrance_year', '=', rec.entrance_year.id), ('company_id', '=', rec.company_id.id)], 
                    order='student_code desc', limit=1
                )

            if last_student and last_student.student_code:
                middle_number = int(last_student.student_code[1:4]) + 1  
            else:
                middle_number = 1

            middle_part = str(middle_number).zfill(3)

            return f"{company_prefix}{middle_part}{year_suffix}"


############# Check Validation of Nation Ids 

    _sql_constraints = [('unique_st_national_id', 'UNIQUE(student_national_id)', "This student's national number is already registered.")]

    
############# Basic Functions to get inforamtion from National ID

    def get_birthdate_from_nid(self, national_id):
            if national_id:
                birth_year = "19" + national_id[1:3] if national_id[0] == '2' else "20" + national_id[1:3]
                birth_month = national_id[3:5]
                birth_day = national_id[5:7]
                birthdate_str = f"{birth_year}-{birth_month}-{birth_day}"
                return date.fromisoformat(birthdate_str)
            return False


    def get_birth_governement_from_nid(self, national_id):
        governorate_codes = {
            '01': 'Cairo', '02': 'Alexandria', '03': 'Port Said', '04': 'Suez', '11': 'Damietta',
            '12': 'Dakahlia', '13': 'Sharqia', '14': 'Qalyubia', '15': 'Kafr El Sheikh', '16': 'Gharbia',
            '17': 'Menoufia', '18': 'Beheira', '19': 'Ismailia', '21': 'Giza', '22': 'Beni Suef',
            '23': 'Faiyum', '24': 'Minya', '25': 'Assiut', '26': 'Sohag', '27': 'Qena', '28': 'Aswan',
            '29': 'Luxor', '31': 'Red Sea', '32': 'New Valley', '33': 'Matrouh', '34': 'North Sinai',
            '35': 'South Sinai', '88': 'Outside Egypt'
        }

        if national_id:
            governorate_code = national_id[7:9]
            governorate = governorate_codes.get(governorate_code, 'Unknown')
            return governorate
        return False

    def get_gender_from_nid(self, national_id):
        if national_id:
            gender_digit = int(national_id[12])
            gender = 'male' if gender_digit % 2 != 0 else 'female'
            return gender
        return False
    
 #############  Function to Get Academic Year
   
    def _get_current_academic_year(self):
        today = date.today()
        
        academic_year = self.env['education.academic.year'].sudo().search([
            ('ay_start_date', '<=', today),
            ('ay_end_date', '>=', today),
            ('active', '=', True)
        ], limit=1)
        
        return academic_year.id if academic_year else False

#############  Get inforamtion from National ID - Father

    @api.depends('father_national_id')
    def _get_father_bd(self):
        for rec in self:
            if rec.father_national_id :
                rec.father_birthdate = rec.get_birthdate_from_nid(rec.father_national_id)
            else:
                rec.father_birthdate = False

    @api.depends('father_national_id')
    def _get_father_governement(self):
        for rec in self:
            if rec.father_national_id :
                rec.father_governorate = rec.get_birth_governement_from_nid(rec.father_national_id)
            else:
                    rec.father_governorate = False

    @api.onchange('father_national_id')
    def _get_siblings_by_father_id(self):
        for rec in self:
            if rec.father_national_id:
                siblings = rec.env['education.student'].sudo().search([('father_national_id', '=', rec.father_national_id)])
                rec.siblings_ids = [(6, 0, siblings.ids)]  
                


#############  Get inforamtion from National ID- Mother
    
    @api.depends('mother_national_id')
    def _get_mother_bd(self):
        for rec in self:
            if rec.mother_national_id :
                rec.mother_birthdate = rec.get_birthdate_from_nid(rec.mother_national_id)
            else:
                rec.mother_birthdate = False

    @api.depends('mother_national_id')
    def _get_mother_governement(self):
        for rec in self:
            if rec.mother_national_id :
                rec.mother_governorate = rec.get_birth_governement_from_nid(rec.mother_national_id)
            else:
                    rec.mother_governorate = False                

#############  Get inforamtion from National ID -  Student

    @api.depends('student_national_id')
    def _get_student_bd(self):
        for rec in self:
            if rec.student_national_id:
                rec.date_of_birth = rec.get_birthdate_from_nid(rec.student_national_id)
            else:
                rec.date_of_birth = False

    @api.depends('student_national_id')
    def _get_gender(self):
        for rec in self:
            if rec.student_national_id:
                rec.gender = rec.get_gender_from_nid(rec.student_national_id)
            else:
                rec.gender= False


    @api.depends('student_national_id')
    def _get_student_governement(self):
        for rec in self:
            if rec.student_national_id :
                rec.place_of_birth = rec.get_birth_governement_from_nid(rec.student_national_id)
            else:
                    rec.place_of_birth = False

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


####### Guardian

    @api.onchange('relation_to_student')
    def _onchacnge_guardian_relation(self):
        self.guardian_national_id = False
        self.guardian = False

        if self.relation_to_student:
            if self.relation_to_student.name in ['الاب', 'الام']:
                if self.relation_to_student.name == 'الاب':
                    self.guardian_national_id = self.father_national_id 
                    self.update({
                        'guardian': self.father_name
                    })
                else:
                    self.guardian_national_id = self.mother_national_id
                    self.update({
                        'guardian': self.mother_name
                    })                
        

############### Verify ONLINE
    def action_send_to_verify_online(self):
            for rec in self:
                rec.write({
                    'state': 'online-done'
                })

####### Override Email Validation to make it not required
    @api.model
    def create(self, vals):
        """Overriding the create method and assigning the sequence."""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'education.application') or _('New')
        return super().create(vals)

    @api.constrains('email')
    def _check_email(self):
        """Check email format only if it's provided"""
        for record in self:
            if record.email and not re.match(
                    r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", record.email):
                raise ValidationError(f"Invalid email address: {record.email}")

    
####### Override the original unlink method to bypass the validation
    def unlink(self):
        return super(models.Model, self).unlink()
                    

############# Craete Student aaction

    def action_create_student(self):
        """Create student from the application
            and data and return the student"""
        for rec in self:
            # Get siblings based on father's national ID
            siblings_ids = self.env['education.student'].sudo().search([
                ('father_national_id', '=', rec.father_national_id),
                ('student_national_id', '!=', rec.student_national_id)
            ])

            values = {
                'name': rec.full_arabic_name,                
                'full_arabic_name': rec.full_arabic_name,
                'full_english_name': rec.full_english_name,
                'student_national_id': rec.student_national_id,
                'place_of_birth': rec.place_of_birth,
                'age_next_oct': rec.age_next_oct,
                'religion_id': rec.religion_id.id if rec.religion_id else False,
                'birth_certificate_number': rec.birth_certificate_number,
                'internal_student': rec.internal_student,
                'need_transportation_facility': rec.need_transportation_facility,
                'admission_class_id': rec.admission_class_id.id,
                'grade_id':rec.admission_class_id.id,
                
                'academic_year_id': rec.academic_year_id.id,
                'entrance_year': rec.entrance_year.id,
                'enrollment_date': rec.enrollment_date,
                'bus_city':rec.bus_city.id,
                'founder_son': rec.founder_son,
                'founder_son_level': rec.founder_son_level,
                'worker_son': rec.worker_son,
                'worker_son_level': rec.worker_son_level,
                'join_bus': rec.join_bus,
                'prev_school_id' : rec.prev_school_id.id,
            
                'father_national_id': rec.father_national_id,
                'father_profession': rec.father_profession,
                'father_mobile': rec.father_mobile,
                'father_email': rec.father_email,
                'father_educational_qualifications': rec.father_educational_qualifications,
                'father_birthdate': rec.father_birthdate,
                'father_governorate': rec.father_governorate,
                'father_english_level': rec.father_english_level,
                
                'mother_national_id': rec.mother_national_id,
                'mother_profession': rec.mother_profession,
                'mother_mobile': rec.mother_mobile,
                'mother_email': rec.mother_email,
                'mother_educational_qualifications': rec.mother_educational_qualifications,
                'mother_birthdate': rec.mother_birthdate,
                'mother_governorate': rec.mother_governorate,
                'mother_english_level': rec.mother_english_level,

                'parent_status': rec.parent_status,
                'relation_to_student': rec.relation_to_student.id,
                'guardian': rec.guardian,
                'guardian_national_id':rec.guardian_national_id,
                'reason_of_guardian': rec.reason_of_guardian,
                'emergency_mobile': rec.emergency_mobile,
                'detailed_address': rec.detailed_address,
                'guardian_note': rec.guardian_note,
                'siblings_ids': [(6, 0, siblings_ids.ids)],  # نسخ الإخوة من الطلب

           

                'application_id': rec.id,
                'father_name': rec.father_name,
                'mother_name': rec.mother_name,
                'guardian_id': rec.guardian_id.id,
                'street': rec.street,
                'street2': rec.street2,
                'city': rec.city,
                'state_id': rec.state_id.id,
                'country_id': rec.country_id.id,
                'zip': rec.zip,
                'is_same_address': rec.is_same_address,
                'per_street': rec.per_street,
                'per_street2': rec.per_street2,
                'per_city': rec.per_city,
                'per_state_id': rec.per_state_id.id,
                'per_country_id': rec.per_country_id.id,
                'per_zip': rec.per_zip,
                'gender': rec.gender,
                'date_of_birth': rec.date_of_birth,
                'blood_group': rec.blood_group,
                'nationality_id': rec.nationality_id.id,
                'email': rec.email,
                'mobile': rec.mobile,
                'phone': rec.phone,
                'image_1920': rec.image,
                'is_student': True,
                'medium_id': rec.medium_id.id,
                'caste': rec.caste,
                'sec_lang_id': rec.sec_lang_id.id,
                'mother_tongue': rec.mother_tongue,
                'company_id': rec.company_id.id,
            }
            if not rec.is_same_address:
                pass
            else:
                values.update({
                    'per_street': rec.street,
                    'per_street2': rec.street2,
                    'per_city': rec.city,
                    'per_state_id': rec.state_id.id,
                    'per_country_id': rec.country_id.id,
                    'per_zip': rec.zip,
                })

            student_code = rec.create_student_code()  
            values['student_code'] = student_code 


            partner_vals = {
                'name': rec.full_arabic_name,
                'is_company': False,
                'is_student': True,
                'company_id': rec.company_id.id,
                #'parent_id':rec.company_id,
                'email': rec.email,
                'phone': rec.phone,
                'mobile': rec.mobile,
            }

            student_partner = self.env['res.partner'].create(partner_vals)

            # Add partner id of student to student info
            values['partner_id'] = student_partner.id

            father_is_existing = self.env['education.student'].sudo().search([('father_national_id', '=', rec.father_national_id)], limit=1).exists()
            if father_is_existing and father_is_existing.father_id.id:
                 values['father_id'] = father_is_existing.father_id.id
            else:
                # Create Father partner and Add to student info
                if rec.father_name:
                    father_vals = {
                        'name': rec.father_name,
                        'company_id': rec.company_id.id,
                        #'parent_id':rec.company_id,
                        'is_company': False,
                        'is_parent': True,
                        'phone': rec.father_mobile,
                        'email': rec.father_email,
                    }
                    father_partner = self.env['res.partner'].create(father_vals)
                    values['father_id'] = father_partner.id

            mother_is_existing = self.env['education.student'].sudo().search([('mother_national_id', '=', rec.mother_national_id)], limit=1).exists()
            if mother_is_existing and mother_is_existing.mother_id.id:
                 values['mother_id'] = mother_is_existing.mother_id.id
            else:
            # Create Mother partner and Add to student info
                if rec.mother_name:
                    mother_vals = {
                        'name': rec.mother_name,
                        'company_id': rec.company_id.id,
                        #'parent_id':rec.company_id,
                        'is_company': False,
                        'is_parent': True,
                        'phone': rec.mother_mobile,
                        'email': rec.mother_email,
                    }
                    mother_partner = self.env['res.partner'].create(mother_vals)
                    values['mother_id'] = mother_partner.id


            student = self.env['education.student'].create(values)
            
            rec.write({
                'state': 'done'
            })

            # Update Siblings info
            if rec.siblings_ids:
                # Add the new siblings
                rec.siblings_ids.write({
                    'siblings_ids': [(4, student.id)],
                })

            # For new Student -- add the siblings
            student.write({
                'siblings_ids': [(4, sibling.id) for sibling in rec.siblings_ids],
            })

            return {
                'name': _('Student'),
                'view_mode': 'form',
                'res_model': 'education.student',
                'type': 'ir.actions.act_window',
                'res_id': student.id,
                'context': self.env.context
            }
