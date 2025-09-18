from odoo import models, fields, api

class McSyllabusPerClass(models.Model):
    _name = 'mc.syllabus.per.class'
    _description = 'Syllabus Per Class'

    mc_standard_class_id = fields.Many2one('mc.standard.class', string='Standard Per Class ID', store=True, readonly=True)
    syllabus_id = fields.Many2one('education.syllabus', ondelete="cascade", string='Syllabus', readonly=True)
    syllabus_name = fields.Char(related="syllabus_id.name", string="Syllabus Name", store=True)
    elective = fields.Boolean(readonly=True)
    class_division_id = fields.Many2one('education.class.division', string='Class', readonly=True)
    division = fields.Many2one('education.division', string='Division', related='class_division_id.division_id', store=True, readonly=True)
    class_id = fields.Many2one('education.class', string='Grade', related='class_division_id.class_id', store=True, readonly=True)

    room_regular_id = fields.Many2one('mc.rooms', string='Room Regular')
    faculty_regular_id = fields.Many2one('education.faculty', string='Faculty Regular')

    room_special_id = fields.Many2one('mc.rooms', string='Room Special')
    faculty_special_id = fields.Many2one('education.faculty', string='Faculty Special')

    regular = fields.Boolean(string='Regular', readonly=True)
    special = fields.Boolean(string='Special', readonly=True)
    faculty_phone = fields.Char(string='Phone')
    time_from = fields.Float(string='Time From')
    time_to = fields.Float(string='Time To')
    link = fields.Char(string='One Note Link')
    team_id_sds = fields.Char(string='Team ID', readonly=True)
    faculty_user_id = fields.Many2one('res.users', string='Faculty User', readonly=True)
    enrollment_per_class_ids = fields.One2many('mc.enrollment.per.class', 'user_class', string='Enrollment Per Class')
    company_id = fields.Many2one('res.company')

    @api.model
    def create(self, vals):
        record = super(McSyllabusPerClass, self).create(vals)
        record._sync_faculty_from_enrollment()
        return record

    def write(self, vals):
        result = super(McSyllabusPerClass, self).write(vals)
        self._sync_faculty_from_enrollment()
        return result

    def _sync_faculty_from_enrollment(self):
        for rec in self:
            # التأكد من عدم تكرار الإدخالات
            existing_teachers = self.env['mc.enrollment.per.class'].sudo().search([
                ('user_class', '=', rec.id),
                ('role', '=', 'teacher')
            ])

            # إضافة مدرس الـ Regular
            if rec.faculty_regular_id:
                if not existing_teachers.filtered(lambda e: e.teacher_id == rec.faculty_regular_id):
                    self.env['mc.enrollment.per.class'].create({
                        'user_class': rec.id,
                        'role': 'teacher',
                        'teacher_id': rec.faculty_regular_id.id
                    })

            # إضافة مدرس الـ Special
            if rec.faculty_special_id:
                if not existing_teachers.filtered(lambda e: e.teacher_id == rec.faculty_special_id):
                    self.env['mc.enrollment.per.class'].create({
                        'user_class': rec.id,
                        'role': 'teacher',
                        'teacher_id': rec.faculty_special_id.id
                    })
    
    def open_form_view(self, model, res_id, name):
        """Generic function to open a form view"""
        return {
            'name': name,
            'view_mode': 'form',
            'res_model': model,
            'res_id': res_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'flags': {'mode': 'readonly'},
        }

    def action_open_syllabus(self):
        return self.open_form_view('mc.syllabus.per.class', self.id, 'Syllabus')

    def action_open_regular_faculty(self):
        if self.faculty_regular_id:
            faculty_id = self.faculty_regular_id.id
            return self.open_form_view('education.faculty', faculty_id, 'Faculty')
        
    def action_open_special_faculty(self):
        if self.faculty_special_id:
            faculty_id = self.faculty_special_id.id
            return self.open_form_view('education.faculty', faculty_id, 'Faculty')


    
""" 
    def _sync_faculty_from_enrollment(self):
        for rec in self:
            # Search for teacher enrollment
            enrollment = self.env['mc.enrollment.per.class'].sudo().search([
                ('user_class', '=', rec.id),
                ('role', '=', 'teacher'),
                ('teacher_id', '!=', False)
            ], limit=1)

            # Update faculty_regular_id if needed
            if enrollment and enrollment.teacher_id:
                if rec.faculty_regular_id.id != enrollment.teacher_id.id:
                    rec.with_context(from_enrollment_sync=True).write({
                        'faculty_regular_id': enrollment.teacher_id.id
                    }) """
