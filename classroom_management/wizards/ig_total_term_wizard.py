from odoo import models, fields, api
from odoo.exceptions import ValidationError

class IGTotalTermWizard(models.TransientModel):
    _name = 'ig.total.term.wizard'
    _description = 'IG Total Term Wizard'

    company_id = fields.Many2one('res.company', string='School', 
                                default=lambda self: self.env.company, required=True)
    term_id = fields.Many2one('education.academic.term', 
                             domain="[('school_year_id.company_id', '=', company_id)]", required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True, 
                              domain="[('school','=',company_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", 
                              domain="[('class_id','=',grade_id)]")

    # Adjust Domain of student_ids
    student_ids_domain = fields.Char(string="students domain",
                                    help="Dynamic domain for students based on grade and class",
                                    compute="_compute_student_ids_domain")
                                     
    student_ids = fields.Many2many('education.student', string="Student", 
                                  required=True,
                                  domain="student_ids_domain")
                                        
    full_academic_year = fields.Boolean()
    academic_year = fields.Many2one('education.academic.year')
    student_view = fields.Boolean(string="Student View")

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

    def get_garding_method(self):
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', self.grade_id.id),
            ('company_id', '=', self.company_id.id),
            ('school_year_id', '=', self.term_id.academic_year_id.id)
        ], limit=1)
        
        return grading_method.grading_method if grading_method else 'numeric'

    def generate_ig_total_term_report_wizard(self):
        if not all([self.grade_id, self.term_id, self.company_id]):
            raise ValidationError("Please fill all required fields: School, Grade, and Term")
        
        return self.env.ref('classroom_management.action_report_ig_total_term').report_action(self)