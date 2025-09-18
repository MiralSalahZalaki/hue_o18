from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StudentResultWizard(models.TransientModel):
    _name = 'student.result.wizard'
    _description = 'AD Student Result wizard'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    term_id = fields.Many2one('education.academic.term', required=True ,  domain="[('school_year_id.company_id', '=', company_id)]")
    grade_id = fields.Many2one('education.class', string="Grade", required=True, domain="[('school','=',company_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", domain="[('class_id','=',grade_id)]")
    top_student = fields.Integer(string="Top Student")

    student_ids_domain = fields.Binary(
        string="students domain",
        help="Dynamic domain for students based on grade and class",
        compute="_compute_student_ids_domain"
    )
    student_ids = fields.Many2many(
        'education.student', string="Student",
        required=True, domain="student_ids_domain"
    )

    @api.depends('grade_id', 'class_id')
    def _compute_student_ids_domain(self):
        for rec in self:
            domain = [('id', '=', -1)]
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

    def _get_grade_scale(self, score, max_score):
        if max_score == 0:
            return ''
        percentage = (score / max_score) * 100
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', self.grade_id.id),
            ('company_id', '=', self.company_id.id),
            ('school_year_id', '=', self.term_id.academic_year_id.id)
        ], limit=1)
        
        if not grading_method:
            return ''
        
        for scale in grading_method.grading_scale_id:
            if scale.minimum <= percentage <= scale.maximum:
                return scale.symbol or ''
        return ''

    def generate_student_result_report_wizard(self):
        if not all([self.grade_id, self.term_id, self.company_id]):
            raise ValidationError("يرجى ملء جميع الحقول المطلوبة: المدرسة، الصف، والفصل الدراسي")

        return self.env.ref('classroom_management.action_report_ad_student_result').report_action(self)