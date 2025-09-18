from odoo import models, fields, api
from odoo.exceptions import ValidationError


class IGPeriodicReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.ig_periodic_assessment_template'
    _description = 'IG Periodic Report Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['ig.periodic.report.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_ig_periodic_report_data(wizard)
        print(main_data['syllabus_data'],)
        return {
            'doc_ids': docids,
            'doc_model': 'ig.periodic.report.wizard',
            'docs': [wizard],
            # Main data from wizard
            'students_data':  main_data['students_data'],
            'syllabus_data':  main_data['syllabus_data'],
            'assessment_times':  main_data['assessment_times'],
            'grading_method': main_data['grading_method'],
            'grading_method_comment':   main_data['grading_method_comment'],
            'term_name': wizard.term_id.name if wizard.term_id else None,
            'academic_year': wizard.term_id.academic_year_id.name if wizard.term_id else None,
            'academic_year_obj': wizard.term_id.academic_year_id if wizard.term_id else None,
            'grade_name': wizard.grade_id.name,
            'show_attendance': wizard.show_attendance,
            'top_rank': wizard.top_rank,
            'class_name': wizard.class_id.name if wizard.class_id else 'All Classes',
            'company': wizard.company_id,
            'term': wizard.term_id,
            'grade': wizard.grade_id,
            'class': wizard.class_id,
            'total_students': len( main_data['students_data']),
            'grading_scales':  main_data['grading_scales'], 
        }
    
    def _get_ig_periodic_report_data(self,wizard):
       
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

        syllabus_data = []
        for syllabus in grade_syllabuses:
            # Get syllabus template
            syllabus_template = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('school_year_id', '=', wizard.term_id.academic_year_id.id)
            ], limit=1)
            
            assessments_list = []
            if syllabus_template:
                for assess in syllabus_template.assessments_category_id:
                    assess_max_score = 0.0
                    
                    # البحث في custom_grade_distribution_template أولاً
                    dist_template = syllabus_template.custom_grade_distribution_template.filtered(
                        lambda x: x.item and x.item.assessment 
                    )
                    
                    if dist_template and dist_template.report_mark and dist_template.report_mark > 0:
                        assess_max_score = dist_template.report_mark
                    elif dist_template.report_mark  == 0:
                        # استخدام الـ max_score الأصلي من assessment
                        assess_max_score = assess.max_score if hasattr(assess, 'max_score') else 0.0
                    
                    assess_info = {
                        'id': str(assess.id),
                        'name': assess.item.name if hasattr(assess, 'item') and assess.item and hasattr(assess.item, 'name') and assess.item.name else 'N/A',
                        'max_score': assess_max_score,
                    }
                    assessments_list.append(assess_info)

            syllabus_data.append({
                'syllabus_id': str(syllabus.id),
                'syllabus_name': syllabus.name,
                'certificate_name': syllabus.certificate_name or syllabus.name,
                'is_elective': syllabus.elective,
                'assessments': assessments_list,
            })

        students_data = []
        for index, student in enumerate(students, 1):
            # Get elective syllabus for this student
            elective_syllabuses = self.env['mc.elective.syllabus.students'].sudo().search([
                ('student_id', '=', student.id),
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id)
            ]).mapped('syllabus_id.id')

            student_data = {
                'serial_no': index,
                'student': student.full_english_name,
                'student_code': student.student_code or '',
                'class_name': student.class_division_id.name if student.class_division_id else '',
                'grade_name': student.grade_id.name if student.grade_id else '',
                'seat_number': student.seat_number,
                'subjects_results': {},  
                'registered_subjects': [str(syllabus_id) for syllabus_id in elective_syllabuses],
                'absence_days': {}
            }

            # Get absence days for each assessment time
            for assessment_time in wizard.assessments_times:
                if assessment_time.start_date and assessment_time.end_date:
                    absence_days = self.env['education.attendance.line'].sudo().search_count([
                        ('company_id', '=', wizard.company_id.id),
                        ('student_id', '=', student.id),
                        ('class_id', '=', wizard.grade_id.id),
                        ('division_id', '=', student.class_division_id.id),
                        ('date', '>=', assessment_time.start_date),
                        ('date', '<=', assessment_time.end_date),
                        ('present_morning', '=', False),
                        ('sickness_absence', '=', False)
                    ])
                    student_data['absence_days'][str(assessment_time.id)] = absence_days

            for assessment_time in wizard.assessments_times:
                # البحث في mc.evaluation.grades بدلاً من acc.student.monthly.grades
                evaluation_grades = self.env['mc.evaluation.grades'].sudo().search([
                    ('company_id', '=', wizard.company_id.id),
                    ('grade_id', '=', wizard.grade_id.id),
                    ('class_id', '=', student.class_division_id.id) if student.class_division_id else ('class_id', '!=', False),
                    ('assessments_times', '=', assessment_time.id),
                    ('state', '=', 'done')  # فقط السجلات المؤكدة
                ])

                # Initialize subjects results for this assessment time
                assessment_time_id = str(assessment_time.id)
                student_data['subjects_results'][assessment_time_id] = {}

                # Process evaluation grades records
                for eval_grade in evaluation_grades:
                    # البحث عن درجة الطالب في هذا التقييم
                    student_grade = eval_grade.student_list.filtered(lambda s: s.student_id.id == student.id)
                    if student_grade:
                        syllabus = eval_grade.syllabus_id
                        subject_id = str(syllabus.id)
                        
                        # تحقق من المواد الاختيارية
                        if syllabus.elective and subject_id not in student_data['registered_subjects']:
                            continue

                        # الحصول على الـ max score الصحيح من التمبلت
                        template_max_score = 0.0
                        
                        # البحث في التمبلت لهذا الـ syllabus
                        syllabus_template = self.env['mc.custom.template'].sudo().search([
                            ('company_id', '=', wizard.company_id.id),
                            ('grade_id', '=', wizard.grade_id.id),
                            ('syllabus_id', '=', syllabus.id),
                            ('school_year_id', '=', wizard.term_id.academic_year_id.id)
                        ], limit=1)
                        
                        if syllabus_template:
                            # البحث عن الـ distribution أو assessment في التمبلت
                            if eval_grade.distribution_id:
                                # البحث في custom_grade_distribution_template
                                dist_template = syllabus_template.custom_grade_distribution_template.filtered(
                                    lambda x: x.id == eval_grade.distribution_id.id
                                )
                                if dist_template and dist_template.report_mark and dist_template.report_mark > 0:
                                    template_max_score = dist_template.report_mark
                            
                                elif template_max_score == 0.0 and eval_grade.assessments_category_id:
                                    # البحث في assessments_category_id
                                    assess_template = syllabus_template.assessments_category_id.filtered(
                                        lambda x: x.id == eval_grade.assessments_category_id.id
                                    )
                                    if assess_template and assess_template.max_score:
                                        template_max_score = assess_template.max_score

                        # إذا لم نجد max score من التمبلت، استخدم الـ custom_max_score من الـ evaluation
                        if template_max_score == 0.0:
                            template_max_score = eval_grade.custom_max_score or 0.0

                        # الحصول على النتيجة الأساسية
                        raw_score = 0.0
                        eval_max_score = eval_grade.custom_max_score or 0.0
                        
                        # إذا كان التقييم رقمي
                        if eval_grade.grading_method_type == 'numeric':
                            try:
                                raw_score = float(student_grade.score) if student_grade.score else 0.0
                            except (ValueError, TypeError):
                                raw_score = 0.0
                        # إذا كان التقييم برموز
                        elif eval_grade.grading_method_type == 'evaluation' and student_grade.score_selection:
                            # استخدام القيمة الوسطى للمدى
                            raw_score = (student_grade.score_selection.minimum + student_grade.score_selection.maximum) / 2
                            eval_max_score = eval_grade.custom_max_score or 100.0
                        
                        # حساب الـ scaled score
                        scaled_score = 0.0
                        if eval_max_score > 0 and template_max_score > 0:
                            scaling_factor = template_max_score / eval_max_score
                            scaled_score = raw_score * scaling_factor
                        else:
                            scaled_score = raw_score
                        
                        # Apply custom rounding logic to scaled score
                        if scaled_score > 0:
                            decimal_part = scaled_score % 1
                            if 0.01 < decimal_part < 0.5:
                                scaled_score = int(scaled_score) + 0.5
                            elif 0.5 <= decimal_part < 1:
                                scaled_score = int(scaled_score) + 1

                        # إذا لم يكن الموضوع موجود، أنشئه
                        if subject_id not in student_data['subjects_results'][assessment_time_id]:
                            student_data['subjects_results'][assessment_time_id][subject_id] = {
                                'score': 0.0,
                                'max_score': 0.0,
                                'assessments': {},
                                'total_subject_score': 0.0,
                            }

                        # إضافة درجة التقييم كـ assessment منفرد
                        assess_key = str(eval_grade.assessments_category_id.id) if eval_grade.assessments_category_id else str(eval_grade.distribution_id.id)
                        
                        student_data['subjects_results'][assessment_time_id][subject_id]['assessments'][assess_key] = {
                            'score': scaled_score,
                            'max_score': template_max_score,
                            'raw_score': raw_score,  # الدرجة الأصلية للمراجعة
                            'eval_max_score': eval_max_score,  # الدرجة القصوى في التقييم
                        }
                     
                        # تحديث المجموع الكلي
                        student_data['subjects_results'][assessment_time_id][subject_id]['score'] += scaled_score
                        student_data['subjects_results'][assessment_time_id][subject_id]['max_score'] += template_max_score
                        student_data['subjects_results'][assessment_time_id][subject_id]['total_subject_score'] += scaled_score

            students_data.append(student_data)

        # Get grading method info
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id),
            ('school_year_id', '=', wizard.term_id.academic_year_id.id)
        ], limit=1)
        
        # Get grading scales for legend
        grading_scales = []
        if grading_method and grading_method.grading_method == 'evaluation':
            for scale in grading_method.grading_scale_id:
                grading_scales.append({
                    'symbol': scale.symbol,
                    'description': scale.description,
                    'color': scale.color,
                    'minimum': scale.minimum,
                    'maximum': scale.maximum,
                })

        assessment_times = []
        for time in wizard.assessments_times:
            assessment_times.append({
                'id': time.id,
                'name': time.name,
                'start_date': time.start_date,
                'end_date': time.end_date,
                'distribution': time.distribution if hasattr(time, 'distribution') else False,
            })

        return {
            'students_data': students_data,
            'syllabus_data': syllabus_data,
            'assessment_times': assessment_times,
            'grading_method': grading_method.grading_method if grading_method else 'numeric',
            'grading_method_comment': grading_method.comment if grading_method else '',
       
            'total_students': len(students_data),
            'grading_scales': grading_scales,  # إضافة grading_scales للاستخدام في التقرير
        }