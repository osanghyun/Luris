import re
import sys
import time
import json
import pymysql
import requests
from selenium import webdriver
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class GOSI:
    def __init__(self):
        self.download_location = "/Users/osanghyun/PycharmProjects/DBProject2/Luris/GOSI_file"
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {
            "download.default_directory": self.download_location,
            "safebrowsing.enabled": True
        })
        self.chrome_driver_path = './chromedriver'
        self.driver = webdriver.Chrome(self.chrome_driver_path, options=options)
        self.web_page = "http://luris.molit.go.kr/web/actreg/mapboard/ArMapBoardList.jsp"

        self. dict_gosi: dict = {
            'info': {},
            'detail': {}
        }
        self.dict_info: dict = {
            'day': "",  # 고시일
            'number': "",  # 고시번호
            'divide': "",  # 구분
            'title': "",  # 고시제목
            'gigwan': "",  # 담당기관
            'look': ""  # 조회수
        }
        self.dict_region: dict = {
            'full': "",  # 지역 풀네임
            'level1': "",
            'level2': "",
            'level3': "",
            'level4': "",
            'level5': ""
        }
        self.dict_chumbu: dict = {
            'title': "",  # 제목
            'href': ""  # 링크
        }
        self.dict_detail: dict = {
            'title': "",  # 고시제목
            'gigwan': "",  # 담당기관
            'phone': "",  # 문의처
            'divide': "",  # 구분
            'day': "",  # 고시일
            'region': [],  # 지역
            'yulram': "",  # 열람장소
            'chumbu': [],  # 첨부파일
            'main_text': ""  # 본문
        }
        self.con = pymysql.connect(
            host='',  # host 입력 필요.
            user='',  # user 입력 필요.
            password='',  # pw 입력 필요.
            charset='utf8',
            db='',  # db 입력 필요.
            cursorclass=pymysql.cursors.DictCursor)
        self.cur = self.con.cursor()

    def element_click_wait(self, by_type, locator: str) -> None:
        """
        클릭하고 싶은 element에 대한 예외처리.
        :param by_type:
        :param locator:
        :return:
        """
        print(f"element_click_wait 함수 호출 ({by_type}, {locator})")
        try:
            WebDriverWait(self.driver, 10, poll_frequency=0.01).until(EC.element_to_be_clickable((by_type, locator)))
            return
        except selenium.common.exceptions.TimeoutException:
            print(str(by_type) + str(locator) + " Timeout Error")
            self.driver.close()
            sys.exit()

    def element_locate_wait(self, by_type, locator: str) -> None:
        """
        가져오고 싶은 element에 대한 예외처리.
        :param by_type:
        :param locator:
        :return:
        """
        print(f"element_locate_wait 함수 호출 ({by_type}, {locator})")
        try:
            WebDriverWait(self.driver, 10, poll_frequency=0.01).until(EC.presence_of_element_located((by_type, locator)))
            return
        except selenium.common.exceptions.TimeoutException:
            print(str(by_type) + str(locator) + " Timeout Error")
            self.driver.close()
            sys.exit()

    def insert_into_db(self, dict_gosi: dict):
        sql = "INSERT INTO GOSI (gosi_number, day, gubun, title, gigwan, look, detail) VALUES (%s, %s, %s, %s, %s, %s, %s)"

        var = (dict_gosi['info']['number'], dict_gosi['info']['day'], dict_gosi['info']['divide'],
               dict_gosi['info']['title'], dict_gosi['info']['gigwan'], dict_gosi['info']['look'],
               json.dumps(dict_gosi['detail'], indent=2))

        try:
            self.cur.execute(sql, var)
            self.con.commit()

        except Exception as e:
            print(str(e))

    @staticmethod
    def download(file_name: str, url: str, gosi_number: str):
        """
        첨부파일 다운로드.
        :param file_name:
        :param url:
        :param gosi_number:
        :return:
        """
        index = file_name.rfind('.')
        file_title: str = file_name[:index]
        file_type: str = file_name[index+1:]
        try:
            response = requests.get(url=url, stream=True)
        except requests.exceptions.SSLError:
            response = requests.get(url=url, stream=True)
        except requests.exceptions.ConnectionError:
            response = requests.get(url=url, stream=True)

        if response.status_code == 200:
            with open(f"./GOSI_file/{gosi_number}-{file_title}.{file_type}", 'wb') as f:
                f.write(response.content)
        else:
            try:
                response = requests.get(url=url, stream=True)
            except requests.exceptions.SSLError:
                response = requests.get(url=url, stream=True)
            except requests.exceptions.ConnectionError:
                response = requests.get(url=url, stream=True)

            if response.status_code == 200:
                with open(f"./GOSI_file/{gosi_number}-{file_title}.{file_type}", 'wb') as f:
                    f.write(response.content)
            else:
                print("IMAGE DOWNLOAD ERROR")
                sys.exit()

    def main_page(self):
        """
        메인페이지 접속.
        :return:
        """
        self.driver.get(self.web_page)
        assert "LURIS 토지이용규제정보서비스" in self.driver.title

    def next_page(self):
        """
        다음 페이지로 이동.
        :return:
        """
        self.element_locate_wait(By.ID, "navigationArea")

        navigationArea = self.driver.find_element(by=By.ID, value="navigationArea")

        buttons = navigationArea.find_elements(by=By.TAG_NAME, value="a")
        button_count = len(buttons)

        for i in range(button_count):
            if "#" in buttons[i].get_attribute("href"):
                print("NEXT PAGE")
                buttons[i+1].click()
                break

    def scan_gosi_detail(self, detail_button, gosi_number: str) -> dict:
        """
        고시 상세 정보
        :param detail_button:
        :param gosi_number:
        :return:
        """
        detail_button.click()
        time.sleep(0.5)
        dict_detail: dict = self.dict_detail.copy()
        self.element_locate_wait(By.CLASS_NAME, "gosi_view")
        gosi_view = self.driver.find_element(by=By.CLASS_NAME, value="gosi_view")

        # 고시 제목
        title: str = gosi_view.find_element(by=By.CSS_SELECTOR, value="thead > tr > th").text
        dict_detail['title'] = title

        body = gosi_view.find_element(by=By.TAG_NAME, value="tbody")
        items = body.find_elements(by=By.TAG_NAME, value="tr")

        for item in items:
            heads = item.find_elements(by=By.TAG_NAME, value="th")
            contents = item.find_elements(by=By.TAG_NAME, value="td")

            for i in range(len(contents)):
                head = heads[i]
                content = contents[i]

                if "담당기관" in head.text:
                    dict_detail['gigwan'] = content.text

                if "문의처" in head.text:
                    dict_detail['phone'] = content.text

                if "고시구분" in head.text:
                    dict_detail['divide'] = content.text

                if "고시일" in head.text:
                    dict_detail['day'] = content.text

                if "지역" in head.text:
                    region_list: list = []
                    regions = content.find_elements(by=By.TAG_NAME, value="li")

                    for region in regions:
                        dict_region = self.dict_region.copy()
                        region_text: str = region.text
                        dividing_text: list = region_text.split(' ')

                        for j in range(len(dividing_text)):
                            if j >= 5:
                                dict_region['level5'] = dict_region['level5'] + ' ' + dividing_text[j]
                                continue

                            dict_region[f'level{j+1}'] = dividing_text[j]

                        dict_region['full'] = region_text
                        region_list.append(dict_region)

                    dict_detail['region'] = region_list

                if "열람장소" in head.text:
                    dict_detail['yulram'] = content.text

                if "첨부파일" in head.text:
                    chumbu_list: list = []
                    chumbu = content.find_elements(by=By.TAG_NAME, value="a")
                    for elem in chumbu:
                        dict_chumbu: dict = self.dict_chumbu.copy()
                        file_name: str = elem.text
                        href: str = elem.get_attribute("href")
                        dict_chumbu['title'] = file_name
                        dict_chumbu['href'] = href
                        # self.download(file_name, href, gosi_number)  다운로드
                        chumbu_list.append(dict_chumbu)
                    dict_detail['chumbu'] = chumbu_list

        # 본문
        self.element_click_wait(By.CLASS_NAME, "board_contents")
        main_text: str = self.driver.find_element(by=By.CLASS_NAME, value="board_contents").text
        dict_detail['main_text'] = main_text

        self.driver.back()
        return dict_detail

    def scan_gosi_list(self):
        """
        info 테이블 데이터 스캔.
        :return:
        """

        record_index: int = 0

        while True:
            self.element_locate_wait(By.CLASS_NAME, "gosi_list")
            gosi_list = self.driver.find_element(by=By.CLASS_NAME, value="gosi_list")
            gosi_body = gosi_list.find_element(by=By.TAG_NAME, value="tbody")

            records = gosi_body.find_elements(by=By.TAG_NAME, value="tr")
            record_number = len(records)
            while True:
                self.element_locate_wait(By.CLASS_NAME, "gosi_list")
                gosi_list = self.driver.find_element(by=By.CLASS_NAME, value="gosi_list")
                gosi_body = gosi_list.find_element(by=By.TAG_NAME, value="tbody")

                records = gosi_body.find_elements(by=By.TAG_NAME, value="tr")

                if record_index >= record_number-1:
                    break
                record_index = record_index + 1
                dict_info: dict = self.dict_info.copy()
                attributes = records[record_index].find_elements(by=By.TAG_NAME, value="td")

                day: str = attributes[0].text  # 고시일
                dict_info['day'] = day

                if day < "2018-01-01":
                    return

                number: str = attributes[1].text  # 고시번호
                p = re.compile(r'[\d]+-[\d]+호')
                m: list = p.findall(number)
                list_data: list = number.split(' ')
                gosi_number: str = list_data[0] + ' ' + list_data[1] + ' ' + m[0]
                dict_info['number'] = gosi_number

                title: str = attributes[2].text  # 고시제목
                index: int = title.find(' ')
                dict_info['divide'] = title[1:index-1]
                dict_info['title'] = attributes[2].find_element(by=By.TAG_NAME, value="a").get_attribute("title")

                gigwan: str = attributes[3].text  # 담당기관
                dict_info['gigwan'] = gigwan

                look: str = attributes[4].text  # 조회수
                p = re.compile(r'[\d]')
                m: list = p.findall(look)
                look = ""
                for word in m:
                    look = look + word
                dict_info['look'] = look

                detail_button = attributes[2].find_element(by=By.TAG_NAME, value="a")
                dict_detail = self.scan_gosi_detail(detail_button=detail_button, gosi_number=gosi_number)

                dict_gosi = self.dict_gosi.copy()
                dict_gosi['info'] = dict_info
                dict_gosi['detail'] = dict_detail
                self.insert_into_db(dict_gosi)

                time.sleep(0.5)

            self.next_page()
            record_index = 0

    def start(self):
        self.main_page()

        self.scan_gosi_list()

        self.driver.close()


func = GOSI()
func.start()