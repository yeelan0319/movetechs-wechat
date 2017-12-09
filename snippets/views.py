from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime

from django.http import HttpResponse
from django.shortcuts import render
from wechatpy.enterprise import parse_message, create_reply
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException

from .config import WechatConfig
from .models import Snippet

def index(request):
  # View current week's snippet
  current_week_no = datetime.datetime.now().isocalendar()[1]
  return week(request, current_week_no)

def week(request, week_no):
  snippet_list = Snippet.objects.all()
  context = {
    'week_no': week_no,
    'snippet_list': snippet_list,
  }
  return render(request, 'snippets/index.html', context)

def create(request):
  config = WechatConfig.config()
  crypto = WeChatCrypto(config['token'], config['encodingAESKey'], config['corpId'])

  if request.method == 'GET':
    echo_str = request.GET.get('echostr', '')
    try:
      echo_str = crypto.check_signature(
          signature,
          timestamp,
          nonce,
          echo_str
      )
    except InvalidSignatureException:
      raise  RuntimeError('Signature Validate Failed.')
    return HttpResponse(echo_str)
  else:
    try:
      msg = crypto.decrypt_message(
          request.data,
          signature,
          timestamp,
          nonce
      )
    except InvalidSignatureException:
      raise  RuntimeError('Decrypt Message Failed')
    if msg.type == 'text':
      print(msg.content)
      reply = create_reply(msg.content, msg).render()
    else:
      reply = create_reply('Can not handle this for now', msg).render()
    res = crypto.encrypt_message(reply, nonce, timestamp)
    return HttpResponse(res)

