from deal_price_info import Comm
import requests
import re
from lxml import etree
import random
from lib.log import LogHandler
import time, datetime
import json
log = LogHandler('centaline')

source = '中原地产'


class Centaline:
    def __init__(self):

        self.headers = {'User-Agent':
                            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
                        }
        self.start_url = 'http://www.centaline.com.cn/'
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
        res = requests.get(self.start_url, headers=self.headers)
        res.encoding = 'gbk'
        second_city_list = re.findall('http://\w+.centanet.com/ershoufang/', res.text, re.S | re.M)
        for city in second_city_list:
            city_comm = city.replace('ershoufang', 'xiaoqu')
            city_res = requests.get(city_comm, headers=self.headers)
            city_res.encoding = 'gbk'
            city_html = etree.HTML(city_res.text)
            page_str = city_html.xpath("//a[@class='fsm fb']/@href")[0]
            page = re.search('\d+', page_str).group(0)
            for i in range(1, int(page) + 1):
                while True:
                    try:
                        proxy = self.proxies[random.randint(0, 9)]
                        url = city_comm + "g" + str(i)
                        comm_res = requests.get(url, headers=self.headers, proxies=proxy)
                        break
                    except:
                        continue
                html = etree.HTML(comm_res.text)
                comm_url_list = html.xpath("//ul/li/div/a/@href")
                self.comm_detail(comm_url_list, city_comm)

    def comm_detail(self, comm_url_list, city):

        for comm_url in comm_url_list[1:]:
            try:
                com_url =  city.replace('/xiaoqu/',comm_url)
                statecode = re.search('xq-(.*)',comm_url).group(1)
                code = statecode.upper()
                comm_detail_url = 'http://sh.centanet.com/apipost/GetDealRecord?estateCode='+code+'&posttype=S&pageindex=1&pagesize=10000'
                while True:
                    proxy = self.proxies[random.randint(0, 9)]
                    try:
                        com_res = requests.get(com_url,headers=self.headers,proxies=proxy)
                        res = requests.get(comm_detail_url, headers=self.headers, proxies=proxy)
                        break
                    except:
                        continue
                html = etree.HTML(com_res.text)
                data_dict = json.loads(res.text)
                district_name = html.xpath("//div/h3/text()")[0]
                city_name = html.xpath("//div[@class='idx-city']/text()")[0]
                region = html.xpath("//a[@class='f000']/text()")[0]

                for data in data_dict["result"]:
                    try:
                        co = Comm(source)
                        co.district_name = district_name.strip()
                        co.region = region
                        co.city = city_name
                        try:
                            room_type = data["houseType"]
                            co.room = int(re.search('(\d)室', room_type, re.S | re.M).group(1))
                            co.hall = int(re.search('(\d)厅', room_type, re.S | re.M).group(1))
                        except Exception as e:
                            log.error('roomtype为空'.format(e))

                        area = data['areaSize'].replace('平','')
                        if area:
                            area = float(area)
                            co.area = round(area, 2)

                        co.direction = data['direction']

                        trade_date = '20' + data['dealTime']
                        if trade_date:
                            t = time.strptime(trade_date, "%Y-%m-%d")
                            y = t.tm_year
                            m = t.tm_mon
                            d = t.tm_mday
                            co.trade_date = datetime.datetime(y, m, d)

                        total_price = data['dealPrice']
                        co.total_price = int(re.search('(\d+)', total_price, re.S | re.M).group(1)) * 10000

                        avg_price = data['unitPrice']
                        try:
                            co.avg_price = int(re.search('(\d+)', avg_price, re.S | re.M).group(1))
                        except Exception as e:
                            co.avg_price = None
                        co.insert_db()
                    except Exception as e:
                        log.error('解析失败{}'.format(e))
            except Exception as e:
                log.error("小区成交信息错误{}".format(e))
