from mainapp import views
from django.urls import path

urlpatterns = [
    path('sendmessages/', views.send_messages_view),
    path('getdata/', views.get_data),

    path('addmsgpattern/', views.add_msg_pattern),
    path('deletemsgpattern/<int:id>/', views.delete_msg_pattern),

    path('addinstructorplacement/', views.add_instructor_placement),
    path('deleteinstructorplacement/<int:instructorId>/<int:planId>/', views.delete_instructor_placement),

    path('addinstructorplancolor/', views.add_instructor_plan_color),
    path('updateinstructorplancolor/', views.update_instructor_plan_color),
    path('deleteinstructorplancolor/<int:instructorId>/<int:planId>/', views.delete_instructor_plan_color),

    path('updateplanmsgrequest/', views.update_plan_message),

    path('addplanbuttons/', views.add_plan_buttons),
    path('deleteplanbuttons/', views.delete_plan_buttons),

    path('updateplanplacedcandidates/', views.update_plan_placed_candidates),

    path('updateinstructornotes/', views.update_instructor_notes),

    path('uploadfiletodrive/', views.upload_file_to_drive),
    path('uploadinstructorfiletodrive/', views.upload_instructor_file_to_drive),
    path('uploadinstructorfiletodrivemultiple/', views.upload_instructor_file_to_drive_multiple),
    path('deletedrivefile/<str:fileId>/', views.delete_drive_file),
    path('listinstructorfiles/', views.list_instructor_files),

    path('uploadgooglecontact/', views.upload_google_contact),
    path('deletegooglecontact/<str:resourceName>/', views.delete_google_contact),
    path('updategooglecontact/', views.update_google_contact),

    path('addinstructor/', views.add_instructor),
    path('deleteinstructor/<int:instructorId>/', views.delete_instructor),
    path('updateinstructor/', views.update_instructor),

    path('city_distances/', views.city_distances),

    path('updateschool/', views.update_school),
    path('addschool/', views.add_school),
    path('deleteschool/<int:schoolId>/', views.delete_school),

    path('updatecontact/', views.update_contact),
    path('addcontact/', views.add_contact),
    path('deletecontact/<int:contactId>/', views.delete_contact),

    path('uploadproposaltodrive/', views.upload_proposal_to_drive),

    path('addpayment/', views.add_payment),
    path('updatepayment/', views.update_payment),
    path('deletepayment/<int:paymentId>/', views.delete_payment),

    path('addinvitation/', views.add_invitation),
    path('updateinvitation/', views.update_invitation),
    path('deleteinvitation/<int:invitationId>/', views.delete_invitation),

    path('addplan/', views.add_plan),
    path('updateplan/', views.update_plan),
    path('deleteplan/<int:planId>/', views.delete_plan),

    path('updatesettings/', views.update_settings),

    path('updatepeoplecreds/', views.update_people_creds),
    path('updateinstructorscreds/', views.update_instructors_creds),
    path('updateproposalcreds/', views.update_proposal_creds),
]