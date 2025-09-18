from odoo import models, fields,api
from odoo.exceptions import ValidationError


class MCProjectGrade(models.Model):
    _name = 'mc.project.grades'
    _inherit = ['mail.thread']


 
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    grade_id = fields.Many2one('education.class',  string="Grade")
    syllabus_id = fields.Many2one("education.syllabus", string="Syllabus", required=True, domain="[('company_id', '=', company_id),('class_id', '=', grade_id)]")
    distribution_id = fields.Many2one('mc.custom.distribution', string="Grade Distribution")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string="State", default='draft', required=True)
    student_list = fields.One2many("project.grades.student.list", "connect_id", string="Students")
    check_student = fields.Boolean(default=False)

    academic_year = fields.Many2one('education.academic.year', string="Academic Year", required=True)
    custom_max_score = fields.Float(string="Max Score", required=True)

    another_max_score = fields.Float(string="Maximum")

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.syllabus_id = False
    
    @api.onchange('syllabus_id')
    def _onchange_syllabus_id(self):
        self.distribution_id = False
        
    @api.onchange('distribution_id')
    def _onchange_distribution_id(self):
        for rec in self:
            if rec.distribution_id :
                rec.custom_max_score = rec.distribution_id.maximum
            else:
                rec.custom_max_score = False


    def set_done(self):
        for rec in self:
            if rec.student_list and rec.state == "draft":
                rec.write({"state": "done"})
                rec.check_student = True


    def set_draft(self):
        for rec in self:
            if rec.student_list and rec.state == "done":
                rec.write({"state": "draft"})
                rec.check_student = False


    # Delete all related student_list records before deleting the main record
    def unlink(self):
        for record in self:
            if record.student_list:
                record.student_list.unlink()  # Delete all related records in project.grades.student.list
        return super(MCProjectGrade, self).unlink()

    def get_students_list(self):
        for rec in self:
            if rec.syllabus_id and rec.grade_id:
                if not rec.syllabus_id.elective : # Not Elective
                    enrolled_students = self.env['education.student'].sudo().search([
                    ('grade_id', '=', rec.grade_id.id),
                    ('company_id', '=', rec.company_id.id),
                ])
                    
                if rec.syllabus_id.elective :  # Elective
                    enrolled_students = rec.syllabus_id.students.mapped('student_id')        

                # Get existing student IDs in the student_list
                existing_student_ids = rec.student_list.mapped('student_id.id')

                new_student_records = [
                    {
                        'connect_id': rec.id,
                        'check': True,
                        'student_id': student.id,
                        'grading_method': self.env['mc.grading.method'].sudo().search([
                            ('grade_id', '=', rec.grade_id.id)
                        ], limit=1).id or False,
                    } for student in enrolled_students if student.id not in existing_student_ids
                ]
                if new_student_records:
                    self.env['project.grades.student.list'].create(new_student_records)
                    rec.check_student = True
                else:
                    rec.check_student = False


    def fill_score(self):
        for rec in self:
            if rec.custom_max_score and rec.custom_max_score > 0:
                for student in rec.student_list:
                    student.score = rec.custom_max_score
            else:
                raise ValidationError("Please set a valid Maximum Score greater than 0 before filling scores.")
