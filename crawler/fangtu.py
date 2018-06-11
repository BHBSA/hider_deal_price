from deal_price_info import Comm
import requests
import re
from lxml import etree
import random
import json
import time
import datetime
from lib.log import LogHandler

source = '房途网'
log = LogHandler('fangtu')

class Fangtu:
    def __init__(self):

        self.headers = {'User-Agent':
                            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
                        }
        self.start_url = 'http://hangzhou.fangtoo.com/building/'
        self.proxies = [{"http": "http://192.168.0.96:3234"},
                        {"http": "http://192.168.0.93:3234"},
                        {"http": "http://192.168.0.90:3234"},
                        {"http": "http://192.168.0.94:3234"},
                        {"http": "http://192.168.0.98:3234"},
                        {"http": "http://192.168.0.99:3234"},
                        {"http": "http://192.168.0.100:3234"},
                        {"http": "http://192.168.0.101:3234"},
                        {"http": "http://192.168.0.102:3234"},
                        {"http": "http://192.168.0.103:3234"},]

    def start_crawler(self):
        for i in range(1,346):
            url = self.start_url + "cp" + str(i)
            res =requests.get(url,headers=self.headers)
            html = etree.HTML(res.text)
            comm_info_list = html.xpath("//li//div[@class='fang-info ml20 z']")
            for comm_info in comm_info_list:
                comm_url = comm_info.xpath("./div[@class='title']/a/@href")[0]
                region = comm_info.xpath(".//a[@class='ml20']/text()")[0]
                addr  = comm_info.xpath(".//a[@class='ml10 C000']/text()")[0]

                bu_id = re.search('\d+',comm_url).group(0)
                data = {
                    "buildingId":bu_id,
                    'pageIndex':1,
                    'pageSize':500,
                }
                while True:
                    try:
                        proxy = self.proxies[random.randint(0, 9)]
                        deal_res = requests.post('http://hangzhou.fangtoo.com/Building/GetTradeExchange/',data=data,headers=self.headers,proxies=proxy)
                        deal_dict = json.loads(deal_res.text)
                        break
                    except:
                        continue

                for n in deal_dict['data']:
                    try:
                        co = Comm(source)
                        co.city = '杭州'
                        # co.room_num = n['Addr']
                        size = n['Area']
                        area = size.replace('㎡', '')
                        if area:
                            area = float(area)
                            co.area = round(area, 2)
                        co.district_name = n['ExName']
                        co.total_price = int(re.search('(\d+)', n['Price'], re.S | re.M).group(1))
                        trade_date = n['ExDate']
                        if trade_date:
                            t = time.strptime(trade_date, "%Y/%m/%d %H:%M:%S")
                            y = t.tm_year
                            m = t.tm_mon
                            d = t.tm_mday
                            co.trade_date = datetime.datetime(y, m, d)
                        co.region = region
                        co.insert_db()
                    except Exception as e:
                        log.error("解析错误{}".format(e))
