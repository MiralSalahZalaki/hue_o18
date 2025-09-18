from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ADStudentReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.ad_student_result_template'
    _description = 'AD Student Report Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['student.result.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_ad_student_result_report_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'student.result.wizard',
            'docs': [wizard],
            # Main data from wizard

            'students_data': main_data['students_data'],
            'syllabus_data':  main_data['syllabus_data'],
            'grade_syllabuses':  main_data['grade_syllabuses'],
            'term':  main_data['term'],
            'grade': main_data['grade'],
            'class':  main_data['class'],
            'company':  main_data['company'],
            'total_students':  main_data['total_students'],
         
        }
    
    def _get_ad_student_result_report_data(self,wizard):
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
                            'name': assess.item.name if hasattr(assess, 'item') and assess.item and hasattr(assess.item, 'name') and assess.item.name else 'N/A'
                        }
                        for assess in syllabus_template.assessments_category_id
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
                'grade_scale': wizard._get_grade_scale(st_acc_record.total if st_acc_record else 0.0, st_acc_record.term_total if st_acc_record else 0.0),
                'absence_days': st_acc_record.absence_days if st_acc_record else 0.0,
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

                    assessments_data = {}
                    for assess_line in subject_line.assessment_line_ids:
                        assessments_data[str(assess_line.assessment_id.id)] = {
                            'score': assess_line.score or 0.0,
                            'max_score': assess_line.max_score or 0.0
                        }
                    distributions_data = {}
                    for dist_line in subject_line.distribution_line_ids:
                        distributions_data[str(dist_line.distribution_id.id)] = {
                            'score': dist_line.score or 0.0,
                            'max_score': dist_line.max_score or 0.0
                        }
                    student_data['subjects_results'][subject_id] = {
                        'assessments': assessments_data,
                        'distributions': distributions_data,
                        'total': subject_line.total_subject_score or 0.0,
                        'max_score': subject_line.total_subject_max or 0.0,
                        'grade': wizard._get_grade_scale(
                            subject_line.total_subject_score or 0.0,
                            subject_line.total_subject_max or 0.0
                        )
                    }

            students_data.append(student_data)

        
        for rank, student_data in enumerate(students_data, 1):
            student_data['rank'] = rank

        if wizard.top_student and wizard.top_student > 0:
            students_data.sort(key=lambda x: x['total_score'], reverse=True)  
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

