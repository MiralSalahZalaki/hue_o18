function toggleDiv() {
    var hasSiblings = document.getElementById("has_siblings").checked;
    var div = document.getElementById("siblings_info");

    var studentCode = document.getElementById("student_code");
    var fatherNationalId = document.getElementById("father_national_id");

    if (hasSiblings) {

        div.style.display = "flex";
        studentCode.setAttribute("required", "required");
        fatherNationalId.setAttribute("required", "required");
    } else {

        div.style.display = "none";
        studentCode.removeAttribute("required");
        fatherNationalId.removeAttribute("required");
    }
}


$(document).ready(function () {
    $("#admission_form").validate({

        rules: {
            name: {
                required: true,
                validarabicname: true,
            },

            admission_class_ids: {
                required: true,
            },

            student_national_id: {
                required: true,
                //validnumbers: true,
            },

            city: {
                required: true,
            },


            father_name: {
                required: true,
                validarabicname: true,

            },

            father_national_id: {
                required: true,
                //validnumbers: true,

            },

            father_profession: {
                required: true,
            },

            father_educational_qualifications: {
                required: true,
            },

            father_mobile: {
                required: true,
                //validnumbers: true,

            },

            father_email: {
                required: true,
                validateemail: true,
            },


            mother_name: {
                required: true,
                validarabicname: true,

            },

            mother_profession: {
                required: true,
            },

            mother_educational_qualifications: {
                required: true,
            },

            mother_mobile: {
                required: true,
                //validnumbers: true,

            },

            mother_email: {
                required: true,
                validateemail: true,
            },

            student_code: {
                //validnumbers: true,
            }

        },

        // الرسائل الخاصة بالتحقق
        messages: {
            name: {
                required: "يجب إدخال اسم الطالب",
                validarabicname: "يرجي ادخال الاسم باللغة العربية"
            },

            admission_class_ids: {
                required: "يجب تحديد الصف الدراسي ",

            },
            student_national_id: {
                required: "يجب إدخال الرقم القومي للطالب ",
                minlength: "يرجي ادخال 14 رقم باللغة الانجليزية",
                validnumbers: "يرجي اخال ارقام باللغة الانجليزية"
            },


            father_name: {
                required: "يجب إدخال اسم الأب",
                validarabicname: "يرجي ادخال الاسم باللغة العربية"

            },

            father_national_id: {
                required: "يجب إدخال الرقم القومي للأب ",
                minlength: "يرجي ادخال 14 رقم باللغة الانجليزية",
                validnumbers: "يرجي اخال ارقام باللغة الانجليزية"

            },

            father_profession: {
                required: "يرجي إدخال وظيفة الأب ",
            },

            father_mobile: {
                required: "يجب إدخال رقم للتواصل",
                validnumbers: "يرجي اخال ارقام باللغة الانجليزية"

            },

            father_email: {
                validateemail: "يرجى إدخال بريد إلكتروني صالح",
            },


            mother_name: {
                required: "يجب إدخال اسم الأم",
                validarabicname: "يرجي ادخال الاسم باللغة العربية"

            },

            mother_mobile: {
                required: "يجب إدخال رقم للتواصل",
                validnumbers: "يرجي اخال ارقام باللغة الانجليزية"

            },

            student_code: {
                validnumbers: "يرجي اخال ارقام باللغة الانجليزية"

            }

        },

        errorPlacement: function (error, element) {
            error.insertAfter(element.closest('div')); // ضع رسالة الخطأ بعد العنصر الأب (div)
        },

        /*   // التحكم في الإرسال
          submitHandler: function (form) {
              alert("تم إرسال البيانات بنجاح!");
              form.submit(); // إرسال البيانات فعليًا
          }, */


    });
});

$.validator.addMethod("validarabicname", function (value, element) {
    return /^[\u0600-\u06FF\s]+$/.test(value);
})

$.validator.addMethod("validenglishletters", function (value, element) {
    return /^[a-zA-Z\s]+$/.test(value);
})

/* $.validator.addMethod("validnumbers", function (value, element) {
    return /^[0-9]$/.test(value);
}) */

$.validator.addMethod("validateemail", function (value, element) {
    return /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(value);
})