# -*- coding: utf-8 -*
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import datetime
import itertools

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from wechatpy import parse_message, create_reply, WeChatClient
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.utils import check_signature

from .config import WechatConfig
from .models import Person, Snippet
from .utils import MsgType

CONFIG = WechatConfig.config()
if CONFIG['env'] != 'local':
  print("Environment: Running on server")
  crypto = WeChatCrypto(CONFIG['token'], CONFIG['encodingAESKey'], CONFIG['appid'])
  # I think this is the way to create menu
  client = WeChatClient(CONFIG['appid'], CONFIG['appsecret'])
  client.menu.create({
    "button":[
      {
        "type":"click",
        "name":"获取模版",
        "key":"get_template"
      },
      {
        "type":"click",
        "name":"查看上周周报状态",
        "key":"query_state"
      }
    ]
  })

def view(request):
  # View current week's snippet
  current_year = datetime.datetime.now().year
  current_week_no = datetime.datetime.now().isocalendar()[1]
  return view_by_week(request, current_year, current_week_no)

def view_by_week(request, year, week_no):
  year = int(year)
  week_no = int(week_no)
  snippet_list = Snippet.objects.filter(date__year=year, week=week_no).order_by('has_read')
  prev_week = "year/{}/week/{}".format(year, week_no - 1)
  next_week = "year/{}/week/{}".format(year, week_no + 1)
  if week_no == 1:
    prev_week = "year/{}/week/53".format(year - 1)
  elif week_no == 53:
    next_week = "year/{}/week/1".format(year + 1)
  not_submitted = _get_people_not_in_list([snippet.user for snippet in snippet_list])
  context = {
    'year': year,
    'prev_week': prev_week,
    'week_no': week_no,
    'next_week': next_week,
    'snippet_list': snippet_list,
    'not_submitted': not_submitted,
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

def view_by_star(request):
  snippet_list = Snippet.objects.filter(has_star=True).order_by('-date')
  snippet_list = sorted(snippet_list, key=lambda s: s.user)
  snippet_lists = []
  users = {}
  for name, l in itertools.groupby(snippet_list, lambda s: s.user):
    user = Person.objects.get(name=name)
    snippet_lists.append((name, user.name_pinyin, list(l)))
    users[name] = user.name_pinyin
  context = {
    'users': sorted(users.items()),
    'snippet_lists': snippet_lists
  }
  return render(request, 'snippets/star.html', context)

def update_state_read(request, snippet_id):
  snippet_id = int(snippet_id)
  snippet = Snippet.objects.get(id=snippet_id)
  snippet.has_read = True
  snippet.save()
  return HttpResponse(200)

def update_state_star(request, snippet_id):
  update_star_state(snippet_id, True)
  return HttpResponse(200)

def update_state_unstar(request, snippet_id):
  update_star_state(snippet_id, False)
  return HttpResponse(200)

def update_star_state(snippet_id, to_star):
  snippet_id = int(snippet_id)
  snippet = Snippet.objects.get(id=snippet_id)
  snippet.has_star = to_star
  snippet.save()

@csrf_exempt
def wechat(request):
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
      saved_snippet = _save_snippet(msg)
      if saved_snippet:
        reply = create_reply("定期总结和及时沟通内容已收到", msg)
      else:
        reply = create_reply("用户信息已保存", msg)
    elif msg.type == 'event':
      if msg.key == 'query_state':
        reply = create_reply(_query_last_snippet_state(msg), msg)
      else:
        reply = create_reply(_get_template(), msg)
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
  try:
    person = Person.objects.get(open_id=msg.source)
    week = msg.create_time.isocalendar()[1]
    Snippet.objects.update_or_create(
      user=person.name,
      week=week,
      defaults={
        'date': msg.create_time,
        'content': msg.content,
        'content_type': _msg_type_to_int(msg.type)
      }
    )
    return True
  except ObjectDoesNotExist:
    _save_user(msg)
    return False

def _save_user(msg):
  person = Person(
    name=msg.content,
    open_id=msg.source
  )
  person.save()

def _query_last_snippet_state(msg):
  person = Person.objects.get(open_id=msg.source)
  snippet = Snippet.objects.filter(user=person.name).order_by('-date')[0]
  state = "已读" if snippet.has_read else "未读"
  return "第{}周周报{}".format(snippet.week, state)

def _get_template():
  return "本周工作：\n1.\n2.\n3.\n\n下周计划：\n1.\n2.\n\n需讨论问题：\n1.\n2.\n\n待安排事项：\n1.\n\n有什么想法：\n1.\n\n"

def _get_people_not_in_list(list_of_names):
  everyone_set = set(Person.objects.values_list('name', flat=True))
  exclude_set = set(list_of_names)
  return list(everyone_set - exclude_set)
