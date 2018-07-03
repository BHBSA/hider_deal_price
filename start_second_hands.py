from crawler.centaline import Centaline
from crawler.fangtu import Fangtu
from crawler.goufangwang import Goufangwang
from crawler.kufangwang import Kufangwang
from crawler.leju import Leju
from crawler.leyoujia import Leyoujia
from crawler.lianjiazaixian import Lianjiazaixian
from crawler.maitian import Maitian
from crawler.qfangwang import Qfangwang
from crawler.taiwuwang import Taiwuwang
from crawler.woai import Woai
from crawler.fangtianxia import Fangtianxia
from multiprocessing import Process


if __name__ == '__main__':
    centaline = Centaline()
    fangtianxia = Fangtianxia()
    fangtu = Fangtu()
    goufangwang = Goufangwang()
    kufangwang = Kufangwang()
    leju = Leju()
    leyoujia = Leyoujia()
    lianjiazaixian = Lianjiazaixian()
    maitian = Maitian()
    qfangwang = Qfangwang()
    taiwuwang = Taiwuwang()
    woai = Woai()
    Process(target=centaline.start_crawler).start()
    Process(target=fangtu.start_crawler).start()
    Process(target=goufangwang.start_crawler).start()
    Process(target=kufangwang.start_crawler).start()
    Process(target=leju.start_crawler).start()
    Process(target=leyoujia.start_crawler).start()
    Process(target=lianjiazaixian.start_crawler).start()
    Process(target=maitian.start_crawler).start()
    Process(target=qfangwang.start_crawler).start()
    Process(target=taiwuwang.start_crawler).start()
    Process(target=woai.start_crawler).start()
    Process(target=fangtianxia.start_crawler).start()
