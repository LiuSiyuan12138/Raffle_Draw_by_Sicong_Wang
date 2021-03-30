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
    a= {"name":[name],
            "uid":[id],
            "is_verified":[str(verified)],
            "关注人数":[int(guanzhu)],
            "fan_num":[int(fensi)],
            "gender":[gender],
            "level":[int(urank)]}
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

# ~ def get_infomation(id):
    # ~ d1=get_weibo(id)
    # ~ d1.update(get_userInfo(id))
    # ~ return pd.DataFrame(d1)
    
def get_infomation(id):
    d1=get_weibo(id)
    d2=get_userInfo(id)
    d3={}
    for key,value in d1:
        d3[key]=value
    for key,value in d2:
        d3[key]=value
    return pd.DataFrame(d3)    
    
    


a=pd.read_excel('转发者抽样203个.xlsx')['user'].astype('str').tolist()
a.remove('6097939320')
b=a[160:]
res1=pd.DataFrame(get_weibo(b[0])) 
res2=pd.DataFrame(get_userInfo(b[0]))
x=1

for uid in b:
    print('第'+str(x)+'个'+uid)
    x+=1
    data1=pd.DataFrame(get_weibo(uid))
    res1=pd.concat([res1,data1],axis=0,ignore_index=True)
    data2=pd.DataFrame(get_userInfo(uid))
    res2=pd.concat([res2,data2],axis=0,ignore_index=True)

res1.drop_duplicates('uid','first',inplace=True)
res2.drop_duplicates('uid','first',inplace=True)
res3=pd.merge(res1,res2,on='uid',how='outer')
res3.to_excel('转发者抽样_带特征5.xlsx')

