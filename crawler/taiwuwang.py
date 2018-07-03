import requests
import re
from deal_price_info import Comm
import random
import time, datetime


class Taiwuwang:
    def __init__(self):
        self.url = 'http://www.taiwu.com/building/'

    def start_crawler(self):
        page = self.get_all_page()
        for i in range(1, page):
            url = 'http://www.taiwu.com/building/cp' + str(i) + '/'

            while True:
                try:
                    res = requests.get(url)
                    if res.status_code == 200:
                        break
                except Exception as e:
                    print('请求出错', e)

            # print(res.content.decode())
            all_info = re.search('<ul class="fang-list">.*?</ul>', res.content.decode(), re.S | re.M).group(0)
            for k in re.findall('<li>.*?</li>', all_info, re.S | re.M):
                source = '太屋网'
                city = '上海'
                area = re.search('<div class="adds">.*?<a href="/building/.*?/">(.*?)</a>', k, re.S | re.M).group(
                    1)  # 区域
                building_id = re.search('<a href="/building/(.*?)/', k, re.S | re.M).group(1)
                detail_url = "http://www.taiwu.com/Building/GetHouseExchange/"
                payload = "------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"buildingId\"\r\n\r\n" + building_id + "\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"pageIndex\"\r\n\r\n1\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"pageSize\"\r\n\r\n5000\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--"
                headers = {
                    'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
                    'Cache-Control': "no-cache",
                }
                while True:
                    try:
                        response = requests.request("POST", detail_url, data=payload, headers=headers)
                        if res.status_code == 200:
                            break
                    except Exception as e:
                        print('请求出错', e)

                try:
                    result_json = response.json()
                    data_list = result_json['data']
                except Exception as e:
                    print(e)
                    continue
                for j in data_list:
                    c = Comm(source)
                    c.city = city
                    c.region = area
                    c.room = j['RoomCount']
                    c.hall = j['HollCount']
                    c.district_name = j['BuildingName']
                    c.area = j['BldArea']
                    trade_date = j['ExDate']
                    trade_date_ = int(re.search('(\d+)', trade_date).group(1))
                    if trade_date_:
                        t = time.localtime(int(trade_date_ / 1000))
                        y = t.tm_year
                        m = t.tm_mon
                        d = t.tm_mday
                        c.trade_date = datetime.datetime(y, m, d)
                    c.total_price = j['ExPrice']
                    c.insert_db()

    @staticmethod
    def get_all_page():
        # todo  嗯 你们记得获取所有页面
        return 1069


if __name__ == '__main__':
    t = Taiwuwang()
    t.start_crawler()
