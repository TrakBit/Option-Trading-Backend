from rest_framework.decorators import api_view
from rest_framework.views import Response
from upstox_api.api import Session, Upstox, LiveFeedType, OHLCInterval
import json
import itertools as it
from app.models import Instrument, Full_Quote
from datetime import datetime, date
import calendar
from dateutil import relativedelta
from time import sleep
from rq import Queue
from worker import conn
from app.background_process import full_quotes_queue
from statistics import stdev
from django.db import connection
import requests
import ast
import os
import redis
from math import sqrt

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r = redis.from_url(redis_url)

api_key = 'Qj30BLDvL96faWwan42mT45gFHyw1mFs8JxBofdx'
redirect_uri = 'https://www.explainoid.com/home'
secret_key = 'pqmnwsq8ja'
master_contract_FO = 'NSE_FO'
master_contract_EQ = 'NSE_EQ'
nse_index = 'NSE_INDEX'
niftyit = 'niftyit'
symbols = ['BANKNIFTY', 'NIFTY']
expiry_date = "19JUN"
current_month_expiry = date(2019, 6, 27)
next_month_expirt = date(2019, 7, 25)

@api_view()
def get_redirect_url(request):
    session = Session(api_key)
    session.set_redirect_uri(redirect_uri)
    session.set_api_secret(secret_key)
    return Response({"url": session.get_login_url()})


@api_view(['POST'])
def get_access_token(request):
    r.flushall()
    request_data = json.loads(json.dumps(request.data))
    session = Session(api_key)
    session.set_redirect_uri(redirect_uri)
    session.set_api_secret(secret_key)
    session.set_code(request_data['requestcode'])
    access_token = session.retrieve_access_token()
    return Response({"accessToken": access_token})

@api_view(['POST'])
def historical_option(request):
    request_data = json.loads(json.dumps(request.data))
    access_token = request_data['accessToken']
    def create_session(request):
        upstox = Upstox(api_key, access_token)
        return upstox
    def fetch_option():
        upstox = create_session(request)
        upstox.get_master_contract(nse_index)
        historical =  upstox.get_ohlc(
            upstox.get_instrument_by_symbol(nse_index, 'NIFTY_50'), 
            OHLCInterval.Day_1, datetime.strptime('06/06/2018', '%d/%m/%Y').date(), 
            datetime.strptime('06/06/2019', '%d/%m/%Y').date()
        )
        historical_array = []
        for ops in historical:
             symbol = json.loads(json.dumps(ops))
             date = (datetime.fromtimestamp(int(symbol['timestamp'])/1000))
             closing = symbol['close']
             option_data = (date, closing)
             historical_array.append(option_data)
        return historical_array
    def historic_sigma():
        option_list = fetch_option()
        ltp_changes = []
        old_close = 0.0
        for idx, ops in enumerate(option_list):
            if(idx > 0):
                ltp_change_val = (float(ops[1])/float(old_close)) - 1.0
                ltp_changes.append(ltp_change_val)
            old_close = ops[1]
        historic_sigma = stdev(ltp_changes)* sqrt(252) * 100
    ltp_change()
    return Response({"historical": (fetch_option())})
    

# change the enitre function into a one time event saved to PostgreSQL
@api_view(['POST'])
def save_option(request):
    def create_session():
        request_data = json.loads(json.dumps(request.data))
        upstox = Upstox(api_key, request_data['accessToken'])
        return upstox
    def search_options(symbol):
        upstox = create_session()
        upstox.get_master_contract(master_contract_FO)
        option_search = upstox.search_instruments(master_contract_FO, symbol)
        return option_search
    def list_options():
        # Get First and Last Day of the Current Month/Week
        def get_first_date():
            today = datetime.now().today() + relativedelta.relativedelta(weeks=1)
            first_day_date = datetime(today.year, today.month, 1).timestamp() * 1000
            return first_day_date
        def get_last_date():
            today = datetime.now().today() + relativedelta.relativedelta(weeks=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            last_day_date = datetime(today.year, today.month, last_day).timestamp() * 1000
            return last_day_date
        # Creating Python Objects of all options
        all_options = []
        Instrument.objects.all().delete()
        for symbol in symbols:
            for ops in search_options(symbol):          
                expiry = int(ops[6])
                exchange_val = ops[0]
                token_val = ops[1]
                parent_token_val = ops[2]
                symbol_val = ops[3]
                name_val = ops[4]
                closing_price_val = ops[5]
                expiry_val = ops[6]
                strike_price_val = ops[7]
                tick_size_val = ops[8]
                lot_size_val = ops[9]
                instrument_type_val = ops[10]
                isin_val = ops[11]
                if strike_price_val != None:
                    if closing_price_val != None:
                        # Avoid NIFTYIT since searching for 
                        # NIFTY and BANKNIFTY alongs brings
                        # along this and it lacks liquidity
                        if symbol_val[:7] != niftyit:
                            if expiry >= get_first_date() and expiry <= get_last_date():
                                if ops[5] is None:
                                        closing_price_val = ''
                                if ops[11] is None:
                                        isin_val = ''
                                if ops[7] is None:
                                        strike_price_val = ''
                                if (symbol_val == "banknifty19jun27000ce"):
                                    symbol_val
                                Instrument(
                                    exchange = exchange_val, 
                                    token = token_val,
                                    parent_token = parent_token_val, 
                                    symbol = symbol_val, 
                                    name = name_val,
                                    closing_price = closing_price_val,
                                    expiry = expiry_val,
                                    strike_price = float(strike_price_val), 
                                    tick_size = tick_size_val, 
                                    lot_size = lot_size_val,
                                    instrument_type = instrument_type_val, 
                                    isin = isin_val
                                ).save()
                                all_options.append(Instrument(
                                    ops[0], ops[1], ops[2], ops[3], ops[4],
                                    ops[5], ops[6], ops[7], ops[8], ops[9],
                                    ops[10], ops[11]
                                ))
        return all_options
    list_options()
    return Response({"Message": "Options Saved"})


# Step 1: Fetch all the  Full Quotes and cache it in redis
# NOTE - This is a time consuming process there instruments
# passed through this should be filtred. 
@api_view(['POST'])
def cache_full_quotes_redis(request):
    request_data = json.loads(json.dumps(request.data))
    access_token = request_data['accessToken']
    r.flushall()
    list_options = Instrument.objects.all()
    q = Queue(connection=conn)
    def create_session(accessToken):
        upstox = Upstox(api_key, access_token)
        return upstox
    upstox = create_session(access_token)
    upstox.get_master_contract(master_contract_FO)
    # symbol = request_data['symbol']
    for symbol in symbols:
        symbol_len = len(symbol)
        for ops in list_options:
            # This has been done to differentiate between NIFTY and BANKNIFTY
            symbol_fetched = ops.symbol[:symbol_len]
            if (symbol_fetched.upper() == symbol):
                # This is to fetch Monthly Options only
                trim_symbol = ops.symbol[symbol_len:]
                expiry_date_fetched = trim_symbol[:len(expiry_date)] 
                if(expiry_date_fetched.upper() == expiry_date):
                    print(ops.symbol)
                    q.enqueue(full_quotes_queue, access_token, ops.symbol)
    return Response({"Message": "Quotes Saved"})

# Step 2: From redis move all the Quotes to database
@api_view(['POST'])
def save_full_quotes_db(request):
    request_data = json.loads(json.dumps(request.data))
    # create_session method exclusively while developing in online mode
    def create_session():
        upstox = Upstox(api_key, request_data['accessToken'])
        return upstox
    list_option = Instrument.objects.all()
    Full_Quote.objects.all().delete()
    for symbol in symbols:
        for ops in list_option:
            # This has been done to differentiate between NIFTY and BANKNIFTY
            symbol_len = len(symbol)
            symbol_cache = ops.symbol[:symbol_len]
            if(symbol_cache.upper() == symbol):
                # This is to fetch Monthly Options only
                trim_symbol = ops.symbol[symbol_len:]
                symbol_date = trim_symbol[:len(expiry_date)]
                if (symbol_date.upper() == expiry_date):
                    symbol_key = r.get(ops.symbol)
                    if (symbol_key != None):
                        if (ops.symbol == "banknifty19jun30500ce"):
                            print(ops.symbol)
                        val = symbol_key.decode("utf-8")
                        option = ast.literal_eval(val)
                        Full_Quote(
                            strike_price = ops.strike_price,
                            exchange = option['exchange'],
                            symbol = option['symbol'],
                            ltp = option['ltp'],
                            close = option['close'],
                            open = option['open'],
                            high = option['high'],
                            low = option['low'],
                            vtt = option['vtt'],
                            atp = option['atp'],
                            oi = option['oi'],
                            spot_price = option['spot_price'],
                            total_buy_qty = option['total_buy_qty'],
                            total_sell_qty = option['total_sell_qty'],
                            lower_circuit = option['lower_circuit'],
                            upper_circuit = option['upper_circuit'],
                            yearly_low = option['yearly_low'],
                            yearly_high = option['yearly_high'],
                            ltt = option['ltt']
                        ).save()
    connection.close()
    return Response({"Message": "Full Quotes Saved"})


@api_view(['POST'])
def validate_token(request):
    access_token = json.dumps(request.data)
    access_token_data = json.loads(access_token)
    try:
        upstox = Upstox(api_key, access_token_data['accessToken'])
        return Response({"status": 1})
    except:
        return Response({"status": 0})


@api_view(['POST'])
def get_full_quotes(request):
    request_data = json.loads(json.dumps(request.data))
    access_token = request_data['accessToken']
    indices = request_data['indices']
    symbol = request_data['symbol']
    def create_session(request):
        upstox = Upstox(api_key, access_token)
        return upstox
    def search_equity():
        upstox = create_session(request)
        upstox.get_master_contract(nse_index)
        equity = upstox.get_live_feed(upstox.get_instrument_by_symbol(
            nse_index, indices),
            LiveFeedType.Full)
        equity_data = json.loads(json.dumps(equity))
        print(equity_data)
        stock = Instrument(
            equity_data['exchange'], "", "", 
            equity_data['symbol'], "", 
            equity_data['ltp'], "", 0.0, "", "", "", ""
        )
        return stock
    def search_future():
        upstox = create_session(request)
        upstox.get_master_contract(master_contract_FO)
        future = upstox.get_live_feed(upstox.get_instrument_by_symbol(
            master_contract_FO, symbol+expiry_date+'FUT'),
            LiveFeedType.Full)
        return future
    def pairing():
        list_options = Full_Quote.objects.all()\
                                         .filter(symbol__startswith=symbol)\
                                         .order_by('strike_price')
        def to_lakh(n):
            return float(round(n/100000, 1))
        option_pairs = []
        closest_strike = 10000000
        closest_option = ""
        equity = search_equity()
        call_OI = 0.0
        put_OI = 0.0
        for a, b in it.combinations(list_options, 2):
            if (a.strike_price == b.strike_price):
                # remove strikes which are less than ₹ 10,000 
                if (to_lakh(a.oi) > 0.0 and to_lakh(b.oi) > 0.0):
                    # arrange option pair always in CE and PE order
                    diff = abs(float(equity.name) - float(a.strike_price))
                    call_OI = call_OI + to_lakh(a.oi)
                    put_OI = put_OI + to_lakh(b.oi)
                    if(diff < closest_strike):
                        closest_strike = diff
                        closest_option = a
                    if (a.symbol[-2:] == 'CE'):
                        option_pair = (a, b, a.strike_price)
                        option_pairs.append(option_pair)
                    else:
                        option_pair = (b, a, a.strike_price)
                        option_pairs.append(option_pair)
        pcr = round(put_OI/call_OI, 2)
        connection.close()
        return option_pairs, closest_option, pcr
    option_pairs, closest_option, pcr = pairing()
    def lot_size(symbol):
        if (symbol == "NIFTY"):
            return 75
        elif ("BANKNIFTY"):
            return 20
    def days_to_expiry():
        d1 = date.today()
        d2 = current_month_expiry
        d = d2 - d1
        return d.days
    def obj_dict(obj):
        return obj.__dict__
    def toJson(func):
        return json.loads(json.dumps(func, default=obj_dict))
    return Response({
        "stock": toJson(search_equity()),
        "options": toJson(option_pairs),
        "symbol": symbol,
        "closest_strike" : toJson(closest_option),
        "future": toJson(search_future()),
        "lot_size": toJson(lot_size(symbol)),
        "days_to_expiry": days_to_expiry(),
        "pcr": pcr
    })
