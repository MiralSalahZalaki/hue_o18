from odoo import models, api

class IGTotalTermReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.ig_total_term_template'
    _description = 'IG Total Term Report Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['ig.total.term.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_main_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'ig.total.term.wizard',
            'docs': [wizard],
            # Main data
            'students_data': main_data['students_data'],
            'syllabus_data': main_data['syllabus_data'],
            'grade_syllabuses': main_data['grade_syllabuses'],
            # Wizard fields
            'grading_method_type': self._get_grading_method(wizard),
            'term_name': wizard.term_id.name,
            'academic_year': wizard.term_id.academic_year_id.name,
            'grade_name': wizard.grade_id.name,
            'class_name': wizard.class_id.name if wizard.class_id else '',
            'company': wizard.company_id,
            'total_students': len(main_data['students_data']),
            'system_type': main_data['system_type']
        }
    
    def _get_grading_method(self, wizard):
        """Get grading method from wizard"""
        return wizard.get_garding_method()
    
    def _prepare_main_data(self, wizard):
        """Prepare main report data"""
        # Prepare Students List
        student_domain = [
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id)
        ]
        if wizard.class_id:
            student_domain.append(('class_division_id', '=', wizard.class_id.id))
        
        students = self.env['education.student'].sudo().search(student_domain, order="seat_number")
        if wizard.student_ids:
            students = wizard.student_ids

        # Prepare Grade Syllabus List with assessments
        grade_syllabuses = self.env['education.syllabus'].sudo().search([
            ('company_id', '=', wizard.company_id.id),
            ('class_id', '=', wizard.grade_id.id),
            ('hidden_management_report', '=', False)
        ])
                
        # Get grading method info
        grading_method_type = wizard.get_garding_method()
        
        # Prepare syllabus data based on grading method
        syllabus_data = self._prepare_syllabus_data(wizard, grade_syllabuses, grading_method_type)
        
        # Prepare students data
        students_data = self._prepare_students_data(wizard, students, grading_method_type, syllabus_data)

        return {
            'students_data': students_data,
            'syllabus_data': syllabus_data,
            'grade_syllabuses': grade_syllabuses,
            'system_type': 'british'  
        }

    def _prepare_syllabus_data(self, wizard, grade_syllabuses, grading_method_type):
        """Prepare syllabus data based on grading method"""
        syllabus_data = []

        if grading_method_type == 'numeric':
            syllabus_data = self._prepare_numeric_syllabus_data(wizard, grade_syllabuses)
        elif grading_method_type == 'q_colors':
            syllabus_data = self._prepare_qcolors_syllabus_data(wizard, grade_syllabuses)

        return syllabus_data

    def _prepare_numeric_syllabus_data(self, wizard, grade_syllabuses):
        """Prepare syllabus data for numeric system"""
        syllabus_data = []
        
        for syllabus in grade_syllabuses:
            syllabus_template = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('school_year_id', '=', wizard.term_id.academic_year_id.id)
            ], limit=1)

            # تحديد لو المادة one_weight ولا لأ
            syllabuses_no_add_total = False
            if syllabus_template:
                distributions = syllabus_template.custom_grade_distribution_template
                if len(distributions) == 1 and distributions[0].weight == 100:
                    syllabuses_no_add_total = True
                elif any(dist.weight == 100 for dist in distributions):
                     syllabuses_no_add_total = True

            syllabus_info = {
                'id': syllabus.id,
                'name': syllabus.name,
                'elective': syllabus.elective if hasattr(syllabus, 'elective') else False,
                'syllabuses_no_add_total': syllabuses_no_add_total, 
                'british_categories': {
                    'monthly': {'name': 'Monthly'},
                    'weekly': {'name': 'Weekly'}, 
                    'exam': {'name': 'Exam'}
                }
            }
            syllabus_data.append(syllabus_info)

        return syllabus_data

    def _prepare_qcolors_syllabus_data(self, wizard, grade_syllabuses):
        """Prepare syllabus data for q_colors system"""
        syllabus_data = []
        
        for syllabus in grade_syllabuses:
            syllabus_template = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('school_year_id', '=', wizard.term_id.academic_year_id.id)
            ], limit=1)

            if syllabus_template:
                syllabus_info = {
                    'id': syllabus.id,
                    'name': syllabus.name,
                    'elective': syllabus.elective if hasattr(syllabus, 'elective') else False,
                    'distributions': [
                        {
                            'id': str(dist.id),
                            'name': dist.item.name if hasattr(dist, 'item') and dist.item and hasattr(dist.item, 'name') and dist.item.name else 'N/A'
                        }
                        for dist in syllabus_template.custom_grade_distribution_template
                        if (
                            hasattr(dist, 'item') and dist.item and hasattr(dist.item, 'assessment') and not dist.item.assessment
                            and
                            hasattr(dist, 'control') and dist.control != 'project'
                        )
                    ],
                    'assessments': [
                        {
                            'id': str(assess.id),
                            'name': assess.item.name if hasattr(assess, 'item') and assess.item and hasattr(assess.item, 'name') and assess.item.name else 'N/A',
                            'hidden_student_report': assess.item.hidden_student_report if hasattr(assess, 'item') and assess.item and hasattr(assess.item, 'hidden_student_report') and assess.item.hidden_student_report else False,
                        }
                        for assess in syllabus_template.assessments_category_id
                    ],
                    'maximum': syllabus_template.maximum or 0.0,
                    'dist_ass_len': len(syllabus_template.assessments_category_id) + len(syllabus_template.custom_grade_distribution_template)
                }
                syllabus_data.append(syllabus_info)

        return syllabus_data

    def _prepare_students_data(self, wizard, students, grading_method_type, syllabus_data):
        """Prepare students data"""
        students_data = []
        
        for index, student in enumerate(students, 1):
            st_acc_record = self.env['acc.student.term.grades'].search([
                ('company_id', '=', wizard.company_id.id),
                ('student_id', '=', student.id),
                ('term_id', '=', wizard.term_id.id),
                ('grade_id', '=', wizard.grade_id.id)
            ], limit=1)

            # جلب المواد الاختيارية المسجلة للطالب
            elective_syllabuses = self.env['mc.elective.syllabus.students'].search([
                ('student_id', '=', student.id),
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id)
            ]).mapped('syllabus_id.id')

            # حساب المجموع الكلي والحد الأقصى للمواد التي تضاف للمجموع
            total_score, total_max = self._calculate_student_total(
                st_acc_record, elective_syllabuses, syllabus_data
            )

            student_data = {
                'serial_no': index,
                'name': student.full_english_name,
                'seat_number': getattr(student, 'seat_number', '') or '',
                'grade': getattr(student.grade_id, 'name', '') if student.grade_id else '',
                'total_score': total_score,
                'total_max': total_max,
                'subjects_results': {},
                'registered_subjects': [str(syllabus_id) for syllabus_id in elective_syllabuses]
            }

            # Prepare subject results based on grading method
            if st_acc_record:
                if grading_method_type == 'numeric':
                    student_data['subjects_results'] = self._prepare_student_numeric_results(
                        st_acc_record, student_data['registered_subjects'], wizard
                    )
                elif grading_method_type == 'q_colors':
                    student_data['subjects_results'] = self._prepare_student_qcolors_results(
                        st_acc_record, student_data['registered_subjects'], wizard
                    )

            students_data.append(student_data)

        return students_data

    def _calculate_student_total(self, st_acc_record, elective_syllabuses, syllabus_data):
        """Calculate total score and max for subjects that should be added to total"""
        total_score = 0.0
        total_max = 0.0
        
        if not st_acc_record:
            return total_score, total_max
        
        # إنشاء خريطة للمواد التي لا تضاف للمجموع
        no_add_total_subjects = {}
        for syllabus in syllabus_data:
            if syllabus.get('syllabuses_no_add_total', False):
                no_add_total_subjects[str(syllabus['id'])] = True
        
        # حساب المجموع للمواد المؤهلة
        for subject_line in st_acc_record.subject_line_ids:
            subject_id = str(subject_line.syllabus_id.id)
            syllabus = self.env['education.syllabus'].browse(int(subject_id))
            
            # تخطي المواد الاختيارية غير المسجلة
            if hasattr(syllabus, 'elective') and syllabus.elective and int(subject_id) not in elective_syllabuses:
                continue
            
            # تخطي المواد التي لا تضاف للمجموع
            if subject_id in no_add_total_subjects:
                continue
                
            # إضافة درجة المادة للمجموع
            total_score += subject_line.total_subject_score or 0.0
            total_max += subject_line.total_subject_max or 0.0
        
        return total_score, total_max

    def _prepare_student_numeric_results(self, st_acc_record, registered_subjects, wizard):
        """Prepare student results for numeric system"""
        subjects_results = {}
        
        for subject_line in st_acc_record.subject_line_ids:
            subject_id = str(subject_line.syllabus_id.id)
            syllabus = self.env['education.syllabus'].browse(int(subject_id))
            
            # Skip elective subjects if not registered
            if hasattr(syllabus, 'elective') and syllabus.elective and subject_id not in registered_subjects:
                continue

            subjects_results[subject_id] = {
                'british_monthly': subject_line.british_monthly or 0.0,
                'british_monthly_max': subject_line.british_monthly_max or 0.0,
                'british_weekly': subject_line.british_weekly or 0.0,
                'british_weekly_max': subject_line.british_weekly_max or 0.0,
                'british_exam': subject_line.british_exam or 0.0,
                'british_exam_max': subject_line.british_exam_max or 0.0,
                'british_total': subject_line.british_total or 0.0,
                'british_total_max': subject_line.british_total_max or 0.0,
                'total': subject_line.total_subject_score or 0.0,
                'final_mark_from_6': (subject_line.total_subject_score * 6) / subject_line.total_subject_max if subject_line.total_subject_max else 0.0,
                'max_score': subject_line.total_subject_max or 0.0,
                'grade': subject_line.grading_info or ''
            }

        return subjects_results

    def _prepare_student_qcolors_results(self, st_acc_record, registered_subjects, wizard):
        """Prepare student results for q_colors system"""
        subjects_results = {}
        
        for subject_line in st_acc_record.subject_line_ids:
            subject_id = str(subject_line.syllabus_id.id)
            syllabus = self.env['education.syllabus'].browse(int(subject_id))
            if syllabus.elective and subject_id not in registered_subjects:
                continue

            assessments_data = {}
            for assess_line in subject_line.assessment_line_ids:
                assessments_data[str(assess_line.assessment_id.id)] = {
                    'score': round(assess_line.score, 2) or 0.0,
                    'max_score': assess_line.max_score or 0.0,
                    'description': assess_line.description or "",
                }
                
            distributions_data = {}
            for dist_line in subject_line.distribution_line_ids:
                distributions_data[str(dist_line.distribution_id.id)] = {
                    'score': dist_line.score or 0.0,
                    'max_score': dist_line.max_score or 0.0,
                    'description': dist_line.description or "",
                }
                
            subjects_results[subject_id] = {
                'assessments': assessments_data,
                'distributions': distributions_data,
                'total': subject_line.total_subject_score or 0.0,
                'max_score': subject_line.total_subject_max or 0.0, 
            }

        return subjects_results