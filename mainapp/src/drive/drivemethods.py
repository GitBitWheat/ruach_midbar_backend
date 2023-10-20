from mainapp.src.drive.drivewrapper import DriveWrapper
from mainapp.src.drive.proposalservice import build_proposal_drive_service

INST_BASE_DIR_NAME = 'מסמכי מדריכים'

inst_base_dir_id = None

def _get_instructor_subdirs(area, city, name, dir_names):
    drive_wrapper = DriveWrapper()
    global inst_base_dir_id
    if inst_base_dir_id == None:
        inst_base_dir_id = drive_wrapper.get_subdirectory(INST_BASE_DIR_NAME, 'root')

    area_dir_id = drive_wrapper.get_subdirectory(area, inst_base_dir_id)
    city_dir_id = drive_wrapper.get_subdirectory(city, area_dir_id)
    instructor_dir_id = drive_wrapper.get_subdirectory(name, city_dir_id)
    return [
        drive_wrapper.get_subdirectory(dir_name, instructor_dir_id)
        for dir_name in dir_names
    ]

def upload_instructor_file(area, city, name, dir_name, file):
    drive_wrapper = DriveWrapper()
    global inst_base_dir_id
    if inst_base_dir_id == None:
        inst_base_dir_id = drive_wrapper.get_subdirectory(INST_BASE_DIR_NAME, 'root')

    dir_id = (_get_instructor_subdirs(area, city, name, [dir_name]))[0]

    files_list = drive_wrapper.list_files(dir_id)
    for drive_file in files_list:
        drive_wrapper.delete_file(drive_file['id'])

    return drive_wrapper.upload_file(file, dir_id)

def upload_instructor_file_multiple(area, city, name, dir_name, file):
    drive_wrapper = DriveWrapper()
    global inst_base_dir_id
    if inst_base_dir_id == None:
        inst_base_dir_id = drive_wrapper.get_subdirectory(INST_BASE_DIR_NAME, 'root')

    dir_id = (_get_instructor_subdirs(area, city, name, [dir_name]))[0]
    return drive_wrapper.upload_file(file, dir_id)

def list_instructor_files(area, city, name, dir_names):
    drive_wrapper = DriveWrapper()
    global inst_base_dir_id
    if inst_base_dir_id == None:
        inst_base_dir_id = drive_wrapper.get_subdirectory(INST_BASE_DIR_NAME, 'root')

    return [
        drive_wrapper.list_files(dir_id)
        for dir_id
        in _get_instructor_subdirs(area, city, name, dir_names)
    ]

def delete_file(file_id):
    drive_wrapper = DriveWrapper()
    global inst_base_dir_id
    if inst_base_dir_id == None:
        inst_base_dir_id = drive_wrapper.get_subdirectory(INST_BASE_DIR_NAME, 'root')

    drive_wrapper.delete_file(file_id)



def upload_proposal_file(file, year, district, city, school):
    drive_wrapper = DriveWrapper(service=build_proposal_drive_service())
    dir1_name = 'מחלקת שיווק ומכירות'

    dir1_id = drive_wrapper.get_subdirectory(dir1_name, 'root')
    year_dir_id = drive_wrapper.get_subdirectory(year, dir1_id)
    district_dir_id = drive_wrapper.get_subdirectory(district, year_dir_id)
    city_dir_id = drive_wrapper.get_subdirectory(city, district_dir_id)
    school_dir_id = drive_wrapper.get_subdirectory(school, city_dir_id)

    files_list = drive_wrapper.list_files(school_dir_id)
    for drive_file in files_list:
        drive_wrapper.delete_file(drive_file['id'])

    return drive_wrapper.upload_file(file, school_dir_id)