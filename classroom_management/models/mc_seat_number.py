from odoo import _, api, fields, models


class MCSeatNumber(models.Model):
    _name = 'mc.seat.number'
    _description = 'Seat Numbers for Students'

    company_id = fields.Many2one(
        'res.company',
        string=_('School'),
        default=lambda self: self.env.company,
        required=True
    )
    grade_id = fields.Many2one(
        "education.class",
        string=_("Grade"),
        domain="[('school', '=', company_id)]",
        required=True
    )
    start_from = fields.Integer(string=_("Start From"), required=True)
    gender = fields.Boolean(
        string=_("By Gender"),
        default=False,
        help=_("Arrange student seating by gender, with female students seated first, followed by male students.")
    )
    student_list = fields.One2many(
        'seat.number.student.list',
        'seat_id',
        string=_('Student List')
    )

    _sql_constraints = [
        ('unique_grade_company', 'UNIQUE(grade_id, company_id)', _('This Grade must be unique per School!'))
    ]

    def get_students_list(self):
        for rec in self:
            if rec.grade_id and rec.start_from:
                # Fetch students, initially sorted by full_arabic_name
                student_list = self.env['education.student'].sudo().search([
                    ('grade_id', '=', rec.grade_id.id),
                    ('company_id', '=', rec.company_id.id)
                ], order='full_arabic_name ASC')

                # If sorting by gender, sort programmatically
                if rec.gender:
                    student_list = sorted(
                        student_list,
                        key=lambda s: (s.gender != 'female', s.full_arabic_name)
                    )

                # Get existing student IDs
                existing_student_ids = rec.student_list.mapped('student_id.id')

                # Create new student records
                new_student_records = []
                current_seat = rec.start_from

                for student in student_list:
                    if student.id not in existing_student_ids:
                        new_student_records.append({
                            'seat_id': rec.id,
                            'student_id': student.id,
                            'seat_number': str(current_seat),
                        })
                        # هنا نعدل مباشرة seat_number في education.student
                        student.seat_number = str(current_seat)

                        current_seat += 1


                # Create new records if any
                if new_student_records:
                    self.env['seat.number.student.list'].create(new_student_records)
                    
class SeatNumberStudentList(models.Model):
    _name = 'seat.number.student.list'
    _description = 'List of Students'

    seat_id = fields.Many2one('mc.seat.number', string=_('Seat ID'))
    student_id = fields.Many2one('education.student', string=_('Student'))
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string=_('Gender'), related='student_id.gender')
    student_code = fields.Char(string=_('Student Code'), related='student_id.student_code')
    seat_number = fields.Char(string=_('Seat Number'))