from odoo import models, fields, api
from odoo.exceptions import ValidationError
from collections import defaultdict

class AssessmentsReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.assessments_report_template'
    _description = 'Assessments Report Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['assessments.report.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_assessments_report_data(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'assessments.report.wizard',
            'docs': [wizard],
            # Main data from wizard
            'report_data': main_data['report_data'],
            'categories_list': main_data['categories_list'],
            'syllabi_list': main_data['syllabi_list'],
            'distribution': main_data['distribution'],
            'grade_name': main_data['grade_name'],
            'term_name': main_data['term_name'],
            'assessments_times': main_data['assessments_times'],
            'company': main_data['company'],
        }
    
    def _get_assessments_report_data(self, wizard):
        result_data = []
        categories_list = []
        syllabi_list = []
        
        if wizard.assessments_times:
            # Get all evaluations for the selected grade and assessment time
            evaluations = self.env['mc.evaluation.grades'].sudo().search([
                ('grade_id', '=', wizard.grade_id.id),
                ('assessments_times', '=', wizard.assessments_times.id),
                ('company_id', '=', wizard.company_id.id),
            ])

            classes = evaluations.mapped('class_id')
            all_syllabi = evaluations.mapped('syllabus_id')
            
            # Get all assessment categories used in evaluations (remove duplicates by name)
            all_categories = evaluations.mapped('assessments_category_id').filtered(lambda x: x)
                        
            # Remove duplicate categories (same name, different ID)
            unique_categories = []
            seen_categories = set()
            for cat in all_categories:
                if cat.item.id not in seen_categories:
                    unique_categories.append(cat)
                    seen_categories.add(cat.item.id)
            
            all_categories = unique_categories
            
            # Create complete matrix data for each class and syllabus
            for class_div in classes:
                class_data = {
                    'class_name': class_div.display_name,
                    'subjects': {}
                }
                
                # Get evaluations for this specific class only
                class_evaluations = evaluations.filtered(lambda e: e.class_id.id == class_div.id)
                
                for syllabus in all_syllabi:
                    # Get evaluations for this specific class and syllabus
                    class_syllabus_evaluations = class_evaluations.filtered(
                        lambda e: e.syllabus_id.id == syllabus.id
                    )
                    
                    # Count assessment categories for this class-syllabus combination
                    categories_data = {}
                    for category in all_categories:
                        # Count all evaluations with this category NAME (not just ID)
                        category_evaluations = class_syllabus_evaluations.filtered(
                            lambda e: e.assessments_category_id.item.name == category.item.name
                        )
                        done_count = len(category_evaluations.filtered(lambda e: e.state == 'done'))
                        draft_count = len(category_evaluations.filtered(lambda e: e.state == 'draft'))
                        categories_data[category.item.name] = {
                            'done': done_count,
                            'draft': draft_count
                        }
                    
                    class_data['subjects'][syllabus.display_name] = {
                        'categories': categories_data,
                    }
                
                result_data.append(class_data)
            
            # Set categories and syllabi lists for table headers
            categories_list = [cat.item.name for cat in all_categories]
            syllabi_list = [syl.display_name for syl in all_syllabi]

        elif wizard.term_id:
            # Get all controls for the selected grade and distribution time
            controls = self.env['mc.control.grades'].sudo().search([
                ('grade_id', '=', wizard.grade_id.id),
                ('company_id', '=', wizard.company_id.id),
                ('term_id', '=', wizard.term_id.id),
            ])

            classes = controls.mapped('student_list.student_id.class_division_id')
            all_syllabi = controls.mapped('syllabus_id')
            
            # Get all assessment categories used in distribution (remove duplicates by name)
            all_categories = controls.mapped('distribution_id').filtered(lambda x: x)
                        
            # Remove duplicate categories (same name, different ID)
            unique_categories = []
            seen_categories = set()
            for cat in all_categories:
                if cat.item.id not in seen_categories:
                    unique_categories.append(cat)
                    seen_categories.add(cat.item.id)
            
            all_categories = unique_categories
            
            # Create complete matrix data for each class and syllabus
            for class_div in classes:
                class_data = {
                    'class_name': class_div.display_name,
                    'subjects': {}
                }
                
                # Get controls for this specific grade only
                class_controls = controls.filtered(lambda e: e.grade_id.id == class_div.class_id.id)
                
                for syllabus in all_syllabi:
                    # Get controls for this specific class and syllabus
                    class_syllabus_controls = class_controls.filtered(
                        lambda e: e.syllabus_id.id == syllabus.id
                    )
                    
                    # Count distribution categories for this class-syllabus combination
                    categories_data = {}
                    for category in all_categories:
                        # Count all controls with this category NAME (not just ID)
                        category_controls = class_syllabus_controls.filtered(
                            lambda e: e.distribution_id.item.name == category.item.name
                        )

                        done_count = len(category_controls.filtered(lambda e: e.state == 'done'))
                        draft_count = len(category_controls.filtered(lambda e: e.state == 'draft'))

                        categories_data[category.item.name] = {
                            'done': done_count,
                            'draft': draft_count
                        }
                    
                    class_data['subjects'][syllabus.display_name] = {
                        'categories': categories_data,
                    }
                
                result_data.append(class_data)
            
            # Set categories and syllabi lists for table headers
            categories_list = [cat.item.name for cat in all_categories]
            syllabi_list = [syl.display_name for syl in all_syllabi]

        return {
            'report_data': result_data,
            'categories_list': categories_list,
            'syllabi_list': syllabi_list,
            'distribution': wizard.distribution,
            'grade_name': wizard.grade_id.name,
            'term_name': wizard.term_id.name if wizard.term_id else '',
            'assessments_times': wizard.assessments_times.name if wizard.assessments_times else '',
            'company': wizard.company_id.name,
        }