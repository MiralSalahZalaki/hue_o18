from odoo import models, fields, api
from odoo.exceptions import ValidationError
from collections import defaultdict

class GradingAttendenceAbstract(models.AbstractModel):
    _name = 'report.classroom_management.report_grading_attendence_template'
    _description = 'Grading Attendence Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['grading.attendance.report.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_grading_attendance_report_data(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'grading.attendance.report.wizard',
            'docs': [wizard],
            # Main data from wizard

            'students': main_data['students'],
            'syllabuses': main_data['syllabuses'],
            'term': main_data['term'],
            'grade_name': main_data['grade_name'],
            'class_name': main_data['class_name'],
            'company': main_data['company'],
            'total_students': main_data['total_students'],
            'assessment_times': main_data['assessment_times'],
            'term_name': main_data['term_name'],
            'class_name': main_data['class_name'],
            'company': main_data['company'],
            'assessments_times': main_data['assessments_times'],
            
        }
    
    def _get_grading_attendance_report_data(self,wizard):
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

        # Prepare Grade Syllabus List
        grade_syllabuses = self.env['education.syllabus'].sudo().search([
            ('company_id', '=', wizard.company_id.id),
            ('class_id', '=', wizard.grade_id.id),
            ('hidden_management_report', '=', False),
            
        ])

        # Prepare Syllabus Data
        syllabus_data = []
        for syllabus in grade_syllabuses:
            syllabus_template = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('school_year_id', '=', wizard.term_id.academic_year_id.id)
            ], limit=1)
            if syllabus_template:
                distributions = syllabus_template.custom_grade_distribution_template.filtered(
                    lambda d: d.control == 'control'
                )
                syllabus_data.append({
                    'syllabus_id': str(syllabus.id),
                    'syllabus_name': syllabus.name,
                    'is_elective': syllabus.elective,
                    'distributions': [
                        {
                            'id': str(dist.id),
                            'name': dist.item.name if hasattr(dist, 'item') and dist.item and hasattr(dist.item, 'name') else 'N/A',
                            'max_score': dist.maximum if dist.maximum else dist.weight if dist.weight else 0
                        }
                        for dist in distributions
                    ],
                    'maximum': syllabus_template.maximum or 0.0,
                    'dist_len': len(distributions)
                })

        # Prepare student data
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
                'name': student.full_english_name or student.name,
                'class_name': student.class_division_id.name if student.class_division_id else '',
                'grade_name': student.grade_id.name,
                'seat_number': student.seat_number or '',
                'student_code': student.student_code or '',
                'subjects_results': {},
                'registered_subjects': [str(syllabus_id) for syllabus_id in elective_syllabuses]
            }

            # Process each assessment time
            for time in wizard.assessments_times:
                attendance_domain = [
                    ('company_id', '=', wizard.company_id.id),
                    ('class_id', '=', wizard.grade_id.id),
                    ('student_id', '=', student.id),
                    ('date', '>=', time.start_date),
                    ('date', '<=', time.end_date)
                ]
                all_attendance = self.env['education.attendance.line'].sudo().search(attendance_domain)
                absences = all_attendance.filtered(lambda att: not att.present_morning)
                absence_count = len(absences)
                total_days = (time.end_date - time.start_date).days + 1

                control_grades = self.env['mc.control.grades'].sudo().search([
                    ('company_id', '=', wizard.company_id.id),
                    ('grade_id', '=', wizard.grade_id.id),
                    ('date', '>=', time.start_date),
                    ('date', '<=', time.end_date),
                    ('state', '=', 'done')
                ])

                for syllabus in syllabus_data:
                    subject_id = syllabus['syllabus_id']
                    if syllabus['is_elective'] and subject_id not in student_data['registered_subjects']:
                        continue

                    distributions_data = {}
                    for dist in syllabus['distributions']:
                        score = 0
                        matching_control = control_grades.filtered(
                            lambda cg: cg.syllabus_id.id == int(subject_id) and 
                                    cg.distribution_id.id == int(dist['id'])
                        )
                        if matching_control:
                            student_control_record = self.env['control.grades.student.list'].sudo().search([
                                ('connect_id', 'in', matching_control.ids),
                                ('student_id', '=', student.id)
                            ], limit=1)
                            if student_control_record:
                                if not student_control_record.check:
                                    score = 'abs'
                                else:
                                    actual_score = float(student_control_record.score) if student_control_record.score else 0
                                    control_max_score = matching_control.custom_max_score or 1
                                    if control_max_score > 0 and dist['max_score'] > 0:
                                        score = round((actual_score / control_max_score) * dist['max_score'], 2)
                                    else:
                                        score = 0

                        distributions_data[dist['id']] = {
                            'score': score,
                            'max_score': dist['max_score']
                        }

                    student_data['subjects_results'][subject_id] = {
                        'distributions': distributions_data,
                        'absence_days': absence_count,
                        'total_days': total_days,
                        'time_name': time.name
                    }

            students_data.append(student_data)

        return {
            'students': students_data,
            'syllabuses': syllabus_data,
            'term': wizard.term_id,
            'grade_name': wizard.grade_id.name,
            'class_name': wizard.class_id.name ,
            'company': wizard.company_id,
            'total_students': len(students_data),
            'assessment_times': [{
                'id': time.id,
                'name': time.name,
                'start_date': time.start_date,
                'end_date': time.end_date
            } for time in wizard.assessments_times],
            'term_name': wizard.term_id.name if wizard.term_id else None,
            'class_name': wizard.class_id.name if wizard.class_id else 'All Classes',
            'company': wizard.company_id.name,
            'assessments_times': wizard.assessments_times,
        }

