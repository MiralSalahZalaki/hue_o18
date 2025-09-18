from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCPeriodicReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.mc_periodic_assessment_template'
    _description = 'MC Periodic Report Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['mc.periodic.report.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_mc_periodic_report_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'mc.periodic.report.wizard',
            'docs': [wizard],
            # Main data from wizard
            'students_data': main_data['students_data'],
            'syllabus_data': main_data['syllabus_data'],
            'assessment_times': main_data['assessment_times'],
            'grading_method': main_data['grading_method'],
            'grading_method_comment': main_data['grading_method_comment'],
            'grading_scales': main_data['grading_scales'],
            'distribution': main_data['distribution'],
            'student_view': main_data['student_view'],
            'arabic_report': main_data['arabic_report'],
            'full_academic_year': main_data['full_academic_year'],
            'term_name': main_data['term_name'],
            'academic_year': main_data['academic_year'],
            'academic_year_obj': main_data['academic_year_obj'],
            'grade_name': main_data['grade_name'],
            'class_name': main_data['class_name'],
            'company': main_data['company'],
            'term': main_data['term'],
            'grade': main_data['grade'],
            'class': main_data['class'],
            'total_students': main_data['total_students'],
         
         
        }
    
    def _get_mc_periodic_report_data(self,wiazrd):
       
        # Prepare Students List
        student_domain = [
            ('grade_id', '=',  wiazrd.grade_id.id),
            ('company_id', '=', wiazrd.company_id.id)
        ]
        if wiazrd.class_id:
            student_domain.append(('class_division_id', '=', wiazrd.class_id.id))
        
        students = self.env['education.student'].sudo().search(student_domain, order="seat_number")
        if wiazrd.student_ids:
            students = wiazrd.student_ids

        # Prepare Grade Syllabus List with assessments
        grade_syllabuses = self.env['education.syllabus'].sudo().search([
            ('company_id', '=', wiazrd.company_id.id),
            ('class_id', '=', wiazrd.grade_id.id),
            ('hidden_management_report', '=', False)
        ])

        syllabus_data = []
        for syllabus in grade_syllabuses:
            # Get syllabus template
            syllabus_template = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', wiazrd.company_id.id),
                ('grade_id', '=', wiazrd.grade_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('school_year_id', '=', wiazrd.term_id.academic_year_id.id)
            ], limit=1)
            
            assessments_list = []
            if syllabus_template:
                for assess in syllabus_template.assessments_category_id:
                    # Filter hidden assessments for student view
                    if wiazrd.student_view and hasattr(assess, 'item') and assess.item and hasattr(assess.item, 'hidden_student_report') and assess.item.hidden_student_report:
                        continue
                        
                    assess_info = {
                        'id': str(assess.id),
                        'name': assess.item.name if hasattr(assess, 'item') and assess.item and hasattr(assess.item, 'name') and assess.item.name else 'N/A',
                        'max_score': assess.max_score if hasattr(assess, 'max_score') else 0.0,
                    }
                    assessments_list.append(assess_info)

            syllabus_data.append({
                'syllabus_id': str(syllabus.id),
                'syllabus_name': syllabus.name,
                'certificate_name': syllabus.certificate_name or syllabus.name,
                'is_elective': syllabus.elective,
                'assessments': assessments_list,
            })

        # الحل الصحيح في الـ wizard - استبدل الجزء المشكِل بهذا الكود:

        students_data = []
        for index, student in enumerate(students, 1):
            # Get elective syllabus for this student
            elective_syllabuses = self.env['mc.elective.syllabus.students'].sudo().search([
                ('student_id', '=', student.id),
                ('company_id', '=', wiazrd.company_id.id),
                ('grade_id', '=', wiazrd.grade_id.id)
            ]).mapped('syllabus_id.id')

            student_data = {
                'serial_no': index,
                'student': student.full_english_name,
                'student_code': student.student_code or '',
                'class_name': student.class_division_id.name if student.class_division_id else '',
                'grade_name': student.grade_id.name if student.grade_id else '',
                'seat_number': student.seat_number,
                'subjects_results': {},  # تركيبة جديدة: assessment_time_id -> {subject_id: results}
                'registered_subjects': [str(syllabus_id) for syllabus_id in elective_syllabuses],
                'absence_days': {}
            }

            # Get absence days for each assessment time
            for assessment_time in wiazrd.assessments_times:
                if assessment_time.start_date and assessment_time.end_date:
                    absence_days = self.env['education.attendance.line'].sudo().search_count([
                        ('company_id', '=', wiazrd.company_id.id),
                        ('student_id', '=', student.id),
                        ('class_id', '=', wiazrd.grade_id.id),
                        ('division_id', '=', student.class_division_id.id),
                        ('date', '>=', assessment_time.start_date),
                        ('date', '<=', assessment_time.end_date),
                        ('present_morning', '=', False),
                        ('sickness_absence', '=', False)
                    ])
                    student_data['absence_days'][str(assessment_time.id)] = absence_days

            # المفتاح هنا: تجميع النتائج لكل assessment_time منفصلاً
            for assessment_time in wiazrd.assessments_times:
                # Get student academic records for this specific assessment time only
                st_acc_records = self.env['acc.student.monthly.grades'].sudo().search([
                    ('company_id', '=', wiazrd.company_id.id),
                    ('student_id', '=', student.id),
                    ('assesment_time', '=', assessment_time.id),  # فقط هذا الـ assessment time
                    ('grade_id', '=', wiazrd.grade_id.id)
                ])

                # Initialize subjects results for this assessment time
                assessment_time_id = str(assessment_time.id)
                student_data['subjects_results'][assessment_time_id] = {}

                # Process records for this specific assessment time
                for st_acc_record in st_acc_records:
                    for subject_line in st_acc_record.subject_line_ids:
                        subject_id = str(subject_line.syllabus_id.id)
                        syllabus = subject_line.syllabus_id
                        
                        if syllabus.elective and subject_id not in student_data['registered_subjects']:
                            continue

                        grade_scale_data = wiazrd._get_grade_scale_data(
                            subject_line.total_subject_score or 0.0,
                            subject_line.total_subject_max or 0.0
                        )

                        # Apply custom rounding logic to score
                        score = subject_line.total_subject_score or 0.0
                        if score > 0:
                            decimal_part = score % 1
                            if 0.01 < decimal_part < 0.5:
                                score = int(score) + 0.5
                            elif 0.5 <= decimal_part < 1:
                                score = int(score) + 1

                        # Prepare assessments scores for this subject
                        assessments_scores = {}
                        for assess_line in subject_line.assessment_line_ids:
                            assess_key = str(assess_line.assessment_id.id)
                            
                            # Apply rounding to assessment score too
                            assess_score = assess_line.score or 0.0
                            if assess_score > 0:
                                decimal_part = assess_score % 1
                                if 0.01 < decimal_part < 0.5:
                                    assess_score = int(assess_score) + 0.5
                                elif 0.5 <= decimal_part < 1:
                                    assess_score = int(assess_score) + 1

                            assessments_scores[assess_key] = {
                                'score': assess_score,
                                'max_score': assess_line.max_score or 0.0,
                                'grade': grade_scale_data.get('scale_symbol', '') if grade_scale_data else '',
                            }

                        student_data['subjects_results'][assessment_time_id][subject_id] = {
                            'score': score,
                            'max_score': subject_line.total_subject_max or 0.0, 
                            'grade_scale': grade_scale_data,
                            'grade': grade_scale_data.get('scale_symbol', '') if grade_scale_data else '',
                            'comment': grade_scale_data.get('scale_comment', '') if grade_scale_data else '',
                            'color': grade_scale_data.get('scale_color', '') if grade_scale_data else '',
                            'assessments': assessments_scores
                        }

            students_data.append(student_data)

        # Get grading method info
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', wiazrd.grade_id.id),
            ('company_id', '=', wiazrd.company_id.id),
            ('school_year_id', '=', wiazrd.term_id.academic_year_id.id)
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
        for time in wiazrd.assessments_times:
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
            'grading_scales': grading_scales,
            'distribution': wiazrd.distribution,
            'student_view': wiazrd.student_view,
            'arabic_report': wiazrd.arabic_report,
            'full_academic_year': wiazrd.full_academic_year,
            'term_name': wiazrd.term_id.name if wiazrd.term_id else None,
            'academic_year': wiazrd.term_id.academic_year_id.name if wiazrd.term_id else None,
            'academic_year_obj': wiazrd.term_id.academic_year_id if wiazrd.term_id else None,
            'grade_name': wiazrd.grade_id.name,
            'class_name': wiazrd.class_id.name if wiazrd.class_id else 'All Classes',
            'company': wiazrd.company_id,
            'term': wiazrd.term_id,
            'grade': wiazrd.grade_id,
            'class': wiazrd.class_id,
            'total_students': len(students_data),
        }