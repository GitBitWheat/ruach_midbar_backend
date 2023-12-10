from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, InvalidArgumentException

from waiting import wait, TimeoutExpired

from abc import ABCMeta, abstractclassmethod
from enum import IntEnum
import json



xpaths = dict()

try:
    with open('mainapp/src/whatsappxpaths.json', 'r', encoding='utf-8') as f:
        xpaths = json.load(f)
except FileNotFoundError:
    print('File not found.')
except PermissionError:
    print('Permission denied.')
except IOError:
    print('Error reading file.')

for name, element in xpaths.items():
    classes_xpaths_list = [
        ' and '.join([
            f"contains(concat(' ', normalize-space(@class), ' '), ' {class_name} ')"
             for class_name in class_names_list.split(' ')
        ]) for class_names_list in element['classes']
    ]
    xpaths[name] = element['base'].format(*classes_xpaths_list)



class WhatsappController:
    MESSAGE_INPUT_XPATH = xpaths['message-input']
    SEND_BUTTON_XPATH = xpaths['send-button']
    ATTACH_BUTTON_XPATH = xpaths['attach-button']
    DOCUMENT_INPUT_XPATH = xpaths['document-input']
    IMAGE_INPUT_XPATH = xpaths['image-input']
    SEND_FILE_BUTTON_XPATH = xpaths['send-file-button']
    LAST_MSG_META_XPATH = xpaths['last-msg-meta']
    CONTACT_SEARCH_INPUT_XPATH = xpaths['contact-search-input']

    def __init__(self, driver):
        self.driver = driver

    def click_button(self, xpath):
        button = lambda: WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        button().click()

    def send_to_input(self, xpath, input_content, isText=False):
        input_element = lambda: WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, xpath)))
        if isText:
            input_lines = input_content.split('\n')
            for line in input_lines:
                ie = input_element()
                for c in line:
                    ie.send_keys(c)
                ie.send_keys(Keys.SHIFT, '\n')
        else:
            input_element().send_keys(str(input_content))

    def clear_input(self, xpath):
        input_element = lambda: WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, xpath)))
        input_element().clear()

    def validate_send(self):
        last_msg_status = lambda: WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, self.LAST_MSG_META_XPATH)))
        try:
            wait(lambda: last_msg_status().get_attribute('data-icon') != 'msg-time', timeout_seconds=40, expected_exceptions=Exception)
        except TimeoutExpired:
            return False
        else:
            return True
    
    def navigate(self, phone):
        if phone[0:3] == '972':
            phone = phone[3:]
        if phone[0] == '0':
            phone = phone[1:]
        phone += '\n'
        self.send_to_input(self.CONTACT_SEARCH_INPUT_XPATH, phone)
        time.sleep(1)
        self.clear_input(self.CONTACT_SEARCH_INPUT_XPATH)
        time.sleep(0.5)



class MessageTypes(IntEnum):
    TEXT = 1
    DOCUMENT = 2
    IMAGE = 3

class MessageStatuses(IntEnum):
    SUCCESSFUL = 1
    COULD_NOT_SEND = 2
    WRONG_PHONE = 3
    FAILED_SENDING_VALIDATION = 4
    INVALID_INPUT = 5
    COULD_NOT_LOAD_PAGE = 6



class WhatsappSender:
    def __init__(self, driver, messages):
        self.driver = driver
        self.whatsapp = WhatsappController(driver)
        self.messages = [WhatsappSender.__msg_type_to_class(msg_type)(driver, content) for content, msg_type in messages]
    
    @staticmethod
    def __msg_type_to_class(msg_type):
        if msg_type == MessageTypes.TEXT:
            return WhatsappSender._TextMessage
        elif msg_type == MessageTypes.DOCUMENT:
            return WhatsappSender._DocumentMessage
        elif msg_type == MessageTypes.IMAGE:
            return WhatsappSender._ImageMessage
        else:
            return None

    def send(self, phone, name):
        self.whatsapp.navigate(phone)

        try:
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, xpaths['chatlist-header'])))
        except TimeoutException:
            return MessageStatuses.COULD_NOT_LOAD_PAGE

        try:
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, xpaths['messages-controls-footer'])))
        except TimeoutException:
            return MessageStatuses.WRONG_PHONE

        msg_statuses = []

        for message in self.messages:
            try:
                message.send(name)
            except InvalidArgumentException as err:
                msg_statuses.append(MessageStatuses.INVALID_INPUT)
                print(err)
                continue
            except Exception as err:
                msg_statuses.append(MessageStatuses.COULD_NOT_SEND)
                print(err)
                continue

            time.sleep(1.5)

            if self.whatsapp.validate_send():
                msg_statuses.append(MessageStatuses.SUCCESSFUL)
            else:
                msg_statuses.append(MessageStatuses.FAILED_SENDING_VALIDATION)
        
        return msg_statuses


    class _Message(metaclass=ABCMeta):
        def __init__(self, driver, content):
            self.whatsapp = WhatsappController(driver)
            self.content = content

        @abstractclassmethod
        def send(self, _):
            pass


    class _TextMessage(_Message):
        def send(self, name):
            self.whatsapp.send_to_input(self.whatsapp.MESSAGE_INPUT_XPATH, self.content.format(name=name), isText=True)
            time.sleep(1.5)
            self.whatsapp.click_button(self.whatsapp.SEND_BUTTON_XPATH)


    class _DocumentMessage(_Message):
        def send(self, _):
            self.whatsapp.click_button(self.whatsapp.ATTACH_BUTTON_XPATH)
            time.sleep(1.5)
            self.whatsapp.send_to_input(self.whatsapp.DOCUMENT_INPUT_XPATH, self.content)
            time.sleep(1.5)
            self.whatsapp.click_button(self.whatsapp.SEND_FILE_BUTTON_XPATH)


    class _ImageMessage(_Message):
        def send(self, _):
            self.whatsapp.click_button(self.whatsapp.ATTACH_BUTTON_XPATH)
            time.sleep(1.5)
            self.whatsapp.send_to_input(self.whatsapp.IMAGE_INPUT_XPATH, self.content)
            time.sleep(1.5)
            self.whatsapp.click_button(self.whatsapp.SEND_FILE_BUTTON_XPATH)

    

def send_messages(messages, phones, names, school_ids, contact_ids, is_rep_lst, update_school_status, update_contact_status, success_status, fail_status):
    try:
        driver = webdriver.Chrome()
    except Exception:
        driver = webdriver.Firefox()

    sender = WhatsappSender(driver, messages)

    driver.get("https://web.whatsapp.com")

    try:
        WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.XPATH, xpaths['chatlist-header'])))
    except TimeoutException:
        return [MessageStatuses.COULD_NOT_SEND] * len(phones)

    time.sleep(1.5)

    statuses_lists = []

    for phone, name, school_id, contact_id, is_rep in zip(phones, names, school_ids, contact_ids, is_rep_lst):
        status_list = sender.send(phone, name)
        statuses_lists.append(status_list)

        if school_id != None:
            if (isinstance(status_list, list) and all(status == MessageStatuses.SUCCESSFUL for status in status_list)) or status_list == MessageStatuses.SUCCESSFUL:
                if is_rep:
                    update_school_status(success_status, school_id)
                else:
                    update_contact_status(success_status, contact_id)
            else:
                if is_rep:
                    update_school_status(fail_status, school_id)
                else:
                    update_contact_status(fail_status, contact_id)
            time.sleep(1.5)
    
    driver.quit()
    return statuses_lists