import requests
import re
from deal_price_info import Comm
import time, datetime
from lib.log import LogHandler

log = LogHandler('购房网')

url = 'http://dongguan.qfang.com/'


class Qfangwang():
    def __init__(self):
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119Safari/537.36',
        }
        self.proxy = {}

    def start_crawler(self):
        response = requests.get(url, headers=self.headers, proxies=self.proxy)
        html = response.text
        info_html = re.search('cities-opts clearfix".*?end cities', html, re.S | re.M).group()
        city_str_list = re.findall('<a.*?</a>', info_html, re.S | re.M)
        for city_str in city_str_list:
            city_url_head = re.search('href="(.*?)"', city_str, re.S | re.M).group(1)
            city_url = 'http:' + city_url_head + '/transaction'
            city = re.search('<a.*?>(.*?)<', city_str, re.S | re.M).group(1)
            self.get_city_info(city_url, city)

    def get_city_info(self, city_url, city):
        response = requests.get(city_url, headers=self.headers, proxies=self.proxy)
        html = response.text
        area_str = re.search('class="search-area-detail clearfix".*?</ul>', html, re.S | re.M).group()
        area_info_list = re.findall('<a.*?</a>', area_str, re.S | re.M)[1:]
        for i in area_info_list:
            area_url_head = re.search('href="(.*?)"', i, re.S | re.M).group(1)
            area = re.search('<a.*?>(.*?)<', i, re.S | re.M).group(1)
            area_url = city_url.replace('/transaction', '') + area_url_head
            result = requests.get(area_url, headers=self.headers, proxies=self.proxy)
            content = result.text
            try:
                page_html = re.search('class="turnpage_num".*?</p>', content, re.S | re.M).group()
                page = re.findall('<a.*?>(.*?)<', page_html, re.S | re.M)[-1]
                if not page:
                    log.error('小区，source="{}",url="{}",e="{}"'.format('Q房网', area_url, e))
                for i in range(1, int(page) + 1):
                    page_url = area_url + '/f' + str(i)
                    self.get_page_url(page_url, city, area)
            except Exception as e:
                log.error('请求错误，source="{}",url="{}",e="{}"'.format('Q房网', area_url, e))

    def get_page_url(self, page_url, city, area_):
        response = requests.get(page_url, headers=self.headers, proxies=self.proxy)
        html = response.text
        comm_html_list = re.findall('<li class=" clearfix">.*?</li>', html, re.S | re.M)
        for i in comm_html_list:
            try:
                comm = Comm('Q房网')
                comm.city = city.strip()
                comm.region = area_.strip()
                comm.district_name = re.search('house-title">.*?<a.*?>(.*?)<', i, re.S | re.M).group(1).strip()
                comm.direction = re.search('class="house-about clearfix".*?showKeyword">(.*?)<', i, re.S | re.M).group(
                    1).strip()
                try:
                    comm.height = int(
                        re.search('class="house-about clearfix".*?showKeyword">.*?<span.*?<span>.*?/(.*?)<',
                                  i,
                                  re.S | re.M).group(1).strip())
                except Exception as e:
                    comm.height = None
                total_price = re.search('class="show-price".*?span.*?>(.*?)<', i, re.S | re.M).group(1).strip()
                comm.total_price = int(total_price) * 10000
                avg_price = re.search('class="show-price".*?<p.*?>(.*?)<', i, re.S | re.M).group(1).strip()
                comm.avg_price = int(re.search('(\d+)', avg_price).group(1))
                trade_date = re.search('class="show-price concluded".*?span.*?>(.*?)<', i, re.S | re.M).group(
                    1).strip()
                if trade_date:
                    t = time.strptime(trade_date, "%Y.%m.%d")
                    y = t.tm_year
                    m = t.tm_mon
                    d = t.tm_mday
                    comm.trade_date = datetime.datetime(y, m, d)
                room_type = re.search('house-title">.*?<a.*?>.*? (.*?) ', i, re.S | re.M).group(1).strip()
                try:
                    comm.room = int(re.search('(\d)室', room_type, re.S | re.M).group(1))
                except Exception as e:
                    comm.room = None
                try:
                    comm.hall = int(re.search('(\d)厅', room_type, re.S | re.M).group(1))
                except Exception as e:
                    comm.hall = None
                area = re.search('house-title">.*?<a.*?>.*? .*? (.*?平米)', i, re.S | re.M).group(1).strip()
                area = area.replace('㎡', '').replace('平米', '')
                if area:
                    area = float(area)
                    comm.area = round(area, 2)
                comm.insert_db()
            except Exception as e:
                log.error('解析错误，source="{}",html="{}",e="{}"'.format('Q房网', i, e))
