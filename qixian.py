import time
import asyncio
import logging
import aiohttp
import os

import onetoken as ot
import yaml
from onetoken import Account, log
import time
import math
import time
import numpy as np
import logging
from collections import defaultdict
from threading import Thread





import asyncio

import arrow
import logging
import aiohttp
import onetoken as ot
from onetoken import Tick
import threading  
import numpy as np


current_ask_spot = 0
current_bid_spot = 0
current_ask_volume_spot = 0
current_bid_volume_spot = 0

current_ask_future = 0
current_bid_future = 0
current_ask_volume_future = 0
current_bid_volume_future = 0

future_long_watermark = 0.96  #期货价格太低，买多价格
future_long_win = 0.98 #期货买多平仓价格

future_short_watermart = 0.985 #期货价格太高，卖空价格
future_short_win = 0.975 #期货卖空平仓价格
dist = [0 for i in range(14400)]

eos_spot_num = 0
usdt_spot_num = 0
eos_index = 0
okex = Account("okex/bind-okdeep")
okef = Account("okef/bind-okdeep")
log_fd = open(os.getcwd() + "\\" + "qixian_log", "ab")

def my_print(log_fd, log):
    tm = time.time()
    time_str = time.strftime('%Y:%m:%d:%H:%M:%S ', time.localtime(float(tm)))
    print((time_str + "  "  + log + "\n").encode())
    log_fd.write((time_str + "  "  + log + "\n").encode())
    log_fd.flush()

async def on_update_2(tk: Tick):
    global current_bid_spot
    global current_ask_spot
    global current_bid_future
    global current_ask_future
    global eos_index
    global current_ask_volume_spot
    global current_bid_volume_spot
    global current_ask_volume_future
    global current_bid_volume_future

    if tk.contract == "okef/eos.usd.q" :
      current_ask_future = float(tk.asks[0]["price"])
      current_bid_future = float(tk.bids[0]["price"])
      current_ask_volume_future = float(tk.asks[0]["volume"])
      current_bid_volume_future = float(tk.bids[0]["volume"])
    if tk.contract == "okex/eos.usdt" :
      current_ask_spot = float(tk.asks[0]["price"])
      current_bid_spot = float(tk.bids[0]["price"])
      current_ask_volume_spot = float(tk.asks[0]["volume"])
      current_bid_volume_spot = float(tk.bids[0]["volume"])
    if tk.contract == "okef/eos.usd.i" :
    	eos_index = tk.to_dict()["price"]
    #print(str(current_bid_spot) + " " + str(current_bid_future))

    delay = (arrow.now() - tk.time).total_seconds() 
    if delay > 60:
      print(delay)



async def subscribe_from_ws():
    await ot.quote.subscribe_tick('okef/eos.usd.q', on_update_2)
    await ot.quote.subscribe_tick('okef/eos.usd.i', on_update_2)
    await ot.quote.subscribe_tick('okex/eos.usdt', on_update_2)





async def main(): 
    global current_bid_spot
    global current_ask_spot
    global current_bid_future
    global current_ask_future
    global log_fd
    global eos_spot_num
    global usdt_spot_num
    global eos_index
    global current_ask_volume_spot
    global current_bid_volume_spot
    global current_ask_volume_future
    global current_bid_volume_future
    global future_long_watermark  
    global future_long_win
    global future_short_watermart
    global future_short_win
    global dist

    index = 0
    begin = 0
    await subscribe_from_ws()

    eos_buy_num = 0
    info_f = await okef.get_info()
    info_s = await okex.get_info()
    print(info_f[0])
    print(info_s[0].position_dict["eos"]["available"])
    eos_spot_num = info_s[0].position_dict["eos"]["available"]
    usdt_spot_num = info_s[0].position_dict["usdt"]["available"]
    print(eos_spot_num, usdt_spot_num)



    while 1:
    	if index > 14399:
    		index = 0
    		begin = 1
    	dist[index] = current_ask_future/current_ask_spot
    	index = index + 1
    	if begin == 1:
    		my_print(log_fd, "mean " + str(np.mean(dist)) + " " + str(current_ask_future) + " " + str(current_ask_spot) + " open long:" + str(current_ask_future/current_bid_spot) + " close long:" + str(current_bid_future/current_ask_spot) + " open short:" + str(current_bid_future/current_ask_spot) + " close short:" + str(current_ask_future/current_bid_spot) + " " + str(eos_buy_num))
    	else:
    		my_print(log_fd, str(current_ask_future) + " " + str(current_ask_spot) + " open long:" + str(current_ask_future/current_bid_spot) + " close long:" + str(current_bid_future/current_ask_spot) + " open short:" + str(current_bid_future/current_ask_spot) + " close short:" + str(current_ask_future/current_bid_spot) + " " + str(eos_buy_num))

			#buy future sell spot 开仓
    	if current_ask_future/current_bid_spot < np.mean(dist) - 0.01 and eos_buy_num > -10 + 0.1 and begin == 1:
    		spot_num = int(min(current_ask_volume_future/10, current_bid_volume_spot, 10 - abs(eos_buy_num))*current_ask_future/10)*10/current_ask_future  #保证future_num为整数
    		#future_num = int(spot_num * current_ask_future / 10)
    		if spot_num * current_bid_future/10.0 - int(spot_num * current_bid_future/10.0) > 0.9:
    			future_num = int(spot_num * current_bid_future/10.0) + 1
    		else:
    			future_num = int(spot_num * current_bid_future/10.0)
    		if future_num == 0:
    			await asyncio.sleep(1)
    			continue
    		my_print(log_fd, "abc 0 " + str(current_ask_future) + " " + str(current_bid_spot)+ " " + str(spot_num) + " " + str(future_num) + " " + str(eos_buy_num))
    		eos_buy_num = eos_buy_num - spot_num
    		while 1:
    			rt_future = await okef.place_order("okef/eos.usd.q", price=current_ask_future * 1.005, bs='b', amount=future_num)
    			if rt_future[1]:
    				my_print(log_fd, "abc 159" + str(rt_future[1]))
    				await asyncio.sleep(1)
    				continue
    			else:
    				my_print(log_fd, "abc buy future1 " + str(current_ask_future) + " " +str(future_num))
    				break
    		while 1:
    			rt_spot = await okex.place_order("okex/eos.usdt", price=current_bid_spot * 0.995, bs='s', amount=spot_num)
    			if rt_spot[1]:
    				my_print(log_fd, "abc 168" + str(rt_spot[1]))
    				await asyncio.sleep(1)
    				continue
    			else:
    				my_print(log_fd, "abc sell spot2 " + str(current_bid_spot) + " " + str(spot_num))
    				break
    		exchangeid_future = rt_future[0]["exchange_oid"]
    		exchangeid_spot = rt_spot[0]["exchange_oid"]
    		finish_future = 0
    		finish_spot = 0
    		await asyncio.sleep(1)
    		while future_num - finish_future> 0.1:
    			while 1:
    				rt_future = await okef.get_order_use_exchange_oid(exchangeid_future)
    				if rt_future[1]:
    					my_print(log_fd, "abc 183" + str(rt_future[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					break
    			finish_future = finish_future + float(rt_future[0][0]["dealt_amount"])
    			my_print(log_fd, "abc 3 future finish " + str(rt_future[0][0]["dealt_amount"]))
    			if future_num - finish_future> 0.1:
    				while 1:
    					rt_future = await okef.cancel_use_exchange_oid(exchangeid_future)
    					if rt_future[1]:
    						my_print(log_fd, "abc 194" + str(rt_future[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 4 cancel future buy")
    						break
    				while 1:
    					rt_future = await okef.place_order("okef/eos.usd.q", price=current_ask_future * 1.005, bs='b', amount=future_num-finish_future)
    					if rt_future[1]:
    						my_print(log_fd, "abc 203" + str(rt_future[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 5 buy future " + str(current_ask_future) + " " + str(future_num-finish_future))
    						break
    				exchangeid_future = rt_future[0]["exchange_oid"]
    			
    		while spot_num - finish_spot > 0.1:
    			while 1:
    				rt_spot = await okex.get_order_use_exchange_oid(exchangeid_spot)
    				if rt_spot[1]:
    					my_print(log_fd, "abc 215" + str(rt_spot[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					break
    			finish_spot = finish_spot + float(rt_spot[0][0]["dealt_amount"])
    			my_print(log_fd, "abc 195 spot finish " + str(rt_spot[0][0]["dealt_amount"]))
    			if spot_num - finish_spot > 0.1:
    				while 1:
    					rt_spot = await okex.cancel_use_exchange_oid(exchangeid_spot)
    					if rt_spot[1]:
    						my_print(log_fd, "abc 226" + str(rt_spot[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 203 cancel ")
    						break
    				while 1:
    					rt_spot = await okex.place_order("okex/eos.usdt", price=current_bid_spot * 0.995, bs='s', amount=spot_num-finish_spot)
    					if rt_spot[1]:
    						my_print(log_fd, "abc 235" + str(rt_spot[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 210 sell spot " + str(current_bid_spot) + " " + str(spot_num-finish_spot))
    						break
    				exchangeid_spot = rt_spot[0]["exchange_oid"]
    			if spot_num - finish_spot > 0.1 and future_num - finish_future> 0.1:
    				my_print(log_fd, "abc 215 finish " + str(eos_buy_num))
    				break
    			else:
    				await asyncio.sleep(1)
    			
    	#sell future buy spot 开仓
    	if current_bid_future/current_ask_spot >  np.mean(dist) + 0.01 and eos_buy_num < 10 - 0.1 and begin == 1:
    		spot_num = int(min(current_bid_volume_future/10, current_ask_volume_spot, 10 - abs(eos_buy_num))*current_ask_future/10)*10/current_ask_future
    		#future_num = int(spot_num * current_bid_future / 10)
    		if spot_num * current_bid_future/10.0 - int(spot_num * current_bid_future/10.0) > 0.9:
    			future_num = int(spot_num * current_bid_future/10.0) + 1
    		else:
    			future_num = int(spot_num * current_bid_future/10.0)
    		if future_num== 0:
    			await asyncio.sleep(1)
    			continue
    		my_print(log_fd, "abc 224 " + str(current_bid_future) + " " + str(current_ask_spot) + " " + str(spot_num) + " " + str(future_num) + " " + str(eos_buy_num))
    		eos_buy_num = eos_buy_num + spot_num
    		while 1:
    			rt_future = await okef.place_order("okef/eos.usd.q", price=current_bid_future * 0.995, bs='s', amount=future_num)
    			if rt_future[1]:
    				my_print(log_fd, "abc 264" + str(rt_future[1]))
    				await asyncio.sleep(1)
    				continue
    			else:
    				my_print(log_fd, "abc 232 sell future " + str(current_bid_future) + " " + str(future_num))
    				break
    		while 1:
    			rt_spot = await okex.place_order("okex/eos.usdt", price=current_ask_spot * 1.005, bs='b', amount=spot_num)
    			if rt_spot[1]:
    				my_print(log_fd, "abc 273" + str(rt_spot[1]))
    				await asyncio.sleep(1)
    				continue
    			else:
    				my_print(log_fd, "abc 240 buy spot " + str(current_ask_spot) + " " + str(spot_num))
    				break
    		exchangeid_future = rt_future[0]["exchange_oid"]
    		exchangeid_spot = rt_spot[0]["exchange_oid"]
    		finish_future = 0
    		finish_spot = 0
    		await asyncio.sleep(1)
    		while future_num - finish_future > 0.1:
    			while 1:
    				rt_future = await okef.get_order_use_exchange_oid(exchangeid_future)
    				if rt_future[1]:
    					my_print(log_fd, "abc 288" + str(rt_future[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					break
    			finish_future = finish_future + float(rt_future[0][0]["dealt_amount"])
    			my_print(log_fd, "abc 256 future finish " + str(rt_future[0][0]["dealt_amount"]))
    			if future_num - finish_future > 0.1:
    				while 1:
    					rt_future = await okef.cancel_use_exchange_oid(exchangeid_future)
    					if rt_future[1]:
    						my_print(log_fd, "abc 299" + str(rt_future[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 264 cancel")
    						break
    				while 1:
    					rt_future = await okef.place_order("okef/eos.usd.q", price=current_bid_future * 0.995, bs='s', amount=future_num-finish_future)
    					if rt_future[1]:
    						my_print(log_fd, "abc 308" + str(rt_future[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 272 sell future " + str(current_bid_future) + " " + str(future_num-finish_future))
    						break
    				exchangeid_future = rt_future[0]["exchange_oid"]
    			
    		while spot_num - finish_spot > 0.1:
    			while 1:
    				rt_spot = await okex.get_order_use_exchange_oid(exchangeid_spot)
    				if rt_spot[1]:
    					my_print(log_fd, "abc 320" + str(rt_spot[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					break
    			finish_spot = finish_spot + float(rt_spot[0][0]["dealt_amount"])
    			my_print(log_fd, "abc  284 spot finish " + str(rt_spot[0][0]["dealt_amount"]))
    			if spot_num - finish_spot > 0.1:
    				while 1:
    					rt_spot = await okex.cancel_use_exchange_oid(exchangeid_spot)
    					if rt_spot[1]:
    						my_print(log_fd, "abc 331" + str(rt_spot[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 292 cancel")
    						break
    				while 1:
    					rt_spot = await okex.place_order("okex/eos.usdt", price=current_ask_spot * 1.005, bs='b', amount=spot_num-finish_spot)
    					if rt_spot[1]:
    						my_print(log_fd, "abc 340" + str(rt_spot[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc buy spot " + str(current_ask_spot) + " " + str(spot_num-finish_spot))
    						break
    				exchangeid_spot = rt_spot[0]["exchange_oid"]
    			if spot_num - finish_spot > 0.1 and future_num - finish_future > 0.1:
    				my_print(log_fd, "abc 304 finish " + str(eos_buy_num))
    				break
    			else:
    				await asyncio.sleep(1)    	
    				
    	#sell future buy spot 平仓
    	if current_bid_future/current_ask_spot >  np.mean(dist) and eos_buy_num < 0:
    		spot_num = int(min(current_bid_volume_future/10, current_ask_volume_spot, abs(eos_buy_num))*current_ask_future/10)*10/current_ask_future
    		if spot_num < 0.1 and eos_buy_num < -0.1:
    			spot_num = min(current_bid_volume_future/10, current_ask_volume_spot, abs(eos_buy_num))
    		if spot_num * current_bid_future/10.0 - int(spot_num * current_bid_future/10.0) > 0.9:
    			future_num = int(spot_num * current_bid_future/10.0) + 1
    		else:
    			future_num = int(spot_num * current_bid_future/10.0)
    		if future_num < 0.1 or spot_num < 0.1:
    			await asyncio.sleep(1) 
    			continue
    		my_print(log_fd, "abc 313 win" + str(current_bid_future) + " " + str(current_ask_spot) + " " + str(spot_num) + " " + str(future_num) + " " + str(eos_buy_num))
    		eos_buy_num = eos_buy_num + spot_num
    		if future_num > 0.1:
    			while 1:
    				rt_future = await okef.place_order("okef/eos.usd.q", price=current_bid_future * 0.995, bs='s', amount=future_num)
    				if rt_future[1]:
    					my_print(log_fd, "abc 342" + str(rt_future[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					exchangeid_future = rt_future[0]["exchange_oid"]
    					my_print(log_fd, "abc 321 sell future " + str(current_bid_future) + " " + str(future_num))
    					break
    		if spot_num > 0.1:
    			while 1:
    				rt_spot = await okex.place_order("okex/eos.usdt", price=current_ask_spot * 1.005, bs='b', amount=spot_num)
    				if rt_spot[1]:
    					my_print(log_fd, "abc 352" + str(rt_spot[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					exchangeid_spot = rt_spot[0]["exchange_oid"]
    					my_print(log_fd, "abc 329 buy spot " + str(current_ask_spot) + " " + str(spot_num))
    					break   		
    		finish_future = 0
    		finish_spot = 0
    		await asyncio.sleep(1)
    		while future_num - finish_future > 0.1:
    			while 1:
    				rt_future = await okef.get_order_use_exchange_oid(exchangeid_future)
    				if rt_future[1]:
    					my_print(log_fd, "abc 367" + str(rt_future[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					break
    			finish_future = finish_future + float(rt_future[0][0]["dealt_amount"])
    			my_print(log_fd, "abc 345 future finish " + str(rt_future[0][0]["dealt_amount"]))
    			if future_num - finish_future > 0.1:
    				while 1:
    					rt_future = await okef.cancel_use_exchange_oid(exchangeid_future)
    					if rt_future[1]:
    						my_print(log_fd, "abc 378" + str(rt_future[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 353 cancel")
    						break
    				while 1:
    					rt_future = await okef.place_order("okef/eos.usd.q", price=current_bid_future * 0.995, bs='s', amount=future_num-finish_future)
    					if rt_future[1]:
    						my_print(log_fd, "abc 386" + str(rt_future[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 361 sell future " + str(current_bid_future) + " " + str(future_num-finish_future))
    						break
    				exchangeid_future = rt_future[0]["exchange_oid"]
    		
    		while spot_num - finish_spot > 0.1:
    			while 1:
    				rt_spot = await okex.get_order_use_exchange_oid(exchangeid_spot)
    				if rt_spot[1]:
    					my_print(log_fd, "abc 399" + str(rt_spot[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					break
    			finish_spot = finish_spot + float(rt_spot[0][0]["dealt_amount"])
    			my_print(log_fd, "abc 373 spot finish " + str(rt_spot[0][0]["dealt_amount"]))
    			if spot_num - finish_spot > 0.1:
    				while 1:
    					rt_spot = await okex.cancel_use_exchange_oid(exchangeid_spot)
    					if rt_spot[1]:
    						my_print(log_fd, "abc 410" + str(rt_spot[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 381 cancel")
    						break
    				while 1:
    					rt_spot = await okex.place_order("okex/eos.usdt", price=current_ask_spot * 1.005, bs='b', amount=spot_num-finish_spot)
    					if rt_spot[1]:
    						my_print(log_fd, "abc 419" + str(rt_spot[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 423 buy spot " + str(current_ask_spot) + " " + str(spot_num-finish_spot))
    						break
    				exchangeid_spot = rt_spot[0]["exchange_oid"]
    			if spot_num - finish_spot > 0.1 and future_num - finish_future > 0.1:
    				my_print(log_fd, "abc 393 finish " + str(eos_buy_num))
    				break
    			else:
    				await asyncio.sleep(1)    	

			#buy future sell spot 平仓	
    	if current_ask_future/current_bid_spot <  np.mean(dist) and eos_buy_num > 0:
    		spot_num = int(min(current_ask_volume_future/10, current_bid_volume_spot, abs(eos_buy_num))*current_ask_future/10)*10/current_ask_future
    		if spot_num < 0.1 and eos_buy_num > 0.1:
    			spot_num = min(current_ask_volume_future/10, current_bid_volume_spot, abs(eos_buy_num))
    		if spot_num * current_bid_future/10.0 - int(spot_num * current_bid_future/10.0) > 0.9:
    			future_num = int(spot_num * current_bid_future/10.0) + 1
    		else:
    			future_num = int(spot_num * current_bid_future/10.0)
    		if future_num < 0.1 or spot_num < 0.1:
    			await asyncio.sleep(1)
    			continue
    		my_print(log_fd, "abc 402 win" + str(current_ask_future) + " " + str(current_bid_spot) + " " + str(spot_num) + " " + str(future_num) + " " + str(eos_buy_num))
    		eos_buy_num = eos_buy_num - spot_num
    		if future_num > 0.1:
    			while 1:
    				rt_future = await okef.place_order("okef/eos.usd.q", price=current_ask_future * 1.005, bs='b', amount=future_num)
    				if rt_future[1]:
    					my_print(log_fd, "abc 436" + str(rt_future[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					exchangeid_future = rt_future[0]["exchange_oid"]
    					my_print(log_fd, "abc buy future " + str(current_ask_future) + " " + str(future_num))
    					break
    		if spot_num > 0.1:
    			while 1:
    				rt_spot = await okex.place_order("okex/eos.usdt", price=current_bid_spot * 0.995, bs='s', amount=spot_num)
    				if rt_spot[1]:
    					my_print(log_fd, "abc 447" + str(rt_spot[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					my_print(log_fd, "abc 451 sell spot " + str(current_bid_spot) + " " + str(spot_num))
    					exchangeid_spot = rt_spot[0]["exchange_oid"]
    					break   		
    		finish_future = 0
    		finish_spot = 0
    		await asyncio.sleep(1)
    		while future_num - finish_future > 0.1:
    			while 1:
    				rt_future = await okef.get_order_use_exchange_oid(exchangeid_future)
    				if rt_future[1]:
    					my_print(log_fd, "abc 461" + str(rt_future[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					break
    			finish_future = finish_future + float(rt_future[0][0]["dealt_amount"])
    			my_print(log_fd, "abc 434 future finish " + str(rt_future[0][0]["dealt_amount"]))
    			if future_num - finish_future > 0.1:
    				while 1:
    					rt_future = await okef.cancel_use_exchange_oid(exchangeid_future)
    					if rt_future[1]:
    						my_print(log_fd, "abc 472 cancel error " + str(rt_future[1]))
    						await asyncio.sleep(1)
    						break
    					else:
    						my_print(log_fd, "abc 442 cancel")
    						break
    				while 1:
    					rt_future = await okef.place_order("okef/eos.usd.q", price=current_ask_future * 1.005, bs='b', amount=future_num-finish_future)
    					if rt_future[1]:
    						my_print(log_fd, "abc 480" + str(rt_future[1]) + " " + str(future_num) + " " + str(finish_future))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 450 buy future " + str(current_ask_future) + " " + str(future_num-finish_future) + " " + str(rt_future[0]["exchange_oid"]))
    						break
    				exchangeid_future = rt_future[0]["exchange_oid"]

    		while spot_num - finish_spot > 0.1:
    			while 1:
    				rt_spot = await okex.get_order_use_exchange_oid(exchangeid_spot)
    				if rt_spot[1]:
    					my_print(log_fd, "abc 493" + str(rt_spot[1]))
    					await asyncio.sleep(1)
    					continue
    				else:
    					break
    			finish_spot = finish_spot + float(rt_spot[0][0]["dealt_amount"])
    			my_print(log_fd, "abc 462 spot finish " + str(rt_spot[0][0]["dealt_amount"]))
    			if spot_num - finish_spot > 0.1:
    				while 1:
    					rt_spot = await okex.cancel_use_exchange_oid(exchangeid_spot)
    					if rt_spot[1]:
    						my_print(log_fd, "abc 504" + str(rt_spot[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 470 cancel")
    						break
    				while 1:
    					rt_spot = await okex.place_order("okex/eos.usdt", price=current_bid_spot * 0.995, bs='s', amount=spot_num-finish_spot)
    					if rt_spot[1]:
    						my_print(log_fd, "abc 513" + str(rt_spot[1]))
    						await asyncio.sleep(1)
    						continue
    					else:
    						my_print(log_fd, "abc 517 sell spot " + str(current_bid_spot) + " " + str(spot_num-finish_spot))
    						break
    				exchangeid_spot = rt_spot[0]["exchange_oid"]
    			if spot_num - finish_spot > 0.1 and future_num - finish_future > 0.1:
    				my_print(log_fd, "abc 482 finish " + str(eos_buy_num))
    				break
    			else:
    				await asyncio.sleep(1)    		
    	await asyncio.sleep(1)
 
    


if __name__ == '__main__':
    try:
        from docopt import docopt as docoptinit
    except ImportError:
        print('docopt not installed, run the following command first:')
        print('pip install docopt')
        import sys
        sys.exit(1)

    #docopt = docoptinit(__doc__)
    #Config.print_only_delay = docopt['--print-only-delay']
    print('ots folder', ot)
    print('ots version', ot.__version__)
    print('aiohttp version', aiohttp.__version__)
    ot.log_level(logging.INFO)
    asyncio.get_event_loop().run_until_complete(main())
    print('done')
