from deal_price_info import Comm
import requests
import re
from lxml import etree
import random
import json
import time
import datetime
from lib.log import LogHandler

source = '新浪乐居'
log = LogHandler('leju')


class Leju:
    def __init__(self):
        self.start_url = 'https://esf.leju.com/city/'
        self.headers = {'User-Agent':
                            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
                        }
        self.proxies = [
            {"http": "http://192.168.0.96:3234"},
            {"http": "http://192.168.0.93:3234"},
            {"http": "http://192.168.0.90:3234"},
            {"http": "http://192.168.0.94:3234"},
            {"http": "http://192.168.0.98:3234"},
            {"http": "http://192.168.0.99:3234"},
            {"http": "http://192.168.0.100:3234"},
            {"http": "http://192.168.0.101:3234"},
            {"http": "http://192.168.0.102:3234"},
            {"http": "http://192.168.0.103:3234"}, ]

    def start_crawler(self):
        res = requests.get(self.start_url, headers=self.headers)
        html = etree.HTML(res.text)
        city_list = html.xpath("//dl//dd/a")
        for i in city_list:
            city_url = i.xpath("./@href")[0]
            city_name = i.xpath("./@title")[0]
            if 'house' in city_url:
                second_comm_url = city_url.replace('house', 'community')
            else:
                second_comm_url = city_url + '/community/'
            self.community(second_comm_url, city_name)

    def community(self, second_comm_url, city_name):
        count = 1
        while True:
            page_url = second_comm_url + "n" + str(count)
            proxy = self.proxies[random.randint(0, 9)]
            try:
                res = requests.get(page_url, headers=self.headers, proxies=proxy)
                if '没有符合条件的结果' in res.text:
                    log.info('无二手小区')
                    break
                else:
                    co_html = etree.HTML(res.text)
                    co_list = co_html.xpath("//div[@class='right-information']")
                    count += 1
            except:
                continue
            self.room(co_list, city_name)

    def room(self, co_list, city_name):
        for co in co_list:
            try:
                co_name = co.xpath("./div[1]/a/text()")[0]
                co_url = "http:" + co.xpath("./div[1]/a/@href")[0]
                region = co.xpath("./div[3]/span[1]/a[1]/text()")[0]
                addr = co.xpath("./div[3]/span[3]/@title")[0]
                detail = requests.get(co_url, headers=self.headers)
                html = etree.HTML(detail.text)
                room_url = "http:" + html.xpath("//div[@class='tab-toolbar pr']//li/a/@href")[-1]
                page_index = requests.get(room_url, headers=self.headers)
            except:
                continue
            if re.search('共(\d+)页', page_index.text):
                page_num = re.search('共(\d+)页', page_index.text).group(1)
            else:
                log.info('小区无相关数据')
                continue
            for i in range(1, int(page_num) + 1):
                url = re.sub('#.*', 'n', room_url) + str(i)
                while True:
                    try:
                        proxy = self.proxies[random.randint(0, 9)]
                        res = requests.get(url, headers=self.headers, proxies=proxy)
                        break
                    except:
                        continue
                con = res.text
                room_html = etree.HTML(con)
                room_list = room_html.xpath("//div[@class='right-information']")
                for m in room_list:
                    try:
                        room = Comm(source)
                        room.district_name = co_name
                        room.city = city_name
                        room.region = region
                        room_type = m.xpath("./h3/span[2]/text()")[0]
                        try:
                            room.room = int(re.search('(\d)室', room_type, re.S | re.M).group(1))
                        except Exception as e:
                            room.room = None
                        try:
                            room.hall = int(re.search('(\d)厅', room_type, re.S | re.M).group(1))
                        except Exception as e:
                            room.hall = None

                        size = m.xpath("./h3/span[3]/text()")[0]
                        area = size.replace('平米', '')
                        if area:
                            area = float(area)
                            room.area = round(area, 2)


                        total_price = m.xpath(".//div[@class='price fs14 ']/em/text()")[0]
                        room.total_price = int(re.search('(\d+)', total_price, re.S | re.M).group(1))*10000
                        avg_price = m.xpath(".//div[@class='size  fs14']/text()")[0]
                        room.avg_price = int(re.search('(\d+)', avg_price, re.S | re.M).group(1))
                        try:
                            room.fitment = m.xpath(".//div[@class='t1 fs14']/text()[3]")[0]
                            room.direction = m.xpath(".//div[@class='t1 fs14']/text()[2]")[0]
                            # room.use = m.xpath(".//div[@class='t1 fs14']/text()[1]")[0]
                        except:
                            room.fitment = None
                            room.direction = None
                            # room.use = None
                        floor_info = m.xpath(".//div[@class='fs14']/text()[1]")[0]
                        try:
                            floor = re.search('(.*?)/', floor_info).group(1)
                            room.floor = int(re.search('\d+',floor).group(0))
                        except Exception as e:
                            room.floor = None
                        try:
                            room.height = int(re.search('.*?/(\d+)层', floor_info).group(1))
                        except:
                            room.height = None
                        trade_date = m.xpath(".//div[@class='date']/text()")[0]
                        if trade_date:
                            t = time.strptime(trade_date, "%Y-%m-%d")
                            y = t.tm_year
                            m = t.tm_mon
                            d = t.tm_mday
                            room.trade_date = datetime.datetime(y, m, d)
                        room.insert_db()
                    except Exception as e:
                        log.error('房屋信息提取失败{}'.format(e))
