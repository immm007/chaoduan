import requests
import decimal
from decimal import Decimal


class ZhangTing:
    def __init__(self, info):
        self.__info = info
        self.__detail_url = 'http://quotes.money.163.com/cjmx/{1}/{2}/{0}.xls'

    def fill_detail(self, symbol):
        url = self.__detail_url.format(symbol, '2019', '20190219')
        with requests.get(url) as response:
            return response.text


class Searcher:
    def __init__(self):
        self.__sort_url = "http://quotes.money.163.com/hs/service/diyrank.php?" \
                          "host=http%3A%2F%2Fquotes.money.163.com%2Fhs%2Fservice%2Fdiyrank.php&" \
                          "page={0}&query=STYPE%3AEQA&fields=NO" \
                          "%2CSYMBOL%2CNAME%2CPRICE%2CPERCENT%2CUPDOWN%2CFIVE_MINUTE%2COPEN%2CYESTCLOSE%2CHIGH" \
                          "%2CLOW%2CVOLUME%2CTURNOVER%2CHS%2CLB%2CWB%2CZF%2CPE%2CMCAP%2CTCAP%2CMFSUM" \
                          "%2CMFRATIO.MFRATIO2%2CMFRATIO.MFRATIO10%2CSNAME%2CCODE%2CANNOUNMT%2CUVSNEWS&" \
                          "sort=PERCENT&order=desc&count={1}&type=query"
        self.__context = decimal.getcontext()
        self.__context.prec = 6
        self.__context.rounding = decimal.ROUND_HALF_UP

    def ztj(self, p):
        dc = Decimal(p)
        d = dc * Decimal(0.1)
        ret = dc + d
        return float(ret.quantize(Decimal('0.00', self.__context)))

    def query(self):
        url = self.__sort_url.format(0, 200)
        with requests.get(url) as response:
            result = response.json()
#           pagecount = result['pagecount']
            ret = []
            for info in result['list']:
                if info['PRICE'] == self.ztj(info['YESTCLOSE']):
                    ret.append(info)
                else:
                    if info['PERCENT'] > 0.09:
                        continue
                    else:
                        return ret
            raise RuntimeError("too many stocks zhangting")

