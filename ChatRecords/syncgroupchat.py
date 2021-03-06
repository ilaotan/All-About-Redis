#!/usr/bin/env python
# coding:utf8
import sys
reload(sys)
sys.setdefaultencoding( "utf8" )

import itchat
from itchat.content import *

import logging
import logging.handlers
from subprocess import call
formatter = logging.Formatter('%(asctime)s  %(message)s')

class MyTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def doRollover(self):
        super(MyTimedRotatingFileHandler,self).doRollover()
        main_logger.info("Records log has been rotating...")
        call('git add .', shell = True)
        call('git reset -- ChatRecords/itchat.pkl', shell = True)
        call('git commit -m "commiting..."', shell = True)
        call('git push origin master', shell = True)

def setup_logger(name, log_file):
    """Function setup as many loggers as you want"""

    handler = MyTimedRotatingFileHandler(log_file, when='midnight')
    handler.suffix = "%Y-%m-%d.log"
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


# 自动回复文本等类别的群聊消息
# isGroupChat=True表示为群聊消息
@itchat.msg_register([TEXT, SHARING], isGroupChat=True)
def group_reply_text(msg):
    # 消息来自于哪个群聊
    chatroom_id = msg['FromUserName']
    # 发送者的昵称
    username = msg['ActualNickName']

    #from_chatroom = ''

    # 消息并不是来自于需要同步的群
    if not chatroom_id in chatroom_ids:
        return

    #for item in chatrooms:
    #    if item['UserName'] == chatroom_id:
    #        from_chatroom = item['NickName']

    # 根据消息类型转发至其他需要同步消息的群聊
    if msg['Type'] == TEXT:
        for item in chatrooms:
            if not item['UserName'] == chatroom_id:
                #itchat.send('%s from %s 说: \n%s' % (username, from_chatroom, msg['Content']), item['UserName'])
                itchat.send('%s 说: \n%s' % (username, msg['Content']), item['UserName'])
                #record_logger.info('%s from %s 说: \n%s' % (username, from_chatroom, msg['Content']))
                record_logger.info('%s 说: \n%s' % (username, msg['Content']))

    elif msg['Type'] == SHARING:
        for item in chatrooms:
            if not item['UserName'] == chatroom_id:
                #itchat.send('%s from %s 分享链接:\n %s\n%s' % (username,from_chatroom, msg['Text'], msg['Url']), item['UserName'])
                #record_logger.info('%s from %s 分享链接:\n %s\n%s' % (username,from_chatroom, msg['Text'], msg['Url']))
                itchat.send('%s 分享链接:\n %s\n%s' % (username, msg['Text'], msg['Url']), item['UserName'])
                record_logger.info('%s 分享链接:\n %s\n%s' % (username, msg['Text'], msg['Url']))

# 自动回复图片等类别的群聊消息
# isGroupChat=True表示为群聊消息
@itchat.msg_register([PICTURE, ATTACHMENT, VIDEO], isGroupChat=True)
def group_reply_media(msg):
    # 消息来自于哪个群聊
    chatroom_id = msg['FromUserName']
    # 发送者的昵称
    username = msg['ActualNickName']

    from_chatroom = ''

    for item in chatrooms:
        if item['UserName'] == chatroom_id:
            from_chatroom = item['NickName']

    # 消息并不是来自于需要同步的群
    if not chatroom_id in chatroom_ids:
        return

    # 如果为gif图片则不转发
    if msg['FileName'][-4:] == '.gif':
        return

    # 下载图片等文件
    msg['Text'](msg['FileName'])
    # 转发至其他需要同步消息的群聊
    for item in chatrooms:
        if not item['UserName'] == chatroom_id:
            #itchat.send('%s from %s 发送了：\n' % (username, from_chatroom), item['UserName'])
            #itchat.send('@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName']), item['UserName'])
            itchat.send('%s 发送了：\n' % (username), item['UserName'])
            itchat.send('@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName']), item['UserName'])

@itchat.msg_register(NOTE, isGroupChat=True)
def group_join_note(msg):
   global inviter,invitee
   chatroom_name =""
   # 消息来自于哪个群聊
   chatroom_id = msg['FromUserName']
   for c in chatrooms:
       if( c['UserName'] == chatroom_id):
           chatroom_name = c['NickName']        

   if u'邀请' in msg['Content'] or u'invited' in msg['Content']:
       str = msg['Content'];
       pos_start = str.find('"')
       pos_end = str.find('"',pos_start+1)
       inviter = str[pos_start+1:pos_end]
       rpos_start = str.rfind('"')
       rpos_end = str.rfind('"',0, rpos_start)
       invitee = str[(rpos_end+1) : rpos_start]
#       main_logger.info(msg)
   for item in chatrooms:
       if not item['UserName'] == chatroom_id:
           itchat.send_msg(u"%s 群新来一位朋友 %s， 让我们欢迎他/她吧！" % (chatroom_name,invitee), item['UserName'])
       else:
           itchat.send_msg(u"@%s\u2005欢迎来到本群[微笑]，感谢@%s \u2005邀请！方便的话做个简单自我介绍，再把群名片改为 名字@公司～ 最后看下群公告，谢谢！" % (invitee,inviter), chatroom_id )

if __name__ == '__main__':
    #### main func ###
    main_logger = setup_logger("main_logger","main")
    record_logger = setup_logger('group_logger', 'redisgroup')
    # 扫二维码登录
    itchat.auto_login(hotReload=True,enableCmdQR=2)

    # 获取所有通讯录中的相关群聊
    chatrooms = itchat.search_chatrooms(name="Redis")
    chatroom_ids = [c['UserName'] for c in chatrooms]

    main_logger.info('正在监测的群聊：%d 个' %(len(chatrooms)))
    main_logger.info(' '.join([item['NickName'] for item in chatrooms]))

    # 开始监测
    itchat.run()
