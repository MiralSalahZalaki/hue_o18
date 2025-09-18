{
    'name': 'Classroom Management',
    'version':"18.0.1.0.0",
    'depends': ['base', 'education_core', 'mail', 'mc_app','contacts', 'sale_management'],
    'sequence': 101,
    'author': 'Mansoura College',
    'category': 'Industries',
    'data': [
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',

        #Student Garding
        'views/mc_evaluation_grades.xml',
        'views/mc_control_grades.xml',
        'views/mc_project_grades.xml',
        'views/mc_grading_types.xml',
        'views/mc_grading_comments.xml',
        'views/mc_add_grading_comments.xml',

        #Garde Setup
        'views/mc_grading_method.xml',
        'views/total_student_result.xml',
        'views/total_student_result_monthly.xml',
        'views/mc_evaluation_grades_student_list.xml',
        'views/mc_custom_distribution.xml',
        'views/mc_generic_template.xml',
        'views/mc_assign_generic_template.xml',
        'views/mc_custom_template.xml',
        'views/mc_assessment_times.xml',

        #Garde Config
        'views/education_academic_term.xml',
        'views/mc_grade_distribution.xml',
        'views/mc_assessments_category_types.xml',
        'views/mc_publish_assessment_confg.xml',
        'views/mc_grading_website_publish.xml',
        'views/mc_generate_student_result.xml',
        'views/mc_assessments_category.xml',
        'views/mc_custom_assessments_category.xml',

        #Follow Up
        'views/mc_follow_up_record.xml',
        'views/mc_follow_up_times.xml',
        'views/mc_follow_up_notes.xml',
        'views/mc_follow_up_situation.xml',
        'views/mc_follow_up_behavior.xml',
        'views/mc_follow_supervisor.xml',

        #Wizards
        'wizards/educational_student_grades_wizard.xml',
        'wizards/assessments_report_wizard.xml',
        'wizards/control_grades_wizard.xml',
        'wizards/grading_attendance_report_wizard.xml',
        'wizards/ad_student_result_wizard.xml',
        'wizards/ad_periodic_assessment_report_wizard.xml',
        'wizards/ad_total_term_transcript_wizard.xml',
        'wizards/final_educational_student_grades_wizard.xml',
        'wizards/mc_total_term_wizard.xml',
        'wizards/mc_periodic_report_wizard.xml',
        'wizards/mc_student_result_wizard.xml',
        
        'wizards/ig_periodic_report_wizard.xml',
        'wizards/ig_student_result_wizard.xml',
        'wizards/ig_monthly_report_wizard.xml',
        'wizards/ig_total_term_wizard.xml',


        #reports
        'reports/reports_view.xml',
        'reports/assessments_report_template.xml',
        'reports/control_report_template.xml',
        'reports/educational_student_grades_report_template.xml',
        'reports/grading_attendence_template.xml',
        'reports/final_educational_student_grades_template.xml',
        
        #AD Reports
        'reports/ad_student_result_template.xml',
        'reports/ad_periodic_assessment_template.xml',
        'reports/ad_total_term_transcript_template.xml',

        #MC Reports
        'reports/mc_total_term_template.xml',
        'reports/mc_periodic_assessment_template.xml',
        'reports/mc_student_result_template.xml',


        #IG Reports
        'reports/ig_periodic_assessment_template.xml',
        'reports/ig_monthly_report_template.xml',
        'reports/ig_student_result_template.xml',
        'reports/ig_total_term_template.xml',





        #Supervisor
        'views/mc_grading_supervisor.xml',
        #sear num
        'views/mc_seat_number.xml',

        #acc
        'views/acc_student_term_grades.xml',
        'views/acc_student_montly_grades.xml',

        'views/education_school_year.xml',

    ],


    'assets': {
        'web.assets_backend': [
            'classroom_management/static/src/js/classroom_action_helper/classroom_action_helper.js',
            'classroom_management/static/src/js/classroom_action_helper/classroom_action_helper.xml',
            'classroom_management/static/src/js/subject_lines_widget/*',
            'classroom_management/static/src/views/**/*',

        ],
    },
    'installable': True,
    'application':True,
    "license": "LGPL-3",

    'icon': '/classroom_management/static/description/classroom_manag.png',
}



