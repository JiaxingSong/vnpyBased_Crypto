# encoding: UTF-8

from vnpy.trader import vtConstant
from secGateway import SecGateway

gatewayClass = SecGateway
gatewayName = 'SEC'
gatewayDisplayName = u'飞创证券'
gatewayType = vtConstant.GATEWAYTYPE_EQUITY
gatewayQryEnabled = True