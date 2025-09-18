from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MCEducationAttendence(models.Model):
    _inherit = 'education.attendance'

       
    company_id = fields.Many2one('res.company', string='Company', required = True, default=lambda self: self.env.company)
    class_id = fields.Many2one('education.class', string='Grade',
                               help="Class of the attendance", domain="[('school', '=', company_id)]")
    
    academic_year_id = fields.Many2one('education.academic.year',
                                       string='Academic Year',
                                       related='division_id.academic_year_id',
                                       help="Academic year of the class")
    
    division_id = fields.Many2one('education.class.division',
                                  string='Division', required=True,
                                  help="Class division for attendance", domain="[('class_id', '=', class_id)]")
    
    all_marked_morning = fields.Boolean(string="All Present Morning", default = True,
                                        help='Enable if all students are '
                                             'present in the morning')
    
    
    @api.onchange('company_id')
    def _onchange_company(self):
        for rec in self:
            rec.class_id = False  # Reset grade_id when company changes

    @api.onchange('class_id')
    def _onchange_grade(self):
        for rec in self:
            rec.division_id = False  # Reset grade_id when company changes

    def action_create_attendance_line(self):

        self.name = str(self.date)
        attendance_line_obj = self.env['education.attendance.line']
        students = self.division_id.student_ids

        if not students:
            raise UserError(_('There are no students in this Division'))

        attendance_lines = []  # قائمة لتخزين البيانات قبل إنشائها دفعة واحدة

        for student in students:
            # البحث عن أي غياب مرخص للطالب
            permitted_absence = self.env['mc.student.permitted.absence'].sudo().search([
                ('class_division_id', '=', self.division_id.id),
                ('student_id', '=', student.id),
                ('start_date', '<=', self.date),
                ('end_date', '>=', self.date)
            ], limit=1)

            data = {
                'name': self.name,
                'attendance_id': self.id,
                'student_id': student.id,
                'student_name': student.name,
                'class_id': self.division_id.class_id.id,
                'division_id': self.division_id.id,
                'date': self.date,
                'present_morning': not bool(permitted_absence),  # تعيين الحضور بناءً على الغياب
            }

            if permitted_absence:
                data['sickness_absence'] = True
                if permitted_absence.reason_id:  # التحقق قبل الإضافة
                    data['sickness_reason'] = permitted_absence.reason_id.id


            attendance_lines.append(data)  # إضافة البيانات إلى القائمة

        if attendance_lines:
            attendance_line_obj.create(attendance_lines)  # إنشاء السجلات دفعة واحدة
            self.attendance_created = True  # تعيين الحقل عند نجاح العملية
