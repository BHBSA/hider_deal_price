from deal_price_info import Comm
import requests
import re
from lxml import etree
import time
import datetime

from lib.log import LogHandler


source = '乐有家'
log = LogHandler('leyoujia')

class Leyoujia():
    def __init__(self):
        self.headers = {'User-Agent':
                            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
                        }
        self.start_url = 'https://you.leyoujia.com/bj'

    def start_crawler(self):
        res = requests.get(self.start_url,headers=self.headers)
        html = etree.HTML(res.text)
        city_url_list = html.xpath("//div[@class='foot-tab-boxs clearfix']/div[2]//a/@href")
        self.city_detail(city_url_list)

    def city_detail(self,city_url_list):
        for city_url in city_url_list:
            comm_url = city_url.replace('esf','xq')
            city_res = requests.get(comm_url,headers=self.headers)
            html = etree.HTML(city_res.text)
            page = html.xpath("//div[@class='clearfix']//a[5]/@title")[0]
            for i in range(1,int(page)+1):
                url = comm_url + "?n=" + str(i)
                res = requests.get(url,headers=self.headers)
                page_html = etree.HTML(res.text)
                comm_url_list = page_html.xpath("//ul[@class='xqpd_errow']/li/a/@href")
                self.comm_info(comm_url_list,city_url)

    def comm_info(self,comm_url_list,city_url):

        for comm_url in comm_url_list:
            url = city_url.replace('/esf/',comm_url)
            re_url = url.replace('xq','fangjia')
            res = requests.get(re_url,headers=self.headers)
            con = res.text
            co_name = re.search('wrap-head-name">(.*?)</div',con,re.S|re.M).group(1)
            co_name = co_name.strip()
            try:
                page = re.search('(\d+)">尾页',con).group(1)
            except:
                page = 1
            for i in range(1,int(page)+1):
                page_url = re_url.rstrip('.html') + "/?n=" + str(i)
                co_res = requests.get(page_url,headers=self.headers)
                co_con = co_res.text
                co_html = etree.HTML(co_con)
                city = co_html.xpath("//span[@class='change-city']/text()")[0]
                romm_info_list = co_html.xpath("//div[@class='list-cont']/div")
                for room_info in romm_info_list:
                    try:
                        room = Comm(source)
                        room.city = city
                        room.district_name = co_name
                        floor = room_info.xpath(".//div[@class='text']/p[2]/span[1]/text()")[0]
                        room.floor = int(re.search('\d+', floor).group(0))
                        trade_date = room_info.xpath(".//span[@class='cj-data-num']/text()")[0]
                        if trade_date:
                            t = time.strptime(trade_date, "%Y-%m-%d")
                            y = t.tm_year
                            m = t.tm_mon
                            d = t.tm_mday
                            room.trade_date = datetime.datetime(y, m, d)
                        total_price = room_info.xpath(".//span[@class='cj-data-num c4a4a4a']/em/text()")[0]
                        room.total_price = int(re.search('(\d+)', total_price, re.S | re.M).group(1)) * 10000
                        avg_price = room_info.xpath(".//span[@class='cj-data-num']/em/text()")[0]
                        room.avg_price = int(re.search('(\d+)', avg_price, re.S | re.M).group(1))
                        room.direction = room_info.xpath(".//div[@class='text']/p[2]/span[2]/text()")[0]
                        area = room_info.xpath(".//p[1]/text()")[1]
                        room.region = area
                        size = re.search('建筑面积(.*?)平',area).group(1)
                        if size:
                            area = float(size)
                            room.area = round(area, 2)
                        room.insert_db()
                    except Exception as e:
                        log.error("{}解析房屋错误{}".format(page_url,e))



