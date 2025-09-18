from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCTotalReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.report_mc_total_term_template'
    _description = 'MC Total Report Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['mc.total.term.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_mc_total_term_report_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'mc.total.term.wizard',
            'docs': [wizard],
            # Main data from wizard
            'students_data': main_data['students_data'],
            'syllabus_data': main_data['syllabus_data'],
            'term': main_data['term'],
            'grade': main_data['grade'],
            'class': main_data['class'],
            'company': main_data['company'],
            'total_students': main_data['total_students'],
            'grading_method': main_data['grading_method'],
            'grading_method_comment': main_data['grading_method_comment'],
            'grading_scales': main_data['grading_scales'],
            'arabic_report': main_data['arabic_report'],
            'full_academic_year': main_data['full_academic_year'],
            'grade_name': main_data['grade_name'],
            'term_name': main_data['term_name'],
            'academic_year': main_data['academic_year'],
            'academic_year_obj': main_data['academic_year_obj'],
            'class_name': main_data['class_name'],
         
        }

    def _get_mc_total_term_report_data(self,wizard):
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
            ('hidden_management_report', '=', False)
        ])

        syllabus_data = []
        for syllabus in grade_syllabuses:
            syllabus_data.append({
                'syllabus_id': str(syllabus.id),
                'syllabus_name': syllabus.name,
                'certificate_name': syllabus.certificate_name or syllabus.name,
                'is_elective': syllabus.elective,
            })
            
        students_data = []
        for index, student in enumerate(students, 1):
            st_acc_record = self.env['acc.student.term.grades'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('student_id', '=', student.id),
                ('term_id', '=', wizard.term_id.id),
                ('grade_id', '=', wizard.grade_id.id)
            ], limit=1)

            # Get elective syllabus for this student
            elective_syllabuses = self.env['mc.elective.syllabus.students'].sudo().search([
                ('student_id', '=', student.id),
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id)
            ]).mapped('syllabus_id.id')

            # Get grading comments for this student
            student_grading_comments = self.get_year_grading_comments(wizard, student, wizard.term_id.academic_year_id)

            student_data = {
                'serial_no': index,
                'student': student.full_english_name,
                'student_code': student.student_code or '',
                'class_name': student.class_division_id.name if student.class_division_id else '',
                'grade_name': student.grade_id.name if student.grade_id else '',
                'seat_number': student.seat_number,
                'subjects_results': {},
                'registered_subjects': [str(syllabus_id) for syllabus_id in elective_syllabuses],
                'grading_comments': student_grading_comments  # Add grading comments to student data
            }

            # Prepare Student data for each syllabus
            if st_acc_record:
                for subject_line in st_acc_record.subject_line_ids:
                    subject_id = str(subject_line.syllabus_id.id)
                    syllabus = self.env['education.syllabus'].browse(int(subject_id))
                    if syllabus.elective and subject_id not in student_data['registered_subjects']:
                        continue

                    grade_scale_data = self._get_grade_scale_data(
                        wizard,
                        subject_line.total_subject_score or 0.0,
                        subject_line.total_subject_max or 0.0
                    )

                    # Apply custom rounding logic to score
                    score = subject_line.total_subject_score or 0.0
                    if score > 0:
                        decimal_part = score % 1
                        if 0.01 < decimal_part < 0.5:
                            score = int(score) + 0.5
                        if 0.5 <= decimal_part < 1:
                            score = int(score) + 1

                    student_data['subjects_results'][subject_id] = {
                        'score': score or 0.0,
                        'max_score': subject_line.total_subject_max or 0.0, 
                        'grade_scale': grade_scale_data,
                        'grade': grade_scale_data.get('scale_symbol', '') if grade_scale_data else '',
                        'comment': grade_scale_data.get('scale_comment', '') if grade_scale_data else '',
                        'color': grade_scale_data.get('scale_color', '') if grade_scale_data else ''
                    }

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
        
        return {
            'students_data': students_data,
            'syllabus_data': syllabus_data,
            'term': wizard.term_id,
            'grade': wizard.grade_id,
            'class': wizard.class_id,
            'company': wizard.company_id,
            'total_students': len(students_data),
            'grading_method': grading_method.grading_method if grading_method else '',
            'grading_method_comment': grading_method.comment if grading_method else '',
            'grading_scales': grading_scales,
            'arabic_report': wizard.arabic_report,
            'full_academic_year': wizard.full_academic_year,
            'grade_name': wizard.grade_id.name,
            'term_name': wizard.term_id.name if wizard.term_id else None,
            'academic_year': wizard.term_id.academic_year_id.name if wizard.term_id else None,
            'academic_year_obj': wizard.term_id.academic_year_id if wizard.term_id else None,
            'class_name': wizard.class_id.name if wizard.class_id else 'All Classes',
        }
    
    def _get_grade_scale_data(self,wizard, score, max_score):
        if max_score == 0:
            return ''
            
        percentage = (score / max_score) * 100
        
        # Get the grading method
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id),
            ('school_year_id', '=', wizard.term_id.academic_year_id.id)
        ], limit=1)
        
        if not grading_method:
            return ''
        
        if grading_method.grading_method == 'evaluation': 
            for scale in grading_method.grading_scale_id:
                if scale.minimum <= percentage <= scale.maximum:
                    return {
                        "scale_symbol": scale.symbol,
                        "scale_comment": scale.description,
                        "scale_color": scale.color,
                    }
        
        return ''
    
    def get_year_grading_comments(self,wizard, student, academic_year):
        # Search for mc.add.grading.comments records
        grading_comment_records = self.env['mc.add.grading.comments'].sudo().search([
            ('company_id', '=', wizard.company_id.id),
            ('grade_id', '=', wizard.grade_id.id),
            ('year', '=', academic_year.id),
            ('state', '=', 'done')  # Only get finalized records
        ])
        
        student_comments = []
        for record in grading_comment_records:
            # Find student in the student_list
            student_record = record.student_list.filtered(lambda s: s.student_id.id == student.id)
            if student_record and student_record.grading_comment:
                student_comments.append({
                    'connect_id': record,
                    'syllabus': record.syllabus_id.name,
                    'grading_type': record.grading_type.name,
                    'notes': student_record.grading_comment.name
                })
        
        return student_comments
