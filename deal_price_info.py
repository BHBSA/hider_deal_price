"""
    二手成交数据字段
"""
from lib.log import LogHandler
from lib.mongo import Mongo
import yaml
import datetime
from lib.standardization import standard_block, standard_city

log = LogHandler('deal_price_info')
setting = yaml.load(open('./config_local.yaml'))
m = Mongo(setting['mongo']['host'], setting['mongo']['port'])
db = m.connect[setting['mongo']['db_name']]
coll = db[setting['mongo']['coll_comm']]


def serialization_info(info):
    """
    对象转字典
    :param info:
    :return: data:
    """
    data = {}
    for key, value in vars(info).items():
        data[key] = value
    return data


def compare(comm_keys):
    """
    防止程序员瞎写错误字段
    :param comm_keys: 字典
    :return:
    """
    c = Comm(source=None)

    for i in comm_keys:
        if i not in vars(c).keys():
            raise KeyError


class Comm:
    def __init__(self, source, trade_date=None, city=None, region=None, district_name=None,
                 avg_price=None, total_price=None, house_num=None, unit_num=None,
                 room_num=None, area=None, direction=None, fitment=None, height=None, floor=None, m_date=None,
                 room=None, hall=None, toilet=None,
                 ):
        self.city = city  # 城市
        self.region = region  # 区域
        self.district_name = district_name  # 小区名
        self.avg_price = avg_price  # 均价 Int 元/平方米
        self.total_price = total_price  # 总价 Int 单位元
        self.house_num = house_num  # 楼栋号
        self.unit_num = unit_num  # 单元号
        self.room_num = room_num  # 室号
        self.area = area  # 面积 float
        self.direction = direction  # 朝向
        self.fitment = fitment  # 装修
        self.source = source  # 来源网站
        self.room = room  # 室数 Int
        self.hall = hall  # 厅数 Int
        self.toilet = toilet  # 卫数 Int
        self.height = height  # 总楼层 Int
        self.floor = floor  # 所在楼层 Int
        self.trade_date = trade_date  # 交易时间
        self.m_date = m_date  # 更新时间
        self.create_date = datetime.datetime.now()  # 创建时间

    def insert_db(self):
        data = serialization_info(self)
        compare(data)

        city_success, data['city'] = standard_city(data['city'])
        region_success, data['region'] = standard_block(data['city'], data['region'])

        # todo 插入判断

        if city_success is False or region_success is False:
            log.error('城市区域数据格式化失败data={}'.format(data))

        elif not coll.find_one({'city': data['city'], 'region': data['region'], 'district_name': data['district_name'],
                                'source': data['source'], 'trade_date': data['trade_date'], 'area': data['area']}):
            coll.insert_one(data)
            log.info('插入数据={}'.format(data))

        else:
            log.info('已经存在数据={}'.format(data))