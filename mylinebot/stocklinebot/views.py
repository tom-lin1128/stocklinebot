from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from datetime import timedelta, datetime
 
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage,TextMessage

import twstock
 
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
 
 
@csrf_exempt
def callback(request):

    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            events = parser.parse(body, signature)  # 傳入的事件
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            if not isinstance(event, MessageEvent):
                 continue
            if not isinstance(event.message, TextMessage):
                 continue

            text=event.message.text
            
            if(text.lower()=='你好'):
                message_text(event)
            elif(text.lower() in twstock.twse) : 
                content = ''

                stock_rt = twstock.realtime.get(text)
                stock = twstock.Stock(text)#twstock.Stock('2330')

                my_datetime = datetime.fromtimestamp(stock_rt['timestamp'])
                my_time = my_datetime.strftime('%H:%M:%S')

                content += '%s (%s) %s\n' %(
                    stock_rt['info']['name'],
                    stock_rt['info']['code'],
                    my_time)
                content += '現價: %s / 幅度: %s\n'%(
                    stock_rt['realtime']['latest_trade_price'],
                    format(float(stock_rt['realtime']['latest_trade_price']) - stock.data[-2][6],'.2f'))
                print(float(stock_rt['realtime']['latest_trade_price']),stock.data[-2][6])
                content += '最高: %s / 最低: %s\n' %(
                    stock_rt['realtime']['high'],
                    stock_rt['realtime']['low'])
                content += '量: %s\n' %(stock_rt['realtime']['accumulate_trade_volume'])            
                content += '--------------\n'
                content += '最近五日價格: \n'
                price5 = stock.price[-5:][::-1]
                date5 = stock.date[-5:][::-1]
                for i in range(len(price5)):
                    #content += '[%s] %s\n' %(date5[i].strftime("%Y-%m-%d %H:%M:%S"), price5[i])
                    content += '[%s] %s\n' %(date5[i].strftime("%Y-%m-%d"), price5[i])
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=content)
                )
            else :           
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='非台股上市公司')
                )
        return HttpResponse()
    else:
        return HttpResponseBadRequest()
    


def message_text(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event)
    )