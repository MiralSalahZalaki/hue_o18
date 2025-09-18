from odoo import models, fields, api


class TimetableByClassAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_report_timetable_by_class'
    _description = 'Timetable by Class Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['timetable.by.calss.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        timetable_data = self._prepare_timetable_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'timetable.by.calss.wizard',
            'docs': [wizard],
            # Basic wizard info
            'class_division': wizard.class_division_id.name,
            'company_name': wizard.company_id.name,
            # Main data
            'is_student_specific': timetable_data.get('is_student_specific', False),
            'class_timetable': timetable_data.get('class_timetable', {}),
            'student_timetables': timetable_data.get('student_timetables', {}),
        }

    def _prepare_timetable_data(self, wizard):
        """Prepare timetable data based on wizard configuration"""
        wizard.ensure_one()
        
        # إنشاء جدول الفصل الكامل بغض النظر عن اختيار الطلاب
        class_timetable = self._prepare_class_timetable(wizard)
        
        # إذا تم اختيار طلاب محددين، قم بإنشاء جداول الطلاب
        if wizard.student_id:
            student_timetables = self._prepare_student_timetables(wizard)
            return {
                'class_timetable': class_timetable,
                'student_timetables': student_timetables,
                'is_student_specific': True
            }
        else:
            # إذا لم يتم اختيار طلاب محددين، قم بإرجاع جدول الفصل فقط
            return {
                'class_timetable': class_timetable,
                'is_student_specific': False
            }

    def _prepare_class_timetable(self, wizard):
        """Prepare class timetable data"""
        domain = [('class_division_id', '=', wizard.class_division_id.id)]
        timetable_records = self.env['education.timetable.schedule'].sudo().search(domain)
        class_timetable = {}
        
        for schedule in timetable_records:
            day_name = dict(schedule._fields['week_day'].selection).get(schedule.week_day)
            period = schedule.period_id.name
            time_from = schedule.time_from
            time_till = schedule.time_till
            subject = schedule.syllabus.name
            teacher = self._get_teacher_name(schedule)
            
            if day_name not in class_timetable:
                class_timetable[day_name] = []
            
            class_timetable[day_name].append({
                'period': period,
                'subject': subject,
                'time_from': self._float_to_time(time_from),
                'time_till': self._float_to_time(time_till),
                'teacher': teacher
            })
        
        return class_timetable

    def _prepare_student_timetables(self, wizard):
        """Prepare individual student timetables"""
        student_timetables = {}
        
        # معالجة كل طالب على حدة
        for student in wizard.student_id:
            student_timetable = self._prepare_single_student_timetable(wizard, student)
            # تخزين جدول الطالب مع اسمه
            student_timetables[student.name] = student_timetable
                
        return student_timetables

    def _prepare_single_student_timetable(self, wizard, student):
        """Prepare timetable for a single student"""
        # البحث عن المواد الاختيارية للطالب المحدد
        student_records = self.env['mc.elective.syllabus.students'].sudo().search([
            ('student_id', '=', student.id)
        ])
        
        if student_records:
            # الطالب لديه مواد اختيارية
            elective_syllabus_ids = student_records.mapped('syllabus_id')
            
            # بناء الاستعلام للحصول على جدول الطالب
            # الذي يتضمن المواد العامة للفصل + المواد الاختيارية الخاصة به
            domain = ['|',
                ('class_division_id', '=', wizard.class_division_id.id),
                ('syllabus', 'in', elective_syllabus_ids.ids)
            ]
        else:
            # الطالب ليس لديه مواد اختيارية، نبحث فقط عن المواد الإجبارية
            compulsory_syllabus = self.env['education.syllabus'].sudo().search([
                ('elective', '=', False)
            ])
            
            domain = [
                ('class_division_id', '=', wizard.class_division_id.id),
                ('syllabus', 'in', compulsory_syllabus.ids)
            ]
            
        # إنشاء جدول خاص لكل طالب
        timetable_records = self.env['education.timetable.schedule'].sudo().search(domain)
        student_timetable = {}
        
        for schedule in timetable_records:
            day_name = dict(schedule._fields['week_day'].selection).get(schedule.week_day)
            period = schedule.period_id.name
            time_from = schedule.time_from
            time_till = schedule.time_till
            subject = schedule.syllabus.name
            teacher = self._get_teacher_name(schedule)
            
            if day_name not in student_timetable:
                student_timetable[day_name] = []
            
            student_timetable[day_name].append({
                'period': period,
                'subject': subject,
                'time_from': self._float_to_time(time_from),
                'time_till': self._float_to_time(time_till),
                'teacher': teacher
            })
        
        return student_timetable

    def _get_teacher_name(self, schedule):
        """Get teacher name for a schedule"""
        teacher = self.env['mc.syllabus.per.class'].sudo().search([
            ('syllabus_id', '=', schedule.syllabus.id),
            ('class_division_id', '=', schedule.class_division_id.id)
        ]).faculty_regular_id.name or "N/A"
        
        return teacher

    def _float_to_time(self, float_time):
        """Convert float time to time string format"""
        hours = int(float_time)
        minutes = round((float_time - hours) * 60)
        # معالجة حالة إذا وصلت الدقائق إلى 60 بعد التقريب
        if minutes == 60:
            hours += 1
            minutes = 0
        return f"{hours:02d}:{minutes:02d}"