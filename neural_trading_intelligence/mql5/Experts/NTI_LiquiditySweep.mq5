//+------------------------------------------------------------------+
//| NTI_LiquiditySweep.mq5                                           |
//| Neural Trading Intelligence - XAUUSD liquidity-sweep EA          |
//|                                                                  |
//| Mirrors nti/strategy/liquidity_sweep.py (Python research core).  |
//| SAFETY:                                                          |
//|  * Refuses to trade on REAL accounts (INIT_FAILED). Demo only.   |
//|  * Default mode = OBSERVE: detects and logs, sends no orders.    |
//|  * Stop-loss mandatory; lot never increases after losses;        |
//|    no martingale, no grid, no averaging.                         |
//|  * Kill switch: GlobalVariable "NTI_KILL"=1 or file              |
//|    <Common>\Files\NTI\KILL  -> closes EA positions, blocks entries|
//| Liquidity pools are HYPOTHESES (we cannot see stop orders);      |
//| sweeps are OBSERVED price behaviour.                             |
//+------------------------------------------------------------------+
#property copyright "Neural Trading Intelligence"
#property version   "0.20"
#property description "Liquidity-sweep detector/executor for XAUUSD (XM: GOLD). Demo accounts only."

#include <Trade/Trade.mqh>

enum ENUM_NTI_MODE { NTI_OBSERVE = 0, NTI_DEMO_TRADE = 1 };

input group "Mode"
input ENUM_NTI_MODE   InpMode            = NTI_OBSERVE;   // OBSERVE = no orders
input ENUM_TIMEFRAMES InpTF              = PERIOD_H1;
input long            InpMagic           = 18860001;
input group "Risk (hard limits)"
input double InpRiskPct          = 0.25;  // % equity risked per trade
input double InpMaxDailyLossPct  = 1.0;   // block new trades for the day
input double InpMaxDDPct         = 5.0;   // kill switch from equity peak
input int    InpMaxPositions     = 1;
input double InpMaxSpreadUSD     = 0.60;  // price units (USD/oz)
input bool   InpUseNewsFilter    = true;  // MT5 economic calendar, USD high impact
input int    InpNewsBlackoutMin  = 30;
input group "Strategy"
input int    InpSwingK           = 3;
input double InpMinPenATR        = 0.05;
input double InpMaxPenATR        = 1.5;
input double InpSLBufferATR      = 0.15;
input double InpMaxSLATR         = 2.5;
input double InpRR               = 2.0;
input int    InpMaxHoldBars      = 24;
input int    InpPoolMaxAgeBars   = 240;
input double InpEqTolATR         = 0.15;
input int    InpMinTouches       = 1;
input bool   InpTradeLondon      = true;  // 07-13 UTC
input bool   InpTradeNewYork     = true;  // 13-21 UTC
input bool   InpSkipAbnormalVol  = true;  // ATR percentile >= 97% over 500 bars
input bool   InpTrendFilter      = false; // only trade with H4 structure trend
input int    InpLookback         = 700;
input bool   InpDrawPools        = true;

CTrade   g_trade;
datetime g_lastBar = 0;
string   GV_PEAK, GV_DAYEQ, GV_DAY, GV_KILLED;

//--- helpers --------------------------------------------------------
int GmtOffsetSec()
{
   long d = (long)TimeTradeServer() - (long)TimeGMT();
   return (int)(MathRound(d / 1800.0) * 1800);   // round to 30 min
}

int UtcHour(datetime server_t)
{
   MqlDateTime s; TimeToStruct(server_t - GmtOffsetSec(), s); return s.hour;
}

long UtcDay(datetime server_t) { return (long)((server_t - GmtOffsetSec()) / 86400); }

void Log(string action, string detail)
{
   int h = FileOpen("NTI\\signals.csv", FILE_READ|FILE_WRITE|FILE_CSV|FILE_COMMON|FILE_SHARE_READ, ';');
   if(h == INVALID_HANDLE) { Print("NTI log error ", GetLastError()); return; }
   FileSeek(h, 0, SEEK_END);
   FileWrite(h, TimeToString(TimeGMT(), TIME_DATE|TIME_SECONDS), _Symbol, action, detail);
   FileClose(h);
   Print("NTI | ", action, " | ", detail);
}

// Wilder ATR over rates (oldest first) - identical to nti.analysis.volatility.atr
void WilderATR(const MqlRates &r[], int n, int p, double &out[])
{
   ArrayResize(out, n); ArrayInitialize(out, EMPTY_VALUE);
   double a = 0; double alpha = 1.0 / p; int cnt = 0;
   for(int i = 0; i < n; i++)
   {
      double tr = r[i].high - r[i].low;
      if(i > 0) tr = MathMax(tr, MathMax(MathAbs(r[i].high - r[i-1].close), MathAbs(r[i].low - r[i-1].close)));
      a = (i == 0) ? tr : alpha * tr + (1 - alpha) * a;
      cnt++;
      if(cnt >= p) out[i] = a;
   }
}

bool IsSwingHigh(const MqlRates &r[], int j, int k)
{
   for(int t = j - k; t <= j + k; t++) if(t != j && r[t].high >= r[j].high) return false;
   return true;
}
bool IsSwingLow(const MqlRates &r[], int j, int k)
{
   for(int t = j - k; t <= j + k; t++) if(t != j && r[t].low <= r[j].low) return false;
   return true;
}

// HTF structure trend (+1/-1/0) on closed bars - mirrors nti.analysis.structure
int StructureTrend(ENUM_TIMEFRAMES tf, int k)
{
   MqlRates r[]; ArraySetAsSeries(r, false);
   int n = CopyRates(_Symbol, tf, 1, 300, r);
   if(n < 2 * k + 5) return 0;
   int trend = 0; double sh = 0, sl = 0; bool shOk = false, slOk = false;
   for(int i = 0; i < n; i++)
   {
      int j = i - k;
      if(j >= k)
      {
         if(IsSwingHigh(r, j, k)) { sh = r[j].high; shOk = true; }
         if(IsSwingLow(r, j, k))  { sl = r[j].low;  slOk = true; }
      }
      if(shOk && r[i].close > sh)      { trend = 1;  shOk = false; }
      else if(slOk && r[i].close < sl) { trend = -1; slOk = false; }
   }
   return trend;
}

//--- liquidity pools ----------------------------------------------
struct Pool { double price; int known; int side; string src; };   // side +1 buy-side (above), -1 sell-side

void AddPool(Pool &pools[], double price, int known, int side, string src)
{
   int s = ArraySize(pools); ArrayResize(pools, s + 1);
   pools[s].price = price; pools[s].known = known; pools[s].side = side; pools[s].src = src;
}

// Build pools valid right before the last closed bar (index n-1)
void BuildPools(const MqlRates &r[], int n, Pool &pools[])
{
   ArrayResize(pools, 0);
   int k = InpSwingK;
   for(int j = k; j + k <= n - 2; j++)
   {
      if(IsSwingHigh(r, j, k)) AddPool(pools, r[j].high, j + k, 1, "swing_high");
      if(IsSwingLow(r, j, k))  AddPool(pools, r[j].low,  j + k, -1, "swing_low");
   }
   // previous UTC day high/low, known at first bar of each UTC day
   // and Asia (00-07 UTC) range, known at first bar with UTC hour >= 7
   for(int i = 1; i <= n - 2; i++)
   {
      long d = UtcDay(r[i].time);
      if(d != UtcDay(r[i-1].time))
      {
         double hi = -DBL_MAX, lo = DBL_MAX; bool any = false;
         for(int t = i - 1; t >= 0 && UtcDay(r[t].time) == d - 1; t--) { hi = MathMax(hi, r[t].high); lo = MathMin(lo, r[t].low); any = true; }
         if(any) { AddPool(pools, hi, i, 1, "PDH"); AddPool(pools, lo, i, -1, "PDL"); }
      }
      if(UtcHour(r[i].time) >= 7 && (UtcHour(r[i-1].time) < 7 || UtcDay(r[i-1].time) != d))
      {
         double hi = -DBL_MAX, lo = DBL_MAX; bool any = false;
         for(int t = i - 1; t >= 0 && UtcDay(r[t].time) == d && UtcHour(r[t].time) < 7; t--) { hi = MathMax(hi, r[t].high); lo = MathMin(lo, r[t].low); any = true; }
         if(any) { AddPool(pools, hi, i, 1, "asia_high"); AddPool(pools, lo, i, -1, "asia_low"); }
      }
   }
   // keep only pools still valid: on the right side at birth, not traded through since, not too old
   Pool keep[]; ArrayResize(keep, 0);
   for(int p = 0; p < ArraySize(pools); p++)
   {
      int b = pools[p].known;
      if((n - 2) - b > InpPoolMaxAgeBars) continue;
      if(pools[p].side == 1 && pools[p].price <= r[b].close) continue;
      if(pools[p].side == -1 && pools[p].price >= r[b].close) continue;
      bool swept = false;
      for(int t = b + 1; t <= n - 2 && !swept; t++)
         swept = (pools[p].side == 1) ? (r[t].high > pools[p].price) : (r[t].low < pools[p].price);
      if(!swept) { int s = ArraySize(keep); ArrayResize(keep, s + 1); keep[s] = pools[p]; }
   }
   ArrayResize(pools, ArraySize(keep));
   for(int p = 0; p < ArraySize(keep); p++) pools[p] = keep[p];
}

void DrawPools(const Pool &pools[])
{
   ObjectsDeleteAll(0, "NTI_POOL_");
   if(!InpDrawPools) return;
   for(int p = 0; p < ArraySize(pools); p++)
   {
      string nm = "NTI_POOL_" + IntegerToString(p);
      ObjectCreate(0, nm, OBJ_HLINE, 0, 0, pools[p].price);
      ObjectSetInteger(0, nm, OBJPROP_COLOR, pools[p].side == 1 ? clrTomato : clrDodgerBlue);
      ObjectSetInteger(0, nm, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetString(0, nm, OBJPROP_TEXT, pools[p].src + " (hypothesis)");
   }
}

//--- risk ------------------------------------------------------------
bool KillSwitchOn()
{
   if(GlobalVariableCheck("NTI_KILL") && GlobalVariableGet("NTI_KILL") >= 1) return true;
   if(FileIsExist("NTI\\KILL", FILE_COMMON)) return true;
   return GlobalVariableCheck(GV_KILLED) && GlobalVariableGet(GV_KILLED) >= 1;
}

int OwnPositions()
{
   int c = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagic) c++;
   return c;
}

void CloseOwn(string why)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(PositionSelectByTicket(tk) && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagic)
         if(g_trade.PositionClose(tk)) Log("CLOSE", why + " ticket=" + (string)tk);
   }
}

bool NewsBlackout(string &why)
{
   if(!InpUseNewsFilter || MQLInfoInteger(MQL_TESTER)) return false;  // calendar unavailable in tester
   MqlCalendarValue vals[];
   datetime now = TimeTradeServer();
   datetime a = now - InpNewsBlackoutMin * 60, b = now + InpNewsBlackoutMin * 60;
   if(CalendarValueHistory(vals, a, b, NULL, "USD") <= 0) return false;
   for(int i = 0; i < ArraySize(vals); i++)
   {
      MqlCalendarEvent ev;
      if(CalendarEventById(vals[i].event_id, ev) && ev.importance == CALENDAR_IMPORTANCE_HIGH)
      { why = ev.name + " @ " + TimeToString(vals[i].time); return true; }
   }
   return false;
}

bool RiskAllows(string &why)
{
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   long today = UtcDay(TimeTradeServer());
   if(!GlobalVariableCheck(GV_DAY) || (long)GlobalVariableGet(GV_DAY) != today)
   { GlobalVariableSet(GV_DAY, (double)today); GlobalVariableSet(GV_DAYEQ, eq); }
   double peak = MathMax(eq, GlobalVariableCheck(GV_PEAK) ? GlobalVariableGet(GV_PEAK) : eq);
   GlobalVariableSet(GV_PEAK, peak);
   if(KillSwitchOn()) { why = "kill switch"; return false; }
   if(eq <= peak * (1 - InpMaxDDPct / 100.0))
   { GlobalVariableSet(GV_KILLED, 1); why = "max drawdown reached -> kill switch latched"; CloseOwn(why); return false; }
   if(eq <= GlobalVariableGet(GV_DAYEQ) * (1 - InpMaxDailyLossPct / 100.0)) { why = "daily loss limit"; return false; }
   if(OwnPositions() >= InpMaxPositions) { why = "max positions"; return false; }
   double spread = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(spread > InpMaxSpreadUSD) { why = StringFormat("spread %.2f > %.2f", spread, InpMaxSpreadUSD); return false; }
   string nw;
   if(NewsBlackout(nw)) { why = "news blackout: " + nw; return false; }
   why = "ok"; return true;
}

double LotsForRisk(double entry, double stop)
{
   double dist = MathAbs(entry - stop);
   double tsize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tval  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tval <= 0) tval = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(dist <= 0 || tsize <= 0 || tval <= 0) return 0;
   double lossPerLot = dist / tsize * tval;
   double budget = AccountInfoDouble(ACCOUNT_EQUITY) * InpRiskPct / 100.0;
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lots = MathFloor(budget / lossPerLot / step + 1e-9) * step;   // round DOWN
   if(lots < vmin) return 0;                                            // never round risk UP
   return NormalizeDouble(MathMin(lots, vmax), 2);
}

bool VerifyStops(ulong ticket, double sl, double tp)
{
   if(!PositionSelectByTicket(ticket)) return false;
   double psl = PositionGetDouble(POSITION_SL), ptp = PositionGetDouble(POSITION_TP);
   double tol = 10 * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   return psl > 0 && ptp > 0 && MathAbs(psl - sl) <= tol + MathAbs(sl) * 1e-4 && MathAbs(ptp - tp) <= tol + MathAbs(tp) * 1e-4;
}

void ManageTimeStops()
{
   int secs = PeriodSeconds(InpTF) * InpMaxHoldBars;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(!PositionSelectByTicket(tk)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      if(TimeCurrent() - (datetime)PositionGetInteger(POSITION_TIME) >= secs)
         if(g_trade.PositionClose(tk)) Log("CLOSE", "time stop ticket=" + (string)tk);
   }
}

//--- core -------------------------------------------------------------
void OnNewBar()
{
   MqlRates r[]; ArraySetAsSeries(r, false);
   int n = CopyRates(_Symbol, InpTF, 1, InpLookback, r);     // closed bars only, oldest first
   if(n < 600) { Print("NTI: not enough history (", n, ")"); return; }
   double atr[]; WilderATR(r, n, 14, atr);
   int i = n - 1;                                             // the bar that just closed
   if(atr[i] == EMPTY_VALUE || atr[i] <= 0) return;

   Pool pools[]; BuildPools(r, n, pools); DrawPools(pools);

   // session & regime
   int uh = UtcHour(r[i].time);
   bool sessOk = (InpTradeLondon && uh >= 7 && uh < 13) || (InpTradeNewYork && uh >= 13 && uh < 21);
   int below = 0, cnt = 0;
   for(int t = MathMax(0, i - 499); t <= i; t++) if(atr[t] != EMPTY_VALUE) { cnt++; if(atr[t] <= atr[i]) below++; }
   double pct = cnt > 0 ? (double)below / cnt : 0;
   bool abnormal = cnt >= 70 && pct >= 0.97;

   for(int side = 1; side >= -1; side -= 2)
   {
      double deepest = 0; bool hit = false; string srcs = "";
      for(int p = 0; p < ArraySize(pools); p++)
      {
         if(pools[p].side != side) continue;
         bool h = side == 1 ? r[i].high > pools[p].price : r[i].low < pools[p].price;
         if(!h) continue;
         if(!hit || (side == 1 ? pools[p].price > deepest : pools[p].price < deepest)) deepest = pools[p].price;
         hit = true;
         if(StringFind(srcs, pools[p].src) < 0) srcs += (srcs == "" ? "" : "/") + pools[p].src;
      }
      if(!hit) continue;
      double extreme = side == 1 ? r[i].high : r[i].low;
      double pen = MathAbs(extreme - deepest) / atr[i];
      bool closedBack = side == 1 ? r[i].close < deepest : r[i].close > deepest;
      if(!closedBack || pen < InpMinPenATR || pen > InpMaxPenATR) continue;
      int touches = 0;
      for(int p = 0; p < ArraySize(pools); p++)
         if(pools[p].side == side && MathAbs(pools[p].price - deepest) <= InpEqTolATR * atr[i]) touches++;

      int dir = -side;      // swept buy-side -> short ; swept sell-side -> long
      string ev = StringFormat("dir=%s swept=%s level=%.2f pen=%.2fATR touches=%d utc_hour=%d atr_pct=%.2f",
                               dir == 1 ? "LONG" : "SHORT", srcs, deepest, pen, touches, uh, pct);
      if(!sessOk)                { Log("SKIP", ev + " | outside session"); continue; }
      if(InpSkipAbnormalVol && abnormal) { Log("SKIP", ev + " | abnormal volatility"); continue; }
      if(touches < InpMinTouches) { Log("SKIP", ev + " | touches"); continue; }
      if(InpTrendFilter)
      {
         int tr = StructureTrend(PERIOD_H4, InpSwingK);
         if(tr != dir) { Log("SKIP", ev + StringFormat(" | H4 trend=%d", tr)); continue; }
      }
      double stop = extreme + (dir == 1 ? -1 : 1) * InpSLBufferATR * atr[i];
      if(MathAbs(r[i].close - stop) > InpMaxSLATR * atr[i]) { Log("SKIP", ev + " | stop too wide"); continue; }

      double entry = dir == 1 ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double risk = (entry - stop) * dir;
      if(risk <= 0) { Log("SKIP", ev + " | price already beyond stop"); continue; }
      double tp = entry + dir * InpRR * risk;
      int dg = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
      stop = NormalizeDouble(stop, dg); tp = NormalizeDouble(tp, dg);
      double minDist = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      if(MathAbs(entry - stop) < minDist || MathAbs(tp - entry) < minDist) { Log("SKIP", ev + " | stops level"); continue; }
      ev += StringFormat(" entry=%.2f sl=%.2f tp=%.2f rr=%.1f", entry, stop, tp, InpRR);

      if(InpMode == NTI_OBSERVE) { Log("SIGNAL_OBSERVED", ev); continue; }
      string why;
      if(!RiskAllows(why)) { Log("BLOCKED", ev + " | " + why); continue; }
      double lots = LotsForRisk(entry, stop);
      if(lots <= 0) { Log("BLOCKED", ev + " | lot below minimum for risk budget"); continue; }
      double margin;
      if(OrderCalcMargin(dir == 1 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, _Symbol, lots, entry, margin) &&
         margin > AccountInfoDouble(ACCOUNT_MARGIN_FREE)) { Log("BLOCKED", ev + " | insufficient margin"); continue; }

      bool ok = dir == 1 ? g_trade.Buy(lots, _Symbol, 0, stop, tp, "NTI sweep")
                         : g_trade.Sell(lots, _Symbol, 0, stop, tp, "NTI sweep");
      if(!ok) { Log("ORDER_FAIL", ev + StringFormat(" | retcode=%d %s", g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription())); continue; }
      ulong deal = g_trade.ResultDeal(); ulong pos = 0;
      if(HistoryDealSelect(deal)) pos = (ulong)HistoryDealGetInteger(deal, DEAL_POSITION_ID);
      if(pos == 0 || !VerifyStops(pos, stop, tp))
      {
         Log("STOPS_MISSING", ev + " -> closing position immediately");
         if(pos > 0) g_trade.PositionClose(pos);
         continue;
      }
      Log("ORDER_OPEN", ev + StringFormat(" lots=%.2f ticket=%I64u", lots, pos));
   }
}

int OnInit()
{
   GV_PEAK = "NTI_PEAK_" + (string)InpMagic; GV_DAYEQ = "NTI_DAYEQ_" + (string)InpMagic;
   GV_DAY = "NTI_DAY_" + (string)InpMagic;   GV_KILLED = "NTI_KILLED_" + (string)InpMagic;
   long tm = AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(InpMode == NTI_DEMO_TRADE && tm != ACCOUNT_TRADE_MODE_DEMO)
   {
      Alert("NTI: trading is only allowed on DEMO accounts in this version. EA disabled.");
      return INIT_FAILED;
   }
   if(StringFind(_Symbol, "GOLD") < 0 && StringFind(_Symbol, "XAU") < 0)
      Print("NTI WARNING: designed for gold (XM symbol GOLD). Current symbol: ", _Symbol);
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(30);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   FolderCreate("NTI", FILE_COMMON);
   Log("INIT", StringFormat("mode=%s account=%s demo=%s gmt_offset=%ds tf=%s",
       InpMode == NTI_OBSERVE ? "OBSERVE" : "DEMO_TRADE", AccountInfoString(ACCOUNT_SERVER),
       tm == ACCOUNT_TRADE_MODE_DEMO ? "yes" : "NO", GmtOffsetSec(), EnumToString(InpTF)));
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) { ObjectsDeleteAll(0, "NTI_POOL_"); }

void OnTick()
{
   if(InpMode == NTI_DEMO_TRADE)
   {
      if(KillSwitchOn() && OwnPositions() > 0) CloseOwn("kill switch");
      ManageTimeStops();
   }
   datetime bt = iTime(_Symbol, InpTF, 0);
   if(bt == 0 || bt == g_lastBar) return;
   g_lastBar = bt;
   OnNewBar();
}
//+------------------------------------------------------------------+
