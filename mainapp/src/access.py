from mainapp.src.accessconnect import create_connection, tables
import json
from threading import Lock

access_lock_inst = Lock()
def access_lock(func):
    def wrapper(*args, **kwargs):
        with access_lock_inst:
            return func(*args, **kwargs)
    return wrapper

conn = create_connection()

tbl_names = tables['tblNames']
tbl_cols = tables['tblCols']
uniques_names = tables['uniques']
condensed_true_false = tables['condensedTrueFalse']

def get_tbl_data(tbl_name, col_names, condensed_tf_cols=None):
    cursor = conn.cursor()
    cursor.execute(f'SELECT {", ".join(col_names.values())} FROM {tbl_name}' + (f' ORDER BY {col_names["id"]}' if "id" in col_names else ''))
    records = [{column_name: column_value if column_value != '' else None
                for column_name, column_value in zip(col_names.keys(), row) if column_name != None} for row in cursor.fetchall()]

    if condensed_tf_cols != None:
        for record in records:
            for condensed_col_name, condesned_col_fields in condensed_tf_cols:
                establish_condensed_true_false(record, col_names['id'], tbl_name, condensed_col_name, condesned_col_fields)
    return records

def establish_condensed_true_false(record, id_col_name, tbl_name, condensed_col_name, condensed_col_fields):
    cursor = conn.cursor()
    cursor.execute(f'SELECT {", ".join(map(lambda field: f"[{field}]", condensed_col_fields))} FROM {tbl_name} WHERE {id_col_name}={record["id"]};')
    true_false_values = cursor.fetchone()
    record[condensed_col_name] = [tf_field for tf_field, tf_value in zip(condensed_col_fields, true_false_values) if tf_value]

def uniques_data(tables, data):
    for table_name, table_uniques_names in tables.items():
        for field_data, field_obj in table_uniques_names.items():
            lst_field = [obj[field_obj] for obj in data[table_name]]
            data[field_data] = [{'id': idx, 'desc': val} for idx, val in enumerate(set(lst_field))]
            data[field_data].sort(key=lambda x: x['desc'] if x['desc'] != None else '')
    return data

@access_lock
def get_all_data():
    data = dict()
    for tbl_english_name, tbl_db_name in tbl_names.items():
        if tbl_english_name in condensed_true_false:
            data[tbl_english_name] = get_tbl_data(tbl_db_name, tbl_cols[tbl_english_name], condensed_true_false[tbl_english_name].items())
        else:
            data[tbl_english_name] = get_tbl_data(tbl_db_name, tbl_cols[tbl_english_name])
    data = uniques_data(uniques_names, data)

    data['settings'] = None
    try:
        with open('mainapp/data/general_settings.json', 'r', encoding='utf-8') as general_settings:
            data['settings'] = json.load(general_settings)
    except FileNotFoundError:
        print('File not found.')
    except PermissionError:
        print('Permission denied.')
    except IOError:
        print('Error reading file.')

    return data



# Auxiallary functions
def prepare_ISO8601_date(ISO8601_str):
    return f'#{ISO8601_str.split("T")[0]}#' if ISO8601_str else 'NULL'

def prepare_number(num):
    return num if num else 'NULL'

def xstr(s):
    if s:
        return str(s).replace('\'', '\'\'')
    else:
        return ''



@access_lock
def update_school_status(newStatus, id):
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["schools"]} \
        SET {tbl_cols["schools"]["status"]}=\'{xstr(newStatus)}\' \
        WHERE {tbl_cols["schools"]["id"]}={id};')
    cursor.commit()

@access_lock
def update_contact_status(newStatus, id):
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["contacts"]} \
        SET {tbl_cols["contacts"]["status"]}=\'{xstr(newStatus)}\' \
        WHERE {tbl_cols["contacts"]["id"]}={id};')
    cursor.commit()

# The queries of adding and deleting a message pattern in the Access database
@access_lock
def add_msg_pattern_to_db(msg1, msg2, msg3, title):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO {tbl_names["messages"]} ({tbl_cols["messages"]["msg1"]}, {tbl_cols["messages"]["msg2"]},\
        {tbl_cols["messages"]["msg3"]}, {tbl_cols["messages"]["title"]})\
        VALUES (\'{xstr(msg1)}\', \'{xstr(msg2)}\', \'{xstr(msg3)}\', \'{xstr(title)}\');')
    cursor.commit()
    cursor.execute(f'SELECT @@IDENTITY FROM {tbl_names["messages"]};')
    # Returning the id of the new message pattern
    return cursor.fetchone()[0]

@access_lock
def delete_msg_pattern_from_db(msg_id):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {tbl_names["messages"]} WHERE {tbl_cols["messages"]["id"]}={msg_id};')
    cursor.commit()



# The queries of adding and deleting an "instructor plan color" in the Access database
@access_lock
def add_instructor_plan_color_in_db(instructorId, planId, colorId):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO {tbl_names["instructorPlanColors"]} ({tbl_cols["instructorPlanColors"]["instructorId"]}, {tbl_cols["instructorPlanColors"]["planId"]},\
        {tbl_cols["instructorPlanColors"]["colorId"]}) \
        VALUES ({instructorId}, {planId}, {colorId});')
    cursor.commit()

@access_lock
def delete_instructor_plan_color_in_db(instructorId, planId):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {tbl_names["instructorPlanColors"]} WHERE \
        {tbl_cols["instructorPlanColors"]["instructorId"]}={instructorId} AND {tbl_cols["instructorPlanColors"]["planId"]}={planId};')
    cursor.commit()

@access_lock
def update_instructor_plan_color_in_db(instructorId, planId, colorId):
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["instructorPlanColors"]} \
        SET {tbl_cols["instructorPlanColors"]["colorId"]}={colorId} \
        WHERE {tbl_cols["instructorPlanColors"]["instructorId"]}={instructorId} AND {tbl_cols["instructorPlanColors"]["planId"]}={planId};')
    cursor.commit()

# The queries of adding and deleting an instructor placement in the Access database
@access_lock
def add_instructor_placement_to_db(instructorId, planId):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO {tbl_names["instructorPlacements"]} ({tbl_cols["instructorPlacements"]["planId"]}, {tbl_cols["instructorPlacements"]["instructorId"]}) \
        VALUES ({planId}, {instructorId});')
    cursor.commit()

@access_lock
def delete_instructor_placement_from_db(instructorId, planId):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {tbl_names["instructorPlacements"]} \
        WHERE {tbl_cols["instructorPlacements"]["instructorId"]}={instructorId} AND {tbl_cols["instructorPlacements"]["planId"]}={planId};')
    cursor.commit()

# Update default message of a plan
@access_lock
def update_plan_message(planId, msg):
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["plans"]} \
        SET {tbl_cols["plans"]["msg"]}=\'{xstr(msg)}\' \
        WHERE {tbl_cols["plans"]["id"]}={planId};')
    cursor.commit()

apostrophe = "'"
double_apostrophe = "''"

# Adding and deleting selected instructor query buttons for each plan
@access_lock
def add_plan_buttons(planId, buttons):
    cursor = conn.cursor()
    for button in buttons:
        cursor.execute(f'INSERT INTO {tbl_names["planButtons"]} ({tbl_cols["planButtons"]["planId"]}, {tbl_cols["planButtons"]["button"]}) \
            VALUES ({planId}, \'{xstr(button.replace(apostrophe, double_apostrophe))}\');')
    cursor.commit()

@access_lock
def delete_plan_buttons(planId, buttons):
    cursor = conn.cursor()
    for button in buttons:
        cursor.execute(f'DELETE FROM {tbl_names["planButtons"]} \
            WHERE {tbl_cols["planButtons"]["button"]}=\'{xstr(button.replace(apostrophe, double_apostrophe))}\' \
            AND {tbl_cols["planButtons"]["planId"]}={planId};')
    cursor.commit()

# Updating the candidates that have been placed to a plan
@access_lock
def update_plan_placed_candidates(planId, instructor1, instructor2, instructor3, instructor4):
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["plans"]} \
        SET {tbl_cols["plans"]["instructor1"]}=\'{xstr(instructor1)}\', \
            {tbl_cols["plans"]["instructor2"]}=\'{xstr(instructor2)}\', \
            {tbl_cols["plans"]["instructor3"]}=\'{xstr(instructor3)}\', \
            {tbl_cols["plans"]["instructor4"]}=\'{xstr(instructor4)}\' \
        WHERE {tbl_cols["plans"]["id"]}={planId};')
    cursor.commit()

@access_lock
def update_instructor_notes(instructorId, notes):
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["instructors"]} \
        SET {tbl_cols["instructors"]["notes"]}=\'{xstr(notes)}\' \
        WHERE {tbl_cols["instructors"]["id"]}={instructorId};')
    cursor.commit()

booleanToAccess = lambda cond: "true" if cond else "false"

# Update instructors data
@access_lock
def add_instructor(firstName, lastName, cv, certificates, policeApproval, insurance, agreement, city, area, sector, instructorTypes):
    instructorTypeValues = [booleanToAccess(instructorTypes[type]) for type in condensed_true_false["instructors"]["instructorTypes"]]
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO {tbl_names["instructors"]} ({tbl_cols["instructors"]["firstName"]}, {tbl_cols["instructors"]["lastName"]}, \
        {tbl_cols["instructors"]["cv"]}, {tbl_cols["instructors"]["certificates"]}, {tbl_cols["instructors"]["policeApproval"]}, {tbl_cols["instructors"]["insurance"]}, \
        {tbl_cols["instructors"]["agreement"]}, \
        {tbl_cols["instructors"]["city"]}, {tbl_cols["instructors"]["area"]}, {tbl_cols["instructors"]["sector"]}, ' +
        ', '.join([f'[{i_type}]' for i_type in condensed_true_false["instructors"]["instructorTypes"]]) + ') ' +
        f'VALUES (\'{xstr(firstName)}\', \'{xstr(lastName)}\', \'{xstr(cv)}\', \'{xstr(certificates)}\', \'{xstr(policeApproval)}\', \'{xstr(insurance)}\', \'{xstr(agreement)}\', \'{xstr(city)}\', \'{xstr(area)}\', \'{xstr(sector)}\', ' +
        ', '.join(instructorTypeValues) + ');')
    cursor.commit()
    cursor.execute(f'SELECT @@IDENTITY FROM {tbl_names["instructors"]};')
    # Returning the id of the new instructor
    return cursor.fetchone()[0]

@access_lock
def delete_instructor(instructorId):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {tbl_names["instructors"]} \
        WHERE {tbl_cols["instructors"]["id"]}={instructorId};')
    cursor.commit()

@access_lock
def update_instructor(id, record_data):
    record_data = {key: value if value else '' for key, value in record_data.items()}
    cursor = conn.cursor()
    # Updating pricing doesn't work yet
    cursor.execute(f'UPDATE {tbl_names["instructors"]} \
        SET  \
            {tbl_cols["instructors"]["firstName"]}=\'{xstr(record_data["firstName"])}\', \
            {tbl_cols["instructors"]["lastName"]}=\'{xstr(record_data["lastName"])}\', \
            {tbl_cols["instructors"]["cv"]}=\'{xstr(record_data["cv"])}\', \
            {tbl_cols["instructors"]["city"]}=\'{xstr(record_data["city"])}\', \
            {tbl_cols["instructors"]["area"]}=\'{xstr(record_data["area"])}\', \
            {tbl_cols["instructors"]["sector"]}=\'{xstr(record_data["sector"])}\', \
            {tbl_cols["instructors"]["notes"]}=\'{xstr(record_data["notes"])}\', \
            {tbl_cols["instructors"]["certificates"]}=\'{xstr(record_data["certificates"])}\', \
            {tbl_cols["instructors"]["policeApproval"]}=\'{xstr(record_data["policeApproval"])}\', \
            {tbl_cols["instructors"]["insurance"]}=\'{xstr(record_data["insurance"])}\', \
            {tbl_cols["instructors"]["agreement"]}=\'{xstr(record_data["agreement"])}\', '
            + ', '.join([f'[{i_type}]={booleanToAccess(record_data["instructorTypes"][i_type])}' for i_type in condensed_true_false["instructors"]["instructorTypes"]]) +
        f' WHERE {tbl_cols["instructors"]["id"]}={id};')
        
    cursor.commit()

@access_lock
def update_school(school_id, record_data):
    record_data = {key: value if value else '' for key, value in record_data.items()}
    cursor = conn.cursor()
    # Updating date is not yet possible
    cursor.execute(f'UPDATE {tbl_names["schools"]} \
        SET  \
            {tbl_cols["schools"]["name"]}=\'{xstr(record_data["name"])}\', \
            {tbl_cols["schools"]["sym"]}={prepare_number(record_data["sym"])}, \
            {tbl_cols["schools"]["level"]}=\'{xstr(record_data["level"])}\', \
            {tbl_cols["schools"]["sector"]}=\'{xstr(record_data["sector"])}\', \
            {tbl_cols["schools"]["schoolType"]}=\'{xstr(record_data["schoolType"])}\', \
            {tbl_cols["schools"]["city"]}=\'{xstr(record_data["city"])}\', \
            {tbl_cols["schools"]["representative"]}=\'{xstr(record_data["representative"])}\', \
            {tbl_cols["schools"]["status"]}=\'{xstr(record_data["status"])}\', \
            {tbl_cols["schools"]["schoolDate"]}={prepare_ISO8601_date(record_data["schoolDate"])} \
        WHERE {tbl_cols["schools"]["id"]}={school_id};')
    cursor.commit()

@access_lock
def delete_school(schoolId):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {tbl_names["schools"]} \
        WHERE {tbl_cols["schools"]["id"]}={schoolId};')
    cursor.commit()

@access_lock
def add_school(schoolName, sym, level, sector, schoolType, city, representative, status):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO {tbl_names["schools"]} ({tbl_cols["schools"]["name"]}, {tbl_cols["schools"]["sym"]}, {tbl_cols["schools"]["level"]}, \
        {tbl_cols["schools"]["sector"]}, {tbl_cols["schools"]["schoolType"]}, {tbl_cols["schools"]["city"]}, \
        {tbl_cols["schools"]["representative"]}, {tbl_cols["schools"]["status"]}) ' +
        f'VALUES (\'{xstr(schoolName)}\', {prepare_number(sym)}, \'{xstr(level)}\', \'{xstr(sector)}\', \'{xstr(schoolType)}\', \'{xstr(city)}\', \'{xstr(representative)}\', \'{xstr(status)}\');')
    cursor.commit()
    cursor.execute(f'SELECT @@IDENTITY FROM {tbl_names["schools"]};')
    # Returning the id of the new school
    return cursor.fetchone()[0]

@access_lock
def update_contact(contact_id, record_data):
    record_data = {key: value if value else '' for key, value in record_data.items()}
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["contacts"]} \
        SET {tbl_cols["contacts"]["schoolId"]}={record_data["schoolId"]}, \
            {tbl_cols["contacts"]["schoolName"]}=\'{xstr(record_data["schoolName"])}\', \
            {tbl_cols["contacts"]["firstName"]}=\'{xstr(record_data["firstName"])}\', \
            {tbl_cols["contacts"]["lastName"]}=\'{xstr(record_data["lastName"])}\', \
            {tbl_cols["contacts"]["role"]}=\'{xstr(record_data["role"])}\', \
            {tbl_cols["contacts"]["phone"]}=\'{xstr(record_data["phone"])}\', \
            {tbl_cols["contacts"]["status"]}=\'{xstr(record_data["status"])}\' \
        WHERE {tbl_cols["contacts"]["id"]}={contact_id};')
    cursor.commit()

@access_lock
def add_contact(schoolId, schoolName, firstName, lastName, role, phone, status, googleContactsResourceName):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO {tbl_names["contacts"]} ({tbl_cols["contacts"]["firstName"]}, {tbl_cols["contacts"]["lastName"]}, \
        {tbl_cols["contacts"]["schoolId"]}, {tbl_cols["contacts"]["schoolName"]}, {tbl_cols["contacts"]["role"]}, \
        {tbl_cols["contacts"]["phone"]}, {tbl_cols["contacts"]["status"]}, {tbl_cols["contacts"]["googleContactsResourceName"]}) ' +
        f'VALUES (\'{xstr(firstName)}\', \'{xstr(lastName)}\', {schoolId}, \'{xstr(schoolName)}\', \'{xstr(role)}\', \'{xstr(phone)}\', \'{xstr(status)}\', \'{xstr(googleContactsResourceName)}\');')
    cursor.commit()
    cursor.execute(f'SELECT @@IDENTITY FROM {tbl_names["contacts"]};')
    # Returning the id of the new conatct
    return cursor.fetchone()[0]

@access_lock
def delete_contact(contactId):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {tbl_names["contacts"]} \
        WHERE {tbl_cols["contacts"]["id"]}={contactId};')
    cursor.commit()

# Add and update an invitation
@access_lock
def add_invitation(issueDate, issuer, planName, payed, checkDate, sym):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO {tbl_names["invitations"]} ({tbl_cols["invitations"]["issueDate"]}, {tbl_cols["invitations"]["issuer"]}, {tbl_cols["invitations"]["planName"]}, \
        {tbl_cols["invitations"]["payed"]}, {tbl_cols["invitations"]["checkDate"]}, {tbl_cols["invitations"]["sym"]}) ' +
        f'VALUES ({prepare_ISO8601_date(issueDate)}, \'{xstr(issuer)}\', \'{xstr(planName)}\', \'{xstr(payed)}\', {prepare_ISO8601_date(checkDate)}, {sym});')
    cursor.commit()
    cursor.execute(f'SELECT @@IDENTITY FROM {tbl_names["invitations"]};')
    # Returning the id of the new invitation
    return cursor.fetchone()[0]

@access_lock
def update_invitation(id, record_data):
    record_data = {key: value if value else '' for key, value in record_data.items()}
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["invitations"]} \
        SET \
            {tbl_cols["invitations"]["sym"]}={record_data["sym"]}, \
            {tbl_cols["invitations"]["schoolName"]}=\'{xstr(record_data["schoolName"])}\', \
            {tbl_cols["invitations"]["city"]}=\'{xstr(record_data["city"])}\', \
            {tbl_cols["invitations"]["planName"]}=\'{xstr(record_data["planName"])}\', \
            {tbl_cols["invitations"]["issueDate"]}={prepare_ISO8601_date(record_data["issueDate"])}, \
            {tbl_cols["invitations"]["issuer"]}=\'{xstr(record_data["issuer"])}\', \
            {tbl_cols["invitations"]["checkDate"]}={prepare_ISO8601_date(record_data["checkDate"])}, \
            {tbl_cols["invitations"]["payed"]}=\'{xstr(record_data["payed"])}\' \
        WHERE {tbl_cols["invitations"]["id"]}={id};')
    cursor.commit()

@access_lock
def delete_invitation(invitationId):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {tbl_names["invitations"]} \
        WHERE {tbl_cols["invitations"]["id"]}={invitationId};')
    cursor.commit()

# Add and update a payment
@access_lock
def add_payment(issuer, schoolName, plan, payed, sym):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO {tbl_names["payments"]} ({tbl_cols["payments"]["issuer"]}, {tbl_cols["payments"]["schoolName"]}, \
        {tbl_cols["payments"]["plan"]}, {tbl_cols["payments"]["payed"]}, {tbl_cols["payments"]["sym"]}) ' +
        f'VALUES (\'{xstr(issuer)}\', \'{xstr(schoolName)}\', \'{xstr(plan)}\', {payed}, {sym});')
    cursor.commit()
    cursor.execute(f'SELECT @@IDENTITY FROM {tbl_names["payments"]};')
    # Returning the id of the new payment
    return cursor.fetchone()[0]

# Update payments data
@access_lock
def update_payment(id, record_data):
    record_data = {key: value if value else '' for key, value in record_data.items()}
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["payments"]} \
        SET  \
            {tbl_cols["payments"]["issuer"]}=\'{xstr(record_data["issuer"])}\', \
            {tbl_cols["payments"]["schoolName"]}=\'{xstr(record_data["schoolName"])}\', \
            {tbl_cols["payments"]["city"]}=\'{xstr(record_data["city"])}\', \
            {tbl_cols["payments"]["plan"]}=\'{xstr(record_data["plan"])}\', \
            {tbl_cols["payments"]["payed"]}={record_data["payed"]}, \
            {tbl_cols["payments"]["sym"]}=\'{xstr(record_data["sym"])}\' \
        WHERE {tbl_cols["payments"]["id"]}={id};')
    cursor.commit()

# Delete a payment
@access_lock
def delete_payment(paymentId):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {tbl_names["payments"]} \
        WHERE {tbl_cols["payments"]["id"]}={paymentId};')
    cursor.commit()

# Update plans data
@access_lock
def add_plan(year, proposal, status, invitation, level, sym, schoolId, institution, contact, date, district, city, plan, days, day, weeks, grade,
             lessonsPerDay, lessons, pricePerHour, overall, details):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO {tbl_names["plans"]} ({tbl_cols["plans"]["year"]}, {tbl_cols["plans"]["proposal"]}, {tbl_cols["plans"]["status"]}, \
        {tbl_cols["plans"]["invitation"]}, {tbl_cols["plans"]["level"]}, {tbl_cols["plans"]["sym"]}, \
        {tbl_cols["plans"]["schoolId"]}, \
        {tbl_cols["plans"]["institution"]}, {tbl_cols["plans"]["contact"]}, {tbl_cols["plans"]["date"]}, \
        {tbl_cols["plans"]["district"]}, {tbl_cols["plans"]["city"]}, {tbl_cols["plans"]["plan"]}, {tbl_cols["plans"]["days"]}, \
        {tbl_cols["plans"]["day"]}, {tbl_cols["plans"]["weeks"]}, {tbl_cols["plans"]["grade"]}, \
        {tbl_cols["plans"]["lessonsPerDay"]}, {tbl_cols["plans"]["lessons"]}, {tbl_cols["plans"]["pricePerHour"]}, \
        {tbl_cols["plans"]["overall"]}, {tbl_cols["plans"]["details"]}) ' +
        f'VALUES (\'{xstr(xstr(year))}\', \'{xstr(xstr(proposal))}\', \'{xstr(xstr(status))}\', \'{xstr(xstr(invitation))}\', \'{xstr(xstr(level))}\', {sym}, {schoolId}, \'{xstr(xstr(institution))}\', \
            \'{xstr(xstr(contact))}\', {prepare_ISO8601_date(date)}, \'{xstr(xstr(district))}\', \'{xstr(xstr(city))}\', \'{xstr(xstr(plan))}\', \'{xstr(xstr(days))}\', \'{xstr(xstr(day))}\', {weeks}, \
            \'{xstr(xstr(grade))}\',  {lessonsPerDay}, {lessons}, {pricePerHour}, {overall}, \'{xstr(xstr(details))}\');')
    cursor.commit()
    cursor.execute(f'SELECT @@IDENTITY FROM {tbl_names["plans"]};')
    return cursor.fetchone()[0]

@access_lock
def update_plan(id, record_data):
    record_data = {key: value if value else '' for key, value in record_data.items()}
    cursor = conn.cursor()
    cursor.execute(f'UPDATE {tbl_names["plans"]} \
        SET  \
            {tbl_cols["plans"]["year"]}=\'{xstr(record_data["year"])}\', \
            {tbl_cols["plans"]["proposal"]}=\'{xstr(record_data["proposal"])}\', \
            {tbl_cols["plans"]["status"]}=\'{xstr(record_data["status"])}\', \
            {tbl_cols["plans"]["invitation"]}=\'{xstr(record_data["invitation"])}\', \
            {tbl_cols["plans"]["level"]}=\'{xstr(record_data["level"])}\', \
            {tbl_cols["plans"]["sym"]}={prepare_number(record_data["sym"])}, \
            {tbl_cols["plans"]["schoolId"]}={prepare_number(record_data["schoolId"])}, \
            {tbl_cols["plans"]["institution"]}=\'{xstr(record_data["institution"])}\', \
            {tbl_cols["plans"]["contact"]}=\'{xstr(record_data["contact"])}\', \
            {tbl_cols["plans"]["date"]}={prepare_ISO8601_date(record_data["date"])}, \
            {tbl_cols["plans"]["district"]}=\'{xstr(record_data["district"])}\', \
            {tbl_cols["plans"]["city"]}=\'{xstr(record_data["city"])}\', \
            {tbl_cols["plans"]["plan"]}=\'{xstr(record_data["plan"])}\', \
            {tbl_cols["plans"]["days"]}=\'{xstr(record_data["days"])}\', \
            {tbl_cols["plans"]["day"]}=\'{xstr(record_data["day"])}\', \
            {tbl_cols["plans"]["weeks"]}={prepare_number(record_data["weeks"])}, \
            {tbl_cols["plans"]["grade"]}=\'{xstr(record_data["grade"])}\', \
            {tbl_cols["plans"]["lessonsPerDay"]}={prepare_number(record_data["lessonsPerDay"])}, \
            {tbl_cols["plans"]["lessons"]}={prepare_number(record_data["lessons"])}, \
            {tbl_cols["plans"]["pricePerHour"]}={prepare_number(record_data["pricePerHour"])}, \
            {tbl_cols["plans"]["overall"]}={prepare_number(record_data["overall"])}, \
            {tbl_cols["plans"]["details"]}=\'{xstr(record_data["details"])}\', \
            {tbl_cols["plans"]["msg"]}=\'{xstr(record_data["msg"])}\' \
        WHERE {tbl_cols["plans"]["id"]}={id};')
    cursor.commit()

@access_lock
def delete_plan(planId):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {tbl_names["plans"]} \
        WHERE {tbl_cols["plans"]["id"]}={planId};')
    cursor.commit()

def update_settings(settings):
    with open('mainapp/data/general_settings.json', 'w', encoding='utf-8') as general_settings_file:
        json.dump(settings, general_settings_file)