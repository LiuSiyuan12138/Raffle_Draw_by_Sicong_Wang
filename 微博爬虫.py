import requests
from bs4 import BeautifulSoup
import re
import urllib.request
import json
import pandas as pd
from pyquery import PyQuery as pq
import numpy as np
#设置代理IP
proxy_addr="122.241.72.191:808"

#定义页面打开函数
def use_proxy(url,proxy_addr):
    req=urllib.request.Request(url)
    req.add_header("User-Agent","Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0")
    proxy=urllib.request.ProxyHandler({'http':proxy_addr})
    opener=urllib.request.build_opener(proxy,urllib.request.HTTPHandler)
    urllib.request.install_opener(opener)
    data=urllib.request.urlopen(req).read().decode('utf-8','ignore')
    return data

#获取微博主页的containerid，爬取微博内容时需要此id
def get_containerid(url):
    data=use_proxy(url,proxy_addr)
    content=json.loads(data).get('data')
    for data in content.get('tabsInfo').get('tabs'):
        if(data.get('tab_type')=='weibo'):
            containerid=data.get('containerid')
    return containerid

def get_userInfo(id):
    url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+id
    data=use_proxy(url,proxy_addr)
    content=json.loads(data).get('data')
    profile_image_url=content.get('userInfo').get('profile_image_url')
    description=content.get('userInfo').get('description')
    profile_url=content.get('userInfo').get('profile_url')
    verified=content.get('userInfo').get('verified')
    guanzhu=content.get('userInfo').get('follow_count')
    name=content.get('userInfo').get('screen_name')
    fensi=content.get('userInfo').get('followers_count')
    gender=content.get('userInfo').get('gender')
    urank=content.get('userInfo').get('urank')
    description=content.get('userInfo').get('description')
    a= {"name":[name],
            "uid":[id],
            "is_verified":[str(verified)],
            "关注人数":[int(guanzhu)],
            "fan_num":[int(fensi)],
            "gender":[gender],
            "level":[int(urank)],
            "description":[description]}
    return a

#获取微博内容信息,并保存到文本中，内容包括：每条微博的内容、微博详情页面地址、点赞数、评论数、转发数等
def get_weibo(id):
    texts=[]
    attitudes=[]
    comments=[]
    reposts=[]
    times=[]
    sources=[]
    is_original=[]
    have_pic=[]
    i=1
    target=True
    while target:
        url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+id
        weibo_url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+id+'&containerid='+get_containerid(url)+'&page='+str(i)
        try:
            data=use_proxy(weibo_url,proxy_addr)
            content=json.loads(data).get('data')
            cards=content.get('cards')
            if(len(cards)>0):
                for j in range(len(cards)):
                    print("-----正在爬取第"+str(i)+"页，第"+str(j)+"条微博------")
                    card_type=cards[j].get('card_type')
                    if(card_type==9):
                        mblog=cards[j].get('mblog')
                        attitudes_count=mblog.get('attitudes_count')
                        comments_count=mblog.get('comments_count')
                        created_at=mblog.get('created_at')
                        reposts_count=mblog.get('reposts_count')
                        scheme=cards[j].get('scheme')
                        text=pq(mblog.get('text')).text()
                        source=mblog.get('source')
                        
                        texts.append(text)
                        attitudes.append(attitudes_count)
                        comments.append(comments_count)
                        reposts.append(reposts_count)
                        if '-' in created_at:
                            times.append(int(created_at.replace('-','')))
                        else:
                            times.append(int(1129))
                        sources.append(source)
                        if mblog.get('retweeted_status')==None:
                            is_original.append(1)
                        else:
                            is_original.append(0)
                        if mblog.get('thumbnail_pic')==None:
                            have_pic.append(0)
                        else:
                            have_pic.append(1)
                            
                       
                i+=1
            else:
                break
        except Exception as e:
            print(e)
            pass
        if times[-1]<1011 or i==56:
            target=False
    a=pd.DataFrame({'texts':texts,'attitudes':attitudes,'comments':comments,'reposts':reposts,'times':times,'sources':sources,'is_original':is_original,'have_pic':have_pic})
    a = a[(a['times']<=1111)&(a['times']>=1011)]
    b={'original_count':[a['is_original'].sum()],
       'have_pic_count':[a['have_pic'].sum()],
       'total_weibo_count':[a['is_original'].count()],
       'source':[a['sources'].mode().tolist()[0]],
       'sum_attitudes':[a['attitudes'].sum()],
       'sum_comments':[a['comments'].sum()],
       'sum_reposts':[a['reposts'].sum()],
       'mean_attitudes':[a['attitudes'].mean()],
       'mean_comments':[a['comments'].mean()],
       'uid':[id],
       'mean_reposts':[a['reposts'].mean()]}
    if b['total_weibo_count'][0]==0:
        return {'original_count': [0], 'have_pic_count': [0], 'total_weibo_count': [0], 'source': [np.nan], 'sum_attitudes': [0], 'sum_comments': [0], 'sum_reposts': [0],'mean_attitudes': [0],'mean_comments': [0],'uid':[id],'mean_reposts': [0]}
    else:
        return b

def get_xinyong(uid):
    url='https://weibo.com/p/100505'+str(uid)+'/info?mod=pedit_more'
    headers = {
    'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8',
    'Accept-Encoding':'gzip, deflate, br',
    'Accept-Language': 'zh-CN',
    'Connection':'Keep-Alive',
    'Cookie': 'wb_view_log=1536*8641.25; SINAGLOBAL=2056188645548.1892.1534946300336; ALF=1566482313; ULV=1543585752977:3:2:2:1422179051951.1645.1543585752561:1543581912199; SUHB=0ebssnM7ZIopAa; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WFzd3woboF_FaNwvMU8VmOW; SUB=_2AkMrXb_5f8NxqwJRmPETy2ngaYlzzgvEieKdAU4iJRMxHRl-yT83qlIltRB6AN2RFgY5bnhL9VHqaxV8E-7LgCy7n-KQ; YF-Page-G0=86b4280420ced6d22f1c1e4dc25fe846; _s_tentry=-; Apache=1422179051951.1645.1543585752561',
    'Host': 'weibo.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134',
    }
    r=requests.get(url,headers=headers)
    html=r.text
    soup=BeautifulSoup(html,'lxml')
    a=soup.findAll('script')[:]
    b=[]
    for s in a:
        b.append(s.get_text())
    c=''.join(b)
    res_tr = r'<div class=\\"text_box available avable_color\\">\\n(.*?)<\\/div>\\n'
    m_tr = re.findall(res_tr, c, re.S | re.M)[0].strip()
    abbb=r'<p>(.*?)<\\/p>'
    out = re.findall(abbb, m_tr, re.S | re.M)
    return {'uid':[uid],'credit_level':[''.join(out)]}
    
def getInfo(uid):
    data1=pd.DataFrame(get_weibo(uid))
    data2=pd.DataFrame(get_userInfo(uid))
    data3=pd.DataFrame(get_xinyong(uid))
    res1=pd.merge(data1,data2,on='uid',how='outer')
    res2=pd.merge(res1,data3,on='uid',how='outer')
    return res2

a=pd.read_excel('转发者抽样203个.xlsx')['user'].astype('str').tolist()
a.remove('6097939320')
b=a[0:3]
res=pd.DataFrame(get_weibo(b[0])) 
x=1
for uid in b:
    print('第'+str(x)+'个'+uid)
    x+=1
    result=getInfo(uid)
    res=res.append(result.copy())
res=res.reset_index(drop=True)
res.drop_duplicates()
res=res.reset_index(drop=True)
res=res.drop([0])
res.to_excel('233.xlsx')

