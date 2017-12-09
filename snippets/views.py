from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from wechatpy import parse_message, create_reply
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.utils import check_signature

from .config import WechatConfig
from .models import Snippet

CONFIG = WechatConfig.config()

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

@csrf_exempt
def create(request):
  signature = request.GET.get('signature', '')
  timestamp = request.GET.get('timestamp', '')
  nonce = request.GET.get('nonce', '')
  echo_str = request.GET.get('echostr', '')
  encrypt_type = request.GET.get('encrypt_type', '')
  msg_signature = request.GET.get('msg_signature', '')

  print('signature:', signature)
  print('timestamp: ', timestamp)
  print('nonce:', nonce)
  print('echo_str:', echo_str)
  print('encrypt_type:', encrypt_type)
  print('msg_signature:', msg_signature)

  try:
    check_signature(CONFIG['token'], signature, timestamp, nonce)
  except InvalidSignatureException:
    raise RuntimeError('Signature Validate Failed.')
  if request.method == 'GET':
    return HttpResponse(echo_str)
  else:
    print('Raw message: \n%s' % request.body)
    crypto = WeChatCrypto(CONFIG['token'], CONFIG['encodingAESKey'], CONFIG['appid'])
    try:
      msg = crypto.decrypt_message(
          request.body,
          msg_signature,
          timestamp,
          nonce
      )
      print('Descypted message: \n%s' % msg)
    except (InvalidSignatureException, InvalidAppIdException):
      raise RuntimeError('Signature Validate Failed.')
    msg = parse_message(msg)
    if msg.type == 'text':
      reply = create_reply(msg.content, msg)
    else:
      reply = create_reply('Sorry, can not handle this for now', msg)
    return HttpResponse(crypto.encrypt_message(
      reply.render(),
      nonce,
      timestamp
    ))

