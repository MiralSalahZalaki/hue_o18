from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCStudentReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.report_mc_student_result_template'
    _description = 'MC Student Report Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['mc.student.result.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_mc_student_result_report_data(wizard)
        
        # Get grading method info
        grading_method_info = self._get_grading_method_info(wizard, main_data)
        
        return {
            'doc_ids': docids,
            'doc_model': 'mc.student.result.wizard',
            'docs': [wizard],
            # Main data from wizard
            'students_data': main_data['students_data'],
            'syllabus_data': main_data['syllabus_data'],
            'grade_syllabuses': main_data['grade_syllabuses'],
            'assessments_times': main_data.get('assessments_times'),
            'term': main_data.get('term'),
            'grade': main_data['grade'],
            'class': main_data['class'],
            'company': main_data['company'],
            'total_students': main_data['total_students'],
            'school_year': main_data.get('school_year'),
            # Additional info
            'grade_name': wizard.grade_id.name,
            'term_name': wizard.term_id.name if wizard.term_id else None,
            'assessments_times_name': wizard.assessments_times.name if wizard.assessments_times else None,
            'grading_method': grading_method_info['grading_method'],
            'class_name': wizard.class_id.name if wizard.class_id else 'جميع الفصول',
        }

    def _prepare_mc_student_result_report_data(self, wizard):
        """Prepare main report data"""
        # قائمة الطلاب
        student_domain = [
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id)
        ]
        if wizard.class_id:
            student_domain.append(('class_division_id', '=', wizard.class_id.id))
        students = self.env['education.student'].sudo().search(student_domain, order="seat_number")
        if wizard.student_ids:
            students = wizard.student_ids

        # قائمة المناهج للصف
        grade_syllabuses = self.env['education.syllabus'].sudo().search([
            ('company_id', '=', wizard.company_id.id),
            ('class_id', '=', wizard.grade_id.id),
        ])

        if wizard.term_id:
            return self._prepare_term_report_data(wizard, students, grade_syllabuses)
        elif wizard.assessments_times:
            return self._prepare_assessment_report_data(wizard, students, grade_syllabuses)
        
        return {
            'students_data': [],
            'syllabus_data': [],
            'grade_syllabuses': grade_syllabuses,
            'term': None,
            'grade': wizard.grade_id,
            'class': wizard.class_id,
            'company': wizard.company_id,
            'total_students': 0
        }

    def _prepare_term_report_data(self, wizard, students, grade_syllabuses):
        """Prepare report data for term-based report"""
        # إعداد بيانات المناهج كقائمة
        syllabus_data = []
        for syllabus in grade_syllabuses:
            syllabus_template = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('school_year_id', '=', wizard.term_id.academic_year_id.id)
            ], limit=1)
            if syllabus_template:
                syllabus_data.append({
                    'syllabus_id': str(syllabus.id),
                    'syllabus_name': syllabus.name,
                    'is_elective': syllabus.elective,
                    'distributions': [
                        {
                            'id': 'total_assessments' if getattr(dist, "item", None) and getattr(dist.item, "assessment", False)
                                else str(dist.id),
                            'name': (
                                "Total Assessments"
                                if getattr(dist, "item", None) and getattr(dist.item, "assessment", False)
                                else dist.item.name if getattr(dist, "item", None) and getattr(dist.item, "name", None)
                                else "N/A"
                            ),
                            'dist_maximum': dist.maximum if dist.maximum else (dist.weight if dist.weight else None),
                        }
                        for dist in syllabus_template.custom_grade_distribution_template
                        if (
                            hasattr(dist, 'control') and dist.control != 'project'
                        )
                    ],
                    'maximum': syllabus_template.maximum or 0.0
                })
        
        # إعداد بيانات الطلاب
        students_data = []
        
        for index, student in enumerate(students, 1):
            st_acc_record = self.env['acc.student.term.grades'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('student_id', '=', student.id),
                ('term_id', '=', wizard.term_id.id),
                ('grade_id', '=', wizard.grade_id.id)
            ], limit=1)

            # جلب المواد الاختيارية المسجلة للطالب
            elective_syllabuses = self.env['mc.elective.syllabus.students'].sudo().search([
                ('student_id', '=', student.id),
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id)
            ]).mapped('syllabus_id.id')

            student_data = {
                'serial_no': index,
                'student': student.full_english_name,
                'seat_number': getattr(student, 'seat_number', '') or '',
                'total_score': st_acc_record.total if st_acc_record else 0.0,
                'total_max': st_acc_record.term_total if st_acc_record else 0.0,
                'percentage': round((st_acc_record.total / st_acc_record.term_total * 100), 2) if st_acc_record and st_acc_record.term_total > 0 else 0.0,
                'grade_scale': self._get_grade_scale(wizard, st_acc_record.total if st_acc_record else 0.0, st_acc_record.term_total if st_acc_record else 0.0, 'term'),
                'subjects_results': {},
                'registered_subjects': [str(syllabus_id) for syllabus_id in elective_syllabuses]
            }

            # إعداد نتائج الطالب لكل مادة
            if st_acc_record:
                for subject_line in st_acc_record.subject_line_ids:
                    subject_id = str(subject_line.syllabus_id.id)
                    syllabus = self.env['education.syllabus'].browse(int(subject_id))
                    if syllabus.elective and subject_id not in student_data['registered_subjects']:
                        continue

                    total_assessment_score = sum(assess_line.score or 0.0 for assess_line in subject_line.assessment_line_ids)

                    distributions_data = {}
                    for dist_line in subject_line.distribution_line_ids:
                        distributions_data[str(dist_line.distribution_id.id)] = {
                            'score': dist_line.score or 0.0,
                            'check': dist_line.check  # إضافة حقل check
                        }
                    # إضافة "Total Assessments" إلى distributions_data
                    distributions_data['total_assessments'] = {
                        'id': 'total_assessments',
                        'score': total_assessment_score or 0.0,
                        'check': True  # Total Assessments مالهاش check، فنعطيه True افتراضيًا
                    }

                    student_data['subjects_results'][subject_id] = {
                        'distributions': distributions_data,
                        'total': subject_line.total_subject_score or 0.0,
                        'max_score': subject_line.total_subject_max or 0.0,
                        'grade': self._get_grade_scale(
                            wizard,
                            subject_line.total_subject_score or 0.0,
                            subject_line.total_subject_max or 0.0,
                            'term'
                        )['symbol'],
                        'color': self._get_grade_scale(
                            wizard,
                            subject_line.total_subject_score or 0.0,
                            subject_line.total_subject_max or 0.0,
                            'term'
                        )['color']
                    }

            students_data.append(student_data)
        
        # ترتيب وفلترة الطلاب
        students_data.sort(key=lambda x: x['total_score'], reverse=True)
        for rank, student_data in enumerate(students_data, 1):
            student_data['rank'] = rank

        if wizard.top_student and wizard.top_student > 0:
            students_data = students_data[:wizard.top_student]
            # إعادة تعيين rank بعد الفلتر
            for rank, student_data in enumerate(students_data, 1):
                student_data['rank'] = rank

        return {
            'students_data': students_data,
            'syllabus_data': syllabus_data,
            'grade_syllabuses': grade_syllabuses,
            'term': wizard.term_id,
            'grade': wizard.grade_id,
            'class': wizard.class_id,
            'company': wizard.company_id,
            'total_students': len(students_data)
        }

    def _prepare_assessment_report_data(self, wizard, students, grade_syllabuses):
        """Prepare report data for assessment-based report"""
        # إعداد بيانات المناهج كقائمة
        syllabus_data = []
        school_year = self.env['education.academic.year'].sudo().search([
            ('ay_start_date', '<=', wizard.assessments_times.start_date),
            ('ay_end_date', '>=', wizard.assessments_times.end_date),
        ], limit=1)

        for syllabus in grade_syllabuses:
            syllabus_template = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('school_year_id', '=', school_year.id if school_year else False)
            ], limit=1)

            if syllabus_template:
                syllabus_data.append({
                    'syllabus_id': str(syllabus.id),
                    'syllabus_name': syllabus.name,
                    'is_elective': syllabus.elective,
                    'distributions': [
                        {
                            'id': 'total_assessments',
                            'name': "Total Assessments",
                            'dist_maximum': dist.maximum if dist.maximum else (dist.weight if dist.weight else None),
                        }
                        for dist in syllabus_template.custom_grade_distribution_template
                        if getattr(dist, "item", None) and getattr(dist.item, "assessment", False)
                    ],
                    'maximum': syllabus_template.maximum or 0.0
                })

        # إعداد بيانات الطلاب
        students_data = []
        
        for index, student in enumerate(students, 1):
            st_acc_record = self.env['acc.student.monthly.grades'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('student_id', '=', student.id),
                ('assesment_time', '=', wizard.assessments_times.id),
                ('grade_id', '=', wizard.grade_id.id)
            ], limit=1)

            # جلب المواد الاختيارية المسجلة للطالب
            elective_syllabuses = self.env['mc.elective.syllabus.students'].sudo().search([
                ('student_id', '=', student.id),
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id)
            ]).mapped('syllabus_id.id')

            student_data = {
                'serial_no': index,
                'student': student.full_english_name,
                'seat_number': getattr(student, 'seat_number', '') or '',
                'total_score': st_acc_record.total if st_acc_record else 0.0,
                'total_max': st_acc_record.time_total if st_acc_record else 0.0,
                'percentage': round((st_acc_record.total / st_acc_record.time_total * 100), 2) if st_acc_record and st_acc_record.time_total > 0 else 0.0,
                'grade_scale': self._get_grade_scale(wizard, st_acc_record.total if st_acc_record else 0.0, st_acc_record.time_total if st_acc_record else 0.0, 'assessment', school_year),
                'subjects_results': {},
                'registered_subjects': [str(syllabus_id) for syllabus_id in elective_syllabuses]
            }

            # إعداد نتائج الطالب لكل مادة
            if st_acc_record:
                for subject_line in st_acc_record.subject_line_ids:
                    subject_id = str(subject_line.syllabus_id.id)
                    syllabus = self.env['education.syllabus'].browse(int(subject_id))
                    if syllabus.elective and subject_id not in student_data['registered_subjects']:
                        continue

                    total_assessment_score = sum(assess_line.score or 0.0 for assess_line in subject_line.assessment_line_ids)

                    assessment_data = {}
                    for assessment_line in subject_line.assessment_line_ids:
                        assessment_data[str(assessment_line.assessment_id.id)] = {
                            'score': assessment_line.score or 0.0,
                        }
                    # إضافة "Total Assessments" إلى assessment_data
                    assessment_data['total_assessments'] = {
                        'id': 'total_assessments',  # إضافة id للتعرف عليه في التقرير
                        'score': total_assessment_score or 0.0,
                    }
                        
                    student_data['subjects_results'][subject_id] = {
                        'distributions': assessment_data,
                        'total': subject_line.total_subject_score or 0.0,
                        'max_score': subject_line.total_subject_max or 0.0,
                        'percentage': round((subject_line.total_subject_score / subject_line.total_subject_max * 100), 2) if subject_line.total_subject_max > 0 else 0.0,
                        'grade': self._get_grade_scale(
                            wizard,
                            subject_line.total_subject_score or 0.0,
                            subject_line.total_subject_max or 0.0,
                            'assessment',
                            school_year
                        )['symbol'],  # Use symbol from the dictionary
                        'color': self._get_grade_scale(
                            wizard,
                            subject_line.total_subject_score or 0.0,
                            subject_line.total_subject_max or 0.0,
                            'assessment',
                            school_year
                        )['color']  # Add color to the data
                    }
            students_data.append(student_data)
        
        # ترتيب الطلاب حسب النتيجة الإجمالية
        students_data.sort(key=lambda x: x['total_score'], reverse=True)

        for rank, student_data in enumerate(students_data, 1):
            student_data['rank'] = rank

        if wizard.top_student and wizard.top_student > 0:
            students_data = students_data[:wizard.top_student]
            # إعادة تعيين rank بعد الفلتر
            for rank, student_data in enumerate(students_data, 1):
                student_data['rank'] = rank

        return {
            'students_data': students_data,
            'syllabus_data': syllabus_data,
            'grade_syllabuses': grade_syllabuses,
            'assessments_times': wizard.assessments_times.name,
            'grade': wizard.grade_id,
            'class': wizard.class_id,
            'company': wizard.company_id,
            'total_students': len(students_data),
            'school_year': school_year
        }

    def _get_grade_scale(self, wizard, score, max_score, report_type, school_year=None):
        """Get grade scale information"""
        if max_score == 0:
            return {'symbol': '', 'color': ''}
        percentage = (score / max_score) * 100

        # Determine the appropriate academic year
        if report_type == 'term':
            academic_year_id = wizard.term_id.academic_year_id.id
        elif report_type == 'assessment' and school_year:
            academic_year_id = school_year.id
        else:
            return {'symbol': '', 'color': ''}

        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id),
            ('school_year_id', '=', academic_year_id)
        ], limit=1)

        if not grading_method:
            return {'symbol': '', 'color': ''}

        for scale in grading_method.grading_scale_id:
            if scale.minimum <= percentage <= scale.maximum:
                return {
                    'symbol': scale.symbol or '',
                    'color': scale.color or ''  # Assuming color is a field in the grading scale
                }
        return {'symbol': '', 'color': ''}

    def _get_grading_method_info(self, wizard, main_data):
        """Get grading method information"""
        # تحديد العام الدراسي المناسب للبحث عن grading_method
        if wizard.term_id:
            academic_year_id = wizard.term_id.academic_year_id.id
        elif wizard.assessments_times and main_data.get('school_year'):
            academic_year_id = main_data['school_year'].id
        else:
            academic_year_id = False

        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id),
            ('school_year_id', '=', academic_year_id)
        ], limit=1)

        return {
            'grading_method': grading_method.grading_method if grading_method else ''
        }