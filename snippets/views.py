# -*- coding: utf-8 -*
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from wechatpy import parse_message, create_reply
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.utils import check_signature

from .config import WechatConfig
from .models import Person, Snippet
from .utils import MsgType

CONFIG = WechatConfig.config()
crypto = WeChatCrypto(CONFIG['token'], CONFIG['encodingAESKey'], CONFIG['appid'])

def view(request):
  # View current week's snippet
  current_week_no = datetime.datetime.now().isocalendar()[1]
  return view_by_week(request, current_week_no)

def view_by_week(request, week_no):
  week_no = int(week_no)
  snippet_list = Snippet.objects.filter(week=week_no).order_by('has_read', 'is_done')
  context = {
    'prev_week': week_no - 1,
    'week_no': week_no,
    'next_week': week_no + 1,
    'snippet_list': snippet_list,
  }
  return render(request, 'snippets/index.html', context)

def view_by_name(request, name_pinyin):
  user = Person.objects.get(name_pinyin=name_pinyin)
  snippet_list = Snippet.objects.filter(user=user.name).order_by('-date')
  context = {
    'name': user.name,
    'snippet_list': snippet_list
  }
  return render(request, 'snippets/name.html', context)

def update_state_read(request, snippet_id):
  snippet_id = int(snippet_id)
  snippet = Snippet.objects.get(id=snippet_id)
  snippet.has_read = True
  snippet.save()
  return view_by_week(request, snippet.week)

def update_state_done(request, snippet_id):
  snippet_id = int(snippet_id)
  snippet = Snippet.objects.get(id=snippet_id)
  snippet.is_done = True
  snippet.save()
  return view_by_week(request, snippet.week)

@csrf_exempt
def create(request):
  signature = request.GET.get('signature', '')
  timestamp = request.GET.get('timestamp', '')
  nonce = request.GET.get('nonce', '')
  echo_str = request.GET.get('echostr', '')
  encrypt_type = request.GET.get('encrypt_type', '')
  msg_signature = request.GET.get('msg_signature', '')

  # print('signature:', signature)
  # print('timestamp: ', timestamp)
  # print('nonce:', nonce)
  # print('echo_str:', echo_str)
  # print('encrypt_type:', encrypt_type)
  # print('msg_signature:', msg_signature)

  try:
    check_signature(CONFIG['token'], signature, timestamp, nonce)
  except InvalidSignatureException:
    raise RuntimeError('Signature Validate Failed.')

  if request.method == 'GET':
    return HttpResponse(echo_str)
  else:
    msg = _decrypt_and_parse_msg(request.body, msg_signature, timestamp, nonce)
    if msg.type == 'text':
      _save_snippet(msg)
      reply = create_reply("定期总结和及时沟通内容已收到", msg)
    else:
      reply = create_reply('对不起，现在尚不能支持此消息类型', msg)
    return HttpResponse(crypto.encrypt_message(
      reply.render(),
      nonce,
      timestamp
    ))

def _decrypt_and_parse_msg(body, msg_signature, timestamp, nonce):
  # print('Raw message: \n%s' % request.body)
  try:
    msg = crypto.decrypt_message(
      body,
      msg_signature,
      timestamp,
      nonce
    )
    # print('Descypted message: \n%s' % msg)
    return parse_message(msg)
  except (InvalidSignatureException, InvalidAppIdException):
    raise RuntimeError('Signature Validate Failed.')

def _msg_type_to_int(type):
  return MsgType[type].value

def _save_snippet(msg):
  person = Person.objects.filter(open_id=msg.source)
  snippet = Snippet(
    user=person.name,
    date=msg.create_time,
    content=msg.content,
    content_type=_msg_type_to_int(msg.type)
  )
  snippet.save()

# Todos:
# 2. 更新，url这块