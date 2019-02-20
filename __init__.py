import requests
import decimal
from decimal import Decimal
import pandas as pd
import datetime


class ZhangTing:
    __url = 'http://quotes.money.163.com/cjmx/{1}/{2}/{0}.xls'
    __session = requests.session()
    __context = decimal.getcontext()
    __context.prec = 6
    __context.rounding = decimal.ROUND_HALF_UP

    def __init__(self, info):
        self.__info = info
        self.split_info()
        today = datetime.datetime.today().strftime('%Y%m%d')
        url = self.__url.format(info['CODE'], '2019', today)
        with self.__session.get(url) as response:
            with open('tmp.xls', 'wb') as f:
                f.write(response.content)
            self.__detail = pd.read_excel('tmp.xls')
            self.analyze_detail()
            
    @property
    def detail(self):
        return self.__detail
    
    @property
    def info(self):
        return self.__info

    def to_series(self):
        ret = pd.Series(self.__info)
        ret.name = self.__info['NAME']
        return ret
    
    def split_info(self):
        mfratio = self.__info['MFRATIO']
        self.__info['PROFIT'] = mfratio['MFRATIO2']
        self.__info['REVENUE'] = mfratio['MFRATIO10']
        del self.__info['MFRATIO']
    
    @classmethod
    def ztj(self, p):
        dc = Decimal(p)
        d = dc * Decimal(0.1)
        ret = dc + d
        return float(ret.quantize(Decimal('0.00', self.__context)))
    
    def analyze_detail(self):
        y_close = self.__info['YESTCLOSE']
        _open = self.__info['OPEN']
        close = self.__info['PRICE']
        ztj = self.ztj(y_close)
        self.__info['IS_OPEN_ZT'] = _open == ztj
        self.__info['IS_CLOSE_ZT'] = close ==ztj
        scsb = None
        zhsb = None
        for index in self.__detail.index:
            if self.__detail['成交价'][index] == ztj:
                self.__info['SCSB'] = self.__detail['成交时间'][index]
                scsb = index
                break
        for index in reversed(self.__detail.index):
            if self.__detail['成交价'][index] == ztj:
                self.__info['ZHSB'] = self.__detail['成交时间'][index]
                zhsb = index
                break
        ycfs = True
        for index in self.__detail.index[scsb:]:
            if self.__detail['成交价'][index] != ztj:
                ycfs = False
                break
        self.__info['YCFS'] = ycfs
                
        
class Searcher:
    def __init__(self):
        self.__sort_url = "http://quotes.money.163.com/hs/service/diyrank.php?" \
                          "host=http%3A%2F%2Fquotes.money.163.com%2Fhs%2Fservice%2Fdiyrank.php&" \
                          "page={0}&query=STYPE%3AEQA&fields=NO" \
                          "%2CSYMBOL%2CNAME%2CPRICE%2CPERCENT%2CUPDOWN%2CFIVE_MINUTE%2COPEN%2CYESTCLOSE%2CHIGH" \
                          "%2CLOW%2CVOLUME%2CTURNOVER%2CHS%2CLB%2CWB%2CZF%2CPE%2CMCAP%2CTCAP%2CMFSUM" \
                          "%2CMFRATIO.MFRATIO2%2CMFRATIO.MFRATIO10%2CSNAME%2CCODE%2CANNOUNMT%2CUVSNEWS&" \
                          "sort=PERCENT&order=desc&count={1}&type=query"
                          
    def query(self):
        url = self.__sort_url.format(0, 200)
        with requests.get(url) as response:
            result = response.json()
#           pagecount = result['pagecount']
            ret = []
            for info in result['list']:
                if info['HIGH'] == ZhangTing.ztj(info['YESTCLOSE']):
                    ret.append(ZhangTing(info).to_series())
                else:
                    if info['PERCENT'] > 0.09:
                        continue
                    else:
                        return pd.DataFrame(ret)
            raise RuntimeError("too many stocks zhangting")

        
s = Searcher()
a = s.query()