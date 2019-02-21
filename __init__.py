import requests
import decimal
from decimal import Decimal
import pandas as pd
import numpy as np
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
        self.__name = self.__info['NAME']
        today = datetime.datetime.today().strftime('%Y%m%d')
        url = self.__url.format(info['CODE'], '2019', today)
        with self.__session.get(url) as response:
            with open('tmp.xls', 'wb') as f:
                f.write(response.content)
            self.__detail = pd.read_excel('tmp.xls')
            self.analyze_detail()
            self.remove_extra()
            
    @property
    def detail(self):
        return self.__detail
    
    @property
    def info(self):
        return self.__info

    def to_series(self):
        ret = pd.Series(self.__info)
        ret.name = self.__name
        return ret
    
    def split_info(self):
        mfratio = self.__info['MFRATIO']
        self.__info['PROFIT'] = mfratio['MFRATIO2']
        self.__info['REVENUE'] = mfratio['MFRATIO10']
        del self.__info['MFRATIO']
        if 'ANNOUNMT' in self.__info:
            content = self.__info['ANNOUNMT']
            self.__info['ANNOUNMT'] = content[0]['ANNOUNMT2']
        
    
    @classmethod
    def ztj(cls, price):
        return cls.cal_price(price, 0.1)

    @classmethod
    def cal_price(cls, price, percent):
        dc = Decimal(price)
        d = dc * Decimal(percent)
        ret = dc + d
        return float(ret.quantize(Decimal('0.00', cls.__context)))
    
    def analyze_detail(self):
        y_close = self.__info['YESTCLOSE']
        _open = self.__info['OPEN']
        close = self.__info['PRICE']
        ztj = self.ztj(y_close)
        self.__info['一字版'] = _open == ztj
        self.__info['涨停收盘'] = close == ztj
        cjj = self.__detail['成交价']
        cjsj = self.__detail['成交时间']
        cjl = self.__detail['成交量（手）']
# 计算首次上板时间
        scsb = None
        for index in self.__detail.index:
            if self.__detail['成交价'][index] == ztj:
                self.__info['首次上板'] = self.__detail['成交时间'][index]
                scsb = index
                break
# 计算是否一次封死
        ycfs = True
        for index in self.__detail.index[scsb+1:]:
            if self.__detail['成交价'][index] != ztj:
                ycfs = False
                break
        self.__info['一次封死'] = ycfs
# 计算首次开板时间
        sckb = None
        if not ycfs:
            for index in self.__detail.index[scsb+1:]:
                if self.__detail['成交价'][index] != ztj:
                    self.__info['首次开板'] = self.__detail['成交时间'][index]
                    sckb = index
                    break
        else:
            self.__info['首次开板'] = np.NAN
# 计算最后一次回封时间
        zhhf = None
        if not self.__info['一次封死'] and self.__info['涨停收盘']:
            last = None
            for index in reversed(self.__detail.index):
                if self.__detail['成交价'][index] == ztj:
                    last = index
                    continue
                else:
                    self.__info['最后回封'] = self.__detail['成交时间'][last]
                    break
        else:
            self.__info['最后回封'] = np.nan
# 统计筹码分布
        hp = self.cal_price(y_close, 0.07)
        sum_vol = cjl.sum()
        hp_vol = self.__detail[cjj >= hp]['成交量（手）'].sum()
        vol_percent = hp_vol / sum_vol
        self.__info['高价比例'] = vol_percent

    def remove_extra(self):
        del self.__info['FIVE_MINUTE']
        del self.__info['CODE']
        del self.__info['HIGH']
        del self.__info['LB']
        del self.__info['LOW']
        del self.__info['MFSUM']
        del self.__info['NAME']
        del self.__info['OPEN']
        del self.__info['SNAME']
        del self.__info['UPDOWN']
        del self.__info['WB']
        del self.__info['YESTCLOSE']
        del self.__info['NO']
#        if 'ANNOUNMT' in self.__info:
#            del self.__info['ANNOUNMT']

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
today = datetime.datetime.today().strftime('%Y%m%d')
a.to_excel(today+'.xls')