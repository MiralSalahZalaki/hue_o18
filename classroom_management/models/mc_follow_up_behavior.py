from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class MCFollowUpBehavior(models.Model):
    _name = 'mc.follow.up.behavior'
    _description = 'Follow Up Behavior'
    _inherit = ['mail.thread']

    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)    
    grade_id = fields.Many2one("education.class", string="Grade", domain="[('school', '=', company_id)]")
    syllabus_id = fields.Many2one("education.syllabus", string="Syllabus", required=True, domain="[('company_id', '=', company_id),('class_id','=',grade_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", required=True, domain="[('class_id', '=', grade_id),('school_id', '=', company_id)]")
    date = fields.Date('Date', required=True , default=fields.Datetime.now,)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string="State", default='draft', required=True)
    check_student = fields.Boolean(string="Check Student")
    tree_clo_acl_ids = fields.Char('Tree Clo Acl', readonly = True)
    student_list = fields.One2many('follow.up.student.behavior.list', "connect_id", string="Students")
    follow_up_time = fields.Many2one('mc.follow.up.times',string='Follow Up Time', compute="_compute_follow_up_time", store=True)
    situation = fields.Many2one('mc.follow.up.situation',string='Situation')
    
    @api.depends('company_id', 'grade_id', 'date')
    def _compute_follow_up_time(self):
        for rec in self:
            rec.follow_up_time = False
            if rec.company_id and rec.grade_id and rec.date:
                follow_up_time = self.env['mc.follow.up.times'].sudo().search([
                    ('company_id', '=', rec.company_id.id),
                    ('grade_ids', 'in', [rec.grade_id.id]),
                    ('start_date', '<=', rec.date),
                    ('end_date', '>=', rec.date)
                ], limit=1)
                rec.follow_up_time = follow_up_time.id


    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.follow_up_time = False
    
    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.class_id = False

    def set_done(self):
        for rec in self:
            if rec.student_list and rec.state == "draft":
                rec.write({"state": "done"})

    def set_draft(self):
        for rec in self:
            if rec.student_list and rec.state == "done":
                rec.write({"state": "draft"})

    # Delete all related student_list records before deleting the main record
    def unlink(self):
        for record in self:
            if record.student_list:
                record.student_list.unlink()  # Delete all related records in follow.up.student.behavior.list
        return super(MCFollowUpBehavior, self).unlink()


    def get_students_list(self):
        for rec in self:
            if rec.syllabus_id and rec.class_id:
                # Find the syllabus per class record for the given syllabus and class
                syllabus_per_class = self.env['mc.syllabus.per.class'].sudo().search([
                    ('syllabus_id', '=', rec.syllabus_id.id),
                    ('class_division_id', '=', rec.class_id.id),
                    ('company_id', '=', rec.company_id.id),
                ], limit=1)

                if syllabus_per_class:
                    # Get students enrolled in this syllabus (from enrollment_per_class_ids)
                    enrolled_students = syllabus_per_class.enrollment_per_class_ids.filtered(
                        lambda e: e.role == 'student' and e.student_id
                    ).mapped('student_id')

                    # Get existing student IDs in the student_list
                    existing_student_ids = rec.student_list.mapped('student_id.id')

                    # Prepare new student records for those not already in student_list
                    new_student_records = [
                        {
                            'connect_id': rec.id,
                            'student_id': student.id,
                        } for student in enrolled_students if student.id not in existing_student_ids
                    ]

                    # Create new student records if any
                    if new_student_records:
                        self.env['follow.up.student.behavior.list'].create(new_student_records)
                        rec.check_student = True
                    else:
                        rec.check_student = False
                else:
                    # If no syllabus per class is found, set check_student to False
                    rec.check_student = False

    def fill_situation(self):
        for rec in self:
            if rec.situation:
                for student in rec.student_list:
                    student.situation = rec.situation
            else:
                raise ValidationError("Please set a the situation first.")
