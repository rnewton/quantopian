''' 
    Coffeshop Investing strategy with solar & wind energy funds to replace 
    foreign market and real-estate funds.
    
    Long only, lazy investing at its finest!
'''
import datetime
import pytz
import pandas as pd

class BalancedEtf:   
    def __init__(self, symbol, target_percent):
        self.symbol = symbol
        self.target_percent = target_percent
        self.limit_price = 0
        self.stop_price = 0
        self.unbalanced = False

def initialize(context):
    context.etfs = [
        BalancedEtf(sid(33652), 0.30), # BND (Vanguard Total Bond Market ETF)
        BalancedEtf(sid(40107), 0.10), # VOO (Vanguard S&P 500 ETF)
        BalancedEtf(sid(25909), 0.10), # VTV (Vanguard Value ETF)
        BalancedEtf(sid(25899), 0.10), # VB  (Vanguard Small-Cap ETF)
        BalancedEtf(sid(25901), 0.10), # VBR (Vanguard Small-Cap Value ETF)
        BalancedEtf(sid(25905), 0.10), # VGT (Vanguard Information Technology ETF)
        BalancedEtf(sid(36057), 0.10), # TAN (Guggenheim Solar ETF)
        BalancedEtf(sid(36416), 0.10)  # FAN (First Trust Global Wind Energy ETF)
    ]

    set_long_only()
    set_commission(commission.PerTrade(cost=1))
    set_slippage(slippage.VolumeShareSlippage(volume_limit=0.25, price_impact=0.1))
    
    schedule_function(func=rebalance, date_rule=date_rules.every_day(), time_rule=time_rules.market_open(minutes=30))
   
def handle_data(context, data):
    # Returns calculation used by Quantopian includes cash added after algorithm start
    # This doesn't allow for an accurate calculation if you fund the account while the
    # algorithm is running
    record(ActualReturns=(context.portfolio.pnl/context.portfolio.positions_value)*100)

'''
    Sets values on each ETF for use in rebalance()
'''
def setup_stats(context, data):
    for etf in context.etfs:
        if etf.symbol in data:
            # If an ETF is going to be sold, set the stop and limit prices to a 10% range
            etf.limit_price = data[etf.symbol].price * 1.10
            etf.stop_price = data[etf.symbol].price * 0.90
            
            # Determine if the ETF is unbalanced compared to the target
            value = context.portfolio.positions[etf.symbol].amount * context.portfolio.positions[etf.symbol].last_sale_price
            current_percent = value / context.portfolio.portfolio_value
            diff = abs((current_percent - etf.target_percent)/((current_percent + etf.target_percent)/2))

            # A 20% difference is a good threshold to rebalance on in order to not lose cash on commission
            if diff > 0.2:
                log.info('{} -- Current: {}% Target: {}%'.format(etf.symbol.security_name, current_percent * 100, etf.target_percent * 100))
                etf.unbalanced = True
            else: 
                etf.unbalanced = False

'''
    Rebalance function for performing actual ETF orders
'''
def rebalance(context, data):
    setup_stats(context, data)
    
    for etf in context.etfs:
        if etf.symbol in data and etf.unbalanced:
            order_target_percent(etf.symbol, etf.target_percent, style=StopLimitOrder(etf.limit_price, etf.stop_price))
    
    if get_open_orders():
        log.info('Rebalanced on {}'.format(pd.Timestamp(get_datetime()).tz_convert('US/Eastern')))
