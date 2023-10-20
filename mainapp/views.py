import json
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from mainapp.src.whatsappsender import send_messages, MessageTypes
import mainapp.src.access as db
import mainapp.forms as forms
import mainapp.src.drive.drivemethods as drivemethods
import mainapp.src.drive.service as instructors_service
import mainapp.src.drive.proposalservice as proposal_service
import mainapp.src.people.people as people
import mainapp.src.distances.distances as distances

from threading import Lock
import os

@csrf_exempt
def send_messages_view(request):
    school_error_status = 'שגוי'
    
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)


    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['msg1', 'msg2', 'msg3', 'phones', 'names', 'schoolIds', 'contactIds', 'isRepLst', 'status']):
        return HttpResponseBadRequest('Invalid JSON structure')


    # Check the data types in the JSON
    if not all(isinstance(data[key], str) or data[key] == None for key in ['msg1', 'msg2', 'msg3']):
        return HttpResponseBadRequest('Invalid data type')

    if not isinstance(data['phones'], list) or data['phones'] == None:
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['names'], list) or data['names'] == None:
        return HttpResponseBadRequest('Invalid data type')

    if data['phones'] != None and not all(isinstance(phone, str) for phone in data['phones']):
        return HttpResponseBadRequest('Invalid data type')
    if data['names'] != None and not all(isinstance(phone, str) for phone in data['names']):
        return HttpResponseBadRequest('Invalid data type')
    
    # Ids CAN be None


    # Prepare the messages and send them
    messages = []

    if data['msg1'] != None:
        messages.append((data['msg1'].replace('{NAME}', '{name}'), MessageTypes.TEXT))
    if data['msg2'] != None:
        messages.append((data['msg2'], MessageTypes.DOCUMENT))
    if data['msg3'] != None:
        messages.append((data['msg3'].replace('{NAME}', '{name}'), MessageTypes.TEXT))
    
    msg_statuses_lists = send_messages(messages, data['phones'], data['names'], data['schoolIds'], data['contactIds'],
        data['isRepLst'], db.update_school_status, db.update_contact_status, data['status'], school_error_status)

    response = []
    for statuses_list in msg_statuses_lists:
        if isinstance(statuses_list, list):
            statuses = {
                'msg1': None,
                'msg2': None,
                'msg3': None
            }
            for status, msg in zip(statuses_list, [msg for msg in ('msg1', 'msg2', 'msg3') if data[msg] != None]):
                statuses[msg] = int(status)
            response.append(statuses)
        else:
            response.append(int(statuses_list))

    return JsonResponse({'msg_statuses': response})



def get_data(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'GET':
        return HttpResponse(status=405)
    else:
        return JsonResponse(db.get_all_data())



# Adding an instructor placement in the Access database and returning the id of the new placement
@csrf_exempt
def add_instructor_placement(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['instructorId', 'planId']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not all(isinstance(data[field], int) for field in ('instructorId', 'planId')):
        return HttpResponseBadRequest('Invalid data type')

    return JsonResponse({'id': db.add_instructor_placement_to_db(data['instructorId'], data['planId'])})



# Canceling an instructor placement in the Access database
@csrf_exempt
def delete_instructor_placement(request, instructorId, planId):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    db.delete_instructor_placement_from_db(instructorId, planId)
    return HttpResponse(status=204)




@csrf_exempt
def add_msg_pattern(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['msg1', 'msg2', 'msg3', 'title']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not all(isinstance(data[field], str) for field in ('msg1', 'msg2', 'msg3', 'title')):
        return HttpResponseBadRequest('Invalid data type')



    msg1, msg2, msg3, title = '', '', '', ''
    if data['msg1'] != None:
        msg1 = data['msg1']
    if data['msg2'] != None:
        msg2 = data['msg2']
    if data['msg3'] != None:
        msg3 = data['msg3']
    if data['title'] != None:
        title = data['title']

    db.add_msg_pattern_to_db(msg1, msg2, msg3, title)
    return HttpResponse(status=200)
    



@csrf_exempt
def delete_msg_pattern(request, id):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)
    
    db.delete_msg_pattern_from_db(id)
    return HttpResponse(status=204)





# Adding an instructor placement in the Access database and returning the id of the new placement
@csrf_exempt
def add_instructor_plan_color(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['instructorId', 'planId', 'colorId']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not all(isinstance(data[field], int) for field in ('instructorId', 'planId', 'colorId')):
        return HttpResponseBadRequest('Invalid data type')

    db.add_instructor_plan_color_in_db(data['instructorId'], data['planId'], data['colorId'])
    return HttpResponse(status=200)



# Adding an instructor placement in the Access database and returning the id of the new placement
@csrf_exempt
def update_instructor_plan_color(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['instructorId', 'planId', 'colorId']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not all(isinstance(data[field], int) for field in ('instructorId', 'planId', 'colorId')):
        return HttpResponseBadRequest('Invalid data type')

    db.update_instructor_plan_color_in_db(data['instructorId'], data['planId'], data['colorId'])
    return HttpResponse(status=200)



# Canceling an instructor placement in the Access database
@csrf_exempt
def delete_instructor_plan_color(request, instructorId, planId):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    db.delete_instructor_plan_color_in_db(instructorId, planId)
    return HttpResponse(status=204)



# Updating the default message of a plan
@csrf_exempt
def update_plan_message(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['planId', 'msg']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not all(isinstance(data[field], int) for field in ['planId']):
        return HttpResponseBadRequest('Invalid data type')
    if not all(isinstance(data[field], str) for field in ['msg']):
        return HttpResponseBadRequest('Invalid data type')

    db.update_plan_message(data['planId'], data['msg'])
    return HttpResponse(status=200)



# Adding and deleting selected instructor query buttons for each plan
@csrf_exempt
def add_plan_buttons(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['planId', 'buttons']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not isinstance(data['planId'], int) or not isinstance(data['buttons'], list):
        return HttpResponseBadRequest('Invalid data type')
    if not all(isinstance(button_desc, str) for button_desc in data['buttons']):
        return HttpResponseBadRequest('Invalid data type')

    db.add_plan_buttons(data['planId'], data['buttons'])
    return HttpResponse(status=200)

@csrf_exempt
def delete_plan_buttons(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['planId', 'buttons']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not isinstance(data['planId'], int) or not isinstance(data['buttons'], list):
        return HttpResponseBadRequest('Invalid data type')
    if not all(isinstance(button_desc, str) for button_desc in data['buttons']):
        return HttpResponseBadRequest('Invalid data type')

    db.delete_plan_buttons(data['planId'], data['buttons'])
    return HttpResponse(status=200)



# Updating the candidates that have been placed to a plan
@csrf_exempt
def update_plan_placed_candidates(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['planId', 'instructor1', 'instructor2', 'instructor3', 'instructor4']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not isinstance(data['planId'], int):
        return HttpResponseBadRequest('Invalid data type')
    if not all(isinstance(data[field], str) for field in ['instructor1', 'instructor2', 'instructor3', 'instructor4']):
        return HttpResponseBadRequest('Invalid data type')

    db.update_plan_placed_candidates(data['planId'], data['instructor1'], data['instructor2'], data['instructor3'], data['instructor4'])
    return HttpResponse(status=200)



@csrf_exempt
def update_instructor_notes(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['instructorId', 'notes']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not isinstance(data['instructorId'], int):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['notes'], str):
        return HttpResponseBadRequest('Invalid data type')

    db.update_instructor_notes(data['instructorId'], data['notes'])
    return HttpResponse(status=200)



@csrf_exempt
def upload_file_to_drive(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    form = forms.DriveUploadForm(request.POST, request.FILES) # A form bound to the POST data

    if form.is_valid():
        file = request.FILES.get('file')
        if file == None:
            return HttpResponseBadRequest('File is null')
        try:
            drive_link = drivemethods.upload_file(file=file, dir_name='test1')
            return JsonResponse({
                'drive_link': drive_link,
            })
        except Exception as err:
            print(err)
            return HttpResponse(status=500, content=err)
    else:
        return HttpResponseBadRequest('Invalid form')

@csrf_exempt
def delete_drive_file(request, fileId):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    try:
        drivemethods.delete_file(fileId)
        return HttpResponse(status=200)
    except Exception as err:
        print(err)
        return HttpResponse(status=500, content=err)

# Upload an instructor file to google drive
@csrf_exempt
def upload_instructor_file_to_drive(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    form = forms.DriveUploadForm(request.POST, request.FILES) # A form bound to the POST data

    if form.is_valid():
        file = request.FILES.get('file')
        area = request.POST.get('area')
        city = request.POST.get('city')
        name = request.POST.get('name')
        dir_name = request.POST.get('dir_name')

        if file == None:
            return HttpResponseBadRequest('File is null')
        try:
            file_id, drive_link = drivemethods.upload_instructor_file(
                area=area, city=city, name=name, dir_name=dir_name, file=file
            )
            return JsonResponse({
                'id': file_id,
                'drive_link': drive_link,
            })
        except Exception as err:
            print(err)
            return HttpResponse(status=500, content=err)
    else:
        return HttpResponseBadRequest('Invalid form')

# Upload an instructor file to google drive
# Allows multiple files under the same category
@csrf_exempt
def upload_instructor_file_to_drive_multiple(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    form = forms.DriveUploadForm(request.POST, request.FILES) # A form bound to the POST data

    if form.is_valid():
        file = request.FILES.get('file')
        area = request.POST.get('area')
        city = request.POST.get('city')
        name = request.POST.get('name')
        dir_name = request.POST.get('dir_name')

        if file == None:
            return HttpResponseBadRequest('File is null')
        try:
            file_id, drive_link = drivemethods.upload_instructor_file_multiple(
                area=area, city=city, name=name, dir_name=dir_name, file=file
            )
            return JsonResponse({
                'id': file_id,
                'drive_link': drive_link,
            })
        except Exception as err:
            print(err)
            return HttpResponse(status=500, content=err)
    else:
        return HttpResponseBadRequest('Invalid form')

list_instructor_files_lock = Lock()
@csrf_exempt
def list_instructor_files(request):
    with list_instructor_files_lock:
        # Return a 405 Method Not Allowed error for non-POST requests
        if request.method != 'POST':
            return HttpResponse(status=405)

        # Validate the JSON structure
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')
        if not isinstance(data, dict) or not all(key in data for key in ['area', 'city', 'name', 'dirNames']):
            return HttpResponseBadRequest('Invalid JSON structure')

        return JsonResponse({
            'instructorFiles': drivemethods.list_instructor_files(
                data['area'], data['city'], data['name'], data['dirNames']
            )
        })

# Update data of an instructor
@csrf_exempt
def add_instructor(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    if not isinstance(data, dict) or not all(key in data for key in ['firstName', 'lastName', 'cv', 'certificates',
        'policeApproval', 'insurance', 'agreement', 'city', 'area', 'sector', 'instructorTypes']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not all(isinstance(data[field], str) for field in ['firstName', 'lastName', 'cv', 'certificates',
        'policeApproval', 'insurance', 'agreement', 'city', 'area', 'sector']):
        return HttpResponseBadRequest('Invalid data type')
    if not all(isinstance(data[field], dict) for field in ['instructorTypes']):
        return HttpResponseBadRequest('Invalid data type')

    id = db.add_instructor(data['firstName'], data['lastName'], data['cv'], data['certificates'],
        data['policeApproval'], data['insurance'], data['agreement'], data['city'], data['area'],
        data['sector'], data['instructorTypes'])
    return JsonResponse({'id': id})

@csrf_exempt
def delete_instructor(request, instructorId):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    db.delete_instructor(instructorId)
    return HttpResponse(status=204)

@csrf_exempt
def update_instructor(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    db.update_instructor(data['id'], data['recordData'])
    return HttpResponse(status=200)



@csrf_exempt
def city_distances(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    return JsonResponse({ 'dists': distances.get_distances(data['origin'], data['destinations']) })



@csrf_exempt
def add_school(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['name', 'sym', 'level', 'sector', 'schoolType', 'city', 'representative', 'status']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if data['name'] and not isinstance(data['name'], str):
        return HttpResponseBadRequest('Invalid data type')
    if data['sym'] and not isinstance(data['sym'], int):
        return HttpResponseBadRequest('Invalid data type')
    if data['level'] and not isinstance(data['level'], str):
        return HttpResponseBadRequest('Invalid data type')
    if data['sector'] and not isinstance(data['sector'], str):
        return HttpResponseBadRequest('Invalid data type')
    if data['schoolType'] and not isinstance(data['schoolType'], str):
        return HttpResponseBadRequest('Invalid data type')
    if data['city'] and not isinstance(data['city'], str):
        return HttpResponseBadRequest('Invalid data type')
    if data['representative'] and not isinstance(data['representative'], str):
        return HttpResponseBadRequest('Invalid data type')
    if data['status'] and not isinstance(data['status'], str):
        return HttpResponseBadRequest('Invalid data type')

    try:
        id = db.add_school(data['name'], data['sym'], data['level'], data['sector'], data['schoolType'], data['city'], data['representative'], data['status'])
        return JsonResponse({'id': id})
    except Exception as err:
        return HttpResponse(status=500, content=f'Could not upload school details to database.\n{err}')



@csrf_exempt
def update_school(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    
    db.update_school(data['schoolId'], data['schoolData'])
    return HttpResponse(status=200)



@csrf_exempt
def delete_school(request, schoolId):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    db.delete_school(schoolId)
    return HttpResponse(status=204)



@csrf_exempt
def add_contact(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['schoolId', 'schoolName', 'firstName', 'lastName', 'role', 'phone', 'status', 'googleContactsResourceName']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if data['schoolId'] and not isinstance(data['schoolId'], int):
        return HttpResponseBadRequest('Invalid data type')
    if all(data[key] and not isinstance(data[key], str) for key in
           ['schoolName', 'firstName', 'lastName', 'role', 'phone', 'status', 'googleContactsResourceName']):
        return HttpResponseBadRequest('Invalid data type')

    try:
        id = db.add_contact(data['schoolId'], data['schoolName'], data['firstName'], data['lastName'], data['role'], data['phone'], data['status'], data['googleContactsResourceName'])
        return JsonResponse({'id': id})
    except Exception as err:
        return HttpResponse(status=500, content=f'Could not upload contact details to database.\n{err}')



@csrf_exempt
def update_contact(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    db.update_contact(data['contactId'], data['contactData'])
    return HttpResponse(status=200)



@csrf_exempt
def delete_contact(request, contactId):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    db.delete_contact(contactId)
    return HttpResponse(status=204)



@csrf_exempt
def upload_google_contact(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['name', 'phone']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not isinstance(data['name'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['phone'], str):
        return HttpResponseBadRequest('Invalid data type')

    try:
        person = people.upload_contact(data['name'], data['phone'])
        return JsonResponse({
            'resourceName': person['resourceName']
        })
    except Exception as err:
        return HttpResponse(status=500, content=f'Could not upload contact to Google Contacts\n{err}')

@csrf_exempt
def update_google_contact(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['resourceName', 'name', 'phone']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not isinstance(data['name'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['phone'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['resourceName'], str):
        return HttpResponseBadRequest('Invalid data type')

    try:
        people.update_contact(data['resourceName'], data['name'], data['phone'])
        return HttpResponse(status=200)
    except Exception as err:
        return HttpResponse(status=500, content=f'Could not update google contact\n{err}')

@csrf_exempt
def delete_google_contact(request, resourceName):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    try:
        people.remove_contact(resourceName)
        return HttpResponse(status=200)
    except Exception as err:
        return HttpResponse(status=500, content=f'Could not upload contact to Google Contacts\n{err}')



@csrf_exempt
def upload_proposal_to_drive(request):
    # Return a 405 Method Not Allowed error for non-POST requests
    if request.method != 'POST':
        return HttpResponse(status=405)

    form = forms.ProposalUploadForm(request.POST, request.FILES) # A form bound to the POST data

    if form.is_valid():

        proposal_file = request.FILES.get('proposalFile')
        year = request.POST.get('year')
        district = request.POST.get('district')
        city = request.POST.get('city')
        school = request.POST.get('school')

        success, drive_link = \
            drivemethods.upload_proposal_file(proposal_file, year, district, city, school) \
            if proposal_file != None else (True, None)

        if success:
            return JsonResponse({'drive_link': drive_link})
        else:
            return HttpResponse(status=500)
    else:
        return HttpResponseBadRequest('Invalid form')




# Update payments data
@csrf_exempt
def add_payment(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['issuer', 'schoolName', 'plan', 'payed', 'sym']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not isinstance(data['issuer'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['schoolName'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['plan'], str):
        return HttpResponseBadRequest('Invalid data type')
    # TO DO: Change to int
    if not isinstance(data['payed'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['sym'], int):
        return HttpResponseBadRequest('Invalid data type')

    try:
        id = db.add_payment(data['issuer'], data['schoolName'], data['plan'], data['payed'], data['sym'])
        return JsonResponse({'id': id})
    except Exception as err:
        return HttpResponse(status=500, content=f'Could not upload payment details to database.\n{err}')

@csrf_exempt
def update_payment(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    db.update_payment(data['id'], data['recordData'])
    return HttpResponse(status=200)

@csrf_exempt
def delete_payment(request, paymentId):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    db.delete_payment(paymentId)
    return HttpResponse(status=204)



# Add and update an invitation
@csrf_exempt
def add_invitation(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['issueDate', 'issuer', 'planName', 'payed', 'checkDate', 'sym']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    if not isinstance(data['issueDate'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['issuer'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['planName'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['payed'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['checkDate'], str):
        return HttpResponseBadRequest('Invalid data type')
    if not isinstance(data['sym'], int):
        return HttpResponseBadRequest('Invalid data type')

    id = db.add_invitation(data['issueDate'], data['issuer'], data['planName'], data['payed'], data['checkDate'], data['sym'])
    return JsonResponse({'id': id})

@csrf_exempt
def update_invitation(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    db.update_invitation(data['id'], data['recordData'])
    return HttpResponse(status=200)

@csrf_exempt
def delete_invitation(request, invitationId):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    db.delete_invitation(invitationId)
    return HttpResponse(status=204)



# Update plans data
@csrf_exempt
def add_plan(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    if not isinstance(data, dict) or not all(key in data for key in ['year', 'proposal', 'status', 'invitation', 'level', 'sym', 'schoolId', 'institution',
        'contact', 'date', 'district', 'city', 'plan', 'days', 'day', 'weeks', 'grade', 'lessonsPerDay', 'lessons', 'pricePerHour', 'overall', 'details']):
        return HttpResponseBadRequest('Invalid JSON structure')
    
    # Check the data types in the JSON
    #if not all(data[field] == None or isinstance(data[field], str) for field in ['year', 'status', 'invitation', 'level', 'institution',
    #    'contact', 'date', 'district', 'city', 'plan', 'days', 'day', 'grade', 'details']):
    #    return HttpResponseBadRequest('Invalid data type')
    #if not all(data[field] == None or isinstance(data[field], int) for field in ['sym', 'weeks', 'lessonsPerDay', 'lessons', 'pricePerHour', 'overall']):
    #    return HttpResponseBadRequest('Invalid data type')

    try:
        id = db.add_plan(data['year'], data['proposal'], data['status'], data['invitation'], data['level'], data['sym'], data['schoolId'], data['institution'], data['contact'],
            data['date'], data['district'], data['city'], data['plan'], data['days'], data['day'], data['weeks'], data['grade'], data['lessonsPerDay'], data['lessons'],
            data['pricePerHour'], data['overall'], data['details'])
        return JsonResponse({'id': id})
    except Exception as err:
        return HttpResponse(status=500, content=f'Could not upload plan details to database.\n{err}')



@csrf_exempt
def update_plan(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    db.update_plan(data['id'], data['recordData'])
    return HttpResponse(status=200)



@csrf_exempt
def delete_plan(request, planId):
    # Return a 405 Method Not Allowed error for non-DELETE requests
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    db.delete_plan(planId)
    return HttpResponse(status=204)



@csrf_exempt
def update_settings(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Validate the JSON structure
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    try:
        db.update_settings(data)
    except Exception as err:
        return HttpResponse(status=500, content=f'Could not update general settings.\n{err}')

    return HttpResponse(status=200)



@csrf_exempt
def update_people_creds(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        if os.path.isfile(people.CREDS_PATH):
            os.remove(people.CREDS_PATH)
        people.get_creds()
        return HttpResponse(status=200)
    except Exception as err:
        print(err)
        return HttpResponse(status=500, content=f'Could not get people creds.')

@csrf_exempt
def update_instructors_creds(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        if os.path.isfile(instructors_service.CREDS_PATH):
            os.remove(instructors_service.CREDS_PATH)
        instructors_service.get_creds()
        return HttpResponse(status=200)
    except Exception as err:
        print(err)
        return HttpResponse(status=500, content=f'Could not get instructors creds.')

@csrf_exempt
def update_proposal_creds(request):
    # Return a 405 Method Not Allowed error for non-GET requests
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        if os.path.isfile(proposal_service.CREDS_PATH):
            os.remove(proposal_service.CREDS_PATH)
        proposal_service.get_creds()
        return HttpResponse(status=200)
    except Exception as err:
        print(err)
        return HttpResponse(status=500, content=f'Could not get proposal creds.')