from lib.mongo import Mongo
import requests
from lxml import etree
import yaml
from deal_price_info import Comm
import re
import time
import random
import datetime
from lib.standardization import standard_block
from lib.log import LogHandler

setting = yaml.load(open('./config_local.yaml'))
source = '麦田'
log = LogHandler('maitian')


class Maitian():
    def __init__(self):
        self.headers = {'User-Agent':
                            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
                        }
        self.url = 'http://bj.maitian.cn/xqall'
        self.proxies = [{"http": "http://192.168.0.96:3234"},
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
        res = requests.get(self.url, headers=self.headers)
        html = etree.HTML(res.text)
        city_list = html.xpath("//div[@class='filter_select clearfix selectBox']//li/a/@href")
        for city in city_list:
            city_url = city + "/xqall"
            self.crawler(city_url, city)

    def crawler(self, city_url, city):
        res = requests.get(city_url, headers=self.headers)
        con = etree.HTML(res.text)
        last_page = con.xpath("//a[@class='down_page']/@href")[1]
        page_num = re.search('\d+', last_page).group(0)
        for i in range(1, int(page_num) + 1):
            page_url = city_url + "/PG" + str(i)
            page_res = requests.get(page_url, headers=self.headers)
            page_con = etree.HTML(page_res.text)
            temp = page_con.xpath("//h1/a/@href")
            for temp_url in temp:
                try:
                    com = Comm(source)
                    comm_url = city + temp_url
                    while True:
                        try:
                            proxy = self.proxies[random.randint(0, 9)]
                            co_res = requests.get(comm_url, headers=self.headers, proxies=proxy, timeout=10)
                            break
                        except:
                            continue
                    time.sleep(2)
                    co_con = etree.HTML(co_res.text)
                    com.city = co_con.xpath("//div/a[@class='show']/text()")[0]
                    region = co_con.xpath("//section/p/a/text()")[-1]
                    com.region = region
                    com.district_name = co_con.xpath("//cite/span/text()")[0]
                    info = co_con.xpath("//table/tbody/tr")
                    for tag in info:
                        size = tag.xpath("./td[2]/text()")[0]
                        area = size.replace('㎡', '')
                        area = float(area)
                        com.area = round(area, 2)
                        avg_price = tag.xpath("./td[3]/text()")[0]
                        com.avg_price = int(re.search('(\d+)', avg_price, re.S | re.M).group(1))
                        total_price = tag.xpath("./td/span/text()")[0]
                        com.total_price = int(re.search('(\d+)', total_price, re.S | re.M).group(1)) * 10000
                        trade_date = tag.xpath("./td/text()")[-2]
                        if trade_date:
                            t = time.strptime(trade_date, "%Y-%m-%d")
                            y = t.tm_year
                            m = t.tm_mon
                            d = t.tm_mday
                            com.trade_date = datetime.datetime(y, m, d)

                        room_type = tag.xpath("./td//p/a/text()")[0]
                        try:
                            com.room = int(re.search('(\d)室', room_type, re.S | re.M).group(1))
                        except Exception as e:
                            com.room = None
                        try:
                            com.hall = int(re.search('(\d)厅', room_type, re.S | re.M).group(1))
                        except Exception as e:
                            com.hall = None

                        floor = tag.xpath("./td//p/span/text()")[0]
                        com.floor = int(re.search('(\d+)层', floor).group(1))
                        com.direction = re.search('层 (.*?)', floor).group(1)

                        com.insert_db()
                except Exception as e:
                    log.error("{}小区信息提取错误".format(comm_url))
