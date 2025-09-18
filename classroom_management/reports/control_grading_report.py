from odoo import models, fields, api
from odoo.exceptions import ValidationError
from collections import defaultdict

class ControlGradingAbstract(models.AbstractModel):
    _name = 'report.classroom_management.control_report_template'
    _description = 'Control Grading Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['control.grades.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_control_grades_data(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'control.grades.wizard',
            'docs': [wizard],
            # Main data from wizard

            'students': main_data['students'],
            'subjects': main_data['subjects'],
            'distributions': main_data['distributions'],
            'distribution': main_data['distribution'],
            'grade_name': main_data['grade_name'],
            'term_name': main_data['term_name'],
            'assessments_times': main_data['assessments_times'],

        }
    
    def _get_control_grades_data(self, wizard):
        """Get control grades data for the report"""
        # Validate required fields
        if not all([wizard.company_id, wizard.grade_id, wizard.term_id]):
            return {
                'students': [],
                'subjects': [],
                'distributions': [],
                'distribution': '',
                'grade_name': '',
                'term_name': '',
                'assessments_times': '',
            }
        
        # Build domain for control grades
        domain = [
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id),
            ('term_id', '=', wizard.term_id.id),
            ('state', '=', 'done')
        ]
        
        # Add optional filters
        if wizard.distribution:
            domain.append(('distribution_id.item', '=', wizard.distribution.id))

        if wizard.assessments_times:
            domain.extend([
                ('date', '>=', wizard.assessments_times.start_date),
                ('date', '<=', wizard.assessments_times.end_date)
            ])
        
        # Get controls
        controls = self.env['mc.control.grades'].sudo().search(domain)
        
        if not controls:
            return {
                'students': [],
                'subjects': [],
                'distributions': [],
                'distribution': wizard.distribution.name if wizard.distribution else 'All Distributions',
                'grade_name': wizard.grade_id.name,
                'term_name': wizard.term_id.name,
                'assessments_times': wizard.assessments_times.name if wizard.assessments_times else '',
            }

        # Process data more efficiently
        students_dict = {}
        subjects_set = set()
        subject_distributions = defaultdict(set)
        
        for control in controls:
            # Add subject info
            subjects_set.add(control.syllabus_id)
            subject_id = control.syllabus_id.id
            subject_distributions[subject_id].add(control.distribution_id)
            
            # Process students for this control
            student_records = control.student_list
            
            # Apply class filter if specified
            if wizard.class_id:
                student_records = student_records.filtered(
                    lambda s: s.class_division_id.id == wizard.class_id.id
                )
            
            for student_record in student_records:
                student_id = student_record.student_id.id
                
                # Initialize student dict if not exists
                if student_id not in students_dict:
                    students_dict[student_id] = {
                        'student': student_record.student_id,
                        'student_name': getattr(student_record.student_id, 'full_english_name', '') or student_record.student_id.name,
                        'seat_number': student_record.seat_number or '',
                        'student_code': student_record.student_code or '',
                        'class_division': student_record.class_division_id,
                        'grades': {}
                    }
                
                # Add grade for this subject/distribution
                dist_id = control.distribution_id.id
                
                if subject_id not in students_dict[student_id]['grades']:
                    students_dict[student_id]['grades'][subject_id] = {}
                
                students_dict[student_id]['grades'][subject_id][dist_id] = {
                    'score': student_record.score if student_record.check else 0,
                    'check': student_record.check
                }

        # Convert to sorted lists
        students_list = list(students_dict.values())
        
        # Sort students by seat number (handle non-numeric seat numbers)
        def sort_key(student):
            seat_num = student.get('seat_number', '')
            if seat_num and str(seat_num).isdigit():
                return int(seat_num)
            return 9999  # Put non-numeric at end
        
        students_list.sort(key=sort_key)
        
        # Process subjects and distributions
        subjects_list = sorted(list(subjects_set), key=lambda x: x.name)
        
        # Create distributions with subject mapping
        distributions_with_names = []
        for subject_id, dists in subject_distributions.items():
            for dist in sorted(list(dists), key=lambda x: getattr(x.item, 'name', '')):
                distributions_with_names.append({
                    'id': dist.id,
                    'name': getattr(dist.item, 'name', ''),
                    'item': dist.item.id,
                    'subject_id': subject_id
                })
        
        # Create subjects with their distributions
        subjects_with_names = []
        for subject in subjects_list:
            subject_dists = [d for d in distributions_with_names if d['subject_id'] == subject.id]
            subjects_with_names.append({
                'id': subject.id,
                'name': subject.name,
                'dists': subject_dists,
                'dists_count': len(subject_dists)
            })

        return {
            'students': students_list,
            'subjects': subjects_with_names,
            'distributions': distributions_with_names,
            'distribution': wizard.distribution.name if wizard.distribution else 'All Distributions',
            'grade_name': wizard.grade_id.name,
            'term_name': wizard.term_id.name,
            'assessments_times': wizard.assessments_times.name if wizard.assessments_times else '',
        }