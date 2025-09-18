from odoo import http, models
from odoo.http import request
from datetime import date
import logging
from werkzeug.utils import redirect


_logger = logging.getLogger(__name__)

class AdmissionApplicationController(http.Controller):  

    # First route 'Apply' where the user can select the COMPANY  
    @http.route('/apply', methods=["GET"], type="http", auth="public", csrf=False, website=True)
    def select_company_form(self, **kwargs):
        company_ids = request.env['res.company'].sudo().search([('name', 'ilike', 'Mansoura')])
        student_national_id = kwargs.get('student_national_id')
        existing_application = None
        
        if student_national_id:
            # Search for existing application with this national ID
            existing_application = request.env['education.application'].sudo().search([
                ('student_national_id', '=', student_national_id)
            ], limit=1)

        values = {
            "company_ids": company_ids,
            "existing_application": existing_application
        } 
        return request.render('mc_app.select_company_form_template', values)

    # Form Route
    @http.route('/apply/<int:company_id>', methods=["GET"], type="http", auth="public", csrf=False, website=True)
    def student_admission_application_form(self, company_id, **kwargs):
        company_ids = request.env['res.company'].sudo().search([('name', 'ilike', 'Mansoura')]).ids

        if company_id not in company_ids:
            return redirect('/apply')
        
        # Get company RECORD instead of just ID
        company = request.env['res.company'].sudo().browse(company_id)
        admission_class_ids = request.env['education.class'].sudo().search([('school.id', '=', company_id)])

        # Check if national_id is provided as query parameter
        student_national_id = kwargs.get('student_national_id')
        existing_application = None
        
        if student_national_id:
            # Search for existing application with this national ID
            existing_application = request.env['education.application'].sudo().search([
                ('student_national_id', '=', student_national_id)
            ], limit=1)

        values = {
            "admission_class_ids": admission_class_ids,
            "company_id": company,
            "existing_application": existing_application,
        }
        
        return request.render('mc_app.admission_application_form_template', values)

    @http.route('/submit_student_admission', methods=["POST"], type="http", auth="public", csrf=False, website=True)
    def submit_student_admission(self, **post):
        company_id = None
        try:
            # Safely convert company_id to integer
            company_id_raw = post.get('company_id')
            company_id = self._extract_company_id(company_id_raw)
        
            # Check if this is an update (edit) or new submission
            student_national_id = post.get('student_national_id')

            # Check for existing records
            existing_application = self._get_existing_application(student_national_id)

            if existing_application and existing_application.name and existing_application.company_id:
                return self._render_error_response(
                    company_id,
                    f"You have an application with no {existing_application.name} in the school {existing_application.company_id.name}",
                    f"لديك طلب تقديم رقم {existing_application.name} في المدرسة {existing_application.company_id.name}",
                    existing_application
                )
            
            # Get student sequence
            student_seq = request.env['ir.sequence'].sudo().next_by_code('education.application')
            if not student_seq:
                return self._render_error_response(
                    company_id,
                    "Could not generate student sequence!",
                    "لن نتمكن من انشاء كود الطالب"
                )

            # Basic data
            name = post.get('name')
            admission_class_id = int(post.get('admission_class_ids'))
            prev_school = post.get('prev_school')
            street = post.get('street')
            
            # Validate academic year
            academic_year_id = self._get_current_academic_year()
            if not academic_year_id:
                return self._render_error_response(
                    company_id,
                    "No active academic year found!",
                    "لا يوجد عام دراسي"
                )

            # Extract student data from national ID
            try:
                date_of_birth = request.env['education.application'].sudo().get_birthdate_from_nid(student_national_id)
                place_of_birth = request.env['education.application'].sudo().get_birth_governement_from_nid(student_national_id)
                gender = request.env['education.application'].sudo().get_gender_from_nid(student_national_id)
            except Exception as e:
                _logger.error(f"Invalid student national ID: {str(e)}")
                return self._render_error_response(
                    company_id,
                    "Invalid Student National ID format!",
                    "الرقم القومي للطالب غير صالح"
                )

            # Father's information
            father_data = self._process_parent_information(
                post.get('father_name'),
                post.get('father_profession'),
                post.get('father_educational_qualifications'),
                post.get('father_mobile'),
                post.get('father_email'),
                post.get('father_english_level'),
                post.get('father_national_id'),
                'Father',
                company_id
            )
            
            if isinstance(father_data, http.Response):
                return father_data

            # Mother's information
            mother_data = self._process_parent_information(
                post.get('mother_name'),
                post.get('mother_profession'),
                post.get('mother_educational_qualifications'),
                post.get('mother_mobile'),
                post.get('mother_email'),
                post.get('mother_english_level'),
                post.get('mother_national_id'),
                'Mother',
                company_id
            )
            
            if isinstance(mother_data, http.Response):
                return mother_data

            # Get siblings based on father's national ID
            siblings_ids = request.env['education.student'].sudo().search([
                ('father_national_id', '=', father_data['national_id']),
                ('student_national_id', '!=', student_national_id)
            ])

            # Create student application
            student_application = request.env['education.application'].sudo().create({
                'full_arabic_name': name,
                'state': 'online-draft',
                'company_id': company_id,
                'admission_class_id': admission_class_id,
                'academic_year_id': academic_year_id,
                'student_national_id': student_national_id,
                'date_of_birth': date_of_birth,
                'place_of_birth': place_of_birth,
                'gender': gender,
                'prev_school': prev_school,
                'street': street,
                'siblings_ids': [(6, 0, siblings_ids.ids)],
                'email': f'{student_seq}@mc.edu',

                'father_name': father_data['name'],
                'father_profession': father_data['profession'],
                'father_educational_qualifications': father_data['educational_qualifications'],
                'father_mobile': father_data['mobile'],
                'father_email': father_data['email'],
                'father_english_level': father_data['english_level'],
                'father_national_id': father_data['national_id'],
                'father_birthdate': father_data['birthdate'],
                'father_governorate': father_data['governorate'],

                'mother_name': mother_data['name'],
                'mother_profession': mother_data['profession'],
                'mother_educational_qualifications': mother_data['educational_qualifications'],
                'mother_mobile': mother_data['mobile'],
                'mother_email': mother_data['email'],
                'mother_english_level': mother_data['english_level'],
                'mother_national_id': mother_data['national_id'],
                'mother_birthdate': mother_data['birthdate'],
                'mother_governorate': mother_data['governorate'],
            })
            
            # Get application_id and add it to submit_values
            if student_application:
                submit_values = {
                    "company_id": company_id,
                    "application_id": student_application.name,
                }
                return request.render('mc_app.submission_done_template', submit_values)
            else:
                return self._render_error_response(
                    company_id,
                    "Application not created properly.",
                    "حدث خطأ أثناء إنشاء الطلب"
                )

        except Exception as e:
            _logger.error(f"Error in submit_student_admission: {str(e)}")           
            return self._render_error_response(
                company_id,
                f"An unexpected error occurred: {str(e)}",
                "حدث خطأ غير متوقع"
            )

    @http.route('/update/<int:company_id>', type='http', auth="public", website=True)
    def apply_form(self, company_id, **kwargs):
        # Extract values from URL
        student_national_id = kwargs.get('student_national_id')
        application_id = kwargs.get('application_id')

        # Search for existing_application in database
        existing_application = request.env['education.application'].sudo().search([
            ('id', '=', application_id),
            ('student_national_id', '=', student_national_id),
        ], limit=1)
        
        admission_class_ids = request.env['education.class'].sudo().search([('school.id', '=', company_id)])
        company = request.env['res.company'].sudo().search([('id', '=', company_id)])

        # Pass the object to the Template
        return request.render("mc_app.admission_application_form_template", {
            'existing_application': existing_application,
            "admission_class_ids": admission_class_ids,
            "company_id": company,
        })
    
    @http.route('/update_student_admission', methods=["POST"], type="http", auth="public", csrf=False, website=True)
    def update_student_admission(self, **post):
        company_id = None
        application_id = post.get('application_id')
        try:
            # Safely convert company_id to integer
            company_id_raw = post.get('company_id')
            company_id = self._extract_company_id(company_id_raw)
            
            # احصل على الطلب الموجود أولاً
            existing_application = request.env['education.application'].sudo().browse(int(application_id))
            if not existing_application.exists():
                return self._render_error_response(
                    company_id,
                    "Application not found!",
                    "لم يتم العثور على الطلب"
                )
            
            # Basic data
            name = post.get('name')
            admission_class_id = int(post.get('admission_class_ids'))
            prev_school = post.get('prev_school')
            street = post.get('street')
            student_code = post.get('student_code')
            
            # استخدم الرقم القومي من السجل الموجود (لا تأخذه من POST)
            student_national_id = existing_application.student_national_id
            
            # Validate academic year
            academic_year_id = self._get_current_academic_year()
            if not academic_year_id:
                return self._render_error_response(
                    company_id,
                    "No active academic year found!",
                    "لا يوجد عام دراسي"
                )
            
            # استخدم البيانات الموجودة بالفعل (التاريخ، المكان، الجنس) بدلاً من إعادة حسابها
            date_of_birth = existing_application.date_of_birth
            place_of_birth = existing_application.place_of_birth  
            gender = existing_application.gender

            # Father's information
            father_data = self._process_parent_information(
                post.get('father_name'),
                post.get('father_profession'),
                post.get('father_educational_qualifications'),
                post.get('father_mobile'),
                post.get('father_email'),
                post.get('father_english_level'),
                post.get('father_national_id'),
                'Father',
                company_id
            )
            
            if isinstance(father_data, http.Response):
                return father_data

            # Mother's information
            mother_data = self._process_parent_information(
                post.get('mother_name'),
                post.get('mother_profession'),
                post.get('mother_educational_qualifications'),
                post.get('mother_mobile'),
                post.get('mother_email'),
                post.get('mother_english_level'),
                post.get('mother_national_id'),
                'Mother',
                company_id
            )
            
            if isinstance(mother_data, http.Response):
                return mother_data

            sibling_student = request.env['education.student'].sudo().search([
                ('student_code', '=', student_code),
            ], limit=1)
            
            # Update siblings if sibling_student exists
            if sibling_student:
                existing_application.write({
                    'siblings_ids': [(4, sibling_student.id)],
                })
                
            # Update existing record - لا تحدث البيانات الأساسية للطالب
            existing_application.write({
                'full_arabic_name': name,
                'state': 'online-draft',
                'company_id': company_id,
                'admission_class_id': admission_class_id,
                'academic_year_id': academic_year_id,
                
                # لا تحدث هذه البيانات - خليها كما هي
                # 'student_national_id': student_national_id,  # احذف هذا السطر
                # 'date_of_birth': date_of_birth,              # احذف هذا السطر  
                # 'place_of_birth': place_of_birth,            # احذف هذا السطر
                # 'gender': gender,                            # احذف هذا السطر
                
                'prev_school': prev_school,
                'street': street,                
                
                'father_name': father_data['name'],
                'father_profession': father_data['profession'],
                'father_educational_qualifications': father_data['educational_qualifications'],
                'father_mobile': father_data['mobile'],
                'father_email': father_data['email'],
                'father_english_level': father_data['english_level'],
                'father_birthdate': father_data['birthdate'],
                'father_governorate': father_data['governorate'],

                'mother_name': mother_data['name'],
                'mother_profession': mother_data['profession'],
                'mother_educational_qualifications': mother_data['educational_qualifications'],
                'mother_mobile': mother_data['mobile'],
                'mother_email': mother_data['email'],
                'mother_english_level': mother_data['english_level'],
                'mother_birthdate': mother_data['birthdate'],
                'mother_governorate': mother_data['governorate'],
            })

            submit_values = {
                "existing_application": existing_application,
            }

            return request.render('mc_app.submission_updated_template', submit_values)

        except Exception as e:
            _logger.error(f"Error in update_student_admission: {str(e)}")           
            return self._render_error_response(
                company_id,
                f"An unexpected error occurred: {str(e)}",
                "حدث خطأ غير متوقع"
            )
        
    # Helper methods
    def _extract_company_id(self, company_id_raw):
        """Safely extract numeric company ID from various formats"""
        if isinstance(company_id_raw, str):
            # Handle cases where company_id might be in format "res.company(5,)"
            return int(''.join(filter(str.isdigit, company_id_raw)))
        return int(company_id_raw)
    
    def _get_existing_application(self, student_national_id):
        """Get existing application by student national ID"""
        return request.env['education.application'].sudo().search([
            ('student_national_id', '=', student_national_id)
        ], limit=1)
    
    def _render_error_response(self, company_id, en_reason, ar_reason, existing_application=None):
        """Render error response template with provided reasons"""
        values = {
            'en_reason': en_reason,
            'ar_reason': ar_reason,
            'company_id': company_id,
            'can_edit': existing_application and existing_application.state == "online-draft",
        }
        
        if existing_application:
            values['existing_application'] = existing_application
            
        return request.render('mc_app.submission_failed_template', values)

    
    def _process_parent_information(self, name, profession, educational_qualifications, 
                                  mobile, email, english_level, national_id, parent_type, company_id):
        """Process parent information and validate national ID"""
        try:
            birthdate = request.env['education.application'].sudo().get_birthdate_from_nid(national_id)
            governorate = request.env['education.application'].sudo().get_birth_governement_from_nid(national_id)
            
            return {
                'name': name,
                'profession': profession,
                'educational_qualifications': educational_qualifications,
                'mobile': mobile,
                'email': email,
                'english_level': english_level,
                'national_id': national_id,
                'birthdate': birthdate,
                'governorate': governorate
            }
        except Exception as e:
            _logger.error(f"Invalid {parent_type}'s National ID: {str(e)}")
            return self._render_error_response(
                company_id,
                f"Invalid {parent_type}'s National ID format!",
                f"الرقم القومي لل{'أب' if parent_type == 'Father' else 'أم'} غير صالح"
            )

    def _get_current_academic_year(self):
        """Get current active academic year ID"""
        today = date.today()
        
        academic_year = request.env['education.academic.year'].sudo().search([
            ('ay_start_date', '<=', today),
            ('ay_end_date', '>=', today),
            ('active', '=', True)
        ], limit=1)
        
        return academic_year.id if academic_year else False