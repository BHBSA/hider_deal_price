import requests
import re
from deal_price_info import Comm
import time, datetime
from lib.log import LogHandler

url = 'http://sh.koofang.com/xiaoqu/pg1'

log = LogHandler('上海酷房网')


class Kufangwang():
    def __init__(self):
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119Safari/537.36',
        }

    def start_crawler(self):
        self.get_comm_info(url)
        self.get_all_comm_url(url)

    def get_comm_info(self, page_url):
        response = requests.get(page_url, headers=self.headers)
        html = response.text
        comm_info_html_list = re.findall('<div class="avail_conr">.*?</li>', html, re.S | re.M)
        for i in comm_info_html_list:
            comm = Comm('上海酷房网')
            comm.city = '上海'
            comm.district_name = re.search('class="avail_cont".*?>(.*?)<', i, re.S | re.M).group(1).strip()
            comm.region = re.search('class="avail_district".*?<a.*?>(.*?)<', i, re.S | re.M).group(1).strip()
            comm_id = re.search('class="avail_cont".*?href="/xiaoqu/(.*?)\.html"', i, re.S | re.M).group(1)
            self.get_comm_detail(comm_id, comm)

    def get_comm_detail(self, comm_id, comm):
        comm_detail_url = 'http://webapi.koofang.com/api/Community/SaleRealtyDealViewPageList'
        payload = "{\"PublicRequest\":{\"AppVersion\":\"1\",\"SourceWay\":10},\"AreaCode\":\"B024\",\"PageNumber\":1,\"PageSize\":1000,\"Search\":{\"CommunityId\":\"" + comm_id + "\"}}"
        headers = {
            'Content-Type': "application/json",
        }
        try:
            response = requests.post(comm_detail_url, data=payload, headers=headers)
            try:
                html = response.json()
                comm_list = html['PageData']['Data']
                if not comm_list:
                    return
                for i in comm_list:
                    comm.room = i['RoomNum']
                    comm.hall = i['LivingRoomNum']
                    comm.direction = i['FaceOrientationName'].strip()
                    trade_date = i['DealTime'].strip()
                    if trade_date:
                        t = time.strptime(trade_date, "%Y-%m-%d")
                        y = t.tm_year
                        m = t.tm_mon
                        d = t.tm_mday
                        comm.trade_date = datetime.datetime(y, m, d)
                    comm.avg_price = int(i['DealUnitAmount'])
                    comm.total_price = int(i['DealAmount']) * 10000
                    comm.area = i['ConstructionArea']
                    comm.insert_db()
            except Exception as e:
                log.error('解析错误,source="{}"，html = "{}",e="{}"'.format('上海酷房网', html, e))
        except Exception as e:
            log.error('请求错误,source="{}"，url="{}",data="{}",e="{}"'.format('上海酷房网', comm_detail_url, payload, e))

    def get_all_comm_url(self, url_page):
        try:
            response = requests.get(url_page, headers=self.headers)
            html = response.text
            try:
                page = re.search('next_page nextPage".*?xiaoqu/pg(.*?)"', html, re.S | re.M).group(1)
            except Exception as e:
                return
            page_url = 'http://sh.koofang.com/xiaoqu/pg' + str(page)
            self.get_comm_info(page_url)
            self.get_all_comm_url(page_url)
        except Exception as e:
            log.error('请求错误,source="{}"，url="{}",e="{}"'.format('上海酷房网', url_page, e))
