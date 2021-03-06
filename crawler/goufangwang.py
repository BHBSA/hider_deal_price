import requests
import re
from deal_price_info import Comm
import time
import datetime
from lib.log import LogHandler

log = LogHandler('购房网')

url = 'http://tj.goufang.com/xqsearch/o/1-1/p/1'


class Goufangwang():
    def __init__(self):
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119Safari/537.36',
        }

    def start_crawler(self):
        city_list = self.get_city_info()
        city_real = self.rinse(city_list)
        self.get_comm_info(city_real)
        self.get_comm_all(url)

    def get_city_info(self):
        response = requests.get('http://www1.goufang.com/', headers=self.headers)
        html = response.text
        city_info = re.search('<dl class="city">.*?</dl>', html, re.S | re.M).group()
        city_list = re.findall('http://(.*?)\..*?>(.*?)<', city_info, re.S | re.M)
        return city_list

    def rinse(self, city_list):
        list_ = []
        for url, city in city_list:
            city_url = 'http://' + url + '.goufang.com/xqsearch/o/1-1'
            try:
                response = requests.get(city_url, headers=self.headers)
                html = response.text
                city_name = re.search('<h3>(.*?)</h3>', html, re.S | re.M).group(1)
                if not city_name == '天津':
                    list_.append((url, city))
                else:
                    log.info('此城市没有数据，city="{}",url="{}"'.format(city, city_url))
            except Exception as e:
                log.error('请求出错，url={}'.format(city_url))
        return list_

    def get_comm_all(self, page_url):
        try:
            response = requests.get(page_url, headers=self.headers)
            html = response.text
            try:
                page = re.search('class="pagebreak".*?/p/(.*?)"', html, re.S | re.M).group(1)
            except Exception as e:
                return
            url_page = 'http://tj.goufang.com/xqsearch/o/1-1/p/' + page
            self.get_comm_info(url_page)
            self.get_comm_all(url_page)
        except Exception as e:
            log.error('请求错误,source="{}"，url="{}",e="{}"'.format('购房网', page_url, e))

    def get_comm_info(self, city_real):
        city_real.append(('tj', '天津'))
        for code, city in city_real:
            try:
                url_page = 'http://' + code + '.goufang.com/xqsearch/o/1-1'
                response = requests.get(url_page, headers=self.headers)
                html = response.text
                list_page = re.findall('<h3 class="tit">.*?class="param">', html, re.S | re.M)
                if not list_page:
                    log.error('此城市没有数据，url="{}"'.format(url_page))
                for i in range(1, 1001):
                    url_page_real = 'http://' + code + '.goufang.com/xqsearch/o/1-1/p/' + str(i)
                    res = requests.get(url_page_real, headers=self.headers)
                    paper = res.text
                    list_page_list = re.findall('<h3 class="tit">.*?class="param">', paper, re.S | re.M)
                    if not list_page_list:
                        log.error('此页没有数据，url="{}"'.format(url_page_real))
                    for list_page_html in list_page_list:
                        comm_url = re.search('<h3 class="tit">.*?href="(.*?)"', list_page_html, re.S | re.M).group(1)
                        region = re.search('地址：\[(.*?)\]', list_page_html, re.S | re.M).group(1)
                        self.get_comm_detail(comm_url, region, city)
            except Exception as e:
                log.error('请求错误,source="{}"，url="{}",e="{}"'.format('购房网', url_page, e))

    def get_comm_detail(self, comm_url, region, city):
        comm = Comm('购房网')
        comm.region = region.strip()
        comm.city = city
        try:
            response = requests.get(comm_url, headers=self.headers)
            html = response.text
            comm.district_name = re.search('title fl.*?<h1>(.*?)</h1>', html, re.S | re.M).group(1).strip()
            comm_info_html = re.search('<ul class="lscjlist">.*?</ul>', html, re.S | re.M).group()
            comm_info_list = re.findall('<li>(.*?)</li>', comm_info_html, re.S | re.M)
            if not comm_info_list:
                log.error('此小区没有数据，url="{}"'.format(comm_url))
            for i in comm_info_list:
                try:
                    trade_date = re.search('<span>(.*?)</span>', i, re.S | re.M).group(1).strip()
                    if trade_date:
                        t = time.strptime(trade_date, "%Y-%m-%d")
                        y = t.tm_year
                        m = t.tm_mon
                        d = t.tm_mday
                        comm.trade_date = datetime.datetime(y, m, d)
                    room_type = re.search('<span>.*?<span>(.*?)</span>', i, re.S | re.M).group(1).strip()
                    try:
                        comm.room = int(re.search('(\d)室', room_type, re.S | re.M).group(1))
                        comm.hall = int(re.search('(\d)厅', room_type, re.S | re.M).group(1))
                    except Exception as e:
                        comm.room = None
                        comm.hall = None
                    area = re.search('<span>.*?<span>.*?<span>(.*?)</span>', i, re.S | re.M).group(1).strip().replace(
                        '㎡', '').replace('平', '')
                    if area:
                        area = float(area)
                        comm.area = round(area, 2)
                    try:
                        height = re.search('<span>.*?<span>.*?<span>.*?<span>.*?/(.*?)</span>', i, re.S | re.M).group(
                            1).strip()
                        comm.height = int(re.search('(\d+)', height).group(1))
                    except Exception as e:
                        comm.height = None
                    comm.fitment = re.search('<span>.*?<span>.*?<span>.*?<span>.*?<span>(.*?)</span>', i,
                                             re.S | re.M).group(1).strip()
                    comm.direction = re.search('<span>.*?<span>.*?<span>.*?<span>.*?<span>.*?<span>(.*?)</span>', i,
                                               re.S | re.M).group(1).strip()
                    avg_price = re.search('<span>.*?<span>.*?<span>.*?<span>.*?<span>.*?<span>.*?<span>(.*?)</span>',
                                          i,
                                          re.S | re.M).group(1)
                    comm.avg_price = int(re.search('(\d+)', avg_price, re.S | re.M).group(1))
                    total_price = re.search(
                        '<span>.*?<span>.*?<span>.*?<span>.*?<span>.*?<span>.*?<span>.*?<span.*?>(.*?)</span>', i,
                        re.S | re.M).group(1)
                    comm.total_price = int(re.search('(\d+)', total_price, re.S | re.M).group(1)) * 10000
                    comm.insert_db()
                except Exception as e:
                    log.error('解析错误,source="{}"，url="{}",e="{}"'.format('购房网', comm_url, e))
        except Exception as e:
            log.error('请求错误,source="{}"，url="{}",e="{}"'.format('购房网', comm_url, e))
