import os, numpy as np, pandas as pd
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from threading import Lock
from fastapi.staticfiles import StaticFiles
app=FastAPI(title='Market Intelligence AI',version='1.2.0')
LIVE_QUOTES={}
QUOTE_LOCK=Lock()
BRIDGE_TOKEN=os.getenv('BRIDGE_TOKEN','')
class QuotePayload(BaseModel):
 broker:str='Exness'
 symbol:str
 broker_symbol:str
 bid:float
 ask:float
 time:int

ROOT=os.path.dirname(__file__); app.mount('/static',StaticFiles(directory=ROOT+'/static'),name='static')
SYMS={'XAUUSD':3980.0,'NATGAS':3.45,'EURUSD':1.155,'GBPUSD':1.315,'USDJPY':153.5,'BTCUSD':105000.0}; TFS={'M5':5,'M15':15,'H1':60,'H4':240,'D1':1440}
def demo(symbol,tf,n=350):
 seed=sum(map(ord,symbol+tf)); r=np.random.default_rng(seed); p=SYMS[symbol]; vol={'XAUUSD':.002,'NATGAS':.008,'EURUSD':.0007,'GBPUSD':.0008,'USDJPY':.0006,'BTCUSD':.004}[symbol]; c=p+np.cumsum(r.normal(0,vol*p*.6,n)); o=np.r_[c[0],c[:-1]]; w=np.abs(r.normal(vol*p*.55,vol*p*.2,n)); now=pd.Timestamp.now(tz='UTC'); t=pd.date_range(end=now,periods=n,freq=f'{TFS[tf]}min'); return pd.DataFrame({'time':t,'open':o,'high':np.maximum(o,c)+w,'low':np.minimum(o,c)-w,'close':c,'volume':r.integers(80,1500,n)})
def indicators(d):
 d=d.copy(); c=d.close
 for n in (20,50,200): d[f'ema{n}']=c.ewm(span=n,adjust=False).mean()
 delta=c.diff(); up=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean(); dn=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean(); d['rsi']=100-100/(1+up/dn.replace(0,np.nan))
 pc=c.shift(); tr=pd.concat([d.high-d.low,(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1); d['atr']=tr.ewm(alpha=1/14,adjust=False).mean()
 d['macd']=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean(); d['macds']=d.macd.ewm(span=9,adjust=False).mean()
 mid=c.rolling(20).mean(); sd=c.rolling(20).std(); d['bbu']=mid+2*sd; d['bbl']=mid-2*sd
 d['adx']=((d.high.diff().abs().ewm(alpha=1/14,adjust=False).mean()/(d.atr+1e-9))*100).clip(0,100)
 tp=(d.high+d.low+c)/3; d['vwap']=(tp*d.volume).cumsum()/d.volume.cumsum(); return d.dropna().reset_index(drop=True)
def analyse(d,sym,tf,source):
 d=indicators(d); x=d.iloc[-1]; price=float(x.close); a=float(x.atr); bull=sum([x.ema20>x.ema50,x.close>x.ema200,x.macd>x.macds,50<x.rsi<70]); bear=sum([x.ema20<x.ema50,x.close<x.ema200,x.macd<x.macds,30<x.rsi<50]); direction='BULLISH' if bull>=3 and bull>bear else 'BEARISH' if bear>=3 and bear>bull else 'NEUTRAL'; score=int(max(bull,bear)*25) if direction!='NEUTRAL' else 50
 recent=d.tail(30); hi=float(recent.high.iloc[:-1].max()); lo=float(recent.low.iloc[:-1].min()); struct='Bullish BOS candidate' if x.close>hi else 'Bearish BOS candidate' if x.close<lo else 'No confirmed recent break'
 fvg='No recent FVG candidate'; q=d.iloc[-3:];
 if q.iloc[2].low>q.iloc[0].high:fvg=f'Bullish FVG candidate: {q.iloc[0].high:.5f}–{q.iloc[2].low:.5f}'
 elif q.iloc[2].high<q.iloc[0].low:fvg=f'Bearish FVG candidate: {q.iloc[2].high:.5f}–{q.iloc[0].low:.5f}'
 sample=d.tail(100); fh=float(sample.high.max()); fl=float(sample.low.min()); span=fh-fl
 fib={'Swing high':fh,'Swing low':fl,'23.6%':fh-span*.236,'38.2%':fh-span*.382,'50.0%':fh-span*.5,'61.8%':fh-span*.618,'78.6%':fh-span*.786,'127.2% ext':fl+span*1.272,'161.8% ext':fl+span*1.618}
 body=abs(x.close-x.open); rng=max(x.high-x.low,1e-9); pats=[]
 if body/rng<.1:pats.append('Doji')
 if min(x.open,x.close)-x.low>body*2:pats.append('Hammer candidate')
 if x.high-max(x.open,x.close)>body*2:pats.append('Shooting-star candidate')
 p=d.iloc[-2]
 if x.close>x.open and p.close<p.open and x.close>p.open and x.open<p.close:pats.append('Bullish engulfing')
 if x.close<x.open and p.close>p.open and x.open>p.close and x.close<p.open:pats.append('Bearish engulfing')
 if not pats:pats=['No strong single-candle pattern detected']
 if direction=='BULLISH': stop,t1,t2=price-1.5*a,price+1.5*a,price+2.5*a
 elif direction=='BEARISH':stop,t1,t2=price+1.5*a,price-1.5*a,price-2.5*a
 else:stop=t1=t2=None
 candles=[{'time':str(z.time),'open':float(z.open),'high':float(z.high),'low':float(z.low),'close':float(z.close),'volume':int(z.volume)} for z in d.tail(120).itertuples()]
 return {'symbol':sym,'timeframe':tf,'source':source,'generated_at':datetime.now(timezone.utc).isoformat(),'direction':direction,'confluence_score':score,'score_explanation':'Rule-based confluence score out of 100; NOT a win probability.','latest':{k:float(x[k]) for k in ['close','ema20','ema50','ema200','rsi','macd','macds','atr','adx','vwap','bbu','bbl']},'reasons':[s for s,v in [('EMA20 above EMA50',x.ema20>x.ema50),('Price above EMA200',x.close>x.ema200),('MACD above signal',x.macd>x.macds),('RSI bullish momentum',50<x.rsi<70),('EMA20 below EMA50',x.ema20<x.ema50),('Price below EMA200',x.close<x.ema200),('MACD below signal',x.macd<x.macds),('RSI bearish momentum',30<x.rsi<50)] if v],'structure':struct,'fvg':fvg,'order_block':'No verified institutional order block; candidate zones require manual review.','liquidity_high_estimate':float(recent.high.quantile(.9)),'liquidity_low_estimate':float(recent.low.quantile(.1)),'fibonacci':fib,'patterns':pats,'trade_plan':{'entry_zone':[price-.15*a,price+.15*a] if direction!='NEUTRAL' else None,'stop_loss':stop,'target_1':t1,'target_2':t2,'status':'SETUP CANDIDATE — verify spread, news and candle close' if direction!='NEUTRAL' else 'NO TRADE — insufficient confluence'},'candles':candles,'disclaimer':'Demo prices are synthetic. No guaranteed accuracy or profitability.'}
@app.get('/',response_class=HTMLResponse)
def home(): return open(ROOT+'/static/index.html').read()
@app.get('/api/health')
def health():return {'status':'ok','version':'1.2.0'}
@app.post('/api/bridge/quotes')
def receive_quote(q:QuotePayload, authorization:str|None=Header(default=None)):
 if not BRIDGE_TOKEN: raise HTTPException(503,'Live bridge is not configured on the server')
 if authorization != f'Bearer {BRIDGE_TOKEN}': raise HTTPException(401,'Invalid bridge token')
 if q.bid<=0 or q.ask<=0 or q.ask<q.bid: raise HTTPException(400,'Invalid bid/ask quote')
 item=q.model_dump(); item['received_at']=datetime.now(timezone.utc).isoformat()
 with QUOTE_LOCK: LIVE_QUOTES[q.symbol.upper()] = item
 return {'accepted':True,'symbol':q.symbol.upper(),'received_at':item['received_at']}
@app.get('/api/live-quotes')
def live_quotes():
 with QUOTE_LOCK: return {'quotes':dict(LIVE_QUOTES),"source":"Broker quotes relayed from the MT5 terminal; quote availability depends on the laptop and terminal being online."}
@app.get('/api/market')
def market(symbol:str='XAUUSD',timeframe:str='M15'):
 symbol=symbol.upper(); timeframe=timeframe.upper()
 if symbol not in SYMS or timeframe not in TFS:raise HTTPException(400,'Unsupported symbol or timeframe')
 return analyse(demo(symbol,timeframe),symbol,timeframe,'DEMO DATA — synthetic, not live')
@app.post('/api/analyze-csv')
async def csv(file:UploadFile=File(...),symbol:str='XAUUSD',timeframe:str='M15'):
 try:
  d=pd.read_csv(file.file);d.columns=[x.strip().lower() for x in d.columns]
  if not {'open','high','low','close'}.issubset(d.columns):raise ValueError('CSV requires open, high, low, close columns')
  if 'volume' not in d:d['volume']=1
  if 'time' not in d:d['time']=pd.date_range(end=pd.Timestamp.now(tz='UTC'),periods=len(d),freq='15min')
  else:d['time']=pd.to_datetime(d.time,utc=True,errors='coerce')
  return analyse(d,symbol.upper(),timeframe.upper(),'User-uploaded CSV')
 except Exception as e:raise HTTPException(400,str(e))
