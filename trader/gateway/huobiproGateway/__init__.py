# encoding: UTF-8

from vnpy.trader import vtConstant
from huobiproGateway import HuobiGateway

gatewayClass = HuobiGateway
gatewayName = 'huobi'
gatewayDisplayName = 'HUOBI'
gatewayType = vtConstant.GATEWAYTYPE_BTC
gatewayQryEnabled = True