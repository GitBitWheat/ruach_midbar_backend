from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, InvalidArgumentException

from waiting import wait, TimeoutExpired

from io import BytesIO
import win32clipboard

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



class MessageTypes(IntEnum):
    TEXT = 1
    DOCUMENT = 2
    IMAGE = 3
    COPY_IMAGE = 4

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
        self.messages = [WhatsappSender.__msg_type_to_class(msg_type)(driver, content) for content, msg_type in messages]
    
    @staticmethod
    def __msg_type_to_class(msg_type):
        if msg_type == MessageTypes.TEXT:
            return WhatsappSender._TextMessage
        elif msg_type == MessageTypes.DOCUMENT:
            return WhatsappSender._DocumentMessage
        elif msg_type == MessageTypes.IMAGE:
            return WhatsappSender._ImageMessage
        elif msg_type == MessageTypes.COPY_IMAGE:
            return WhatsappSender._CopyImageMessage
        else:
            return None


    def send(self, phone, name):
        self.driver.get(f'https://web.whatsapp.com/send?phone={phone}')

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

            if message.validate_send():
                msg_statuses.append(MessageStatuses.SUCCESSFUL)
            else:
                msg_statuses.append(MessageStatuses.FAILED_SENDING_VALIDATION)
        
        return msg_statuses


    class _Message(metaclass=ABCMeta):
        MESSAGE_INPUT_XPATH = xpaths['message-input']
        SEND_BUTTON_XPATH = xpaths['send-button']
        ATTACH_BUTTON_XPATH = xpaths['attach-button']
        DOCUMENT_INPUT_XPATH = xpaths['document-input']
        IMAGE_INPUT_XPATH = xpaths['image-input']
        SEND_FILE_BUTTON_XPATH = xpaths['send-file-button']
        LAST_MSG_META_XPATH = xpaths['last-msg-meta']

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
                input_element().send_keys(input_content)

        def validate_send(self):
            last_msg_status = lambda: WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, self.LAST_MSG_META_XPATH)))
            try:
                wait(lambda: last_msg_status().get_attribute('data-icon') != 'msg-time', timeout_seconds=40, expected_exceptions=Exception)
            except TimeoutExpired:
                return False
            else:
                return True

        @abstractclassmethod
        def send(self, _):
            pass


    class _TextMessage(_Message):
        def __init__(self, driver, text):
            super().__init__(driver)
            self.text = text
        
        def send(self, name):
            self.send_to_input(self.MESSAGE_INPUT_XPATH, self.text.format(name=name), isText=True)
            self.click_button(self.SEND_BUTTON_XPATH)


    class _DocumentMessage(_Message):
        def __init__(self, driver, filepath):
            super().__init__(driver)
            self.filepath = filepath

        def send(self, _):
            self.click_button(self.ATTACH_BUTTON_XPATH)
            time.sleep(1.5)
            self.send_to_input(self.DOCUMENT_INPUT_XPATH, self.filepath)
            time.sleep(1.5)
            self.click_button(self.SEND_FILE_BUTTON_XPATH)


    class _ImageMessage(_Message):
        def __init__(self, driver, filepath):
            super().__init__(driver)
            self.filepath = filepath

        def send(self, _):
            self.click_button(self.ATTACH_BUTTON_XPATH)
            time.sleep(1.5)
            self.send_to_input(self.IMAGE_INPUT_XPATH, self.filepath)
            time.sleep(1.5)
            self.click_button(self.SEND_FILE_BUTTON_XPATH)

    
    class _CopyImageMessage(_Message):
        def __init__(self, driver, filepath):
            super().__init__(driver)
            self.filepath = filepath

        def copy_image_to_clipboard(self, filepath):
            image = None #Image.open(filepath)
            output = BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()

        def send(self, _):
            time.sleep(1.5)
            self.copy_image_to_clipboard(self.filepath)
            self.send_to_input(self.MESSAGE_INPUT_XPATH, Keys.CONTROL + 'v')
            time.sleep(1.5)
            self.click_button(self.SEND_FILE_BUTTON_XPATH)



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



if __name__ == "__main__":
    #send_messages([
    #    (r'C:\Users\Owner\Pictures\Screenshots\Screenshot (1).png', MessageTypes.COPY_IMAGE)
    #],
    #['fr23', '971.543547270'],
    #['1']*2,
    #[None]*2, lambda: 0, None, None)
    print(xpaths['chatlist-header'])