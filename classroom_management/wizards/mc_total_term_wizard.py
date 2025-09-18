from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class MCTotalTermWizard(models.TransientModel):
    _name = 'mc.total.term.wizard'
    _description = 'MC Total Term wizard'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    term_id = fields.Many2one('education.academic.term',  domain="[('school_year_id.company_id', '=', company_id)]", required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True, domain="[('school','=',company_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", domain="[('class_id','=',grade_id)]")

    # تصحيح نوع الـ field إلى Char بدلاً من Binary
    student_ids_domain = fields.Char(string="Students Domain",
                                     help="Dynamic domain for students based on grade and class",
                                     compute="_compute_student_ids_domain")
                                     
    student_ids = fields.Many2many('education.student', string="Student", 
                                  required=True,
                                  domain="student_ids_domain")    
    final_report = fields.Boolean()
    arabic_report = fields.Boolean()
    full_academic_year = fields.Boolean()
    previos_result = fields.Boolean()
    academic_year = fields.Many2one('education.academic.year')

    @api.depends('grade_id', 'class_id')
    def _compute_student_ids_domain(self):
        for rec in self:
            domain = [('id', '=', -1)]
            if rec.grade_id:
                domain = [('grade_id', '=', rec.grade_id.id)]
                if rec.class_id:
                    domain.append(('class_division_id', '=', rec.class_id.id))
            rec.student_ids_domain = str(domain)

    @api.onchange('class_id')
    def _onchange_class_id(self):
        self.student_ids = False

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.student_ids = False
        self.class_id = False



    def generate_mc_total_term_wizard(self):
        return self.env.ref('classroom_management.action_report_mc_total_term').report_action(self)