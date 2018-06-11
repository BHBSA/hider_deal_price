import requests
import re
from deal_price_info import Comm
import time, datetime
from lib.log import LogHandler

log = LogHandler('房天下')

url = 'http://esf.sh.fang.com/newsecond/esfcities.aspx'


class Fangtianxia():
    def __init__(self):
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119Safari/537.36',
        }

    def start_crawler(self):
        response = requests.get(url, headers=self.headers)
        html = response.text
        city_url_list = re.findall('class="red" href="(.*?)".*?>(.*?)<', html, re.S | re.M)
        for i in city_url_list:
            index_url = i[0] + '/chengjiao/'
            self.city_info(index_url, i[1])

    def city_info(self, index_url, city):
        for i in range(1, 101):
            index_url_ = index_url + 'i3' + str(i) + '/'
            if i == 1:
                index_url_ = index_url
            try:
                response = requests.get(index_url_, headers=self.headers)
                html = response.text
                try:
                    city_real = re.search('city = "(.*?)"', html, re.S | re.M).group(1)
                    if city != city_real:
                        break
                    house_num = re.search('class="org">(.*?)</b>', html, re.S | re.M).group(1)
                    if house_num == '0':
                        break
                    comm_info_paper_list = re.findall('class="info rel floatr".*?</dd>', html, re.S | re.M)
                    for comm_info_paper in comm_info_paper_list:
                        comm = Comm('房天下')
                        comm.city = city
                        comm.district_name = re.search('<a.*?>(.*?)<', comm_info_paper, re.S | re.M).group(1).strip()

                        if '�' in comm.district_name:
                            log.error('网页出现繁体字, url={}'.format(index_url_))
                            continue

                        comm.direction = re.search('class="mt18">(.*?)<', comm_info_paper, re.S | re.M).group(1)
                        try:
                            comm.height = int(re.search('共(.*?)层', comm_info_paper, re.S | re.M).group(1))
                        except Exception as e:
                            comm.height = None
                        comm.region = re.search('class="mt15">.*?<a.*?chengjiao.*?>(.*?)<', comm_info_paper,
                                                re.S | re.M).group(
                            1)
                        total_price = re.search('class="price">(.*?)<', comm_info_paper, re.S | re.M).group(1)
                        if '*' in total_price:
                            continue
                        comm.total_price = int(total_price) * 10000
                        comm.room = int(re.search('(\d+)室', comm.district_name, re.S | re.M).group(1))
                        comm.hall = int(re.search('(\d+)厅', comm.district_name, re.S | re.M).group(1))
                        try:
                            comm.area = float(re.search('(\d+\.\d+)平米', comm.district_name, re.S | re.M).group(1))
                        except Exception as e:
                            comm.area = None
                        trade_date = re.search('class="time".*?>(.*?)<', comm_info_paper, re.S | re.M).group(1)
                        t = time.strptime(trade_date, "%Y-%m-%d")
                        y = t.tm_year
                        m = t.tm_mon
                        d = t.tm_mday
                        comm.trade_date = datetime.datetime(y, m, d)
                        try:
                            comm.avg_price = int(comm.total_price / comm.area)
                        except Exception as e:
                            comm.avg_price = None
                        comm.insert_db()
                except Exception as e:
                    log.error('解析错误,source="{}",html="{}",e="{}"'.format('房天下', html, e))
            except Exception as e:
                log.error('请求错误,source="{}"，url="{}",e="{}"'.format('房天下', index_url_, e))
