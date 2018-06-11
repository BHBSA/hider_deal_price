import requests
import re
from deal_price_info import Comm
import time, datetime
from lib.log import LogHandler

log = LogHandler('链家在线')
url = 'https://sh.lianjia.com/'


class Lianjiazaixian():
    def __init__(self):
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119Safari/537.36',
        }

    def start_crawler(self):
        response = requests.get(url, headers=self.headers)
        html = response.text
        city_list_html = re.search('city-tab".*?</div></div></div>', html, re.S | re.M).group()
        city_a_html_list = re.findall('<a.*?</a>', city_list_html, re.S | re.M)
        city_dict = {}
        for i in city_a_html_list:
            city = re.search('<a.*?>(.*?)<', i, re.S | re.M).group(1)
            city_url = re.search('href="(.*?)"', i, re.S | re.M).group(1)
            if 'you' not in city_url and 'fang' not in city_url:
                city_dict[city] = city_url
        self.get_city_info(city_dict)

    def get_city_info(self, city_dict):
        for city in city_dict:
            city_url = city_dict[city] + 'chengjiao/'
            try:
                response = requests.get(city_url, headers=self.headers)
                html = response.text
                area_html = re.search('data-role="ershoufang".*?地铁', html, re.S | re.M).group()
                area_list_str = re.findall('<a.*?</a>', area_html, re.S | re.M)
                for area_i in area_list_str:
                    if 'ershoufang' in area_i:
                        continue
                    area_url = re.search('href="(.*?)"', area_i, re.S | re.M).group(1)
                    area = re.search('<a.*?>(.*?)<', area_i, re.S | re.M).group(1)
                    for i in range(1, 101):
                        city_url_ = city_url.replace('/chengjiao/', '') + area_url + 'pg' + str(i)
                        try:
                            result = requests.get(city_url_, headers=self.headers)
                            content = result.text
                            comm_str_list = re.findall('class="info".*?</div></div></li>', content,
                                                       re.S | re.M)
                            for i in comm_str_list:
                                comm = Comm('链家在线')
                                comm.region = area.strip()
                                comm.city = city.strip()
                                comm.district_name = re.search('target="_blank">(.*?)<', i, re.S | re.M).group(
                                    1).strip()
                                comm.direction = re.search('class="houseIcon"></span>(.*?) \|', i, re.S | re.M).group(
                                    1).strip()
                                try:
                                    comm.fitment = re.search('class="houseIcon"></span>.*? \|(.*?)\| ', i,
                                                             re.S | re.M).group(1).strip()
                                except Exception as e:
                                    comm.fitment = None
                                try:
                                    height = re.search('class="positionIcon"></span>.*?\((.*?)\)', i,
                                                       re.S | re.M).group(1).strip()
                                    comm.height = int(re.search('(\d+)', height, re.S | re.M).group(1))
                                except Exception as e:
                                    comm.height = None
                                total_price = re.search("class='number'>(.*?)<", i, re.S | re.M).group(1).strip()
                                if "*" in total_price:
                                    continue
                                comm.total_price = int(re.search('(\d+)', total_price, re.S | re.M).group(1)) * 10000
                                room_type = re.search('arget="_blank">.*? (.*?) ', i, re.S | re.M).group(1).strip()
                                try:
                                    comm.room = int(re.search('(\d)室', room_type, re.S | re.M).group(1))
                                except Exception as e:
                                    comm.room = 0
                                try:
                                    comm.hall = int(re.search('(\d)厅', room_type, re.S | re.M).group(1))
                                except Exception as e:
                                    comm.hall = None
                                area_ = re.search('target="_blank">.*? .*? (.*?平米)', i, re.S | re.M).group(1).strip()
                                if area_:
                                    area_ = area_.replace('㎡', '').replace('平米', '')
                                    try:
                                        area_ = float(area_)
                                        comm.area = round(area_, 2)
                                    except Exception as e:
                                        comm.area = None
                                trade_date = re.search('dealDate">(.*?)<', i, re.S | re.M).group(1).strip()
                                if trade_date:
                                    t = time.strptime(trade_date, "%Y.%m.%d")
                                    y = t.tm_year
                                    m = t.tm_mon
                                    d = t.tm_mday
                                    comm.trade_date = datetime.datetime(y, m, d)
                                try:
                                    comm.avg_price = int(i['total_price'] / i['area'])
                                except Exception as e:
                                    comm.avg_price = None
                                comm.insert_db()
                        except Exception as e:
                            log.error('解析错误，source="{}",html="{}",e="{}"'.format('链家在线', html, e))
            except Exception as e:
                log.error('请求错误，source="{}",url="{}",e="{}"'.format('链家在线', city_url, e))
