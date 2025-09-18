from odoo import models, fields, api
from odoo.exceptions import ValidationError

class IGStudentReportWizard(models.TransientModel):
    _name = 'ig.student.result.wizard'
    _description = 'IG Student Report Wizard'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    term_id = fields.Many2one('education.academic.term', domain="[('school_year_id.company_id', '=', company_id)]", required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True, domain="[('school','=',company_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", domain="[('class_id','=',grade_id)]")
    top_rank = fields.Integer(string="Top Ranks")

    # Adjust Domain of student_ids
    student_ids_domain = fields.Char(string="students domain",
                                     help="Dynamic domain for students based on grade and class",
                                     compute="_compute_student_ids_domain")
                                     
    student_ids = fields.Many2many('education.student', string="Student", 
                                  required=True,
                                  domain="student_ids_domain")

    @api.depends('grade_id', 'class_id')
    def _compute_student_ids_domain(self):
        for rec in self:
            domain = [('id','=',-1)]
            if rec.grade_id:
                domain = [('grade_id', '=', rec.grade_id.id)]
                if rec.class_id:
                    domain.append(('class_division_id', '=', rec.class_id.id))
            rec.student_ids_domain = domain
    
    @api.onchange('class_id')
    def _onchange_class_id(self):
        self.student_ids = False

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.student_ids = False
        self.class_id = False

    def generate_ig_student_report_wizard(self):
        """Generate the report using AbstractModel approach"""
        if not all([self.grade_id, self.term_id, self.company_id]):
            raise ValidationError("Please fill all required fields: School, Grade, and Term")
        
        # Pass the wizard record itself to the report
        return self.env.ref('classroom_management.action_report_ig_student').report_action(self)